import os
import json
import openai
import tempfile
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from pydantic import BaseModel
from datetime import datetime, timezone
from dotenv import load_dotenv

from database import Base, get_db
import database
import models
import services
import templates_importer
import validation

# Імпортуємо обидва файли
import field_metadata
import field_groups

load_dotenv()
CODEMIE_API_KEY = os.getenv("CODEMIE_API_KEY")
CODEMIE_PROXY_URL = "https://codemie.lab.epam.com/llms"
Base.metadata.create_all(bind=database.engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"INFO:      Запуск сканування шаблонів...")
    db = database.SessionLocal()
    try:
        db.get_bind().execution_options(isolation_level="SERIALIZABLE")
        templates_importer.run_auto_import(db)
    except Exception as e:
        print(f"ERROR:     Помилка при імпорті шаблонів: {e}")
    finally:
        db.close()
    yield
    print("INFO:      Зупинка сервера.")

app = FastAPI(title="Contract AI Builder", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("storage/templates", exist_ok=True)

# === MODELS ===

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    session_id: str
    user_message: str
    chat_history: list[ChatMessage] = []
    template_code: str = ""

class ExtractFieldsRequest(BaseModel):
    user_message: str
    group_fields: list[str]
    extraction_hint: str

class ConversationalCollectRequest(BaseModel):
    session_id: str
    user_message: str
    chat_history: list[ChatMessage] = []
    current_group_fields: list[str] = []

class ReviewRequest(BaseModel):
    user_message: str
    chat_history: list[ChatMessage] = []

# === HELPERS ===

def get_human_field_name(field_key: str) -> str:
    meta = field_metadata.FIELD_METADATA.get(field_key, {})
    return meta.get("description", field_key)

def get_fallback_question(fields: list[str]) -> str:
    names = [get_human_field_name(f) for f in fields]
    return f"\n\nБудь ласка, вкажіть: {', '.join(names)}?"

# === ENDPOINTS ===

# --- 1. Отримання саммарі (для фінальної перевірки) ---
@app.get("/session/{session_id}/formatted_summary")
def get_formatted_summary(session_id: str, db: Session = Depends(get_db)):
    """Повертає гарно відформатований список відповідей"""
    session = db.query(models.ContractSession).filter(models.ContractSession.id == session_id).first()
    if not session: raise HTTPException(404, "Session not found")
    
    answers = session.answers or {}
    schema = session.template.json_schema
    
    summary_lines = ["📋 **Перевірте ваші дані:**\n"]
    
    for key, value in answers.items():
        human_name = get_human_field_name(key)
        # Якщо в метаданих немає, пробуємо знайти в схемі
        if human_name == key:
             field_info = schema.get(key, {})
             human_name = field_info.get("description", key)
        
        summary_lines.append(f"• {human_name}: **{value}**")
        
    summary_lines.append("\nЧи бажаєте ви щось змінити? Якщо ні — напишіть 'Генеруй', 'Все вірно' або 'Ок'.")
    return {"summary": "\n".join(summary_lines)}

# --- 2. Режим перевірки (Review Mode) ---
class ReviewIntentRequest(BaseModel):
    session_id: str
    user_message: str
    chat_history: list[ChatMessage] = [] # Додали історію для контексту!
    template_code: str

@app.post("/assistant/review_mode")
async def review_mode_chat(req: ReviewIntentRequest, db: Session = Depends(get_db)):
    """
    AI для фінального етапу. Визначає намір:
    1. 'generate' -> користувач погоджується.
    2. 'update' -> користувач хоче змінити поле.
    """
    if not CODEMIE_API_KEY: raise HTTPException(500, "API Key missing")

    # Отримуємо всі поля шаблону, щоб AI знав контекст
    all_fields = field_groups.get_all_required_fields(req.template_code)
    all_fields_desc = field_metadata.get_fields_context(all_fields)

    system_prompt = f"""
Ти — аналізатор фінального етапу заповнення договору.
Користувач перевіряє дані перед генерацією.

ТВОЯ ЗАДАЧА — Визначити намір користувача, враховуючи історію діалогу.

АЛГОРИТМ:
1. Якщо користувач погоджується ("Все ок", "Генеруй", "Так", "Правильно") -> поверни дію "generate".
2. Якщо користувач хоче щось виправити:
   - Якщо чітко вказано поле і нове значення -> "update".
   - Якщо користувач називає тільки значення (наприклад "+380..."), а в минулому повідомленні ти питав про це -> "update".
   - Якщо неясно -> "chat".

СПИСОК ПОЛІВ ШАБЛОНУ:
{all_fields_desc}

ФОРМАТ ВІДПОВІДІ (JSON):
Варіант 1 (Генерація):
{{"action": "generate", "message": "Чудово! Генерую документ..."}}

Варіант 2 (Зміна даних):
{{"action": "update", "fields": {{"key": "new_value"}}, "message": "Зрозумів, змінюємо [назва поля] на [значення]."}}

Варіант 3 (Просто балачки/Уточнення):
{{"action": "chat", "message": "Я не зрозумів. Уточніть, що саме змінити?"}}
"""
    # Формуємо історію для контексту
    messages = [{"role": "system", "content": system_prompt}]
    for m in req.chat_history[-6:]:
        role = "assistant" if m.role in ["bot", "assistant"] else "user"
        messages.append({"role": role, "content": m.content})
    
    messages.append({"role": "user", "content": req.user_message})

    try:
        client = openai.AzureOpenAI(
            api_key=CODEMIE_API_KEY,
            azure_endpoint=CODEMIE_PROXY_URL,
            api_version="2024-02-01"
        )
        response = client.chat.completions.create(
            model="gpt-5-mini-2025-08-07",
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Review Error: {e}")
        return {"action": "chat", "message": "Вибачте, сталася помилка. Спробуйте ще раз."}

# --- Існуючі ендпоінти ---

@app.post("/assistant/chat")
async def chat_with_codemie(request: ChatRequest, db: Session = Depends(get_db)):
    if not CODEMIE_API_KEY:
        raise HTTPException(status_code=500, detail="API Key не налаштовано.")

    system_prompt = r"""
## Роль
Ти — досвідчений український юрист-консультант.

## Правила (СУВОРО):
1. Стиль: Діловий, ввічливий.
2. Табу на технічні терміни.
3. Відповідай ТІЛЬКИ на питання про документи.
   - На офтоп відповідай: "Вибачте, я можу відповідати лише на запитання, пов'язані з документами та юридичною тематикою."
""".strip()

    messages = [{"role": "system", "content": system_prompt}]

    if request.template_code:
        template = db.query(models.ContractTemplate).filter_by(code=request.template_code).first()
        if template:
            messages.append({"role": "system", "content": f"Ми працюємо з документом: '{template.name}'."})

    for m in request.chat_history:
        messages.append({"role": m.role, "content": m.content})

    messages.append({"role": "user", "content": request.user_message})

    try:
        client = openai.AzureOpenAI(
            api_key=CODEMIE_API_KEY,
            azure_endpoint=CODEMIE_PROXY_URL,
            api_version="2024-02-01"
        )
        response = client.chat.completions.create(
            model="gpt-5-mini-2025-08-07",
            messages=messages,
            temperature=0.3
        )
        return {"assistant_reply": response.choices[0].message.content}
    except Exception as e:
        return {"assistant_reply": "Вибачте, сервіс тимчасово недоступний."}

# Модель для уточнення
class ClarifyRequest(BaseModel):
    missing_fields: list[str]
    filled_fields: list[str] = [] 

@app.post("/assistant/clarify")
async def clarify_missing_fields(req: ClarifyRequest):
    if not req.missing_fields:
        return {"message": "Вкажіть дані."}

    # Конвертуємо ключі в людські назви
    missing_human = [get_human_field_name(f) for f in req.missing_fields]
    filled_human = [get_human_field_name(f) for f in req.filled_fields]
    
    missing_str = ", ".join(missing_human)
    filled_str = ", ".join(filled_human) if filled_human else "нічого"

    system_prompt = "Ти — ввічливий асистент ДІЯ. Твоя мета — попросити користувача доввести дані."
    
    user_prompt = f"""
    Ситуація: Користувач заповнював форму.
    Він щойно надав дані для: {filled_str}.
    Але ще НЕ вистачає: {missing_str}.
    
    Завдання:
    1. Підтвердь, що надані дані прийнято (коротко).
    2. Ввічливо попроси надати те, чого не вистачає (використовуй назви: {missing_str}).
    3. Пиши українською, природною мовою. Не використовуй списки, пиши реченням.
    """

    try:
        client = openai.AzureOpenAI(
            api_key=CODEMIE_API_KEY,
            azure_endpoint=CODEMIE_PROXY_URL,
            api_version="2024-02-01"
        )
        response = client.chat.completions.create(
            model="gpt-5-mini-2025-08-07",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return {"message": response.choices[0].message.content}
    except Exception as e:
        print(f"AI Clarify Error: {e}")
        return {"message": f"Дані записано. Будь ласка, додайте ще: {missing_str}."}


@app.post("/assistant/conversational_collect")
async def conversational_collect(request: ConversationalCollectRequest, db: Session = Depends(get_db)):
    if not CODEMIE_API_KEY:
        raise HTTPException(status_code=500, detail="API Key missing")
    session = db.query(models.ContractSession).filter(models.ContractSession.id == request.session_id).first()
    if not session: raise HTTPException(status_code=404, detail="Session not found")

    fields_context = field_metadata.get_fields_context(request.current_group_fields)
    fallback_question = get_fallback_question(request.current_group_fields)

    system_prompt = f"""
Ти — асистент ДІЯ. Твоя задача — зібрати поля:
{fields_context}

ПРАВИЛА:
1. Якщо користувач ставить питання — відповідай.
2. Якщо надає дані — витягни їх (JSON).
3. Якщо даних мало — подякуй і запитай решту.

ВАЖЛИВО (ОФТОП):
Якщо питання не про документи — поверни JSON:
{{"action": "chat", "message": "Вибачте, я можу відповідати лише на запитання, пов'язані з документами. {fallback_question}"}}

ФОРМАТ:
{{"action": "chat", "message": "..."}}
АБО
{{"action": "extract", "fields": {{"field_name": "value"}}}}
""".strip()

    messages = [{"role": "system", "content": system_prompt}]
    for m in request.chat_history[-10:]:
        role = "assistant" if m.role in ["bot", "assistant"] else "user"
        messages.append({"role": role, "content": m.content})
    messages.append({"role": "user", "content": request.user_message})

    try:
        client = openai.AzureOpenAI(
            api_key=CODEMIE_API_KEY,
            azure_endpoint=CODEMIE_PROXY_URL,
            api_version="2024-02-01"
        )
        response = client.chat.completions.create(
            model="gpt-5-mini-2025-08-07",
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Extraction Error: {e}")
        return {
            "action": "chat", 
            "message": f"Вибачте, сталася помилка. {fallback_question}"
        }

@app.post("/session/{session_id}/answer")
def submit_answer(session_id: str, answer_data: dict, skip_validation: bool = False, db: Session = Depends(get_db)):
    session = db.query(models.ContractSession).filter(models.ContractSession.id == session_id).first()
    if not session: raise HTTPException(status_code=404, detail="Session not found")

    current_answers = dict(session.answers) if session.answers else {}
    merged_answers = current_answers.copy()

    clean_data = {}
    for k, v in answer_data.items():
        if v is not None and str(v).strip() != "":
            clean_data[k.lower()] = v
            
    if not clean_data:
         return {"status": "skipped", "current_answers": session.answers}

    merged_answers.update(clean_data)

    if not skip_validation:
        template_code = session.template.code
        is_valid, errors = validation.validate_session_answers(template_code, merged_answers)
        
        if not is_valid:
            relevant_errors = [e for e in errors if e['field'] in clean_data]
            if relevant_errors:
                raise HTTPException(status_code=422, detail={
                    "validation_errors": relevant_errors,
                    "tip": "Будь ласка, перевірте дані та спробуйте ввести їх коректно ще раз."
                })

    session.answers = merged_answers
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(session, "answers")
    db.commit()
    
    return {
        "status": "updated", 
        "current_answers": session.answers,
        "updated_fields": list(clean_data.keys()) 
    }

@app.post("/session/{session_id}/generate")
def generate_contract(session_id: str, db: Session = Depends(get_db)):
    session = db.query(models.ContractSession).filter(models.ContractSession.id == session_id).first()
    if not session: raise HTTPException(status_code=404, detail="Session not found")

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
            tmp_path = tmp_file.name

        services.generate_contract_docx(
            template_path=session.template.docx_path,
            answers=session.answers,
            output_path=tmp_path
        )
        with open(tmp_path, "rb") as f:
            file_content = f.read()
        os.remove(tmp_path)
        session.status = models.SessionStatus.completed
        db.commit()
        
        return Response(
            content=file_content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={session.template.code}.docx"}
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"GENERATE ERROR: {e}") 
        raise HTTPException(500, str(e))

@app.get("/templates")
def get_templates(db: Session = Depends(get_db)):
    return db.query(models.ContractTemplate).all()

@app.post("/start_session")
def start_session(template_code: str, db: Session = Depends(get_db)):
    template = db.query(models.ContractTemplate).filter(models.ContractTemplate.code == template_code).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    new_session = models.ContractSession(template_id=template.id, created_at=datetime.now(timezone.utc))
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    print(f"DEBUG: Starting session for template_code='{template_code}'")

    groups = field_groups.get_group_info(template_code)
    if not groups:
        print(f"DEBUG: Групи для '{template_code}' не знайдені. Fallback до 'nadannya_poslug'...")
        groups = field_groups.get_group_info("nadannya_poslug")

    greeting_intro = f"Вітаю! Я ваш персональний помічник ДІЯ. 🇺🇦\nЯ допоможу вам скласти документ: {template.name}."

    first_question = ""
    if groups and len(groups) > 0:
        first_group = groups[0]
        first_question = first_group.get("prompt") or first_group.get("initial_prompt", "Давайте почнемо заповнення.")
    else:
        first_question = "Давайте почнемо. Введіть, будь ласка, місто та дату укладання договору."

    full_start_message = f"{greeting_intro}\n\n{first_question}"

    return {
        "session_id": str(new_session.id),
        "schema": template.json_schema,
        "field_groups": groups,
        "start_message": full_start_message
    }
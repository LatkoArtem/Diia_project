import shutil
import os
import json
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

# Ваші модулі
from database import engine, Base, get_db
import database  # <-- Додано імпорт модуля database
import models
import services
import templates_importer # <-- Ваш файл імпорту

# Створення таблиць (автоматична міграція для MVP)
Base.metadata.create_all(bind=engine)

# --- LIFESPAN (Заміна on_event) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код при старті сервера
    print("INFO:     Запуск сканування шаблонів...")
    db = database.SessionLocal()
    try:
        # Запускаємо ваш імпортер
        templates_importer.run_auto_import(db)
    except Exception as e:
        print(f"ERROR:    Помилка при імпорті шаблонів: {e}")
    finally:
        db.close()

    yield # Тут працює додаток

    # Код при зупинці (якщо треба)
    print("INFO:     Зупинка сервера.")

app = FastAPI(title="Contract AI Builder", lifespan=lifespan)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Дозволяє запити з будь-якого фронтенду
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Директорії
os.makedirs("storage/templates", exist_ok=True)
os.makedirs("storage/generated", exist_ok=True)

# --- 1. ADMIN: Завантажити шаблон ---
@app.post("/admin/templates")
def create_template(
    name: str = Form(...),
    code: str = Form(...),
    description: str = Form(...),
    json_schema: str = Form(...), # Передаємо як string, потім парсимо
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Зберігаємо файл
    file_location = f"storage/templates/{code}.docx"
    with open(file_location, "wb+") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Зберігаємо в БД
    db_template = models.ContractTemplate(
        name=name,
        code=code,
        description=description,
        json_schema=json.loads(json_schema),
        docx_path=file_location
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

# --- 2. USER: Отримати список шаблонів ---
@app.get("/templates")
def get_templates(db: Session = Depends(get_db)):
    return db.query(models.ContractTemplate).all()

# --- 3. USER: Старт сесії ---
@app.post("/start_session")
def start_session(template_code: str, db: Session = Depends(get_db)):
    template = db.query(models.ContractTemplate).filter(models.ContractTemplate.code == template_code).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    new_session = models.ContractSession(template_id=template.id)
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return {"session_id": str(new_session.id), "schema": template.json_schema}

# --- 4. USER: Відправити відповідь (або всі відповіді разом) ---
@app.post("/session/{session_id}/answer")
def submit_answer(session_id: str, answer_data: dict, db: Session = Depends(get_db)):
    session = db.query(models.ContractSession).filter(models.ContractSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Оновлюємо відповіді (merge)
    current_answers = dict(session.answers) if session.answers else {}
    current_answers.update(answer_data)

    session.answers = current_answers
    # Force update (SQLAlchemy іноді не бачить змін всередині JSON)
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(session, "answers")

    db.commit()
    return {"status": "updated", "current_answers": session.answers}

# --- 5. USER: Генерація документа ---
@app.post("/session/{session_id}/generate")
def generate_contract(session_id: str, db: Session = Depends(get_db)):
    session = db.query(models.ContractSession).filter(models.ContractSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    template = session.template

    # Шлях для нового файлу
    output_filename = f"{session.id}_{template.code}.docx"
    output_path = f"storage/generated/{output_filename}"

    try:
        # Виклик сервісу генерації
        services.generate_contract_docx(
            template_path=template.docx_path,
            answers=session.answers,
            output_path=output_path
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

    # Оновлюємо статус
    session.status = models.SessionStatus.completed

    # Запис в generated_contracts
    gen_contract = models.GeneratedContract(
        session_id=session.id,
        file_path=output_path
    )
    db.add(gen_contract)
    db.commit()

    return {"file_url": f"/download/{output_filename}", "status": "completed"}

# --- 6. Завантаження готового файлу ---
@app.get("/download/{filename}")
def download_file(filename: str):
    path = f"storage/generated/{filename}"
    if os.path.exists(path):
        return FileResponse(path, filename=filename)
    raise HTTPException(status_code=404, detail="File not found")
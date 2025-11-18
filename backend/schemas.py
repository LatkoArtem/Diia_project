from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

# --- TEMPLATES ---

# Базова схема (спільні поля)
class ContractTemplateBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None

# Те, що ми приймаємо при створенні (через API)
class ContractTemplateCreate(ContractTemplateBase):
    json_schema: Dict[str, Any]

# Те, що ми віддаємо на фронтенд (з ID і датою)
class ContractTemplate(ContractTemplateBase):
    id: int
    json_schema: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True  # Дозволяє читати дані прямо з SQLAlchemy моделей

# --- SESSIONS ---

class ContractSessionBase(BaseModel):
    template_code: str

class ContractSession(BaseModel):
    id: str
    template_id: int
    answers: Dict[str, Any]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- ANSWERS ---

class AnswerUpdate(BaseModel):
    answer: Dict[str, Any]
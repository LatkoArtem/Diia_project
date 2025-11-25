import uuid
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from database import Base

class SessionStatus(str, enum.Enum):
    draft = "draft"
    completed = "completed"
    signed = "signed"

class ContractTemplate(Base):
    __tablename__ = "contract_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True)
    json_schema = Column(JSON, nullable=False)
    docx_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

class ContractSession(Base):
    __tablename__ = "contract_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(Integer, ForeignKey("contract_templates.id"))
    user_id = Column(Integer, nullable=True)
    answers = Column(JSON, default={})
    status = Column(Enum(SessionStatus), default=SessionStatus.draft)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    template = relationship("ContractTemplate")

class GeneratedContract(Base):
    __tablename__ = "generated_contracts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("contract_sessions.id"))
    file_path = Column(String, nullable=False)
    signed_file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
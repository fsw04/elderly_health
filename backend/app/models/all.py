import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, JSON, Text
from sqlalchemy.sql import func
from app.db.base_class import Base
from sqlalchemy.orm import relationship

class RoleEnum(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"

class GenderEnum(str, enum.Enum):
    MALE = "M"
    FEMALE = "F"
    UNKNOWN = "U"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    wx_openid = Column(String, unique=True, index=True, nullable=True)
    role = Column(Enum(RoleEnum), default=RoleEnum.USER)
    password_hash = Column(String, nullable=True)
    
    name = Column(String, nullable=True)
    gender = Column(Enum(GenderEnum), default=GenderEnum.UNKNOWN)
    birth_date = Column(String, nullable=True) # YYYY-MM-DD
    id_card = Column(String, nullable=True) # Encrypted ideally
    current_address = Column(String, nullable=True)
    
    device_id = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
class FamilyLinkRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class FamilyLinkRequest(Base):
    __tablename__ = "family_link_requests"
    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"))
    target_phone = Column(String)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    relation_type = Column(String, nullable=True)
    status = Column(Enum(FamilyLinkRequestStatus), default=FamilyLinkRequestStatus.PENDING)
    note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FamilyLink(Base):
    __tablename__ = "family_links"
    id = Column(Integer, primary_key=True, index=True)
    elderly_id = Column(Integer, ForeignKey("users.id"))
    family_id = Column(Integer, ForeignKey("users.id"))
    relation_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SessionStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"

class ExamSession(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True) # sessionId from device
    user_id = Column(Integer, ForeignKey("users.id"))
    device_id = Column(String)
    status = Column(Enum(SessionStatus), default=SessionStatus.IN_PROGRESS)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    vitals_data = Column(JSON, nullable=True)
    ecg_present = Column(Boolean, default=False)
    ecg_data_complete = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    content_json = Column(JSON)
    risk_level = Column(String) # low, medium, high
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ReminderTaskStatus(str, enum.Enum):
    OPEN = "open"
    DONE = "done"

class ReminderTaskType(str, enum.Enum):
    NO_EXAM_3M = "NO_EXAM_3M"
    NO_EXAM_6M = "NO_EXAM_6M"

class ReminderTask(Base):
    __tablename__ = "reminder_tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(Enum(ReminderTaskType))
    status = Column(Enum(ReminderTaskStatus), default=ReminderTaskStatus.OPEN)
    handled_by = Column(Integer, ForeignKey("users.id"), nullable=True) # Admin ID
    handle_action = Column(String, nullable=True)
    handle_note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    content = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)
    target_type = Column(String)
    target_id = Column(String)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.all import GenderEnum

class Token(BaseModel):
    token: str
    expiresAt: datetime
    needBindPhone: bool

class LoginRequest(BaseModel):
    code: str

class SMSSendRequest(BaseModel):
    phone: str
    scene: str

class BindPhoneRequest(BaseModel):
    phone: str
    smsCode: str

class AccountLoginRequest(BaseModel):
    phone: str

class AccountRegisterRequest(BaseModel):
    phone: str
    name: str
    gender: GenderEnum
    birthDate: str
    currentAddress: Optional[str] = None

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    birthDate: Optional[str] = None
    idCard: Optional[str] = None
    currentAddress: Optional[str] = None

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    phone: Optional[str]
    name: Optional[str]
    gender: Optional[GenderEnum]
    age: Optional[int] = None
    birthDate: Optional[str] = Field(default=None, alias="birth_date")
    idCard: Optional[str] = Field(default=None, alias="id_card")
    currentAddress: Optional[str] = Field(default=None, alias="current_address")

class FamilyLinkRequestCreate(BaseModel):
    targetPhone: str
    relationType: Optional[str] = None

class FamilyLinkRequestReview(BaseModel):
    note: Optional[str] = None

class SubscribeSettingItem(BaseModel):
    templateKey: str
    status: str

class SubscribeSettingsPayload(BaseModel):
    settings: List[SubscribeSettingItem]

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminUserCreate(BaseModel):
    phone: str
    name: Optional[str] = None
    gender: Optional[GenderEnum] = GenderEnum.UNKNOWN
    birthDate: Optional[str] = None
    idCard: Optional[str] = None
    currentAddress: Optional[str] = None

class AdminUserUpdate(BaseModel):
    phone: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[GenderEnum] = None
    birthDate: Optional[str] = None
    idCard: Optional[str] = None
    currentAddress: Optional[str] = None

class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    sessionId: str = Field(alias="session_id")
    userId: int = Field(alias="user_id")
    contentJson: Dict[str, Any] = Field(alias="content_json")
    riskLevel: str = Field(alias="risk_level")
    createdAt: datetime = Field(alias="created_at")

class AdminReportDoctorSummaryUpdate(BaseModel):
    height: Optional[str] = None
    weight: Optional[str] = None
    bmi: Optional[str] = None
    bloodPressure: Optional[str] = None
    fastingBloodGlucose: Optional[str] = None
    ecgFinding: Optional[str] = None
    bUltrasound: Optional[str] = None
    tcmConstitution: Optional[str] = None

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    userId: int = Field(alias="user_id")
    title: str
    content: str
    isRead: bool = Field(alias="is_read")
    createdAt: datetime = Field(alias="created_at")

class FamilyLinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    elderlyId: int = Field(alias="elderly_id")
    familyId: int = Field(alias="family_id")
    relationType: Optional[str] = Field(default=None, alias="relation_type")
    createdAt: datetime = Field(alias="created_at")

class FamilyLinkRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    requesterId: int = Field(alias="requester_id")
    targetPhone: str = Field(alias="target_phone")
    targetUserId: Optional[int] = Field(default=None, alias="target_user_id")
    relationType: Optional[str] = Field(default=None, alias="relation_type")
    status: str
    note: Optional[str] = None
    createdAt: datetime = Field(alias="created_at")

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    userId: int = Field(alias="user_id")
    deviceId: Optional[str] = Field(default=None, alias="device_id")
    status: str
    startTime: Optional[datetime] = Field(default=None, alias="start_time")
    endTime: Optional[datetime] = Field(default=None, alias="end_time")
    vitalsData: Optional[Dict[str, Any]] = Field(default=None, alias="vitals_data")
    ecgPresent: bool = Field(alias="ecg_present")
    ecgDataComplete: bool = Field(alias="ecg_data_complete")
    createdAt: datetime = Field(alias="created_at")

class ReminderTaskHandle(BaseModel):
    action: str
    channel: str
    note: Optional[str] = None

class ReminderTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    userId: int = Field(alias="user_id")
    type: str
    status: str
    handledBy: Optional[int] = Field(default=None, alias="handled_by")
    handleAction: Optional[str] = Field(default=None, alias="handle_action")
    handleNote: Optional[str] = Field(default=None, alias="handle_note")
    createdAt: datetime = Field(alias="created_at")
    updatedAt: Optional[datetime] = Field(default=None, alias="updated_at")

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    adminId: int = Field(alias="admin_id")
    action: str
    targetType: str = Field(alias="target_type")
    targetId: str = Field(alias="target_id")
    details: Optional[Dict[str, Any]] = None
    createdAt: datetime = Field(alias="created_at")

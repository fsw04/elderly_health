from copy import deepcopy
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_, select
import re
from app.api.deps import get_db, get_current_admin
from app.schemas.all import *
from app.models.all import (
    AuditLog,
    ExamSession,
    Notification,
    ReminderTask,
    ReminderTaskStatus,
    Report,
    RoleEnum,
    User,
)
from app.core.security import create_access_token, verify_password

router = APIRouter()


def ok(data: Any = None):
    return {"code": "OK", "data": data}


def paginate(items: list[Any], page: int, page_size: int, total: int):
    return ok(
        {
            "page": page,
            "pageSize": page_size,
            "total": total,
            "items": items,
        }
    )


def serialize_user(user: User):
    payload = UserProfileResponse.model_validate(user).model_dump()
    payload["age"] = calc_age_from_birth_date(user.birth_date)
    return payload


def calc_age_from_birth_date(birth_date: str | None) -> int | None:
    raw = (birth_date or "").strip()
    if not raw:
        return None
    normalized = raw.replace("-", "")
    if not re.fullmatch(r"\d{8}", normalized):
        return None
    try:
        dt = datetime.strptime(normalized, "%Y%m%d")
    except ValueError:
        return None
    today = datetime.utcnow().date()
    age = today.year - dt.year - ((today.month, today.day) < (dt.month, dt.day))
    return age if age >= 0 else None


def serialize_report(report: Report):
    return ReportResponse.model_validate(report).model_dump()


def normalize_text_field(value: str | None) -> str:
    return (value or "").strip()


def normalize_doctor_summary_value(key: str, value: str | None) -> str:
    val = normalize_text_field(value)
    if not val:
        return ""
    lowered = val.lower()

    if key == "height":
        if "cm" not in lowered and re.fullmatch(r"\d+(\.\d+)?", val):
            return f"{val} cm"
    elif key == "weight":
        if "kg" not in lowered and re.fullmatch(r"\d+(\.\d+)?", val):
            return f"{val} kg"
    elif key == "bmi":
        if "kg/m" not in lowered and re.fullmatch(r"\d+(\.\d+)?", val):
            return f"{val} kg/m²"
    elif key == "bloodPressure":
        if "mmhg" not in lowered and re.fullmatch(r"\d+\s*/\s*\d+", val):
            return f"{val} mmHg"
    elif key == "fastingBloodGlucose":
        if "mmol/l" not in lowered and re.fullmatch(r"\d+(\.\d+)?", val):
            return f"{val} mmol/L"

    return val


def serialize_session(session: ExamSession):
    return SessionResponse.model_validate(session).model_dump()


def serialize_task(task: ReminderTask):
    return ReminderTaskResponse.model_validate(task).model_dump()


def serialize_audit(item: AuditLog):
    return AuditLogResponse.model_validate(item).model_dump()


async def write_audit(
    db: AsyncSession,
    admin_id: int,
    action: str,
    target_type: str,
    target_id: str,
    details: dict[str, Any] | None = None,
):
    db.add(
        AuditLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
        )
    )


def validate_admin_user_payload(req: AdminUserCreate | AdminUserUpdate):
    phone = getattr(req, "phone", None)
    birth_date = getattr(req, "birthDate", None)
    id_card = getattr(req, "idCard", None)

    if phone is not None and not re.fullmatch(r"\d{11}", phone):
        raise HTTPException(status_code=422, detail="手机号必须是11位数字")

    if birth_date:
        try:
            datetime.strptime(birth_date, "%Y%m%d")
        except ValueError:
            raise HTTPException(status_code=422, detail="出生日期格式必须为YYYYMMDD")

    if id_card:
        # 支持15位数字，或18位（最后一位可X/x）
        if not re.fullmatch(r"(\d{15}|\d{17}[\dXx])", id_card):
            raise HTTPException(status_code=422, detail="证件号格式不正确")

@router.post("/login", response_model=Token)
async def admin_login(req: AdminLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.phone == req.username, User.role == RoleEnum.ADMIN)
    res = await db.execute(stmt)
    user = res.scalars().first()
    
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token_expires = timedelta(days=1)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return Token(
        token=access_token,
        expiresAt=datetime.utcnow() + access_token_expires,
        needBindPhone=False
    )

@router.get("/users")
async def get_users(q: str = "", page: int = 1, pageSize: int = 10, current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.role == RoleEnum.USER)
    if q:
        stmt = stmt.where(
            or_(
                User.name.contains(q),
                User.phone.contains(q),
                User.id_card.contains(q),
                User.current_address.contains(q),
            )
        )
    stmt = stmt.order_by(User.created_at.desc())
    res = await db.execute(stmt)
    all_users = res.scalars().all()
    users = all_users[(page - 1) * pageSize : page * pageSize]

    return paginate([serialize_user(u) for u in users], page, pageSize, len(all_users))


@router.post("/users")
async def create_user(
    req: AdminUserCreate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    validate_admin_user_payload(req)
    user = User(
        phone=req.phone,
        name=req.name,
        gender=req.gender,
        birth_date=req.birthDate,
        id_card=req.idCard,
        current_address=req.currentAddress,
        role=RoleEnum.USER,
    )
    db.add(user)
    await db.flush()
    await write_audit(db, current_admin.id, "create_user", "user", str(user.id), req.model_dump())
    await db.commit()
    await db.refresh(user)
    return ok(serialize_user(user))


@router.get("/users/{id}")
async def get_user_detail(
    id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.id == id, User.role == RoleEnum.USER)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await write_audit(db, current_admin.id, "read_user", "user", str(id))
    await db.commit()
    return ok(serialize_user(user))


@router.put("/users/{id}")
async def update_user(
    id: int,
    req: AdminUserUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    validate_admin_user_payload(req)
    stmt = select(User).where(User.id == id, User.role == RoleEnum.USER)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.phone is not None:
        user.phone = req.phone
    if req.name is not None:
        user.name = req.name
    if req.gender is not None:
        user.gender = req.gender
    if req.birthDate is not None:
        user.birth_date = req.birthDate
    if req.idCard is not None:
        user.id_card = req.idCard
    if req.currentAddress is not None:
        user.current_address = req.currentAddress
    db.add(user)
    await write_audit(db, current_admin.id, "update_user", "user", str(id), req.model_dump(exclude_none=True))
    await db.commit()
    await db.refresh(user)
    return ok(serialize_user(user))


@router.delete("/users/{id}")
async def delete_user(
    id: int,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.id == id, User.role == RoleEnum.USER)
    res = await db.execute(stmt)
    user = res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await write_audit(db, current_admin.id, "delete_user", "user", str(id))
    await db.commit()
    return {"code": "OK"}


@router.get("/users/{id}/sessions")
async def get_user_sessions(
    id: int,
    page: int = 1,
    pageSize: int = 10,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExamSession).where(ExamSession.user_id == id).order_by(ExamSession.created_at.desc())
    res = await db.execute(stmt)
    all_items = res.scalars().all()
    items = all_items[(page - 1) * pageSize : page * pageSize]
    return paginate([serialize_session(item) for item in items], page, pageSize, len(all_items))


@router.get("/users/{id}/reports")
async def get_user_reports(
    id: int,
    page: int = 1,
    pageSize: int = 10,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Report).where(Report.user_id == id).order_by(Report.created_at.desc())
    res = await db.execute(stmt)
    all_items = res.scalars().all()
    items = all_items[(page - 1) * pageSize : page * pageSize]
    return paginate([serialize_report(item) for item in items], page, pageSize, len(all_items))


@router.get("/users/{id}/reminders")
async def get_user_reminders(
    id: int,
    page: int = 1,
    pageSize: int = 10,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ReminderTask).where(ReminderTask.user_id == id).order_by(ReminderTask.created_at.desc())
    res = await db.execute(stmt)
    all_items = res.scalars().all()
    items = all_items[(page - 1) * pageSize : page * pageSize]
    return paginate([serialize_task(item) for item in items], page, pageSize, len(all_items))

@router.get("/reports")
async def get_admin_reports(
    from_: str = Query(default="", alias="from"),
    to: str = "",
    riskLevel: str = "",
    q: str = "",
    page: int = 1,
    pageSize: int = 10,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Report)
    if riskLevel:
        stmt = stmt.where(Report.risk_level == riskLevel)
    if from_:
        stmt = stmt.where(Report.created_at >= from_)
    if to:
        stmt = stmt.where(Report.created_at <= to)
    if q:
        user_stmt = select(User.id).where(or_(User.name.contains(q), User.phone.contains(q)))
        user_res = await db.execute(user_stmt)
        user_ids = user_res.scalars().all()
        if user_ids:
            stmt = stmt.where(Report.user_id.in_(user_ids))
    stmt = stmt.order_by(Report.created_at.desc())
    res = await db.execute(stmt)
    all_reports = res.scalars().all()
    reports = all_reports[(page - 1) * pageSize : page * pageSize]

    return paginate([serialize_report(r) for r in reports], page, pageSize, len(all_reports))


@router.get("/reports/{reportId}")
async def get_admin_report_detail(
    reportId: str,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Report).where(Report.id == reportId)
    res = await db.execute(stmt)
    report = res.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await write_audit(db, current_admin.id, "read_report", "report", reportId)
    await db.commit()
    return ok(serialize_report(report))


@router.put("/reports/{reportId}/doctor-summary")
async def update_admin_report_doctor_summary(
    reportId: str,
    req: AdminReportDoctorSummaryUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Report).where(Report.id == reportId)
    res = await db.execute(stmt)
    report = res.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Use deep copies to ensure SQLAlchemy can detect JSON field changes.
    content = deepcopy(report.content_json) if isinstance(report.content_json, dict) else {}
    doctor_summary = content.get("doctorSummary")
    if not isinstance(doctor_summary, dict):
        doctor_summary = {}
    else:
        doctor_summary = deepcopy(doctor_summary)

    payload = req.model_dump()
    for key, value in payload.items():
        doctor_summary[key] = normalize_doctor_summary_value(key, value)

    content["doctorSummary"] = doctor_summary
    report.content_json = content
    db.add(report)
    await write_audit(
        db,
        current_admin.id,
        "update_report_doctor_summary",
        "report",
        reportId,
        payload,
    )
    await db.commit()
    await db.refresh(report)
    return ok(serialize_report(report))

@router.get("/reminder-tasks")
async def get_reminder_tasks(status: str = "open", type: str = "", q: str = "", page: int = 1, pageSize: int = 10, current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    stmt = select(ReminderTask).where(ReminderTask.status == status)
    if type:
        stmt = stmt.where(ReminderTask.type == type)
    if q:
        user_stmt = select(User.id).where(or_(User.name.contains(q), User.phone.contains(q)))
        user_res = await db.execute(user_stmt)
        user_ids = user_res.scalars().all()
        if user_ids:
            stmt = stmt.where(ReminderTask.user_id.in_(user_ids))
    stmt = stmt.order_by(ReminderTask.created_at.desc())
    res = await db.execute(stmt)
    all_tasks = res.scalars().all()
    tasks = all_tasks[(page - 1) * pageSize : page * pageSize]

    await write_audit(db, current_admin.id, "read_reminder_tasks", "reminder_tasks", "list")
    await db.commit()

    return paginate([serialize_task(t) for t in tasks], page, pageSize, len(all_tasks))

@router.post("/reminder-tasks/{taskId}/handle")
async def handle_reminder_task(taskId: int, req: ReminderTaskHandle, current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    stmt = select(ReminderTask).where(ReminderTask.id == taskId)
    res = await db.execute(stmt)
    task = res.scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = ReminderTaskStatus.DONE
    task.handled_by = current_admin.id
    task.handle_action = req.action
    task.handle_note = req.note
    db.add(task)

    db.add(
        Notification(
            user_id=task.user_id,
            title="体检提醒",
            content=f"医生已通过{req.channel}处理你的未体检提醒，动作：{req.action}",
        )
    )
    await write_audit(
        db,
        current_admin.id,
        "handle_reminder_task",
        "reminder_task",
        str(taskId),
        req.model_dump(),
    )
    await db.commit()
    return {"code": "OK"}


@router.get("/audit")
async def get_audit_logs(
    targetType: str | None = Query(default=None, alias="targetType"),
    targetId: str | None = Query(default=None, alias="targetId"),
    page: int = 1,
    pageSize: int = 10,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
    if targetType:
        stmt = stmt.where(AuditLog.target_type == targetType)
    if targetId:
        stmt = stmt.where(AuditLog.target_id == targetId)
    res = await db.execute(stmt)
    all_items = res.scalars().all()
    items = all_items[(page - 1) * pageSize : page * pageSize]
    return paginate([serialize_audit(item) for item in items], page, pageSize, len(all_items))

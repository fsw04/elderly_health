import re
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from app.api.deps import get_db, get_current_user
from app.schemas.all import *
from app.models.all import (
    FamilyLink,
    FamilyLinkRequest,
    FamilyLinkRequestStatus,
    Notification,
    Report,
    User,
)
from app.core.security import create_access_token

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


def serialize_report(report: Report):
    return ReportResponse.model_validate(report).model_dump()


def serialize_notification(notification: Notification):
    return NotificationResponse.model_validate(notification).model_dump()


def serialize_family_link_request(item: FamilyLinkRequest):
    return FamilyLinkRequestResponse.model_validate(item).model_dump()


def serialize_family_link(item: FamilyLink):
    return FamilyLinkResponse.model_validate(item).model_dump()


def is_valid_phone(phone: str) -> bool:
    return bool(re.fullmatch(r"1\d{10}", phone or ""))


def is_valid_birth_date(birth_date: str) -> bool:
    if not re.fullmatch(r"\d{8}", birth_date or ""):
        return False
    try:
        datetime.strptime(birth_date, "%Y%m%d")
        return True
    except ValueError:
        return False


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

@router.post("/login", response_model=Token)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Mocking WX login
    wx_openid = f"mock_openid_{req.code}"
    stmt = select(User).where(User.wx_openid == wx_openid)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        user = User(wx_openid=wx_openid)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    access_token_expires = timedelta(days=7)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return Token(
        token=access_token,
        expiresAt=datetime.utcnow() + access_token_expires,
        needBindPhone=user.phone is None
    )


@router.post("/account/login", response_model=Token)
async def account_login(req: AccountLoginRequest, db: AsyncSession = Depends(get_db)):
    phone = (req.phone or "").strip()
    if not is_valid_phone(phone):
        raise HTTPException(status_code=400, detail="PHONE_FORMAT_INVALID")

    stmt = select(User).where(User.phone == phone)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="ACCOUNT_NOT_FOUND")

    access_token_expires = timedelta(days=7)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return Token(
        token=access_token,
        expiresAt=datetime.utcnow() + access_token_expires,
        needBindPhone=False,
    )


@router.post("/account/register", response_model=Token)
async def account_register(req: AccountRegisterRequest, db: AsyncSession = Depends(get_db)):
    phone = (req.phone or "").strip()
    name = (req.name or "").strip()
    birth_date = (req.birthDate or "").strip()

    if not is_valid_phone(phone):
        raise HTTPException(status_code=400, detail="PHONE_FORMAT_INVALID")
    if not name:
        raise HTTPException(status_code=400, detail="NAME_REQUIRED")
    if not is_valid_birth_date(birth_date):
        raise HTTPException(status_code=400, detail="BIRTH_DATE_INVALID")

    stmt = select(User).where(User.phone == phone)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="ACCOUNT_EXISTS")

    user = User(
        phone=phone,
        name=name,
        gender=req.gender,
        birth_date=birth_date,
        current_address=(req.currentAddress or "").strip() or None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token_expires = timedelta(days=7)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return Token(
        token=access_token,
        expiresAt=datetime.utcnow() + access_token_expires,
        needBindPhone=False,
    )

@router.post("/sms/send")
async def send_sms(req: SMSSendRequest, db: AsyncSession = Depends(get_db)):
    # Mock sending SMS
    return {"code": "OK"}

@router.post("/bind-phone")
async def bind_phone(req: BindPhoneRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if req.smsCode != "123456": # Mock validation
        raise HTTPException(status_code=400, detail="SMS_400_CODE_INVALID")
    current_user.phone = req.phone
    db.add(current_user)
    await db.commit()
    return {"code": "OK"}

@router.get("/me", response_model=UserProfileResponse)
async def read_me(current_user: User = Depends(get_current_user)):
    return serialize_user(current_user)

@router.put("/me", response_model=UserProfileResponse)
async def update_me(req: UserProfileUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if req.name is not None: current_user.name = req.name
    if req.gender is not None: current_user.gender = req.gender
    if req.birthDate is not None: current_user.birth_date = req.birthDate
    if req.idCard is not None: current_user.id_card = req.idCard
    if req.currentAddress is not None: current_user.current_address = req.currentAddress
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return serialize_user(current_user)

@router.get("/home")
async def get_home(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    report_stmt = (
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    report_result = await db.execute(report_stmt)
    recent_report = report_result.scalars().first()

    notif_stmt = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    )
    notif_result = await db.execute(notif_stmt)
    unread_notifs = len(notif_result.scalars().all())

    request_stmt = select(FamilyLinkRequest).where(
        FamilyLinkRequest.target_user_id == current_user.id,
        FamilyLinkRequest.status == FamilyLinkRequestStatus.PENDING,
    )
    request_result = await db.execute(request_stmt)
    pending_requests = len(request_result.scalars().all())

    return ok(
        {
            "me": serialize_user(current_user),
            "counters": {
                "unreadNotifs": unread_notifs,
                "pendingFamilyRequests": pending_requests,
            },
            "recentReport": serialize_report(recent_report) if recent_report else None,
        }
    )

@router.get("/reports")
async def get_reports(
    page: int = 1, pageSize: int = 10, onlyAbnormal: int = 0, targetUserId: int = None,
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    query_user_id = current_user.id
    if targetUserId:
        # Check family link
        stmt = select(FamilyLink).where(FamilyLink.elderly_id == targetUserId, FamilyLink.family_id == current_user.id)
        res = await db.execute(stmt)
        if not res.scalars().first():
            raise HTTPException(status_code=403, detail="AUTH_403_FORBIDDEN")
        query_user_id = targetUserId
        
    stmt = select(Report).where(Report.user_id == query_user_id)
    if onlyAbnormal == 1:
        stmt = stmt.where(Report.risk_level.in_(["medium", "high"]))
    count_result = await db.execute(stmt)
    all_reports = count_result.scalars().all()
    reports = all_reports[(page - 1) * pageSize : page * pageSize]

    return paginate([serialize_report(r) for r in reports], page, pageSize, len(all_reports))


@router.get("/reports/{reportId}")
async def get_report_detail(
    reportId: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Report).where(Report.id == reportId)
    result = await db.execute(stmt)
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    allowed = report.user_id == current_user.id
    if not allowed:
        link_stmt = select(FamilyLink).where(
            FamilyLink.elderly_id == report.user_id,
            FamilyLink.family_id == current_user.id,
        )
        link_result = await db.execute(link_stmt)
        allowed = link_result.scalars().first() is not None
    if not allowed:
        raise HTTPException(status_code=403, detail="AUTH_403_FORBIDDEN")

    return ok(serialize_report(report))


@router.get("/notifications")
async def get_notifications(
    page: int = 1,
    pageSize: int = 10,
    onlyUnread: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Notification).where(Notification.user_id == current_user.id)
    if onlyUnread == 1:
        stmt = stmt.where(Notification.is_read.is_(False))
    stmt = stmt.order_by(Notification.created_at.desc())
    result = await db.execute(stmt)
    all_items = result.scalars().all()
    items = all_items[(page - 1) * pageSize : page * pageSize]
    return paginate(
        [serialize_notification(item) for item in items],
        page,
        pageSize,
        len(all_items),
    )


@router.post("/notifications/{id}/read")
async def mark_notification_read(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Notification).where(Notification.id == id)
    result = await db.execute(stmt)
    notification = result.scalars().first()
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.add(notification)
    await db.commit()
    return {"code": "OK"}


@router.post("/notifications/read-all")
async def mark_notifications_read_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Notification).where(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    )
    result = await db.execute(stmt)
    notifications = result.scalars().all()
    for item in notifications:
        item.is_read = True
        db.add(item)
    await db.commit()
    return {"code": "OK"}


@router.post("/subscribe-settings")
async def save_subscribe_settings(
    req: SubscribeSettingsPayload,
    current_user: User = Depends(get_current_user),
):
    # MVP阶段仅返回成功，后续可落库存储授权状态。
    return ok({"userId": current_user.id, "settings": [item.model_dump() for item in req.settings]})

@router.post("/family-link-requests")
async def request_family_link(req: FamilyLinkRequestCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.phone == req.targetPhone)
    res = await db.execute(stmt)
    target_user = res.scalars().first()

    existing_stmt = select(FamilyLinkRequest).where(
        FamilyLinkRequest.requester_id == current_user.id,
        FamilyLinkRequest.target_phone == req.targetPhone,
        FamilyLinkRequest.status == FamilyLinkRequestStatus.PENDING,
    )
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalars().first():
        raise HTTPException(status_code=409, detail="FAM_409_PENDING_EXISTS")

    flr = FamilyLinkRequest(
        requester_id=current_user.id,
        target_phone=req.targetPhone,
        target_user_id=target_user.id if target_user else None,
        relation_type=req.relationType,
        status=FamilyLinkRequestStatus.PENDING
    )
    db.add(flr)
    await db.commit()
    return {"code": "OK"}


@router.get("/family-link-requests")
async def get_family_link_requests(
    role: str = Query(default="target"),
    status: str | None = Query(default=None),
    page: int = 1,
    pageSize: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FamilyLinkRequest)
    if role == "target":
        target_filters = [FamilyLinkRequest.target_user_id == current_user.id]
        if current_user.phone:
            target_filters.append(FamilyLinkRequest.target_phone == current_user.phone)
        stmt = stmt.where(or_(*target_filters))
    else:
        stmt = stmt.where(FamilyLinkRequest.requester_id == current_user.id)
    if status:
        stmt = stmt.where(FamilyLinkRequest.status == status)
    stmt = stmt.order_by(FamilyLinkRequest.created_at.desc())
    result = await db.execute(stmt)
    all_items = result.scalars().all()
    items = all_items[(page - 1) * pageSize : page * pageSize]
    return paginate(
        [serialize_family_link_request(item) for item in items],
        page,
        pageSize,
        len(all_items),
    )


@router.post("/family-link-requests/{requestId}/approve")
async def approve_family_link_request(
    requestId: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FamilyLinkRequest).where(FamilyLinkRequest.id == requestId)
    result = await db.execute(stmt)
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    if item.status != FamilyLinkRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="FAM_410_REQUEST_EXPIRED")
    if item.target_user_id not in (None, current_user.id) and item.target_phone != current_user.phone:
        raise HTTPException(status_code=403, detail="AUTH_403_FORBIDDEN")

    item.target_user_id = current_user.id
    item.status = FamilyLinkRequestStatus.APPROVED
    db.add(item)

    link = FamilyLink(
        elderly_id=current_user.id,
        family_id=item.requester_id,
        relation_type=item.relation_type,
    )
    db.add(link)

    notification = Notification(
        user_id=item.requester_id,
        title="家属绑定已通过",
        content=f"{current_user.name or current_user.phone or '老人用户'} 已同意你的绑定申请",
    )
    db.add(notification)
    await db.commit()
    return {"code": "OK"}


@router.post("/family-link-requests/{requestId}/reject")
async def reject_family_link_request(
    requestId: int,
    req: FamilyLinkRequestReview,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FamilyLinkRequest).where(FamilyLinkRequest.id == requestId)
    result = await db.execute(stmt)
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    if item.target_user_id not in (None, current_user.id) and item.target_phone != current_user.phone:
        raise HTTPException(status_code=403, detail="AUTH_403_FORBIDDEN")
    item.target_user_id = current_user.id
    item.status = FamilyLinkRequestStatus.REJECTED
    item.note = req.note
    db.add(item)
    await db.commit()
    return {"code": "OK"}


@router.post("/family-link-requests/{requestId}/cancel")
async def cancel_family_link_request(
    requestId: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FamilyLinkRequest).where(
        FamilyLinkRequest.id == requestId,
        FamilyLinkRequest.requester_id == current_user.id,
    )
    result = await db.execute(stmt)
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Request not found")
    item.status = FamilyLinkRequestStatus.EXPIRED
    db.add(item)
    await db.commit()
    return {"code": "OK"}


@router.get("/family-links")
async def get_family_links(
    page: int = 1,
    pageSize: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FamilyLink).where(
        or_(
            FamilyLink.elderly_id == current_user.id,
            FamilyLink.family_id == current_user.id,
        )
    ).order_by(FamilyLink.created_at.desc())
    result = await db.execute(stmt)
    all_items = result.scalars().all()
    items = all_items[(page - 1) * pageSize : page * pageSize]
    return paginate([serialize_family_link(item) for item in items], page, pageSize, len(all_items))


@router.delete("/family-links/{linkId}")
async def delete_family_link(
    linkId: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(FamilyLink).where(FamilyLink.id == linkId)
    result = await db.execute(stmt)
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=404, detail="Link not found")
    if current_user.id not in (item.elderly_id, item.family_id):
        raise HTTPException(status_code=403, detail="AUTH_403_FORBIDDEN")
    await db.delete(item)
    await db.commit()
    return {"code": "OK"}

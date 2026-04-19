import asyncio
from datetime import datetime, timedelta
from sqlalchemy import delete, select

from app.db.session import async_session, engine
from app.models.all import (
    Base,
    GenderEnum,
    Notification,
    ReminderTask,
    ReminderTaskStatus,
    ReminderTaskType,
    Report,
    RoleEnum,
    SessionStatus,
    User,
    ExamSession,
)


MOCK_USERS = [
    {
        "phone": "13900000001",
        "name": "张建国",
        "gender": GenderEnum.MALE,
        "birth_date": "19580312",
        "id_card": "110101195803122415",
        "risk_level": "high",
    },
    {
        "phone": "13900000002",
        "name": "李桂芳",
        "gender": GenderEnum.FEMALE,
        "birth_date": "19610408",
        "id_card": "110101196104082422",
        "risk_level": "medium",
    },
    {
        "phone": "13900000003",
        "name": "王德顺",
        "gender": GenderEnum.MALE,
        "birth_date": "19551226",
        "id_card": "110101195512263619",
        "risk_level": "low",
    },
]


def build_report_content(name: str, risk_level: str):
    abnormal = []
    if risk_level == "high":
        abnormal = [
            {"name": "收缩压", "code": "SBP", "level": "high", "text": "收缩压偏高"},
            {"name": "血糖", "code": "GLU", "level": "high", "text": "血糖偏高"},
        ]
    elif risk_level == "medium":
        abnormal = [{"name": "心率", "code": "HR", "level": "medium", "text": "心率波动"}]

    sections = [
        {
            "key": "vitals",
            "title": "生命体征",
            "items": [
                {"name": "收缩压", "code": "SBP", "value": 145 if risk_level == "high" else 128, "unit": "mmHg", "level": "high" if risk_level == "high" else "low"},
                {"name": "舒张压", "code": "DBP", "value": 92 if risk_level == "high" else 82, "unit": "mmHg", "level": "medium" if risk_level != "low" else "low"},
                {"name": "心率", "code": "HR", "value": 88, "unit": "bpm", "level": "medium" if risk_level == "medium" else "low"},
            ],
        }
    ]

    return {
        "summary": {"text": f"{name} 本次体检风险等级为 {risk_level}"},
        "abnormalities": abnormal,
        "ruleHits": [
            {
                "ruleCode": f"RISK_{risk_level.upper()}",
                "name": "综合风险评估",
                "level": risk_level,
                "message": f"命中{risk_level}风险规则",
            }
        ],
        "sections": sections,
        "suggestions": [
            "保持规律作息和适量运动",
            "按时复查关键指标",
            "如有不适请及时就医",
        ],
    }


async def seed_mock_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        for idx, item in enumerate(MOCK_USERS, start=1):
            stmt = select(User).where(User.phone == item["phone"], User.role == RoleEnum.USER)
            result = await session.execute(stmt)
            user = result.scalars().first()
            if not user:
                user = User(phone=item["phone"], role=RoleEnum.USER)
                session.add(user)
                await session.flush()

            user.name = item["name"]
            user.gender = item["gender"]
            user.birth_date = item["birth_date"]
            user.id_card = item["id_card"]
            user.device_id = f"DEV-MOCK-{idx:03d}"
            session.add(user)
            await session.flush()

            # 清理旧模拟数据（仅当前用户的会话/报告/提醒/通知）
            await session.execute(delete(Report).where(Report.user_id == user.id))
            await session.execute(delete(ExamSession).where(ExamSession.user_id == user.id))
            await session.execute(delete(ReminderTask).where(ReminderTask.user_id == user.id))
            await session.execute(delete(Notification).where(Notification.user_id == user.id))

            now = datetime.utcnow()
            session_id = f"S{user.id}{now.strftime('%Y%m%d%H%M%S')}"
            report_id = f"R{user.id}{now.strftime('%Y%m%d%H%M%S')}"

            exam = ExamSession(
                id=session_id,
                user_id=user.id,
                device_id=user.device_id,
                status=SessionStatus.COMPLETED,
                start_time=now - timedelta(minutes=30),
                end_time=now - timedelta(minutes=15),
                vitals_data={"sbp": 145 if item["risk_level"] == "high" else 128, "dbp": 92 if item["risk_level"] == "high" else 82, "hr": 88},
                ecg_present=True,
                ecg_data_complete=True,
            )
            session.add(exam)

            report = Report(
                id=report_id,
                session_id=session_id,
                user_id=user.id,
                content_json=build_report_content(item["name"], item["risk_level"]),
                risk_level=item["risk_level"],
            )
            session.add(report)

            reminder_open = ReminderTask(
                user_id=user.id,
                type=ReminderTaskType.NO_EXAM_3M,
                status=ReminderTaskStatus.OPEN,
            )
            reminder_done = ReminderTask(
                user_id=user.id,
                type=ReminderTaskType.NO_EXAM_6M,
                status=ReminderTaskStatus.DONE,
                handle_action="notify",
                handle_note="已电话提醒",
            )
            session.add(reminder_open)
            session.add(reminder_done)

            notice = Notification(
                user_id=user.id,
                title="体检报告已生成",
                content=f"您的最新体检报告（{report_id}）已生成，请及时查看。",
                is_read=False,
            )
            session.add(notice)

        await session.commit()

    print("Mock data seeded successfully. Users:", ", ".join(u["phone"] for u in MOCK_USERS))


if __name__ == "__main__":
    asyncio.run(seed_mock_data())

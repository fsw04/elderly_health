import json
import base64
import hmac
import hashlib
import time
import asyncio
from typing import Dict, Any
from sqlalchemy.future import select
import uuid
import datetime

from app.core.config import settings
from app.db.session import async_session
from app.models.all import User, ExamSession, SessionStatus, Report

def generate_mock_report_content(session_id: str, vitals: dict) -> dict:
    """根据体检数据生成符合前端解析规范的 JSON 报告内容"""
    # 简单判定风险等级：如果血压高或血糖高，定为 medium/high
    risk_level = "low"
    abnormalities = []
    
    # 尝试解析带单位的字符串，如 "115/71 mmHg" -> sys:115, dia:71
    bp_str = vitals.get("bloodPressure", "")
    sys_bp, dia_bp = 120, 80
    if "/" in bp_str:
        try:
            sys_bp = int(bp_str.split("/")[0].strip())
            dia_bp = int(bp_str.split("/")[1].split()[0].strip())
        except:
            pass

    glucose_str = vitals.get("fastingBloodGlucose", "")
    glucose = 5.0
    if glucose_str:
        try:
            glucose = float(glucose_str.split()[0].strip())
        except:
            pass
    
    if sys_bp > 140 or dia_bp > 90:
        risk_level = "medium"
        abnormalities.append({"name": "血压偏高", "level": "medium", "value": f"{sys_bp}/{dia_bp} mmHg"})
    if glucose > 7.0:
        risk_level = "high" if risk_level == "low" else risk_level
        abnormalities.append({"name": "空腹血糖偏高", "level": "high", "value": f"{glucose} mmol/L"})
        
    return {
        "schemaVersion": "1.0",
        "reportId": f"rep_{session_id}",
        "sessionId": session_id,
        "generatedAt": datetime.datetime.now().isoformat(),
        "summary": {
            "riskLevel": risk_level,
            "brief": f"本次体检发现 {len(abnormalities)} 项指标异常。" if abnormalities else "本次体检各项指标正常，请继续保持。"
        },
        "abnormalities": abnormalities,
        "sections": [
            {
                "id": "vitals",
                "title": "基础体征",
                "items": [
                    {"name": "身高", "value": vitals.get("height", "-").replace("cm", "").strip(), "unit": "cm", "status": "normal"},
                    {"name": "体重", "value": vitals.get("weight", "-").replace("kg", "").strip(), "unit": "kg", "status": "normal"},
                    {"name": "BMI", "value": vitals.get("bmi", "-").replace("kg/m2", "").strip(), "unit": "kg/m²", "status": "normal"},
                    {"name": "血压", "value": f"{sys_bp}/{dia_bp}", "unit": "mmHg", "status": "high" if sys_bp>140 else "normal"}
                ]
            },
            {
                "id": "glucose",
                "title": "血糖检测",
                "items": [
                    {"name": "空腹血糖", "value": str(glucose), "unit": "mmol/L", "status": "high" if glucose>7.0 else "normal"}
                ]
            }
        ],
        "doctorSummary": {
            "height": vitals.get("height", ""),
            "weight": vitals.get("weight", ""),
            "bmi": vitals.get("bmi", ""),
            "bloodPressure": vitals.get("bloodPressure", f"{sys_bp}/{dia_bp} mmHg"),
            "fastingBloodGlucose": vitals.get("fastingBloodGlucose", f"{glucose} mmol/L"),
            "ecgFinding": "",
            "bUltrasound": "",
            "tcmConstitution": ""
        }
    }

def verify_mqtt_signature(payload: Dict[str, Any], topic: str) -> bool:
    try:
        if "sig" not in payload:
            return True
            
        device_id = payload.get("deviceId", "")
        ts = payload.get("ts", "")
        sent_at = payload.get("sentAt", "")
        msg_id = payload.get("msgId", "")
        msg_type = payload.get("type", "")
        session_id = payload.get("sessionId", "")
        ver = payload.get("ver", "1.0")
        data = payload.get("data", {})
        sig = payload.get("sig", "")
        
        current_time = int(time.time())
        if abs(current_time - int(sent_at)) > 300:
            return False
        
        data_str = json.dumps(data, separators=(',', ':'), sort_keys=True)
        canonical_str = f"deviceId={device_id}\nts={ts}\nsentAt={sent_at}\nmsgId={msg_id}\ntype={msg_type}\nsessionId={session_id}\nver={ver}\ntopic={topic}\ndata={data_str}"
        
        expected_sig = base64.b64encode(
            hmac.new(settings.MQTT_SECRET_KEY.encode(), canonical_str.encode('utf-8'), hashlib.sha256).digest()
        ).decode()
        
        return hmac.compare_digest(expected_sig, sig)
    except Exception:
        return False

async def process_vitals_to_db(payload: dict):
    device_id = payload.get("deviceId", "unknown_device")
    session_id = payload.get("sessionId") or f"sess_{int(time.time())}"
    data = payload.get("data", {})
    
    phone = data.get("phone")
    name = data.get("name")
    id_card = data.get("idCard")
    
    async with async_session() as db:
        # 1. 查找或创建用户
        result = await db.execute(select(User).where(User.phone == phone))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"🆕 发现新用户 {name}，正在注册...")
            user = User(
                phone=phone,
                name=name,
                id_card=id_card,
                device_id=device_id
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            print(f"✅ 找到已有用户 {name}，更新设备ID...")
            user.device_id = device_id
            user.name = name
            user.id_card = id_card
            await db.commit()
            
        # 2. 插入或更新体检会话数据
        print(f"📊 正在保存体检指标到 Session [{session_id}]...")
        session_result = await db.execute(select(ExamSession).where(ExamSession.id == session_id))
        session = session_result.scalar_one_or_none()
        
        if not session:
            session = ExamSession(
                id=session_id,
                user_id=user.id,
                device_id=device_id,
                vitals_data=data,  
                status=SessionStatus.COMPLETED
            )
            db.add(session)
            print("💾 新建 Session 完成！")
        else:
            session.vitals_data = data
            session.status = SessionStatus.COMPLETED
            print("🔄 找到已有 Session，更新体检数据完成！")
            
        await db.commit()
        
        # 3. 自动生成并关联 Report (报告记录)
        report_result = await db.execute(select(Report).where(Report.session_id == session_id))
        existing_report = report_result.scalar_one_or_none()
        
        report_content = generate_mock_report_content(session_id, data)
        
        if not existing_report:
            new_report = Report(
                id=f"rep_{session_id}",
                session_id=session_id,
                user_id=user.id,
                content_json=report_content,
                risk_level=report_content["summary"]["riskLevel"]
            )
            db.add(new_report)
            print("📋 报告已成功生成入库，前端可见！")
        else:
            existing_report.content_json = report_content
            existing_report.risk_level = report_content["summary"]["riskLevel"]
            print("🔄 报告内容已更新！")
            
        await db.commit()

def setup_mqtt():
    import paho.mqtt.client as mqtt
    
    def on_connect(client, userdata, flags, rc):
        print("✅ 后端已成功连接到 MQTT Broker (Mosquitto), rc=" + str(rc))
        client.subscribe("watch/+/up")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            print(f"\n📥 收到 MQTT 消息，来自主题: {msg.topic}")
            
            if not verify_mqtt_signature(payload, msg.topic):
                print("❌ 签名校验失败或非法消息，已拦截")
                return
            
            msg_type = payload.get("type")
            if msg_type == "vitals":
                asyncio.run(process_vitals_to_db(payload))
            else:
                print(f"⏭️ 收到未处理的消息类型: {msg_type}")
                
        except Exception as e:
            print(f"❌ 处理 MQTT 消息时发生异常: {e}")

    client = mqtt.Client()
    if hasattr(settings, 'MQTT_USER') and settings.MQTT_USER:
        client.username_pw_set(settings.MQTT_USER, getattr(settings, 'MQTT_PASSWORD', ''))
        
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        broker = getattr(settings, 'MQTT_BROKER', '192.168.43.110')
        port = getattr(settings, 'MQTT_PORT', 1883)
        client.connect(broker, port, 60)
        client.loop_start()
        print(f"🚀 MQTT 监听服务已启动 (Broker: {broker}:{port})")
    except Exception as e:
        print(f"⚠️ 无法连接到 MQTT Broker: {e}")

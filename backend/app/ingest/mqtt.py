import json
import base64
import hmac
import hashlib
import time
from typing import Dict, Any
from app.core.config import settings

def verify_mqtt_signature(payload: Dict[str, Any], topic: str) -> bool:
    try:
        # Expected structure: deviceId, ts, sentAt, msgId, type, sessionId, ver, data, sigAlg, sigVer, sig
        device_id = payload.get("deviceId", "")
        ts = payload.get("ts", "")
        sent_at = payload.get("sentAt", "")
        msg_id = payload.get("msgId", "")
        msg_type = payload.get("type", "")
        session_id = payload.get("sessionId", "")
        ver = payload.get("ver", "1.0")
        data = payload.get("data", {})
        sig = payload.get("sig", "")
        
        # Check timestamp window (5 minutes)
        current_time = int(time.time())
        if abs(current_time - int(sent_at)) > 300:
            return False # ING_408_TS_EXPIRED
        
        # Canonical string
        data_str = json.dumps(data, separators=(',', ':'), sort_keys=True)
        canonical_str = f"deviceId={device_id}\nts={ts}\nsentAt={sent_at}\nmsgId={msg_id}\ntype={msg_type}\nsessionId={session_id}\nver={ver}\ntopic={topic}\ndata={data_str}"
        
        expected_sig = base64.b64encode(
            hmac.new(settings.MQTT_SECRET_KEY.encode(), canonical_str.encode('utf-8'), hashlib.sha256).digest()
        ).decode()
        
        return hmac.compare_digest(expected_sig, sig)
    except Exception:
        return False

# This is a placeholder for the actual MQTT client setup
def setup_mqtt():
    import paho.mqtt.client as mqtt
    
    def on_connect(client, userdata, flags, rc):
        print("Connected to MQTT Broker with result code "+str(rc))
        client.subscribe("fc/+/up")
        client.subscribe("watch/+/up")
        client.subscribe("sensor/+/up")

    def on_message(client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            if not verify_mqtt_signature(payload, msg.topic):
                print(f"Invalid signature for msgId {payload.get('msgId')}")
                return
            # Process message based on payload.type
            print(f"Processed valid message: {payload.get('msgId')} of type {payload.get('type')}")
            # Real implementation would queue it or process it in DB
        except Exception as e:
            print(f"Error processing MQTT message: {e}")

    client = mqtt.Client()
    if settings.MQTT_USER and settings.MQTT_PASSWORD:
        client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASSWORD)
        
    # client.on_connect = on_connect
    # client.on_message = on_message
    
    # In a real app, this runs in a separate thread or async task
    # client.connect(settings.MQTT_BROKER, settings.MQTT_PORT, 60)
    # client.loop_start()
    print("MQTT setup initialized (mocked for MVP).")

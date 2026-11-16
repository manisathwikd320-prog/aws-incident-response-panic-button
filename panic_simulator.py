#!/usr/bin/env python3
"""
AWS IoT Core Panic Button Simulator (Virtual Hardware)
Author: Incident Response System Team
Region: ap-southeast-2

Connects to AWS IoT Core via Mutual TLS (X.509) and publishes trigger events
when the user presses [ENTER].
"""

import sys
import os
import time
import json
import ssl
from datetime import datetime, timezone

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("[ERROR] 'paho-mqtt' library is not installed.")
    print("Please install it using: pip install paho-mqtt")
    sys.exit(1)

# ==========================================
# AWS Configuration
# ==========================================
IOT_ENDPOINT = "abqjmt374cvjt-ats.iot.ap-southeast-2.amazonaws.com"
IOT_PORT = 8883
CLIENT_ID = "PanicButtonSimulator"
TOPIC_TRIGGER = "panic/button/trigger"
DEVICE_ID = "panic-button-01"

# Paths to Certificates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERTS_DIR = os.path.join(BASE_DIR, "certs")

ROOT_CA = os.path.join(CERTS_DIR, "AmazonRootCA1.pem")
DEVICE_CERT = os.path.join(CERTS_DIR, "device-certificate.pem.crt")
PRIVATE_KEY = os.path.join(CERTS_DIR, "private.pem.key")


# ==========================================
# Certificate Validation
# ==========================================
def verify_certificates():
    missing_certs = []
    for cert_name, cert_path in [
        ("Amazon Root CA 1", ROOT_CA),
        ("Device Certificate", DEVICE_CERT),
        ("Private Key", PRIVATE_KEY)
    ]:
        if not os.path.isfile(cert_path):
            missing_certs.append(f" - {cert_name}: {cert_path}")

    if missing_certs:
        print("\n" + "=" * 65)
        print("[ERROR] Missing required TLS certificates in ./certs/ folder!")
        print("=" * 65)
        for cert in missing_certs:
            print(cert)
        print("\nPlease place the downloaded AWS IoT certificates inside:")
        print(f"Directory: {CERTS_DIR}")
        print("Required files:")
        print("  1. AmazonRootCA1.pem")
        print("  2. device-certificate.pem.crt")
        print("  3. private.pem.key")
        print("=" * 65 + "\n")
        return False
    return True


# ==========================================
# MQTT Callbacks
# ==========================================
is_connected = False

def on_connect(client, userdata, flags, rc, properties=None):
    global is_connected
    if rc == 0:
        is_connected = True
        print("\n" + "#" * 60)
        print(" [SUCCESS] Connected to AWS IoT Core!")
        print(f" Endpoint:  {IOT_ENDPOINT}:{IOT_PORT}")
        print(f" Client ID: {CLIENT_ID}")
        print(f" Device ID: {DEVICE_ID}")
        print(f" Topic:     {TOPIC_TRIGGER}")
        print("#" * 60)
    else:
        is_connected = False
        rc_codes = {
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized (check AWS IoT Policy & Certificate attachment)"
        }
        error_msg = rc_codes.get(rc, f"Unknown error code ({rc})")
        print(f"\n[ERROR] Connection failed with code {rc}: {error_msg}")


def on_publish(client, userdata, mid, reason_codes=None, properties=None):
    pass  # Confirmation handled synchronously or upon delivery


def on_disconnect(client, userdata, *args):
    global is_connected
    is_connected = False
    print("\n[INFO] Disconnected from AWS IoT Core.")


# ==========================================
# Main Execution Loop
# ==========================================
def main():
    print("=" * 60)
    print(" AWS IoT Core - Incident Response Panic Button Simulator")
    print("=" * 60)

    if not verify_certificates():
        sys.exit(1)

    # Initialize MQTT client with compatibility across paho-mqtt v1 and v2
    try:
        # paho-mqtt >= 2.0.0
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=CLIENT_ID,
            protocol=mqtt.MQTTv311
        )
    except AttributeError:
        # paho-mqtt < 2.0.0
        client = mqtt.Client(
            client_id=CLIENT_ID,
            protocol=mqtt.MQTTv311
        )

    # Attach callbacks
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_disconnect = on_disconnect

    # Configure Mutual TLS (X.509 Authentication)
    print("[INIT] Configuring Mutual TLS...")
    try:
        client.tls_set(
            ca_certs=ROOT_CA,
            certfile=DEVICE_CERT,
            keyfile=PRIVATE_KEY,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLSv1_2,
            ciphers=None
        )
    except Exception as e:
        print(f"[ERROR] Failed to configure TLS: {e}")
        sys.exit(1)

    # Connect to AWS IoT Core
    print(f"[INIT] Connecting to {IOT_ENDPOINT}:{IOT_PORT}...")
    try:
        client.connect(IOT_ENDPOINT, port=IOT_PORT, keepalive=60)
    except Exception as e:
        print(f"[FATAL] Connection attempt failed: {e}")
        sys.exit(1)

    # Start network loop thread
    client.loop_start()

    # Wait for connection confirmation
    wait_time = 0
    while not is_connected and wait_time < 10:
        time.sleep(0.5)
        wait_time += 0.5

    if not is_connected:
        print("[WARNING] Connection is taking longer than expected. Check IoT policies and certs.")

    print("\n------------------------------------------------------------")
    print(" Controls:")
    print("  - Press [ENTER] to trigger PANIC BUTTON")
    print("  - Type 'q' or 'exit' and press [ENTER] to quit")
    print("------------------------------------------------------------\n")

    counter = 0
    try:
        while True:
            user_input = input(">> Press [ENTER] to trigger panic (or 'q' to quit): ").strip()
            if user_input.lower() in ["q", "quit", "exit"]:
                print("\n[INFO] Exiting Panic Button Simulator...")
                break

            current_time = int(time.time())
            iso_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            counter += 1

            payload = {
                "deviceId": DEVICE_ID,
                "action": "PRESSED",
                "timestamp": current_time
            }

            json_payload = json.dumps(payload)

            if not is_connected:
                print("[WARNING] Client is currently disconnected. Attempting to publish...")

            result = client.publish(TOPIC_TRIGGER, json_payload, qos=1)
            result.wait_for_publish(timeout=5)

            if result.is_published():
                print(f"\n[ALERT #{counter} PUBLISHED SUCCESSFULLY]")
                print(f" Topic:     {TOPIC_TRIGGER}")
                print(f" Time (UTC): {iso_time} ({current_time})")
                print(f" Payload:   {json_payload}")
                print("------------------------------------------------------------\n")
            else:
                print(f"\n[ERROR] Failed to publish message (rc={result.rc}).\n")

    except KeyboardInterrupt:
        print("\n\n[INFO] Keyboard interrupt detected. Exiting...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("[INFO] Simulator safely stopped.")


if __name__ == "__main__":
    main()

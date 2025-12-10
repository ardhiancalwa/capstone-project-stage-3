import paho.mqtt.client as mqtt
import time
import json
import random

# Konfigurasi
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "smartambience/sensor/data"

def connect_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="ESP32_Simulator_Corrected")
    client.connect(BROKER, PORT, 60)
    return client

def publish(client):
    print("🚀 Simulasi Sensor Dimulai (Dataset V2: Temp, Hum, Light, Motion)...")
    while True:
        time.sleep(2)
        
        # Skenario berdasarkan dataset
        scenario = random.choice(['panas', 'nyaman', 'gelap_sepi', 'terang_gerak'])
        
        if scenario == 'nyaman':
            temp = round(random.uniform(24.0, 26.0), 1)
            hum = round(random.uniform(45.0, 60.0), 1)
            light = random.randint(300, 800) # Cahaya sedang
            motion = random.choice([0, 1])
        elif scenario == 'panas':
            temp = round(random.uniform(30.0, 34.0), 1)
            hum = round(random.uniform(30.0, 50.0), 1)
            light = random.randint(800, 4000) # Terang sekali
            motion = 1
        elif scenario == 'gelap_sepi':
            temp = round(random.uniform(20.0, 24.0), 1)
            hum = round(random.uniform(60.0, 80.0), 1)
            light = random.randint(0, 100) # Gelap
            motion = 0
        else:
            temp = round(random.uniform(25.0, 29.0), 1)
            hum = round(random.uniform(50.0, 70.0), 1)
            light = random.randint(200, 1000)
            motion = 1

        # Payload sesuai kolom dataset.csv
        payload = {
            "temperature": temp,
            "humidity": hum,
            "light_raw": light,  # Sesuai dataset
            "motion": motion     # Sesuai dataset (0 atau 1)
        }
        
        message = json.dumps(payload)
        result = client.publish(TOPIC, message)
        
        if result[0] == 0:
            print(f"📡 Sent: {message}")
        else:
            print("❌ Failed to send")

if __name__ == '__main__':
    client = connect_mqtt()
    client.loop_start()
    try:
        publish(client)
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()
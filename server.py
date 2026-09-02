import threading, time, random
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app   = Flask(__name__)
CORS(app)

node_data = {}
alert_log = []

# ── Simulate Node B and C ──
def simulate_node(node_id, lat, lng):
    while True:
        soil  = random.randint(30, 60)
        water = random.randint(20, 45)
        vibr  = round(random.uniform(0.8, 1.5), 2)
        alert = False

        # 8% chance of danger (for demo make it higher)
        if random.random() < 0.08:
            soil  = random.randint(75, 95)
            water = random.randint(5, 12)
            vibr  = round(random.uniform(2.8, 4.0), 2)
            alert = True

        data = {
            "node":  node_id,
            "soil":  soil,
            "water": water,
            "vibr":  vibr,
            "alert": alert,
            "lat":   lat,
            "lng":   lng,
            "time":  datetime.now().strftime("%H:%M:%S")
        }
        node_data[node_id] = data

        if alert:
            alert_log.append(data)
            send_whatsapp(data)
            print(f"🔴 {node_id} ALERT! Soil:{soil}% Water:{water}cm")
        else:
            print(f"🟢 {node_id} OK — Soil:{soil}% Water:{water}cm")

        time.sleep(3)

# ── Receive Real ESP32 Data ──
@app.route('/data', methods=['POST'])
def receive():
    data = request.json
    data['time'] = datetime.now().strftime("%H:%M:%S")
    node_data[data['node']] = data
    print(f"📡 ESP32 REAL → {data['node']} "
          f"Soil:{data['soil']}% "
          f"{'🔴 ALERT' if data['alert'] else '🟢 OK'}")
    if data['alert']:
        alert_log.append(data)
        send_whatsapp(data)
    return jsonify({"status": "ok"})

@app.route('/status')
def status():
    return jsonify(node_data)

@app.route('/alerts')
def alerts():
    return jsonify(alert_log[-10:])

# ── WhatsApp Alert ──
def send_whatsapp(data):
    try:
        from twilio.rest import Client
        client = Client("YOUR_TWILIO_SID", "YOUR_TWILIO_TOKEN")
        msg = (
            f"BharatSense — Danger!\n"
            f"Node: {data['node']}\n"
            f"Soil: {data['soil']}%\n"
            f"Water: {data['water']}cm\n"
            f"Vibr: {data['vibr']}g\n"
            f"Time: {data['time']}\n"
            f"Location: maps.google.com/"
            f"?q={data['lat']},{data['lng']}"
        )
        client.messages.create(
            body=msg,
            from_="whatsapp:+14155238886",
            to="whatsapp:+91XXXXXXXXXX"
        )
        print(f"📱 WhatsApp sent!")
    except Exception as e:
        print(f"WhatsApp skip: {e}")

# ── Start Everything ──
if __name__ == '__main__':
    print("="*40)
    print("BharatSense Server Starting...")
    print("="*40)

    t1 = threading.Thread(
        target=simulate_node,
        args=("NODE_B", 11.0200, 76.9600),
        daemon=True
    )
    t2 = threading.Thread(
        target=simulate_node,
        args=("NODE_C", 11.0140, 76.9500),
        daemon=True
    )
    t1.start()
    t2.start()

    print("✅ NODE_B simulated")
    print("✅ NODE_C simulated")
    print("📡 Waiting for NODE_A real ESP32...")
    print("🌐 Open: http://localhost:5000")
    print("="*40)

    app.run(host='0.0.0.0', port=5000, debug=False)
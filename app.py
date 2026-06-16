from flask import Flask, jsonify
import threading, time, random, datetime
from datetime import timezone, timedelta

app = Flask(__name__)

IST = timezone(timedelta(hours=5, minutes=30))
def now_ist():
    return datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

states = {
    "Uttar Pradesh": 231_500_000, "Maharashtra": 126_000_000,
    "Bihar": 128_500_000, "West Bengal": 99_600_000,
    "Madhya Pradesh": 85_400_000, "Tamil Nadu": 77_800_000,
    "Rajasthan": 81_000_000, "Karnataka": 67_700_000,
    "Gujarat": 71_500_000, "Andhra Pradesh": 53_900_000
}
history = {state: [] for state in states}
last_update = now_ist()

def update_population():
    global last_update
    while True:
        time.sleep(300)
        for state in states:
            change = random.randint(-200, 500)
            states[state] += change
            history[state].append({"time": now_ist(), "population": states[state], "change": change})
            if len(history[state]) > 50:
                history[state].pop(0)
        last_update = now_ist()
        print(f"[{last_update}] Population updated", flush=True)

@app.route("/")
def home():
    return """
    <html>
    <head>
        <title>Population Tracker</title>
        <style>
            body { font-family:monospace; background:#111; color:#0f0; padding:30px; }
            table { border-collapse:collapse; width:100%; }
            td, th { padding:8px; text-align:left; }
        </style>
    </head>
    <body>
        <h2>📊 State Population Tracker</h2>
        <p>Last Updated (IST): <span id="last_update">loading...</span></p>
        <p style="color:#aaa">Updates every 5 minutes</p>
        <table>
            <tr style="border-bottom:1px solid #0f0"><th>State</th><th>Population</th><th>Last Change</th></tr>
            <tbody id="rows"><tr><td colspan="3">loading...</td></tr></tbody>
        </table>
        <script>
        async function updateData() {
            const res = await fetch('/api');
            const data = await res.json();
            document.getElementById('last_update').innerText = data.last_updated_ist;
            let rows = '';
            for (const [state, pop] of Object.entries(data.states)) {
                rows += `<tr><td>${state}</td><td>${pop.toLocaleString()}</td><td>--</td></tr>`;
            }
            document.getElementById('rows').innerHTML = rows;
        }
        updateData();
        setInterval(updateData, 5000);
        </script>
    </body></html>"""

@app.route("/api")
def api():
    return jsonify({"last_updated_ist": last_update, "states": states})

if __name__ == "__main__":
    threading.Thread(target=update_population, daemon=True).start()
    app.run(host="0.0.0.0", port=10000, threaded=True)

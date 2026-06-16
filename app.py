from flask import Flask, jsonify
import threading, time, random, datetime
from datetime import timezone, timedelta

app = Flask(__name__)

IST = timezone(timedelta(hours=5, minutes=30))
def now_ist():
    return datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

# Starting populations (approx, in millions) - 10 Indian states
states = {
    "Uttar Pradesh": 231_500_000,
    "Maharashtra": 126_000_000,
    "Bihar": 128_500_000,
    "West Bengal": 99_600_000,
    "Madhya Pradesh": 85_400_000,
    "Tamil Nadu": 77_800_000,
    "Rajasthan": 81_000_000,
    "Karnataka": 67_700_000,
    "Gujarat": 71_500_000,
    "Andhra Pradesh": 53_900_000
}

history = {state: [] for state in states}
last_update = now_ist()

def update_population():
    global last_update
    while True:
        time.sleep(300)  # 5 minutes
        for state in states:
            # Simulate small natural variation (+/- up to 500 people per 5 min)
            change = random.randint(-200, 500)
            states[state] += change
            history[state].append({
                "time": now_ist(),
                "population": states[state],
                "change": change
            })
            if len(history[state]) > 50:
                history[state].pop(0)
        last_update = now_ist()
        print(f"[{last_update}] Population updated for all states", flush=True)

@app.route("/")
def home():
    rows = ""
    for state, pop in states.items():
        last_change = history[state][-1]["change"] if history[state] else 0
        arrow = "🔺" if last_change > 0 else ("🔻" if last_change < 0 else "➖")
        color = "lime" if last_change > 0 else ("red" if last_change < 0 else "gray")
        rows += f"""
        <tr>
            <td style="padding:8px">{state}</td>
            <td style="padding:8px">{pop:,}</td>
            <td style="padding:8px; color:{color}">{arrow} {last_change:+,}</td>
        </tr>"""

    return f"""
    <html>
    <head><title>State Population Tracker</title><meta http-equiv="refresh" content="15"></head>
    <body style="font-family:monospace; background:#111; color:#0f0; padding:30px">
        <h2>📊 State Population Tracker</h2>
        <p>Last Updated (IST): {last_update}</p>
        <p style="color:#aaa">Updates every 5 minutes</p>
        <table style="border-collapse:collapse; width:100%; color:#0f0">
            <tr style="border-bottom:1px solid #0f0">
                <th style="padding:8px; text-align:left">State</th>
                <th style="padding:8px; text-align:left">Population</th>
                <th style="padding:8px; text-align:left">Last Change</th>
            </tr>
            {rows}
        </table>
        <br>
        <a href="/api" style="color:cyan">📡 JSON API</a> |
        <a href="/history" style="color:cyan">📈 History</a>
    </body></html>"""

@app.route("/api")
def api():
    return jsonify({
        "last_updated_ist": last_update,
        "states": states
    })

@app.route("/history")
def full_history():
    return jsonify(history)

if __name__ == "__main__":
    threading.Thread(target=update_population, daemon=True).start()
    app.run(host="0.0.0.0", port=10000, threaded=True)
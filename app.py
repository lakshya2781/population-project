from flask import Flask, jsonify, request
import threading, time, random, datetime, os
from datetime import timezone, timedelta
import psycopg2

app = Flask(__name__)

IST = timezone(timedelta(hours=5, minutes=30))
def now_ist():
    return datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

DATABASE_URL = os.environ.get("DATABASE_URL")
DBVIEW_PASSWORD = os.environ.get("DBVIEW_PASSWORD", "Lakshya2781")

INITIAL_STATES = {
    "Uttar Pradesh": 231_500_000, "Maharashtra": 126_000_000,
    "Bihar": 128_500_000, "West Bengal": 99_600_000,
    "Madhya Pradesh": 85_400_000, "Tamil Nadu": 77_800_000,
    "Rajasthan": 81_000_000, "Karnataka": 67_700_000,
    "Gujarat": 71_500_000, "Andhra Pradesh": 53_900_000
}

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS population_state (
            state_name TEXT PRIMARY KEY,
            population BIGINT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS population_history (
            id SERIAL PRIMARY KEY,
            state_name TEXT NOT NULL,
            log_time TEXT NOT NULL,
            population BIGINT NOT NULL,
            change INTEGER NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS population_meta (
            id INTEGER PRIMARY KEY DEFAULT 1,
            last_updated TEXT NOT NULL
        )
    """)
    cur.execute("SELECT COUNT(*) FROM population_state")
    if cur.fetchone()[0] == 0:
        for name, pop in INITIAL_STATES.items():
            cur.execute("INSERT INTO population_state (state_name, population) VALUES (%s, %s)", (name, pop))
    cur.execute("SELECT COUNT(*) FROM population_meta")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO population_meta (id, last_updated) VALUES (1, %s)", (now_ist(),))
    conn.commit()
    cur.close()
    conn.close()

def get_state():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT state_name, population FROM population_state ORDER BY state_name")
    states = dict(cur.fetchall())
    cur.execute("SELECT last_updated FROM population_meta WHERE id=1")
    last_updated = cur.fetchone()[0]
    cur.close()
    conn.close()
    return states, last_updated

def update_all_states():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT state_name, population FROM population_state")
    rows = cur.fetchall()
    for name, pop in rows:
        change = random.randint(-200, 500)
        new_pop = pop + change
        cur.execute("UPDATE population_state SET population=%s WHERE state_name=%s", (new_pop, name))
        cur.execute(
            "INSERT INTO population_history (state_name, log_time, population, change) VALUES (%s,%s,%s,%s)",
            (name, now_ist(), new_pop, change)
        )
    cur.execute("UPDATE population_meta SET last_updated=%s WHERE id=1", (now_ist(),))
    conn.commit()
    cur.close()
    conn.close()

def update_population():
    while True:
        time.sleep(300)
        update_all_states()
        print(f"[{now_ist()}] Population updated", flush=True)

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
        <h2>📊 State Population Tracker (Persistent)</h2>
        <p>Last Updated (IST): <span id="last_update">loading...</span></p>
        <p style="color:#aaa">Updates every 5 minutes</p>
        <table>
            <tr style="border-bottom:1px solid #0f0"><th>State</th><th>Population</th></tr>
            <tbody id="rows"><tr><td colspan="2">loading...</td></tr></tbody>
        </table>
        <p><a href="/dbview" style="color:cyan">🗄️ View Database</a></p>
        <script>
        async function updateData() {
            const res = await fetch('/api');
            const data = await res.json();
            document.getElementById('last_update').innerText = data.last_updated_ist;
            let rows = '';
            for (const [state, pop] of Object.entries(data.states)) {
                rows += `<tr><td>${state}</td><td>${pop.toLocaleString()}</td></tr>`;
            }
            document.getElementById('rows').innerHTML = rows;
        }
        updateData();
        setInterval(updateData, 5000);
        </script>
    </body></html>"""

@app.route("/api")
def api():
    states, last_updated = get_state()
    return jsonify({"last_updated_ist": last_updated, "states": states})

@app.route("/dbview")
def dbview():
    provided_password = request.args.get("password", "")
    if provided_password != DBVIEW_PASSWORD:
        return """
        <html>
        <head><title>Locked</title></head>
        <body style="font-family:monospace; background:#111; color:#0f0; padding:60px; text-align:center;">
            <h2>🔒 Access Restricted</h2>
            <p>Add ?password=YOUR_PASSWORD to the URL to view this page.</p>
        </body></html>
        """, 401

    conn = get_db()
    cur = conn.cursor()
    sections = []

    cur.execute("SELECT * FROM population_state ORDER BY state_name")
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    sections.append(("population_state", cols, rows))

    cur.execute("SELECT * FROM population_history ORDER BY id DESC LIMIT 15")
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    sections.append(("population_history", cols, rows))

    cur.close()
    conn.close()

    html = """
    <html>
    <head>
        <title>Database Viewer</title>
        <style>
            body { font-family:monospace; background:#111; color:#0f0; padding:30px; }
            h3 { color:cyan; margin-top:30px; }
            table { border-collapse:collapse; width:100%; margin-bottom:10px; }
            td, th { padding:6px 10px; text-align:left; border-bottom:1px solid #333; font-size:13px; }
            th { color:yellow; }
        </style>
    </head>
    <body>
        <h2>🗄️ Population Database Viewer</h2>
    """
    for table_name, cols, rows in sections:
        html += f"<h3>📋 {table_name} ({len(rows)} rows shown)</h3>"
        html += "<table><tr>" + "".join(f"<th>{c}</th>" for c in cols) + "</tr>"
        for row in rows:
            html += "<tr>" + "".join(f"<td>{val}</td>" for val in row) + "</tr>"
        html += "</table>"
    html += "</body></html>"
    return html

if __name__ == "__main__":
    init_db()
    threading.Thread(target=update_population, daemon=True).start()
    app.run(host="0.0.0.0", port=10000, threaded=True)

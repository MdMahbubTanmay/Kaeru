import sqlite3
import json
import os
from flask import Flask, request, jsonify, render_template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "kaeru.db")
PASSWORD_FILE = os.path.join(BASE_DIR, "password.txt")

app = Flask(__name__, template_folder="templates")

# ---------- PASSWORD ----------
def get_server_password():
    if not os.path.exists(PASSWORD_FILE):
        return "admin"
    with open(PASSWORD_FILE, "r") as f:
        return f.read().strip()

# ---------- DATABASE ----------
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS timeline (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL
            )
        """)
        conn.execute("""
            INSERT OR IGNORE INTO timeline (id, data)
            VALUES (1, ?)
        """, (json.dumps({"checkpoints": []}),))

init_db()

# ---------- ROUTES ----------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/login", methods=["POST"])
def login():
    password = request.json.get("password", "")
    if password == get_server_password():
        return jsonify({"success": True})
    return jsonify({"success": False}), 403

@app.route("/api/data", methods=["GET"])
def load_data():
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.execute("SELECT data FROM timeline WHERE id=1")
            row = cur.fetchone()

            if row is None:
                # self-heal database
                empty_data = {"checkpoints": []}
                conn.execute(
                    "INSERT OR REPLACE INTO timeline (id, data) VALUES (1, ?)",
                    (json.dumps(empty_data),)
                )
                return jsonify(empty_data)

            return jsonify(json.loads(row[0]))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/save", methods=["POST"])
def save_data():
    try:
        payload = request.get_json(force=True)

        if payload.get("password") != get_server_password():
            return jsonify({"success": False}), 403

        data = payload.get("data")
        if data is None:
            return jsonify({"error": "No data provided"}), 400

        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                "UPDATE timeline SET data=? WHERE id=1",
                (json.dumps(data),)
            )

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/migrate", methods=["POST"])
def migrate():
    payload = request.json
    if payload.get("password") != get_server_password():
        return jsonify({"success": False}), 403

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "UPDATE timeline SET data=? WHERE id=1",
            (json.dumps(payload["data"]),)
        )
    return jsonify({"success": True, "message": "Migration completed"})

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=True)
# Uncomment the above lines to run the app directly.

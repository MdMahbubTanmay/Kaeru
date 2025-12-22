import sqlite3
import json
import os
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)
DB_FILE = "/var/data/kaeru.db" 
# (On your local computer, this path won't exist, so you might want to use logic like:)

import os
if os.environ.get('RENDER'):
    DB_FILE = "/var/data/kaeru.db"
else:
    DB_FILE = "kaeru.db"

# --- DATABASE SETUP ---
def init_db():
    """Creates the database file and table if they don't exist."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS timeline (id INTEGER PRIMARY KEY, data TEXT)")
        
        # Check if empty, if so, insert a blank record
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM timeline")
        if cursor.fetchone()[0] == 0:
            default_data = {"checkpoints": []}
            conn.execute("INSERT INTO timeline (id, data) VALUES (1, ?)", (json.dumps(default_data),))

# --- ROUTES ---

@app.route('/')
def home():
    """Serves the HTML file."""
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    """Reads the JSON from the database."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute("SELECT data FROM timeline WHERE id=1")
        row = cursor.fetchone()
        # Return the data, or empty object if something went wrong
        return jsonify(json.loads(row[0])) if row else {}

@app.route('/api/save', methods=['POST'])
def save_data():
    """Writes the JSON to the database."""
    req_data = request.json
    password = req_data.get('password')
    app_data = req_data.get('data')

    # Security Check
    if password != "admin":
        return jsonify({"success": False, "message": "Wrong Password"}), 403

    # Save to SQLite
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("UPDATE timeline SET data = ? WHERE id=1", (json.dumps(app_data),))
    
    return jsonify({"success": True})

if __name__ == '__main__':
    init_db()
    print("Kaeru is running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
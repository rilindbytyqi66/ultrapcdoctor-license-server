from flask import Flask, request, jsonify
import sqlite3
import hashlib
from datetime import datetime, timedelta

app = Flask(__name__)

def get_db():
    return sqlite3.connect("licenses.db")

def hw_hash(hw):
    return hashlib.sha256(hw.encode()).hexdigest()

@app.route("/activate", methods=["POST"])
def activate():
    data = request.json
    key = data["key"]
    hwid = hw_hash(data["hwid"])

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT expires, hwid FROM licenses WHERE key=?", (key,))
    row = cur.fetchone()

    if not row:
        return jsonify({"ok": False, "msg": "Invalid license key"})

    expires, bound_hw = row

    if bound_hw and bound_hw != hwid:
        return jsonify({"ok": False, "msg": "License already used on another PC"})

    if datetime.utcnow() > datetime.fromisoformat(expires):
        return jsonify({"ok": False, "msg": "License expired"})

    cur.execute("UPDATE licenses SET hwid=? WHERE key=?", (hwid, key))
    db.commit()

    return jsonify({"ok": True, "days": (datetime.fromisoformat(expires) - datetime.utcnow()).days})

@app.route("/validate", methods=["POST"])
def validate():
    data = request.json
    key = data["key"]
    hwid = hw_hash(data["hwid"])

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT expires, hwid FROM licenses WHERE key=?", (key,))
    row = cur.fetchone()

    if not row:
        return jsonify({"ok": False})

    expires, bound = row
    if bound != hwid:
        return jsonify({"ok": False})

    if datetime.utcnow() > datetime.fromisoformat(expires):
        return jsonify({"ok": False})

    return jsonify({"ok": True, "days": (datetime.fromisoformat(expires) - datetime.utcnow()).days})

app.run(host="0.0.0.0", port=5000)

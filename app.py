import os, sys, secrets, datetime, bcrypt
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pg8000.dbapi as pg
import urllib.parse as urlparse

app = Flask(__name__)
app.secret_key = "AdnanAI_Secret2026"

DATABASE_URL = os.environ.get("DATABASE_URL", "")

def get_conn():
    u = DATABASE_URL.replace('-pooler','')
    url = urlparse.urlparse(u)
    return pg.connect(user=url.username, password=url.password, host=url.hostname,
        port=url.port or 5432, database=url.path[1:] if url.path else "neondb", ssl_context=True)

def login_required(f):
    @wraps(f)
    def w(*a, **k):
        if not session.get("user"): return redirect(url_for("login"))
        return f(*a, **k)
    return w

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        pw = request.form.get("password","")
        device_fp = request.form.get("device_fp","")
        device_name = request.form.get("device_name","Unknown")

        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT password_hash, device_id, active FROM auth_users WHERE email=%s", (email,))
        user = c.fetchone()

        if not user:
            conn.close(); return render_template("login.html", error="Invalid email or password.")

        pw_hash, saved_device, active = user

        if not active:
            conn.close(); return render_template("login.html", error="Your account has been blocked by Admin.")

        if not bcrypt.checkpw(pw.encode(), pw_hash.encode()):
            conn.close(); return render_template("login.html", error="Invalid email or password.")

        if saved_device is None:
            c.execute("UPDATE auth_users SET device_id=%s, device_name=%s, last_login=%s WHERE email=%s",
                      (device_fp, device_name, str(datetime.datetime.now()), email))
            conn.commit()
        elif saved_device != device_fp:
            conn.close()
            return render_template("login.html", error="Login failed: This account is already active on another device. Please contact Admin (+92 306 3871230) to reset your device.")

        conn.close()
        session["user"] = email
        session.permanent = True
        return redirect(url_for("home"))

    return render_template("login.html", error=None)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def home():
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)

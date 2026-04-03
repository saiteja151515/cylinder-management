from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import bcrypt

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_db()
    c = conn.cursor()

    # USERS TABLE
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password BLOB,
        role TEXT
    )''')

    # REPORTS TABLE
    c.execute('''CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        user TEXT,
        opening_142 INTEGER,
        opening_19 INTEGER,
        received_142 INTEGER,
        received_19 INTEGER,
        sold_142 INTEGER,
        sold_19 INTEGER,
        closing_142 INTEGER,
        closing_19 INTEGER
    )''')

    # LOGS TABLE
    c.execute('''CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        action TEXT,
        time TEXT
    )''')

    conn.commit()
    conn.close()

# ---------------- CREATE USERS ----------------
def create_users():
    conn = get_db()
    c = conn.cursor()

    users = [
        ("admin", "admin123", "admin"),
        ("shafi", "shafi123", "user"),
        ("bhagath", "bhagath123", "user")
    ]

    for username, password, role in users:
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        if not c.fetchone():
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            c.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                      (username, hashed, role))

    conn.commit()
    conn.close()

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (user,))
        result = c.fetchone()

        if result and bcrypt.checkpw(pwd.encode(), result[2]):
            session["user"] = user
            session["role"] = result[3]

            if result[3] == "admin":
                return redirect("/admin")
            else:
                return redirect("/dashboard")

    return render_template("login.html")

# ---------------- DASHBOARD (USER + ADMIN) ----------------
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        o142 = int(request.form["o142"])
        o19 = int(request.form["o19"])
        r142 = int(request.form["r142"])
        r19 = int(request.form["r19"])
        s142 = int(request.form["s142"])
        s19 = int(request.form["s19"])

        # AUTO CALCULATION
        c142 = o142 + r142 - s142
        c19 = o19 + r19 - s19

        conn = get_db()
        c = conn.cursor()

        # SAVE REPORT
        c.execute("""INSERT INTO reports 
        (date,user,opening_142,opening_19,received_142,received_19,sold_142,sold_19,closing_142,closing_19)
        VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (datetime.now(), session["user"], o142,o19,r142,r19,s142,s19,c142,c19))

        # LOG ENTRY
        c.execute("INSERT INTO logs (user,action,time) VALUES (?,?,?)",
                  (session["user"], "Added Report", datetime.now()))

        conn.commit()
        conn.close()

    return render_template("dashboard.html")

# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return "Access Denied"

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM reports")
    reports = c.fetchall()

    c.execute("SELECT * FROM logs ORDER BY time DESC")
    logs = c.fetchall()

    conn.close()

    return render_template("admin.html", reports=reports, logs=logs)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN APP ----------------
init_db()
create_users()

if __name__ == "__main__":
    app.run()

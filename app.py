from flask import Flask, render_template, request, session, redirect, url_for
import random
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            attempts INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_score(username, attempts):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO scores (username, attempts) VALUES (?, ?)", (username, attempts))
    conn.commit()
    conn.close()

def get_scores():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, attempts FROM scores ORDER BY attempts ASC LIMIT 5")
    scores = cursor.fetchall()
    conn.close()
    return scores

# ---------- GAME LOGIC ----------
def set_difficulty(level):
    if level == "easy":
        return 1, 50, 10
    elif level == "medium":
        return 1, 100, 7
    elif level == "hard":
        return 1, 200, 5

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    hint = ""

    if "username" not in session:
        return render_template("index.html", ask_name=True)

    if "number" not in session:
        return render_template("index.html", game_started=False, username=session["username"], scores=get_scores())

    if request.method == "POST":
        guess = request.form.get("guess")

        if not guess or not guess.isdigit():
            message = "Enter valid number!"
        else:
            guess = int(guess)
            session["attempts"] -= 1

            if guess < session["number"]:
                message = "Too low!"
                session["low"] = max(session["low"], guess + 1)
            elif guess > session["number"]:
                message = "Too high!"
                session["high"] = min(session["high"], guess - 1)
            else:
                used_attempts = session["max_attempts"] - session["attempts"]
                save_score(session["username"], used_attempts)
                message = f"🎉 You won in {used_attempts} attempts!"
                session.pop("number")
                return render_template("index.html", game_started=False, message=message, scores=get_scores(), username=session["username"])

            hint = f"{session['low']} - {session['high']}"

            if session["attempts"] <= 0:
                message = f"💀 Lost! Number was {session['number']}"
                session.pop("number")
                return render_template("index.html", game_started=False, message=message, scores=get_scores(), username=session["username"])

    return render_template(
        "index.html",
        game_started=True,
        attempts=session["attempts"],
        hint=hint,
        message=message,
        username=session["username"]
    )

@app.route("/setname", methods=["POST"])
def setname():
    session["username"] = request.form.get("username")
    return redirect(url_for("index"))

@app.route("/start/<level>")
def start(level):
    low, high, attempts = set_difficulty(level)

    session["number"] = random.randint(low, high)
    session["low"] = low
    session["high"] = high
    session["attempts"] = attempts
    session["max_attempts"] = attempts

    return redirect(url_for("index"))

@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
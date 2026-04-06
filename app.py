#app.py
from flask import Flask, request, jsonify, redirect, render_template, make_response, url_for
import sqlite3
import bcrypt
from flask_jwt_extended import JWTManager, verify_jwt_in_request, create_access_token, jwt_required, get_jwt_identity, decode_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
from itsdangerous import URLSafeTimedSerializer
import smtplib
from email.mime.text import MIMEText
from werkzeug.security import generate_password_hash

# ---------------- INIT ----------------
load_dotenv()

app = Flask(__name__)




# Secure session settings
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,      #use False for local testing
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=1800
)

# JWT cookie config
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False   #True in production (HTTPS)
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 1800
limiter = Limiter(get_remote_address, app=app)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET")

jwt = JWTManager(app)

# session key (for OAuth)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev_secret_key_12345678901234567890")

@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';"

    return response

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        team_id INTEGER,
        score INTEGER DEFAULT 0
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS challenges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        category TEXT,
        author TEXT,
        points INTEGER,
        file_link TEXT,
        flag TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_email TEXT,
        action TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

init_db()

# ---------------- forget pwd ------------
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

EMAIL_ADDRESS = "harsinianbarasan.1@gmail.com"
EMAIL_PASSWORD = os.getenv("APP_PWD")
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
def generate_reset_token(email):
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    try:
        return serializer.loads(token, salt='password-reset-salt', max_age=expiration)
    except:
        return None

def send_reset_email(to_email, reset_link):
    msg = MIMEText(f"Click to reset password:\n{reset_link}")
    msg['Subject'] = "Password Reset"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        # ---------------- DB CHECK ---------------- #
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        conn.close()

        # ---------------- RESPONSE ---------------- #
        if user:
            token = generate_reset_token(email)
            reset_link = url_for('reset_password', token=token, _external=True)
            send_reset_email(email, reset_link)

        return "If the email exists, a reset link has been sent."

    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)

    if not email:
        return "Invalid or expired link"

    if request.method == 'POST':
        new_password = request.form.get('password')

        # ✅ use bcrypt (same as signup)
        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password=? WHERE email=?", (hashed, email))
        conn.commit()
        conn.close()

        return "Password updated successfully"

    return render_template('reset_password.html')

# ---------------- profile ---------------
@app.route("/api/profile")
@jwt_required()
def profile():
    user_id = get_jwt_identity()

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # user info
    cur.execute("SELECT name, email, score, team_id FROM users WHERE id=?", (user_id,))
    user = cur.fetchone()

    name, email, score, team_id = user

    team_name = None

    if team_id:
        cur.execute("SELECT name FROM teams WHERE id=?", (team_id,))
        team = cur.fetchone()
        if team:
            team_name = team[0]

    return jsonify({
        "name": name,
        "email": email,
        "score": score or 0,
        "team": team_name or "No Team"
    })

# ---------------- SIGNUP ----------------
@app.route("/signup", methods=["POST"])
def signup():
    data = request.json or {}

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"msg": "All fields required"}), 400

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    role = "admin" if email == "admin@ctf.com" else "user"

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, hashed.decode(), role)
        )

        cur.execute(
            "INSERT INTO logs (user_email, action) VALUES (?, ?)",
        (email, "User Registered"))

        conn.commit()
    except:
        return jsonify({"msg": "User already exists"}), 400

    return jsonify({"msg": f"{role} created"})


# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.json or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"msg": "Missing fields"}), 400

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT id, password, role FROM users WHERE email=?", (email,))
    user = cur.fetchone()

    if not user:
        return jsonify({"msg": "Invalid email"}), 401

    if not bcrypt.checkpw(password.encode(), user[1].encode()):
        return jsonify({"msg": "Wrong password"}), 401
    
    cur.execute(
    "INSERT INTO logs (user_email, action) VALUES (?, ?)",
    (email, "User Logged In"))
    conn.commit()

    # ✅ use STRING identity (fixes 422)
    token = create_access_token(
        identity=str(user[0]),
        additional_claims={"role": user[2]}
    )

    response = make_response(jsonify({"msg": "Login successful"}))
    response.set_cookie(
        "access_token_cookie",
        token,
        httponly=True,
        secure=False,   # True in production
        samesite="Lax"
    )
    return response


# ---------------- OAUTH ----------------
app.config["GOOGLE_CLIENT_ID"] = os.getenv("GOOGLE_CLIENT_ID")
app.config["GOOGLE_CLIENT_SECRET"] = os.getenv("GOOGLE_CLIENT_SECRET")

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

@app.route("/login/google")
def google_login():
    return google.authorize_redirect("http://nullarena.duckdns.org:5000/callback")


@app.route("/callback")
def callback():
    # 🔐 get token from Google
    token = google.authorize_access_token()

    # 👤 extract user info
    user_info = token.get("userinfo")

    if not user_info:
        return "Failed to fetch user info", 400

    email = user_info.get("email")
    name = user_info.get("name", "GoogleUser")

    if not email:
        return "Email not provided by Google", 400

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # 🔍 check if user exists
    cur.execute("SELECT id, role FROM users WHERE email=?", (email,))
    user = cur.fetchone()

    # ➕ create user if not exists
    if not user:
        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (name, email, "oauth", "user")   # ⚠️ can improve later
        )
        conn.commit()

        # 🔁 re-fetch user
        cur.execute("SELECT id, role FROM users WHERE email=?", (email,))
        user = cur.fetchone()

    # ❌ safety check
    if not user:
        return "User creation failed", 500

    user_id = user[0]
    role = user[1]

    # 🎫 create JWT
    jwt_token = create_access_token(
        identity=str(user_id),                 # ✅ MUST be string
        additional_claims={"role": role}       # ✅ role stored here
    )

    cur.execute(
        "INSERT INTO logs (user_email, action) VALUES (?, ?)",
    (email, "User Logged In via Google SSO"))
    conn.commit()
    # 🔀 redirect based on role
    if role == "admin":
        response = make_response(redirect("/admin"))
        response.set_cookie(
            "access_token_cookie",
            jwt_token,
            httponly=True,
            secure=False,
        samesite="Lax"
        )
        return response
    else:
        response = make_response(redirect("/dashboard"))
        response.set_cookie(
            "access_token_cookie",
            jwt_token,
            httponly=True,
            secure=False,   #True in production
            samesite="Lax"
        )
        return response
    
@app.route("/logout")
def logout():
    from flask import make_response

    response = make_response(redirect("/"))
    response.delete_cookie("access_token_cookie")
    return response
    
# ---------------- ROUTES ----------------
@app.route("/landing")
def landing():
    try:
        verify_jwt_in_request()
        return redirect("/dashboard")   # already logged in -> skip landing
    except:
        return render_template("landing.html")

@app.route("/")
def home():
    try:
        verify_jwt_in_request()
        return redirect("/dashboard")   # already logged in
    except:
        return redirect("/landing")     # send to landing page first

@app.route("/login", methods=["GET"])
def login_page():
    try:
        verify_jwt_in_request()
        return redirect("/dashboard")
    except:
        return render_template("index.html")  # existing login/signup page


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


from flask_jwt_extended import get_jwt

@app.route("/api/dashboard")
@jwt_required()
def dashboard_data():
    user_id = get_jwt_identity()
    claims = get_jwt()

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT name FROM users WHERE id=?", (user_id,))
    user = cur.fetchone()

    return jsonify({
        "user": {
            "name": user[0],
            "role": claims.get("role")
        }
    })


from flask_jwt_extended import get_jwt
@app.route("/api/add_challenge", methods=["POST"])
@jwt_required()
def add_challenge():
    
    claims = get_jwt()

    if claims.get("role") != "admin":
        return {"msg": "Forbidden"}, 403

    data = request.json

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO challenges 
        (title, description, category, author, points, file_link, flag)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("title"),
        data.get("description"),
        data.get("category"),
        data.get("author"),
        data.get("points"),
        data.get("file_link"),
        data.get("flag")
    ))

    conn.commit()

    return {"msg": "Challenge added successfully"}

@app.route("/api/challenges")
@jwt_required()
def get_challenges():
    user_id = get_jwt_identity()

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # 🔍 get user's team
    cur.execute("SELECT team_id FROM users WHERE id=?", (user_id,))
    team = cur.fetchone()

    solved = set()

    if team and team[0]:
        team_id = team[0]

        # ✅ get solves by ANY team member
        cur.execute("""
            SELECT s.challenge_id
            FROM solves s
            JOIN users u ON s.user_id = u.id
            WHERE u.team_id = ?
        """, (team_id,))

        solved = {r[0] for r in cur.fetchall()}

    else:
        # fallback (solo users)
        cur.execute("SELECT challenge_id FROM solves WHERE user_id=?", (user_id,))
        solved = {r[0] for r in cur.fetchall()}

    # 🔍 get all challenges
    cur.execute("SELECT id, title, description, category, author, points FROM challenges")
    rows = cur.fetchall()

    challenges = []
    for r in rows:
        challenges.append({
            "id": r[0],
            "title": r[1],
            "description": r[2],
            "category": r[3],
            "author": r[4],
            "points": r[5],
            "solved": r[0] in solved   # 🔥 team-based now
        })

    return {"challenges": challenges}

@app.route("/api/submit_flag", methods=["POST"])
@jwt_required()
def submit_flag():
    data = request.get_json()

    chal_id = data.get("challenge_id")
    user_flag = data.get("flag")
    user_id = get_jwt_identity()

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # 🔍 Get correct flag + points
    cur.execute("SELECT flag, points FROM challenges WHERE id=?", (chal_id,))
    challenge = cur.fetchone()

    if not challenge:
        return {"msg": "Challenge not found"}, 404

    correct_flag, points = challenge

    # ❌ Wrong flag
    if user_flag != correct_flag:
        return {"msg": "Wrong flag ❌"}

    # 🔒 Create solves table if not exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS solves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        challenge_id INTEGER
    )
    """)

   # 🔍 Get user's team
    cur.execute("SELECT team_id FROM users WHERE id=?", (user_id,))
    team = cur.fetchone()

    # 🔒 Check if team already solved
    if team and team[0]:
        team_id = team[0]

        cur.execute("""
            SELECT s.* FROM solves s
            JOIN users u ON s.user_id = u.id
            WHERE u.team_id = ? AND s.challenge_id = ?
        """, (team_id, chal_id))

    if cur.fetchone():
        return {"msg": "Already solved"}

    else:
        # fallback for solo users (no team)
        cur.execute(
            "SELECT * FROM solves WHERE user_id=? AND challenge_id=?",
            (user_id, chal_id)
        )
        if cur.fetchone():
            return {"msg": "Already solved ⚠️"}

    # ✅ Record solve
    cur.execute(
        "INSERT INTO solves (user_id, challenge_id) VALUES (?, ?)",
        (user_id, chal_id)
    )

    # 🧑 Add score column if not exists (safe)
    try:
        cur.execute("ALTER TABLE users ADD COLUMN score INTEGER DEFAULT 0")
    except:
        pass

    # 🧑 Update user score
    cur.execute(
        "UPDATE users SET score = score + ? WHERE id=?",
        (points, user_id)
    )

    # 👥 Update team score
    cur.execute("SELECT team_id FROM users WHERE id=?", (user_id,))
    team = cur.fetchone()

    if team and team[0]:
        try:
            cur.execute("ALTER TABLE teams ADD COLUMN score INTEGER DEFAULT 0")
        except:
            pass

        cur.execute(
            "UPDATE teams SET score = score + ? WHERE id=?",
            (points, team[0])
        )

    conn.commit()
    conn.close()

    return {"msg": f"Correct! 🎉 +{points} points"}


@app.route("/admin")
@jwt_required()
def admin():
    claims = get_jwt()

    if claims.get("role") != "admin":
        return redirect("/dashboard")

    return render_template("admin.html")

@app.route("/team")
def team():
    return render_template("teams.html")

@app.route("/api/create_team", methods=["POST"])
@jwt_required()
def create_team():
    data = request.json
    user_id = get_jwt_identity()

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    try:
        hashed_team_pw = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt())
        cur.execute(
        "INSERT INTO teams (name, password) VALUES (?, ?)",
            (data["name"], hashed_team_pw.decode())
        )
        team_id = cur.lastrowid

        cur.execute(
            "UPDATE users SET team_id=? WHERE id=?",
            (team_id, user_id)
        )

        cur.execute("SELECT name FROM users WHERE id=?", (user_id,))
        username = cur.fetchone()[0]

        conn.commit()

        return jsonify({
    "success": True,
    "team": {
        "name": data["name"],
        "points": 0,
        "members": [
            {
                "name": username,
                "score": 0
            }
        ]
    }
})

    except:
        return jsonify({
            "success": False,
            "error": "Team already exists"
        })

@app.route("/api/join_team", methods=["POST"])
@jwt_required()
def join_team():
    data = request.json
    user_id = get_jwt_identity()

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # 🔍 check team exists
    cur.execute("SELECT id, password FROM teams WHERE name=?", (data["name"],))
    team = cur.fetchone()

    if not team:
        return jsonify({
            "success": False,
            "error": "Team not found"
        })

    # 🔐 check password
    if not bcrypt.checkpw(data["password"].encode(), team[1].encode()):
        return jsonify({"success": False, "error": "Wrong password"})

    team_id = team[0]

    # 👤 assign user to team
    cur.execute(
        "UPDATE users SET team_id=? WHERE id=?",
        (team_id, user_id)
    )

    # 🛠 ensure team score column exists
    try:
        cur.execute("ALTER TABLE teams ADD COLUMN score INTEGER DEFAULT 0")
    except:
        pass

    #  get team name + score
    cur.execute("SELECT name, score FROM teams WHERE id=?", (team_id,))
    team_data = cur.fetchone()

    team_name = team_data[0]
    team_score = team_data[1] or 0

    # 👥 get members with scores
    cur.execute("SELECT name, score FROM users WHERE team_id=?", (team_id,))
    members = []

    for r in cur.fetchall():
        members.append({
            "name": r[0],
            "score": r[1] or 0
        })

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "team": {
            "name": team_name,
            "points": team_score,
            "members": members
        }
    })

@app.route("/api/team")
@jwt_required()
def get_team_info():
    user_id = get_jwt_identity()

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # get user's team
    cur.execute("SELECT team_id FROM users WHERE id=?", (user_id,))
    user = cur.fetchone()

    if not user or not user[0]:
        return jsonify({"team": None})

    team_id = user[0]

    # team name + points
    try:
        cur.execute("ALTER TABLE teams ADD COLUMN score INTEGER DEFAULT 0")
    except:
        pass

    cur.execute("SELECT name FROM teams WHERE id=?", (team_id,))
    team_name = cur.fetchone()[0]

    # CALCULATE TOTAL FROM USERS
    cur.execute("SELECT SUM(score) FROM users WHERE team_id=?", (team_id,))
    team_score = cur.fetchone()[0] or 0

    # members
    cur.execute("SELECT name, score FROM users WHERE team_id=?", (team_id,))
    members = [{"name": r[0], "score": r[1] or 0} for r in cur.fetchall()]
    return jsonify({
        "team": {
            "name": team_name,
            "points": team_score,   # ✅ correct total now
            "members": members
        }
    })
    

@app.route("/api/logs")
@jwt_required()
def get_logs():
    claims = get_jwt()

    if claims.get("role") != "admin":
        return {"msg": "Forbidden"}, 403

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT user_email, action, timestamp FROM logs ORDER BY id DESC")
    rows = cur.fetchall()

    logs = []
    for r in rows:
        logs.append({
            "email": r[0],
            "action": r[1],
            "time": r[2]
        })

    return {"logs": logs}

@app.route("/api/users")
@jwt_required()
def get_users():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT name, score FROM users ORDER BY score DESC")
    rows = cur.fetchall()

    users = []
    for r in rows:
        users.append({
            "name": r[0],
            "score": r[1] or 0
        })

    return {"users": users}

@app.route("/api/scoreboard")
@jwt_required()
def get_scoreboard():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # ensure score column exists (safe)
    try:
        cur.execute("ALTER TABLE teams ADD COLUMN score INTEGER DEFAULT 0")
    except:
        pass

    cur.execute("""
        SELECT t.name, COALESCE(SUM(u.score), 0) as total
        FROM teams t
        LEFT JOIN users u ON u.team_id = t.id
        GROUP BY t.id
        ORDER BY total DESC
    """)

    rows = cur.fetchall()

    teams = []
    for r in rows:
        teams.append({
            "name": r[0],
            "score": r[1]
        })

    return {"teams": teams}

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
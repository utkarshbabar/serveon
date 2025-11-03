from flask import Flask, render_template, redirect, url_for, request, flash, session, send_from_directory, jsonify
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json

app = Flask(__name__)
app.secret_key = 'dev_secret_key'  # Simple local secret key

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

bcrypt = Bcrypt(app)

# Local JSON files for simple storage
USERS_FILE = "users.json"
FILES_FILE = "files.json"


# ------------------ Helper Functions ------------------
def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return []

def save_data(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def get_all_users():
    return load_data(USERS_FILE)

def get_all_files():
    return load_data(FILES_FILE)

def add_user(username, password, role="user"):
    users = get_all_users()
    users.append({"username": username, "password": password, "role": role})
    save_data(USERS_FILE, users)

def add_file(display_name, category, original_filename, uploaded_by):
    files = get_all_files()
    uploaded_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    files.append({
        "display_name": display_name,
        "category": category,
        "original_filename": original_filename,
        "uploaded_by": uploaded_by,
        "uploaded_at": uploaded_at
    })
    save_data(FILES_FILE, files)


# ------------------ Routes ------------------

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    search_query = request.args.get("search", "").lower()
    files = get_all_files()
    if search_query:
        files = [f for f in files if
                 search_query in f['display_name'].lower() or
                 search_query in f['category'].lower() or
                 search_query in f['original_filename'].lower()]
    return render_template("index.html", files=files, user=session["user"], role=session["role"])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        users = get_all_users()
        for user in users:
            if user["username"] == username and bcrypt.check_password_hash(user["password"], password):
                session["user"] = username
                session["role"] = user["role"]
                return redirect(url_for("index"))
        flash("Invalid username or password", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        users = get_all_users()
        if any(u["username"] == username for u in users):
            flash("Username already exists!", "danger")
        else:
            add_user(username, password)
            flash("Account created successfully! Please login.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


CYBERSECURITY_CATEGORIES = [
    "Network Security", "Web Application Security", "Cloud Security", "Cryptography",
    "Penetration Testing", "Malware Analysis", "Digital Forensics", "Incident Response",
    "Threat Intelligence", "Vulnerability Assessment", "Ethical Hacking", "Red Teaming",
    "Blue Teaming", "Reverse Engineering", "Wireless Security", "IoT Security",
    "Social Engineering", "Security Tools & Scripts", "CTF Writeups",
    "Bug Bounty Reports", "OSINT (Open Source Intelligence)"
]


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        file = request.files["file"]
        display_name = request.form["display_name"]
        category = request.form["category"]

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            add_file(display_name, category, filename, session["user"])
            flash("File uploaded successfully!", "success")
            return redirect(url_for("index"))
    return render_template("upload.html", categories=CYBERSECURITY_CATEGORIES)


@app.route("/files/<path:filename>")
def download_file(filename):
    if "user" not in session:
        return redirect(url_for("login"))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route("/admin")
def admin():
    if "user" not in session" or session["role"] != "admin":
        flash("You are not authorized to access the admin page.", "danger")
        return redirect(url_for("index"))
    users = get_all_users()
    files = get_all_files()
    return render_template("admin.html", users=users, files=files)


# ------------------ Run ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

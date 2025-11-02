from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import cloudinary.uploader
import uuid
import os
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ------------------ MODELS ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(200))
    category = db.Column(db.String(100))
    original_filename = db.Column(db.String(200))
    cloudinary_url = db.Column(db.String(500))
    uploaded_by = db.Column(db.String(100))

# ------------------ ROUTES ------------------

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    search_query = request.args.get("search", "")
    files = File.query.filter(
        (File.display_name.ilike(f"%{search_query}%")) |
        (File.category.ilike(f"%{search_query}%")) |
        (File.original_filename.ilike(f"%{search_query}%"))
    ).all()
    return render_template("index.html", files=files, user=session["user"], role=session["role"])

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session["user"] = username
            session["role"] = user.role
            return redirect(url_for("index"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")
        if User.query.filter_by(username=username).first():
            flash("Username already exists!")
        else:
            db.session.add(User(username=username, password=password))
            db.session.commit()
            flash("Account created successfully!")
            return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        file = request.files["file"]
        display_name = request.form["display_name"]
        category = request.form["category"]
        if file:
            result = cloudinary.uploader.upload(file)
            new_file = File(
                display_name=display_name,
                category=category,
                original_filename=file.filename,
                cloudinary_url=result["secure_url"],
                uploaded_by=session["user"]
            )
            db.session.add(new_file)
            db.session.commit()
            flash("File uploaded successfully!")
            return redirect(url_for("index"))
    return render_template("upload.html")

@app.route("/admin")
def admin():
    if "user" not in session or session["role"] != "admin":
        return redirect(url_for("index"))
    users = User.query.all()
    files = File.query.all()
    return render_template("admin.html", users=users, files=files)

@app.route("/delete_user/<int:id>")
def delete_user(id):
    if session.get("role") == "admin":
        user = User.query.get(id)
        if user:
            db.session.delete(user)
            db.session.commit()
    return redirect(url_for("admin"))

@app.route("/delete_file/<int:id>")
def delete_file(id):
    if session.get("role") == "admin":
        file = File.query.get(id)
        if file:
            db.session.delete(file)
            db.session.commit()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)

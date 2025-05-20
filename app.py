from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from email.utils import formataddr
from datetime import datetime
from models import db, User, Score, Comment

load_dotenv(dotenv_path=".env", override=True)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "gizli_anahtar")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = formataddr(("CodeByEfe", app.config["MAIL_USERNAME"]))

mail = Mail(app)
db.init_app(app)
serializer = URLSafeTimedSerializer(app.secret_key)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/en")
def english_index():
    return render_template("index_en.html")

@app.route("/hakkimda")
def hakkimda():
    return render_template("hakkimda.html")

@app.route("/hakkimda_en")
def hakkimda_en():
    return render_template("hakkimda_en.html")

@app.route("/sertifikalar")
def sertifikalar():
    return render_template("sertifikalar.html")

@app.route("/sertifikalar_en")
def sertifikalar_en():
    return render_template("sertifikalar_en.html")

@app.route("/basarilar")
def basarilar():
    return render_template("basarilar.html")

@app.route("/achievements")
def achievements_en():
    return render_template("achievements_en.html")

@app.route("/minigame")
def minigame():
    return render_template("minigame.html", username=session.get("username"))

@app.route("/minigame_en")
def minigame_en():
    return render_template("minigame_en.html", username=session.get("username"))

@app.route("/cv")
def cv():
    return render_template("cv.html")

@app.route("/cv_en")
def cv_en():
    return render_template("cv_en.html")

@app.route('/download_cv')
def download_cv():
    return send_from_directory('static/cv', 'ismail_efe_yalcinkaya_cv.pdf', as_attachment=True)

@app.route('/download_cv_en')
def download_cv_en():
    return send_from_directory('static/cv', 'ismail_efe_yalcinkaya_cv_en.pdf', as_attachment=True)

@app.route("/register", methods=["GET", "POST"])
def register():
    lang = request.args.get("lang")
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        if User.query.filter_by(username=username).first():
            flash("Username already exists." if lang == "en" else "Kullanıcı adı zaten var.")
            return redirect("/register")

        user = User(username=username, email=email, password=password, aktif=False)
        db.session.add(user)
        db.session.commit()

        token = serializer.dumps(email, salt='email-confirm')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        msg = Message("Email Confirmation", recipients=[email])
        msg.body = f"Hi {username}, click the link to activate your account: {confirm_url}"
        mail.send(msg)

        flash("Please check your email to activate your account." if lang == "en" else "Lütfen hesabınızı aktifleştirmek için e-postanızı kontrol edin.")
        return redirect("/login")
    return render_template("register_en.html" if lang == "en" else "register.html")

@app.route('/confirm/<token>')
def confirm_email(token):
    lang = request.args.get("lang", "tr")
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except:
        return ("Token expired or invalid", 400) if lang == "en" else ("Bağlantının süresi doldu veya geçersiz.", 400)

    user = User.query.filter_by(email=email).first()
    if user:
        user.aktif = True
        db.session.commit()
        flash("Email confirmed. You can now log in." if lang == "en" else "E-posta onaylandı. Artık giriş yapabilirsiniz.")
        return redirect(f"/login?lang={lang}")
    return ("User not found.", 404) if lang == "en" else ("Kullanıcı bulunamadı.", 404)

@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next")
    lang = request.args.get("lang", "tr")
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.aktif and check_password_hash(user.password, password):
            session['username'] = username
            flash("Login successful." if lang == "en" else "Giriş başarılı.")
            return redirect(next_url or ("/en" if lang == "en" else "/"))
        flash("Invalid credentials or email not confirmed." if lang == "en" else "Geçersiz bilgiler ya da e-posta onaylanmamış.")
        return redirect(url_for('login', lang=lang))
    return render_template("login_en.html" if lang == "en" else "login.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    flash("Logged out.")
    return redirect(request.referrer or "/")

@app.route("/reset", methods=["GET", "POST"])
def reset_password():
    lang = request.args.get("lang", "tr")
    is_en = lang == "en"

    if request.method == "POST":
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(email, salt='reset-password')
            reset_url = url_for('reset_token', token=token, _external=True)
            msg = Message("Password Reset", recipients=[email])
            msg.body = f"Hi, click the link to reset your password:\n{reset_url}" if is_en else f"Merhaba, şifrenizi sıfırlamak için bağlantıya tıklayın:\n{reset_url}"
            mail.send(msg)
            flash("A password reset link has been sent to your email." if is_en else "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.")
        else:
            flash("No account found with this email." if is_en else "Bu e-posta ile kayıtlı hesap bulunamadı.")
        return redirect("/login?lang=en" if is_en else "/login")

    return render_template("reset_en.html" if is_en else "reset.html")


@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_token(token):
    lang = request.args.get("lang", "tr")
    is_en = lang == "en"

    try:
        email = serializer.loads(token, salt='reset-password', max_age=3600)
    except:
        return ("Reset link is invalid or has expired.", 400) if is_en else ("Bağlantı geçersiz veya süresi dolmuş.", 400)

    if request.method == "POST":
        user = User.query.filter_by(email=email).first()
        if user:
            new_password = generate_password_hash(request.form['password'])
            user.password = new_password
            db.session.commit()
            flash("Your password has been updated." if is_en else "Şifreniz güncellendi.")
            return redirect("/login?lang=en" if is_en else "/login")
        return ("User not found.", 404) if is_en else ("Kullanıcı bulunamadı.", 404)

    return render_template("reset_token_en.html" if is_en else "reset_token.html")

@app.route("/submit_score", methods=["POST"])
def submit_score():
    if 'username' not in session:
        return jsonify(success=False, message="Unauthorized"), 401
    username = session['username']
    score_val = int(request.form.get("score", 0))
    existing = Score.query.filter_by(username=username).first()
    newHighScore = False
    if existing:
        if score_val > existing.score:
            existing.score = score_val
            existing.timestamp = datetime.utcnow()
            db.session.commit()
            newHighScore = True
    else:
        db.session.add(Score(username=username, score=score_val))
        db.session.commit()
        newHighScore = True
    return jsonify(success=True, newHighScore=newHighScore)

@app.route("/leaderboard")
def leaderboard():
    skorlar = Score.query.order_by(Score.score.desc()).all()
    return render_template("leaderboard.html", skorlar=skorlar)

@app.route("/leaderboard_en")
def leaderboard_en():
    skorlar = Score.query.order_by(Score.score.desc()).all()
    return render_template("leaderboard_en.html", skorlar=skorlar)

@app.route("/forum", methods=["GET", "POST"])
def forum():
    if request.method == "POST":
        if 'username' not in session:
            flash("You must be logged in to comment.")
            return redirect(url_for("login", next="/forum"))
        yorum = Comment(
            username=session['username'],
            text=request.form.get("yorum"),
            rating=int(request.form.get("puan"))
        )
        db.session.add(yorum)
        db.session.commit()
        return redirect("/forum")
    yorumlar = Comment.query.order_by(Comment.timestamp.desc()).all()
    ortalama = round(sum(y.rating for y in yorumlar) / len(yorumlar), 1) if yorumlar else None
    return render_template("forum.html", yorumlar=yorumlar, ortalama=ortalama,
                           yorum_sayisi=len(yorumlar),
                           dolu_yildiz=int(round(ortalama)) if ortalama else 0,
                           bos_yildiz=5 - int(round(ortalama)) if ortalama else 5,
                           username=session.get("username"))

@app.route("/forum_en", methods=["GET", "POST"])
def forum_en():
    if request.method == "POST":
        if 'username' not in session:
            flash("You must be logged in to comment.")
            return redirect(url_for("login", next="/forum_en"))
        yorum = Comment(
            username=session['username'],
            text=request.form.get("yorum"),
            rating=int(request.form.get("puan"))
        )
        db.session.add(yorum)
        db.session.commit()
        return redirect("/forum_en")
    yorumlar = Comment.query.order_by(Comment.timestamp.desc()).all()
    ortalama = round(sum(y.rating for y in yorumlar) / len(yorumlar), 1) if yorumlar else None
    return render_template("forum_en.html", yorumlar=yorumlar, ortalama=ortalama,
                           yorum_sayisi=len(yorumlar),
                           dolu_yildiz=int(round(ortalama)) if ortalama else 0,
                           bos_yildiz=5 - int(round(ortalama)) if ortalama else 5,
                           username=session.get("username"))

@app.route("/admin")
def admin_panel():
    if session.get("username") != "efeyalcinkayaa":
        return "Yetkisiz erişim", 403
    users = User.query.all()
    scores = Score.query.order_by(Score.score.desc()).all()
    comments = Comment.query.order_by(Comment.timestamp.desc()).all()
    return render_template("admin.html", users=users, scores=scores, comments=comments)

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if session.get("username") != "efeyalcinkayaa":
        return "Yetkisiz erişim", 403
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash("Kullanıcı silindi.")
    return redirect("/admin")

@app.route("/delete_score/<int:score_id>")
def delete_score(score_id):
    if session.get("username") != "efeyalcinkayaa":
        return "Yetkisiz erişim", 403
    score = Score.query.get(score_id)
    if score:
        db.session.delete(score)
        db.session.commit()
        flash("Skor silindi.")
    return redirect("/admin")

@app.route("/delete_comment/<int:comment_id>")
def delete_comment(comment_id):
    if session.get("username") != "efeyalcinkayaa":
        return "Yetkisiz erişim", 403
    comment = Comment.query.get(comment_id)
    if comment:
        db.session.delete(comment)
        db.session.commit()
        flash("Yorum silindi.")
    return redirect("/admin")

@app.route("/google7dcd26d10df7aa08.html")
def google_verification():
    return "google-site-verification: google7dcd26d10df7aa08.html"

if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, redirect, session, url_for, flash
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from dotenv import load_dotenv
from email.utils import formataddr
from datetime import datetime
from flask import jsonify
from flask import send_from_directory

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'gizli_anahtar')

# Flask-Mail Ayarları
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = formataddr(("İsmail Efe", os.getenv('MAIL_USERNAME')))
mail = Mail(app)

serializer = URLSafeTimedSerializer(app.secret_key)

YORUM_DOSYASI = "yorumlar.json"
KULLANICI_DOSYASI = "users.json"
SKOR_DOSYASI = "scores.json"

def skor_yukle():
    if os.path.exists(SKOR_DOSYASI):
        with open(SKOR_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def skor_kaydet(skorlar):
    with open(SKOR_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(skorlar, f, ensure_ascii=False, indent=2)


@app.route("/minigame")
def minigame():
    skorlar = sorted(skor_yukle(), key=lambda x: x["score"], reverse=True)
    max_level = 6
    show_times = {level: max(1, int(6 - level * 0.2)) for level in range(1, 21)}
    return render_template("minigame.html", username=session.get("username"), skorlar=skorlar, max_level=max_level, show_times=show_times)


@app.route("/minigame_en")
def minigame_en():
    skorlar = sorted(skor_yukle(), key=lambda x: x["score"], reverse=True)
    max_level = 6
    show_times = {level: max(1, int(6 - level * 0.2)) for level in range(1, 21)}
    return render_template("minigame_en.html", username=session.get("username"), skorlar=skorlar, max_level=max_level, show_times=show_times)


@app.route("/submit_score", methods=["POST"])
def submit_score():
    if 'username' not in session:
        return jsonify(success=False, message="Unauthorized"), 401

    username = session['username']
    if username.lower() == "guest" or username.lower() == "misafir":
        return jsonify(success=False, message="Guests cannot submit scores."), 403

    score = int(request.form.get("score", 0))
    timestamp = datetime.now().isoformat()

    skorlar = skor_yukle()
    mevcut = next((s for s in skorlar if s["username"] == username), None)

    newHighScore = False

    if mevcut:
        if score > mevcut["score"]:
            mevcut["score"] = score
            mevcut["timestamp"] = timestamp
            newHighScore = True
    else:
        skorlar.append({"username": username, "score": score, "timestamp": timestamp})
        newHighScore = True

    skor_kaydet(skorlar)
    return jsonify(success=True, newHighScore=newHighScore)

@app.route("/leaderboard")
def leaderboard():
    skorlar = sorted(skor_yukle(), key=lambda x: x["score"], reverse=True)
    return render_template("leaderboard.html", skorlar=skorlar)

@app.route("/cv")
def cv():
    return render_template("cv.html")

@app.route('/download_cv')
def download_cv():
    return send_from_directory('static/cv', 'ismail_efe_yalcinkaya_cv.pdf', as_attachment=True)

@app.route('/cv_en')
def cv_en():
    return render_template('cv_en.html')

@app.route('/download_cv_en')
def download_cv_en():
    return send_from_directory('static/cv', 'ismail_efe_yalcinkaya_cv_en.pdf', as_attachment=True)

@app.route("/leaderboard_en")
def leaderboard_en():
    skorlar = sorted(skor_yukle(), key=lambda x: x["score"], reverse=True)
    return render_template("leaderboard_en.html", skorlar=skorlar)

def yorumlari_yukle():
    if os.path.exists(YORUM_DOSYASI):
        with open(YORUM_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def yorumlari_kaydet(yorumlar):
    with open(YORUM_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(yorumlar, f, ensure_ascii=False, indent=2)

def kullanicilari_yukle():
    if os.path.exists(KULLANICI_DOSYASI):
        with open(KULLANICI_DOSYASI, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def kullanicilari_kaydet(kullanicilar):
    with open(KULLANICI_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(kullanicilar, f, ensure_ascii=False, indent=2)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        kullanicilar = kullanicilari_yukle()
        if any(k['username'] == username for k in kullanicilar):
            flash("Username already exists.")
            return redirect("/register")

        token = serializer.dumps(email, salt='email-confirm')
        confirm_url = url_for('confirm_email', token=token, _external=True)
        msg = Message("Email Confirmation", recipients=[email])
        msg.body = f"Hi {username}, click the link to activate your account: {confirm_url}"

        try:
            mail.send(msg)
        except Exception as e:
            print("Mail gönderim hatası:", e)
            flash("E-posta gönderilemedi. Lütfen tekrar deneyin.")
            return redirect("/register")

        kullanicilar.append({"username": username, "email": email, "password": password, "aktif": False})
        kullanicilari_kaydet(kullanicilar)
        flash("Please check your email to activate your account.")
        return redirect("/login")
    lang = request.args.get("lang")
    return render_template("register_en.html" if lang == "en" else "register.html")

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=3600)
    except:
        return "Token expired or invalid", 400

    kullanicilar = kullanicilari_yukle()
    for k in kullanicilar:
        if k['email'] == email:
            k['aktif'] = True
            kullanicilari_kaydet(kullanicilar)
            flash("Email confirmed. You can now log in.")
            return redirect("/login")
    return "User not found", 404

@app.route("/reset", methods=["GET", "POST"])
def reset_password():
    lang = request.args.get("lang") == "en"

    if request.method == "POST":
        email = request.form['email']
        kullanicilar = kullanicilari_yukle()
        user = next((k for k in kullanicilar if k['email'] == email), None)
        if user:
            token = serializer.dumps(email, salt='reset-password')
            reset_url = url_for('reset_token', token=token, _external=True)
            msg = Message("Password Reset Request", recipients=[email])
            msg.body = f"Click the link to reset your password: {reset_url}"
            mail.send(msg)
            flash("A password reset link has been sent to your email." if lang else "Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.")
        else:
            flash("No account found with that email." if lang else "Bu e-posta ile kayıtlı hesap bulunamadı.")
        return redirect("/login?lang=en" if lang else "/login")

    return render_template("reset_en.html" if lang else "reset.html")

@app.route('/reset/<token>', methods=["GET", "POST"])
def reset_token(token):
    lang = request.args.get("lang") == "en"
    try:
        email = serializer.loads(token, salt='reset-password', max_age=3600)
    except:
        return ("Reset token is invalid or has expired.", 400) if lang else ("Sıfırlama bağlantısı geçersiz veya süresi dolmuş.", 400)

    if request.method == "POST":
        new_password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        kullanicilar = kullanicilari_yukle()
        for k in kullanicilar:
            if k['email'] == email:
                k['password'] = new_password
                kullanicilari_kaydet(kullanicilar)
                flash("Your password has been updated. You can now log in." if lang else "Şifreniz güncellendi. Artık giriş yapabilirsiniz.")
                return redirect("/login")
        return ("User not found.", 404) if lang else ("Kullanıcı bulunamadı.", 404)

    return render_template("reset_token_en.html" if lang else "reset_token.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    next_url = request.args.get("next")
    lang = "en" if next_url and "_en" in next_url else "tr"

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        kullanicilar = kullanicilari_yukle()
        user = next((k for k in kullanicilar if k['username'] == username), None)

        if user:
            if not user.get('aktif'):
                flash("Please confirm your email first." if lang == "en" else "Lütfen önce e-postanızı onaylayın.")
                return redirect(url_for('login', next=next_url))
            if check_password_hash(user['password'], password):
                session['username'] = username
                flash("Login successful." if lang == "en" else "Giriş başarılı.")
                return redirect(next_url or ("/en" if lang == "en" else "/"))
        flash("Invalid credentials." if lang == "en" else "Geçersiz kullanıcı adı veya şifre.")

    return render_template("login_en.html" if lang == "en" else "login.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    flash("Logged out.")
    return redirect(request.referrer or "/")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/hakkimda")
def hakkimda():
    return render_template("hakkimda.html")

@app.route("/sertifikalar")
def sertifikalar():
    return render_template("sertifikalar.html")

@app.route("/en")
def english_index():
    return render_template("index_en.html")

@app.route("/hakkimda_en")
def hakkimda_en():
    return render_template("hakkimda_en.html")

@app.route("/sertifikalar_en")
def sertifikalar_en():
    return render_template("sertifikalar_en.html")

@app.route("/basarilar")
def basarilar():
    return render_template("basarilar.html")

@app.route("/achievements")
def achievements_en():
    return render_template("achievements_en.html")

@app.route("/forum", methods=["GET", "POST"])
def forum():
    yorumlar = yorumlari_yukle()
    if request.method == "POST":
        if 'username' not in session:
            flash("You must be logged in to comment.")
            return redirect(url_for("login", next="/forum"))
        isim = session['username']
        yazi = request.form.get("yorum")
        puan = int(request.form.get("puan"))
        yorumlar.append({"isim": isim, "yazi": yazi, "puan": puan})
        yorumlari_kaydet(yorumlar)
        return redirect("/forum")

    ortalama = round(sum(y["puan"] for y in yorumlar) / len(yorumlar), 1) if yorumlar else None
    yorum_sayisi = len(yorumlar)
    dolu_yildiz = int(round(ortalama)) if ortalama else 0
    bos_yildiz = 5 - dolu_yildiz

    return render_template("forum.html", yorumlar=yorumlar, ortalama=ortalama, yorum_sayisi=yorum_sayisi,
                           dolu_yildiz=dolu_yildiz, bos_yildiz=bos_yildiz, username=session.get("username"))

@app.route("/forum_en", methods=["GET", "POST"])
def forum_en():
    yorumlar = yorumlari_yukle()

    if request.method == "POST":
        if 'username' not in session:
            flash("You must be logged in to comment.")
            return redirect(url_for("login", next="/forum_en"))
        isim = session['username']
        yazi = request.form.get("yorum")
        puan = int(request.form.get("puan"))
        tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        yorumlar.append({"isim": isim, "yazi": yazi, "puan": puan, "tarih": tarih})
        yorumlari_kaydet(yorumlar)
        return redirect("/forum_en")

    ortalama = round(sum(y["puan"] for y in yorumlar) / len(yorumlar), 1) if yorumlar else None
    yorum_sayisi = len(yorumlar)
    dolu_yildiz = int(round(ortalama)) if ortalama else 0
    bos_yildiz = 5 - dolu_yildiz

    return render_template("forum_en.html",
                           yorumlar=yorumlar,
                           ortalama=ortalama,
                           yorum_sayisi=yorum_sayisi,
                           dolu_yildiz=dolu_yildiz,
                           bos_yildiz=bos_yildiz,
                           username=session.get("username"))

if __name__ == "__main__":
    app.run(debug=True)

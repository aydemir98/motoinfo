from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import sqlite3
import os
import time
import qrcode
from PIL import Image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Veritabanı ilk çalıştırmada oluşturulsun
def create_users_table():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            plaka TEXT PRIMARY KEY,
            adsoyad TEXT,
            telefon TEXT,
            email TEXT,
            sosyal TEXT,
            foto TEXT,
            instagram TEXT,
            twitter TEXT,
            youtube TEXT
        )
    """)
    conn.commit()
    conn.close()

create_users_table()


# ✅ QR kodu logo ile üret
def generate_qr_with_logo(plaka):
    qr_url = f"https://motoinfo.onrender.com/user/{plaka}"  # kendi domainine göre değiştir

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    # Logoyu aç (orijinal boyutuyla)
    logo_path = "static/logo/logo3.png"
    logo = Image.open(logo_path).convert("RGBA")

    # QR ve logo boyutları
    qr_width, qr_height = qr_img.size
    logo_width, logo_height = logo.size

    # Ortaya yerleştir
    pos = ((qr_width - logo_width) // 2, (qr_height - logo_height) // 2)
    qr_img.paste(logo, pos, logo)

    # Kaydet
    qr_save_path = f"static/qr/{plaka}.png"
    qr_img.save(qr_save_path)

    return qr_save_path

# ✅ Ana sayfa ve form işleme
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        plaka = request.form['plaka'].strip().upper()
        adsoyad = request.form['adsoyad'].strip().title()
        telefon = request.form['telefon'].strip()
        email = request.form.get('email', '').strip()
        sosyal = request.form.get('sosyal', '').strip()
        instagram = request.form.get('instagram', '').strip()
        twitter = request.form.get('twitter', '').strip()
        youtube = request.form.get('youtube', '').strip()

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE plaka = ?", (plaka,))
        if c.fetchone():
            conn.close()
            profil_linki = url_for('profile', plaka=plaka)
            return render_template("form.html", error=f"Bu plakaya ait bir kayıt zaten var. <a href='{profil_linki}'>Profili Gör</a>")

        foto = request.files['foto']
        if foto and foto.filename != "":
            foto_filename = secure_filename(f"{plaka}_{int(time.time())}.jpg")
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], foto_filename))
        else:
            foto_filename = ""

        c.execute("""
            INSERT INTO users (plaka, adsoyad, telefon, email, sosyal, foto, instagram, twitter, youtube)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (plaka, adsoyad, telefon, email, sosyal, foto_filename, instagram, twitter, youtube))

        conn.commit()
        conn.close()

        return redirect(url_for('qr', plaka=plaka))

    return render_template("form.html")


# ✅ QR sayfası
@app.route("/qr/<plaka>")
def qr(plaka):
    generate_qr_with_logo(plaka)
    return render_template("qr.html", plaka=plaka)


# ✅ Profil sayfası
@app.route("/user/<plaka>")
def profile(plaka):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE plaka = ?", (plaka,))
    user = c.fetchone()
    conn.close()

    if user:
        info = {
            'Ad Soyad': user[1],
            'Telefon': user[2],
            'E-Posta': user[3],
            'Sosyal': user[4],
            'Foto': user[5],
            'instagram': user[6],
            'twitter': user[7],
            'youtube': user[8]
        }
        return render_template("profile.html", plaka=plaka, info=info)
    else:
        return "Kullanıcı bulunamadı", 404


if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists("static/qr"):
        os.makedirs("static/qr")
    app.run(debug=True)

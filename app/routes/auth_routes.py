# app/routes/auth_routes.py

# --- Impor Library ---
import re
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import (
    Blueprint, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    session, 
    flash, 
    jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

# --- Impor Modul Internal (Gunakan Impor Relatif) ---
from ..utils.db import query_db, execute_db
from ..utils.mailer import send_reset_email

# --- Definisi Blueprint ---
auth_bp = Blueprint('auth', __name__)

# --- Decorators untuk Autentikasi ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Anda harus login untuk mengakses halaman ini.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Harap login sebagai administrator untuk mengakses halaman ini.', 'warning')
            return redirect(url_for('auth.login_administrator'))
        return f(*args, **kwargs)
    return decorated_function

# --- Fungsi Helper ---
def validate_password(password):
    """Memvalidasi kompleksitas password."""
    errors = []
    if len(password) < 8:
        errors.append("Password harus memiliki minimal 8 karakter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password harus mengandung setidaknya satu huruf kecil.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password harus mengandung setidaknya satu huruf besar.")
    if not re.search(r"[0-9]", password):
        errors.append("Password harus mengandung setidaknya satu angka.")
    return errors

# --- Rute-Rute Autentikasi ---
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_identifier = request.form.get('login_identifier')
        password = request.form.get('password')

        if not login_identifier or not password:
            flash('Email/No. Telepon dan password harus diisi.', 'danger')
            return render_template('auth/login.html')

        query = "SELECT id, password_hash, display_name FROM users WHERE phone_number = %s OR email = %s"
        user = query_db(query, (login_identifier, login_identifier), one=True)
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['logged_in'] = True
            session['user_name'] = user['display_name']
            flash(f"Login berhasil! Selamat datang, {user['display_name']}.", 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Email/No. Telepon atau password salah.', 'danger')
            return render_template('auth/login.html')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        display_name = request.form.get('username')
        phone_number = request.form.get('phone')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Password dan konfirmasi password tidak cocok.', 'danger')
            return redirect(url_for('auth.register'))

        password_errors = validate_password(password)
        if password_errors:
            for error in password_errors:
                flash(error, 'danger')
            return redirect(url_for('auth.register'))

        existing_user = query_db("SELECT id FROM users WHERE phone_number = %s OR email = %s", (phone_number, email), one=True)
        if existing_user:
            flash('Nomor telepon atau email sudah terdaftar.', 'danger')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password)
        success = execute_db(
            "INSERT INTO users (display_name, phone_number, email, password_hash) VALUES (%s, %s, %s, %s)",
            (display_name, phone_number, email, hashed_password)
        )
        
        if success:
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registrasi gagal. Terjadi kesalahan pada server.', 'danger')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
def logout():
    session.clear() # Membersihkan semua data session
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = query_db("SELECT id, display_name, email FROM users WHERE email = %s", (email,), one=True)
        
        if user:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            execute_db("DELETE FROM password_reset_tokens WHERE user_id = %s", (user['id'],))
            execute_db(
                "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user['id'], token, expires_at)
            )
            if send_reset_email(user, token):
                flash('Link untuk mereset password telah dikirim ke email Anda.', 'success')
            else:
                flash('Gagal mengirim email reset. Coba lagi nanti.', 'danger')
        else:
            # Pesan umum untuk keamanan, agar tidak memberitahu email mana yang terdaftar
            flash('Jika email Anda terdaftar, Anda akan menerima link reset password.', 'info')
        
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    token_data = query_db("SELECT user_id, expires_at FROM password_reset_tokens WHERE token = %s", (token,), one=True)

    if not token_data or datetime.utcnow() > token_data['expires_at']:
        flash('Token reset password tidak valid atau telah kedaluwarsa.', 'danger')
        if token_data:
             execute_db("DELETE FROM password_reset_tokens WHERE token = %s", (token,))
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Password dan konfirmasi password tidak cocok.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        hashed_password = generate_password_hash(password)
        execute_db("UPDATE users SET password_hash = %s WHERE id = %s", (hashed_password, token_data['user_id']))
        execute_db("DELETE FROM password_reset_tokens WHERE token = %s", (token,))
        
        flash('Password Anda telah berhasil diperbarui! Silakan login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)

@auth_bp.route('/login_administrator', methods=['GET', 'POST'])
def login_administrator():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Di sini Anda bisa menggunakan hashing atau perbandingan langsung tergantung keamanan
        admin = query_db("SELECT id, username, password_hash FROM admins WHERE username = %s", (username,), one=True)

        if admin and admin['password_hash'] == password: # Ganti dengan check_password_hash jika password di-hash
            session['admin_id'] = admin['id']
            session['admin_logged_in'] = True
            session['admin_username'] = admin['username']
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Username atau password admin salah.', 'danger')
            return redirect(url_for('auth.login_administrator'))

    return render_template('admin/login.html')
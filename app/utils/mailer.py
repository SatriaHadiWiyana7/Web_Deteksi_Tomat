# app/utils/mailer.py
from flask import url_for
from flask_mail import Message
from app import mail # Impor objek mail dari __init__.py

def send_reset_email(user, token):
    reset_url = url_for('auth.reset_password_token', token=token, _external=True)
    msg_title = "Reset Password Akun Anda"
    msg_body = (
        f"Halo {user['display_name']},\n\n"
        "Seseorang (semoga Anda) telah meminta untuk mereset password akun Anda.\n"
        "Silakan klik link di bawah ini untuk melanjutkan:\n"
        f"{reset_url}\n\n"
        "Link ini akan kedaluwarsa dalam 1 jam.\n"
        "Jika Anda tidak merasa meminta ini, abaikan saja email ini.\n\n"
        "Terima kasih."
    )
    msg = Message(subject=msg_title, recipients=[user['email']], body=msg_body)
    try:
        mail.send(msg)
        print(f"Email reset password berhasil dikirim ke {user['email']}")
        return True
    except Exception as e:
        print(f"Gagal mengirim email ke {user['email']}: {e}")
        return False
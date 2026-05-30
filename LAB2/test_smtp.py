#!/usr/bin/env python3
import smtplib
import ssl

# ВСТАВЬТЕ ВАШИ ДАННЫЕ
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@gmail.com"
SMTP_PASS = "your_16_char_app_password"  # Пароль приложения
TEST_EMAIL_TO = "your_email@gmail.com"

def test_smtp():
    print(f"🔍 Тестируем Gmail SMTP...")
    print(f"   Хост: {SMTP_HOST}:{SMTP_PORT}")
    print(f"   Пользователь: {SMTP_USER}")
    print()
    
    try:
        print("📡 Устанавливаем соединение...")
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        
        print("🔐 Начинаем TLS...")
        server.starttls()
        
        print("🔐 Логинимся...")
        server.login(SMTP_USER, SMTP_PASS)
        print("✅ SMTP соединение успешно установлено!")
        
        print("📧 Отправляем тестовое письмо...")
        msg = f"""Subject: Test Email from Smart Home API

Hello!

This is a test email to verify SMTP configuration for Gmail.

If you see this message, SMTP is working correctly!

---
Smart Home API Test
"""
        server.sendmail(SMTP_USER, TEST_EMAIL_TO, msg.encode('utf-8'))
        print(f"✅ Тестовое письмо отправлено на {TEST_EMAIL_TO}!")
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Ошибка аутентификации: {e}")
        print("   Убедитесь, что:")
        print("   1. Вы используете пароль приложения (16 символов)")
        print("   2. Включена двухфакторная аутентификация")
        print("   3. Пароль скопирован без пробелов")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    test_smtp()
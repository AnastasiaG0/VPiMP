#!/usr/bin/env python3
import smtplib
import ssl
import sys

# ВСТАВЬТЕ ВАШИ РЕАЛЬНЫЕ ДАННЫЕ ИЗ .env
SMTP_HOST = "smtp.yandex.ru"
SMTP_PORT = 465
SMTP_USER = "gummelanastasia@yandex.ru"
SMTP_PASS = "fwmiyrndnpbwirab"       # Пароль приложения
TEST_EMAIL_TO = "gummelanastasia@yandex.ru"

def test_smtp():
    print(f"🔍 Тестируем SMTP соединение...")
    print(f"   Хост: {SMTP_HOST}:{SMTP_PORT}")
    print(f"   Пользователь: {SMTP_USER}")
    print(f"   Получатель: {TEST_EMAIL_TO}")
    print()
    
    try:
        print("📡 Устанавливаем SSL соединение...")
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            print("🔐 Логинимся...")
            server.login(SMTP_USER, SMTP_PASS)
            print("✅ SMTP соединение успешно установлено!")
            
            print("📧 Отправляем тестовое письмо...")
            msg = f"""Subject: Test Email from Smart Home API

Привет!

Это тестовое письмо для проверки SMTP настроек.

Если вы видите это сообщение, значит SMTP работает корректно!

---
Smart Home API Test
"""
            server.sendmail(SMTP_USER, TEST_EMAIL_TO, msg.encode('utf-8'))
            print(f"✅ Тестовое письмо отправлено на {TEST_EMAIL_TO}!")
            print("📨 Проверьте ваш почтовый ящик (возможно, письмо попадет в СПАМ)")
            return True
            
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Ошибка аутентификации: {e}")
        print("   Возможные причины:")
        print("   1. Неправильный пароль (используйте пароль приложения, а не основной)")
        print("   2. Неправильный формат email (должен быть полный email)")
        print("   3. Для Gmail нужно разрешить 'ненадежные приложения'")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP ошибка: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {e}")
        return False

def test_alternative_ports():
    """Тестирование альтернативных портов для Яндекс"""
    ports_to_test = [465, 587]
    
    for port in ports_to_test:
        print(f"\n🔍 Тестируем порт {port}...")
        try:
            if port == 465:
                # SSL соединение
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(SMTP_HOST, port, context=context) as server:
                    server.login(SMTP_USER, SMTP_PASS)
                    print(f"✅ Порт {port} работает с SSL")
            else:
                # STARTTLS соединение
                with smtplib.SMTP(SMTP_HOST, port) as server:
                    server.starttls()
                    server.login(SMTP_USER, SMTP_PASS)
                    print(f"✅ Порт {port} работает с STARTTLS")
        except Exception as e:
            print(f"❌ Порт {port} не работает: {str(e)[:100]}")

if __name__ == "__main__":
    print("=" * 50)
    print("SMTP ТЕСТЕР ДЛЯ SMART HOME API")
    print("=" * 50)
    print()
    
    # Проверка основной конфигурации
    success = test_smtp()
    
    if not success:
        print("\n🔧 Хотите проверить альтернативные порты? (y/n)")
        if input().lower() == 'y':
            test_alternative_ports()
    
    sys.exit(0 if success else 1)
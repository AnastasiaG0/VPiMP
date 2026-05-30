import asyncio
import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP"""
    
    def __init__(self):
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate SMTP configuration"""
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            logger.warning("⚠️ SMTP not configured. Email sending will be simulated.")
            return
        
        missing = []
        if not settings.SMTP_HOST: missing.append("SMTP_HOST")
        if not settings.SMTP_PORT: missing.append("SMTP_PORT")
        if not settings.SMTP_USER: missing.append("SMTP_USER")
        if not settings.SMTP_PASS: missing.append("SMTP_PASS")
        if not settings.SMTP_FROM: missing.append("SMTP_FROM")
        
        if missing:
            logger.warning(f"⚠️ Missing SMTP variables: {', '.join(missing)}. Email sending may fail.")
        
    def _create_welcome_email(
        self,
        to_email: str,
        display_name: str,
        user_id: str
    ) -> MIMEMultipart:
        """Create welcome email message"""
        
        # Plain text version
        text_content = f"""
Здравствуйте, {display_name}!

Добро пожаловать в Smart Home API!

Ваш аккаунт был успешно создан. Теперь вы можете:

• Управлять устройствами умного дома
• Настраивать автоматизацию
• Следить за состоянием вашего дома

Данные вашего аккаунта:
- ID пользователя: {user_id}
- Email: {to_email}

Для входа в систему перейдите по ссылке:
http://localhost:4200/auth/login

С уважением,
Команда Smart Home
        """
        
        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; background-color: #f9f9f9; }}
        .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #666; }}
        .button {{ display: inline-block; padding: 10px 20px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; }}
        .info {{ background-color: #e8f4e8; padding: 10px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Добро пожаловать в Smart Home!</h1>
        </div>
        <div class="content">
            <h2>Здравствуйте, {display_name}!</h2>
            <p>Рады приветствовать вас в системе управления умным домом.</p>
            <p>Ваш аккаунт был успешно создан. Теперь вы можете:</p>
            <ul>
                <li>Управлять устройствами умного дома</li>
                <li>Настраивать автоматизацию</li>
                <li>Следить за состоянием вашего дома</li>
            </ul>
            
            <div class="info">
                <strong>Данные вашего аккаунта:</strong><br>
                ID пользователя: {user_id}<br>
                Email: {to_email}
            </div>
            
            <p style="text-align: center;">
                <a href="http://localhost:4200/auth/login" class="button">Войти в систему</a>
            </p>
        </div>
        <div class="footer">
            <p>© 2024 Smart Home API. Все права защищены.</p>
            <p>Это автоматическое сообщение, пожалуйста, не отвечайте на него.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Добро пожаловать в Smart Home!"
        msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
        msg["To"] = to_email
        
        # Attach parts
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        
        return msg
    
    async def send_welcome_email(
        self,
        to_email: str,
        display_name: str,
        user_id: str
    ) -> bool:
        """
        Send welcome email to newly registered user
        
        Args:
            to_email: Recipient email address
            display_name: User's display name
            user_id: User ID
        
        Returns:
            bool: True if sent successfully
        """
        # If SMTP not configured, simulate email sending
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            logger.info(f"📧 [SIMULATED] Welcome email would be sent to {to_email}")
            logger.info(f"   Display name: {display_name}, User ID: {user_id}")
            return True
        
        try:
            # Create email
            msg = self._create_welcome_email(to_email, display_name, user_id)
            
            # Send email in thread pool (smtplib is blocking)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_sync,
                msg,
                to_email
            )
            
            logger.info(f"✉️ Welcome email sent to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP authentication failed: {e}")
            logger.error("   Please check your SMTP_USER and SMTP_PASS in .env")
            raise
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            raise
    
    def _send_sync(self, msg: MIMEMultipart, to_email: str) -> None:
        """Synchronous email sending"""
        context = None
        
        # Create SSL context for secure connection
        if settings.SMTP_SECURE:
            context = ssl.create_default_context()
        
        # Connect and send
        with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASS)
            server.send_message(msg)
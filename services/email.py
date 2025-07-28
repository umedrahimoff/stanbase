import os
import json
from typing import List, Optional
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Environment, Template
from pathlib import Path
from db import SessionLocal
from models import EmailTemplate

class EmailService:
    def __init__(self):
        # Конфигурация почты
        template_dir = Path(__file__).parent.parent / "templates" / "emails"
        self.conf = ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME", "noreply@stanbase.tech"),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
            MAIL_FROM=os.getenv("MAIL_FROM", "noreply@stanbase.tech"),
            MAIL_PORT=int(os.getenv("MAIL_PORT", "465")),
            MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.beget.com"),
            MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Stanbase"),
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True,
            USE_CREDENTIALS=True,
            TEMPLATE_FOLDER=template_dir
        )
        self.fastmail = FastMail(self.conf)

    def _get_template_from_db(self, template_code: str) -> Optional[EmailTemplate]:
        """Получить шаблон из базы данных"""
        db = SessionLocal()
        try:
            template = db.query(EmailTemplate).filter_by(code=template_code, is_active=True).first()
            return template
        finally:
            db.close()

    def _render_template(self, template_content: str, **kwargs) -> str:
        """Рендеринг шаблона с переменными"""
        try:
            template = Template(template_content)
            return template.render(**kwargs)
        except Exception as e:
            print(f"Ошибка рендеринга шаблона: {e}")
            return f"<p>Ошибка рендеринга шаблона: {str(e)}</p>"

    async def send_welcome_email(self, user_email: str, user_name: str):
        """Отправка приветственного письма при регистрации"""
        template = self._get_template_from_db("welcome")
        if not template:
            print("Шаблон приветственного письма не найден")
            return False
        
        html_content = self._render_template(
            template.html_content,
            user_name=user_name,
            site_url=os.getenv("SITE_URL", "https://stanbase.tech")
        )
        
        message = MessageSchema(
            subject=template.subject,
            recipients=[user_email],
            body=html_content,
            subtype="html"
        )
        
        try:
            await self.fastmail.send_message(message)
            return True
        except Exception as e:
            print(f"Ошибка отправки приветственного письма: {e}")
            return False

    async def send_password_reset_email(self, user_email: str, reset_token: str):
        """Отправка письма для сброса пароля"""
        template = self._get_template_from_db("password_reset")
        if not template:
            print("Шаблон сброса пароля не найден")
            return False
        
        reset_url = f"{os.getenv('SITE_URL', 'https://stanbase.tech')}/reset-password?token={reset_token}"
        
        html_content = self._render_template(
            template.html_content,
            reset_url=reset_url,
            site_url=os.getenv("SITE_URL", "https://stanbase.tech")
        )
        
        message = MessageSchema(
            subject=template.subject,
            recipients=[user_email],
            body=html_content,
            subtype="html"
        )
        
        try:
            await self.fastmail.send_message(message)
            return True
        except Exception as e:
            print(f"Ошибка отправки письма сброса пароля: {e}")
            return False

    async def send_email_verification(self, user_email: str, verification_token: str):
        """Отправка письма для подтверждения email"""
        template = self._get_template_from_db("email_verification")
        if not template:
            print("Шаблон подтверждения email не найден")
            return False
        
        verification_url = f"{os.getenv('SITE_URL', 'https://stanbase.tech')}/verify-email?token={verification_token}"
        
        html_content = self._render_template(
            template.html_content,
            verification_url=verification_url,
            site_url=os.getenv("SITE_URL", "https://stanbase.tech")
        )
        
        message = MessageSchema(
            subject=template.subject,
            recipients=[user_email],
            body=html_content,
            subtype="html"
        )
        
        try:
            await self.fastmail.send_message(message)
            return True
        except Exception as e:
            print(f"Ошибка отправки письма подтверждения: {e}")
            return False

    async def send_notification_email(self, user_email: str, subject: str, message: str):
        """Отправка уведомления по email"""
        template = self._get_template_from_db("notification")
        if not template:
            print("Шаблон уведомления не найден")
            return False
        
        html_content = self._render_template(
            template.html_content,
            message=message,
            site_url=os.getenv("SITE_URL", "https://stanbase.tech")
        )
        
        email_message = MessageSchema(
            subject=subject,
            recipients=[user_email],
            body=html_content,
            subtype="html"
        )
        
        try:
            await self.fastmail.send_message(email_message)
            return True
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")
            return False

    async def send_feedback_notification(self, feedback_data: dict):
        """Отправка уведомления о новой обратной связи"""
        template = self._get_template_from_db("feedback_notification")
        if not template:
            print("Шаблон уведомления об обратной связи не найден")
            return False
        
        html_content = self._render_template(
            template.html_content,
            feedback=feedback_data,
            site_url=os.getenv("SITE_URL", "https://stanbase.tech")
        )
        
        # Отправляем администраторам
        admin_emails = os.getenv("ADMIN_EMAILS", "").split(",")
        if admin_emails and admin_emails[0]:
            message = MessageSchema(
                subject=template.subject,
                recipients=admin_emails,
                body=html_content,
                subtype="html"
            )
            
            try:
                await self.fastmail.send_message(message)
                return True
            except Exception as e:
                print(f"Ошибка отправки уведомления об обратной связи: {e}")
                return False
        
        return False

# Создаем экземпляр сервиса
email_service = EmailService() 
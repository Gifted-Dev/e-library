from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from src.config import Config
from pathlib import Path


mail_config = ConnectionConfig(
    MAIL_USERNAME=Config.MAIL_USERNAME,
    MAIL_PASSWORD=Config.MAIL_PASSWORD,
  
    MAIL_FROM=Config.MAIL_FROM,
    MAIL_PORT=Config.MAIL_PORT,
    MAIL_SERVER=Config.MAIL_SERVER,
    MAIL_FROM_NAME=Config.MAIL_FROM_NAME,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    # Define the template folder path relative to this file's location.
    # This is more robust than using a hardcoded path or a config variable.
    TEMPLATE_FOLDER=Path(__file__).parent.parent / 'templates',
)

# Create Object to send emails with the config
mail = FastMail(mail_config)

def create_template_message(recipients: list[str], subject: str, template_body: dict) -> MessageSchema:
    """
    Creates a MessageSchema object specifically for sending an email
    based on a Jinja2 template.
    """
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        template_body=template_body,
        subtype=MessageType.html
    )
    
    return message

async def send_email(message: MessageSchema, template_name: str):
    """
    Sends an email. In development mode, it prints the content to the console.
    In production, it sends the email directly using fastapi-mail.
    """
    if Config.ENVIRONMENT == "development":
        # In development, print the email content to the console for easy testing.
        print("--- DEVELOPMENT EMAIL ---")
        print(f"Subject: {message.subject}")
        print(f"To: {message.recipients}")
        print("Template Body (placeholders):")
        print(message.template_body)
        print("--- END DEVELOPMENT EMAIL ---")
    else:
        # In production, send the email directly. This should be called from a
        # background worker (like Celery) to avoid blocking the main application.
        await mail.send_message(message, template_name=template_name)

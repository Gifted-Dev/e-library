from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from fastapi import BackgroundTasks
from src.config import Config, PROJECT_ROOT
from pathlib import Path


mail_config = ConnectionConfig(
    MAIL_USERNAME=Config.MAIL_USERNAME,
    MAIL_PASSWORD=Config.MAIL_PASSWORD,
  
    MAIL_FROM=Config.MAIL_FROM,
    MAIL_PORT=Config.MAIL_PORT,
    MAIL_SERVER=Config.MAIL_SERVER,
    MAIL_FROM_NAME=Config.MAIL_FROM_NAME,
    MAIL_STARTTLS=Config.MAIL_STARTTLS,
    MAIL_SSL_TLS=Config.MAIL_SSL_TLS,
    USE_CREDENTIALS=Config.USE_CREDENTIALS,
    VALIDATE_CERTS=Config.VALIDATE_CERTS,
    TEMPLATE_FOLDER=PROJECT_ROOT / 'templates',
)

# Create Object to send emails with the config
mail = FastMail(mail_config)

def create_message(recipients: list[str], subject:str, body: str = None, template_body: dict = None):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body, # This can now be None when a template is used
        template_body=template_body,
        subtype=MessageType.html
    )
    
    return message

async def send_email(background_tasks: BackgroundTasks, message: MessageSchema, template_name: str):
    """
    Sends an email. In development mode, it prints the content to the console.
    In production, it sends the email using fastapi-mail.
    """
    if Config.ENVIRONMENT == "development":
        # In development, print the email content to the console for easy testing.
        print("--- DEVELOPMENT EMAIL ---")
        print(f"Subject: {message.subject}")
        print(f"To: {message.recipients}")
        print("Body (placeholders):")
        print(message.template_body)
        print("--- END DEVELOPMENT EMAIL ---")
    else:
        # In production, send the email in the background for better performance.
        background_tasks.add_task(mail.send_message, message, template_name=template_name)

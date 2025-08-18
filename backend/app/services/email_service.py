import smtplib
import secrets
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_verification_token() -> str:
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)


def send_email(to_email: str, subject: str, body_text: str, body_html: str = None) -> None:
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject

        # Add text version
        msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        
        # Add HTML version if provided
        if body_html:
            msg.attach(MIMEText(body_html, 'html', 'utf-8'))

        logger.info(f"Connecting to SMTP server: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        logger.info(f"Using email account: {settings.EMAIL_HOST_USER}")
        
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.set_debuglevel(1)  # Enable debug output
        server.starttls()
        
        logger.info("Authenticating with SMTP server...")
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        
        logger.info(f"Sending email to {to_email}...")
        server.sendmail(settings.DEFAULT_FROM_EMAIL, to_email, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {str(e)}")
        logger.error("Check your Gmail app password or enable 2-factor authentication")
        raise e
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error sending email: {str(e)}")
        raise e


def send_verification_email(to_email: str, username: str, verification_token: str) -> None:
    """Send email verification with HTML template"""
    subject = "✨ Verifica tu cuenta en KandaStory"
    
    # Use correct frontend URL
    verification_url = f"http://localhost:5174/verify-email?token={verification_token}"
    
    # Text version
    body_text = f"""
Hola {username},

¡Bienvenido a KandaStory!

Para completar tu registro, por favor verifica tu dirección de correo electrónico haciendo clic en el siguiente enlace:

{verification_url}

Si no creaste esta cuenta, puedes ignorar este mensaje.

¡Gracias!
El equipo de KandaStory
    """
    
    # HTML version with beautiful template
    body_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verifica tu cuenta - KandaStory</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f8fafc;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-top: 20px;
                margin-bottom: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-align: center;
                padding: 40px 20px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .content {{
                padding: 40px 30px;
                text-align: center;
            }}
            .welcome-text {{
                font-size: 18px;
                margin-bottom: 10px;
                color: #374151;
            }}
            .username {{
                font-weight: 600;
                color: #667eea;
            }}
            .message {{
                font-size: 16px;
                color: #6b7280;
                margin: 20px 0 30px 0;
                line-height: 1.5;
            }}
            .verify-button {{
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                padding: 16px 32px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                margin: 20px 0;
                transition: transform 0.2s;
            }}
            .verify-button:hover {{
                transform: translateY(-2px);
            }}
            .footer {{
                background-color: #f9fafb;
                padding: 30px;
                text-align: center;
                color: #6b7280;
                font-size: 14px;
                border-top: 1px solid #e5e7eb;
            }}
            .logo {{
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 10px;
            }}
            .note {{
                font-size: 14px;
                color: #9ca3af;
                margin-top: 30px;
                padding: 15px;
                background-color: #f3f4f6;
                border-radius: 6px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">🎭 KandaStory</div>
                <h1>¡Bienvenido a KandaStory!</h1>
            </div>
            
            <div class="content">
                <p class="welcome-text">¡Hola <span class="username">{username}</span>!</p>
                
                <p class="message">
                    Gracias por registrarte en KandaStory. Para completar tu registro y acceder a todas las funcionalidades, 
                    necesitas verificar tu dirección de correo electrónico.
                </p>
                
                <a href="{verification_url}" class="verify-button">
                    ✨ Verificar mi cuenta
                </a>
                
                <div class="note">
                    Si no creaste esta cuenta, puedes ignorar este mensaje de forma segura.
                    Este enlace expirará en 24 horas.
                </div>
            </div>
            
            <div class="footer">
                <p>Con cariño,<br><strong>El equipo de KandaStory</strong></p>
                <p style="margin-top: 20px; font-size: 12px;">
                    Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
                    <span style="word-break: break-all;">{verification_url}</span>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    send_email(to_email, subject, body_text, body_html)

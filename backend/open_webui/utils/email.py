"""
Email utility for sending verification and password reset emails
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

log = logging.getLogger(__name__)

# Email configuration from environment
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", SMTP_USERNAME)
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "EdenHub AI")
WEBUI_URL = os.environ.get("WEBUI_URL", "http://localhost:8080")


def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None
) -> bool:
    """
    Send an email using SMTP configuration
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text fallback (optional)
    
    Returns:
        bool: True if sent successfully, False otherwise
    """
    
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        log.error("SMTP credentials not configured. Check .env file.")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg['To'] = to_email
        
        # Attach plain text version (if provided)
        if text_content:
            part1 = MIMEText(text_content, 'plain')
            msg.attach(part1)
        
        # Attach HTML version
        part2 = MIMEText(html_content, 'html')
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        
        log.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        log.error(f"Failed to send email to {to_email}: {e}")
        return False


def send_verification_email(to_email: str, to_name: str, token: str) -> bool:
    """Send email verification link"""
    
    verification_url = f"{WEBUI_URL}/auth/verify-email?token={token}"
    
    subject = "Verify Your Eden AI Account"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Welcome to EdenHub AI!</h1>
            </div>
            <div class="content">
                <h2>Hi {to_name},</h2>
                <p>Thanks for signing up! Please verify your email address to activate your account and start using EdenHub AI.</p>
                
                <div style="text-align: center;">
                    <a href="{verification_url}" class="button">Verify Email Address</a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="background: #fff; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {verification_url}
                </p>
                
                <p><strong>This link expires in 24 hours.</strong></p>
                
                <p>If you didn't create an account with EdenHub, please ignore this email.</p>
            </div>
            <div class="footer">
                <p>© 2024 EdenHub AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Welcome to EdenHub AI!
    
    Hi {to_name},
    
    Thanks for signing up! Please verify your email address by visiting:
    {verification_url}
    
    This link expires in 24 hours.
    
    If you didn't create an account, please ignore this email.
    
    © 2025 EdenHub AI
    """
    
    return send_email(to_email, subject, html_content, text_content)


def send_password_reset_email(to_email: str, to_name: str, token: str) -> bool:
    """Send password reset link"""
    
    reset_url = f"{WEBUI_URL}/auth/reset-password?token={token}"
    
    subject = "Reset Your Eden AI Password"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #ef4444; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #ef4444; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Password Reset Request</h1>
            </div>
            <div class="content">
                <h2>Hi {to_name},</h2>
                <p>We received a request to reset your EdenHub password. Click the button below to create a new password:</p>
                
                <div style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="background: #fff; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {reset_url}
                </p>
                
                <div class="warning">
                    <strong>⚠️ Security Notice:</strong>
                    <ul>
                        <li>This link expires in 1 hour</li>
                        <li>You can only use it once</li>
                        <li>If you didn't request this, please ignore this email</li>
                    </ul>
                </div>
                
                <p>Your password won't change until you access the link above and create a new one.</p>
            </div>
            <div class="footer">
                <p>© 2025 EdenHub AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Password Reset Request
    
    Hi {to_name},
    
    We received a request to reset your EdenHub password. Click this link to create a new password:
    {reset_url}
    
    SECURITY NOTICE:
    - This link expires in 1 hour
    - You can only use it once
    - If you didn't request this, please ignore this email
    
    Your password won't change until you create a new one using the link above.
    
    © 2025 EdenHub AI
    """
    
    return send_email(to_email, subject, html_content, text_content)
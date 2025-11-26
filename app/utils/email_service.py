"""
Email notification service for TerpSpark.
Supports both mock (console) and SMTP (real email) modes.
Configured via EMAIL_MODE environment variable.
"""
from sqlalchemy.orm import Session
from app.models.event import Event
from app.models.registration import Registration
from app.models.user import User
from app.core.config import settings
import logging
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service that supports both mock (console) and SMTP (real email) modes.
    Mode is controlled by EMAIL_MODE environment variable: "mock" or "smtp"
    """

    def __init__(self, db: Session):
        """
        Initialize email service.

        Args:
            db: Database session (for future use with email templates from DB)
        """
        self.db = db
        self.mode = settings.EMAIL_MODE.lower()
        self.templates_dir = Path(__file__).parent.parent / "templates" / "emails"

        # Validate mode
        if self.mode not in ["mock", "smtp"]:
            logger.warning(f"Invalid EMAIL_MODE '{self.mode}', defaulting to 'mock'")
            self.mode = "mock"

        logger.info(f"EmailService initialized in '{self.mode}' mode")

    def _send_smtp_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        qr_code_base64: Optional[str] = None
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            qr_code_base64: Base64 encoded QR code image (optional)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('related')
            msg['Subject'] = subject
            msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg['To'] = to_email

            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Attach QR code image if provided
            if qr_code_base64:
                # Remove data:image/png;base64, prefix if present
                if qr_code_base64.startswith('data:image/png;base64,'):
                    qr_code_base64 = qr_code_base64.replace('data:image/png;base64,', '')

                # Decode base64 to bytes
                qr_image_data = base64.b64decode(qr_code_base64)

                # Create image attachment
                image = MIMEImage(qr_image_data, name='qr_code.png')
                image.add_header('Content-ID', '<qr_code>')
                image.add_header('Content-Disposition', 'inline', filename='qr_code.png')
                msg.attach(image)

            # Connect to SMTP server and send
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()

                # Login
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

                # Send email
                server.send_message(msg)

            logger.info(f"SMTP email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMTP email to {to_email}: {str(e)}")
            return False

    def _print_mock_email(
        self,
        to_email: str,
        subject: str,
        content: str
    ):
        """Print mock email to console."""
        email_display = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    📧 MOCK EMAIL (Console Only)                  ║
╚══════════════════════════════════════════════════════════════════╝

TO: {to_email}
SUBJECT: {subject}

{content}

═══════════════════════════════════════════════════════════════════
        """
        logger.info(f"Mock email logged for {to_email}")
        print(email_display)

    def send_registration_confirmation(
        self,
        user: User,
        event: Event,
        registration: Registration
    ) -> bool:
        """
        Send registration confirmation email with ticket and QR code.

        Args:
            user: The user who registered
            event: The event they registered for
            registration: The registration record with ticket info

        Returns:
            bool: True if email sent successfully
        """
        # Format guest list
        guests_text = "No guests"
        if registration.guests and len(registration.guests) > 0:
            guest_names = [g['name'] for g in registration.guests]
            guests_text = f"{len(guest_names)} guest(s): {', '.join(guest_names)}"

        # Prepare template variables
        event_date = event.date.strftime('%B %d, %Y') if event.date else 'TBD'
        event_time_start = event.start_time.strftime('%I:%M %p') if event.start_time else 'TBD'
        event_time_end = event.end_time.strftime('%I:%M %p') if event.end_time else 'TBD'
        event_time = f"{event_time_start} - {event_time_end}"

        organizer_name = event.organizer.name if event.organizer else 'TBD'
        organizer_email = event.organizer.email if event.organizer else 'N/A'

        registered_at = registration.registered_at.strftime('%B %d, %Y %I:%M %p')

        subject = f"✅ Registration Confirmed - {event.title}"

        if self.mode == "smtp":
            # Load HTML template
            template_path = self.templates_dir / "registration_confirmation.html"

            if not template_path.exists():
                logger.error(f"Template not found: {template_path}")
                return False

            html_content = template_path.read_text()

            # Replace template variables
            html_content = html_content.replace('{{ user_name }}', user.name)
            html_content = html_content.replace('{{ event_title }}', event.title)
            html_content = html_content.replace('{{ event_date }}', event_date)
            html_content = html_content.replace('{{ event_time }}', event_time)
            html_content = html_content.replace('{{ event_venue }}', event.venue)
            html_content = html_content.replace('{{ event_location }}', event.location)
            html_content = html_content.replace('{{ organizer_name }}', organizer_name)
            html_content = html_content.replace('{{ organizer_email }}', organizer_email)
            html_content = html_content.replace('{{ registered_at }}', registered_at)
            html_content = html_content.replace('{{ guests_info }}', guests_text)
            html_content = html_content.replace('{{ ticket_code }}', registration.ticket_code)

            return self._send_smtp_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                qr_code_base64=registration.qr_code
            )
        else:
            # Mock mode - print to console
            content = f"""
Hi {user.name},

Congratulations! You're registered for {event.title}!

📅 EVENT DETAILS:
   Date: {event_date}
   Time: {event_time}
   Venue: {event.venue}
   Location: {event.location}
   Organizer: {organizer_name}

🎫 YOUR TICKET:
   Ticket Code: {registration.ticket_code}
   Registered At: {registered_at}
   Guests: {guests_text}

   [QR CODE ATTACHED]
   {registration.qr_code[:50]}... (truncated for display)

⚠️  IMPORTANT:
   • Save this email or screenshot your QR code
   • Present the QR code at event check-in
   • Arrive 10 minutes early for smooth check-in

📞 QUESTIONS?
   Contact the organizer: {organizer_email}

Thank you for using TerpSpark!
- The TerpSpark Team
            """
            self._print_mock_email(user.email, subject, content)
            return True

    def send_cancellation_confirmation(
        self,
        user: User,
        event: Event,
        registration: Registration
    ) -> bool:
        """
        Send cancellation confirmation email.

        Args:
            user: The user who cancelled
            event: The event they cancelled
            registration: The cancelled registration record

        Returns:
            bool: True if email sent successfully
        """
        event_date = event.date.strftime('%B %d, %Y') if event.date else 'TBD'
        event_time = event.start_time.strftime('%I:%M %p') if event.start_time else 'TBD'

        subject = f"🚫 Registration Cancelled - {event.title}"

        content = f"""
Hi {user.name},

Your registration for {event.title} has been successfully cancelled.

📅 EVENT DETAILS:
   Date: {event_date}
   Time: {event_time}
   Venue: {event.venue}

Your spot has been freed and may be given to someone on the waitlist.

Changed your mind? You can register again if spots are available.

- The TerpSpark Team
        """

        if self.mode == "smtp":
            # For now, use simple HTML wrapper
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                {content.replace(chr(10), '<br>')}
            </body>
            </html>
            """
            return self._send_smtp_email(user.email, subject, html_content)
        else:
            self._print_mock_email(user.email, subject, content)
            return True

    def send_waitlist_promotion(
        self,
        user: User,
        event: Event,
        registration: Registration,
        old_position: int
    ) -> bool:
        """
        Send waitlist promotion notification email.

        Args:
            user: The user who was promoted
            event: The event they're now registered for
            registration: The new registration record
            old_position: Their previous position in waitlist

        Returns:
            bool: True if email sent successfully
        """
        event_date = event.date.strftime('%B %d, %Y') if event.date else 'TBD'
        event_time_start = event.start_time.strftime('%I:%M %p') if event.start_time else 'TBD'
        event_time_end = event.end_time.strftime('%I:%M %p') if event.end_time else 'TBD'
        event_time = f"{event_time_start} - {event_time_end}"

        subject = f"🎉 Great News! You're Off the Waitlist - {event.title}"

        content = f"""
Hi {user.name},

Excellent news! A spot opened up and you've been AUTOMATICALLY REGISTERED
for {event.title}!

📅 EVENT DETAILS:
   Date: {event_date}
   Time: {event_time}
   Venue: {event.venue}
   Location: {event.location}

🎫 YOUR TICKET:
   Ticket Code: {registration.ticket_code}
   Previous Waitlist Position: #{old_position}

   [QR CODE ATTACHED]
   {registration.qr_code[:50]}... (truncated for display)

⚠️  CAN'T ATTEND?
   Please cancel your registration ASAP to free the spot for others!

Present this QR code at event check-in.

- The TerpSpark Team
        """

        if self.mode == "smtp":
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                {content.replace(chr(10), '<br>')}
            </body>
            </html>
            """
            return self._send_smtp_email(
                to_email=user.email,
                subject=subject,
                html_content=html_content,
                qr_code_base64=registration.qr_code
            )
        else:
            self._print_mock_email(user.email, subject, content)
            return True

    def send_waitlist_confirmation(
        self,
        user: User,
        event: Event,
        position: int
    ) -> bool:
        """
        Send waitlist join confirmation email.

        Args:
            user: The user who joined waitlist
            event: The event they joined waitlist for
            position: Their position in the waitlist

        Returns:
            bool: True if email sent successfully
        """
        event_date = event.date.strftime('%B %d, %Y') if event.date else 'TBD'
        event_time = event.start_time.strftime('%I:%M %p') if event.start_time else 'TBD'

        subject = f"📋 Added to Waitlist - {event.title}"

        content = f"""
Hi {user.name},

You've been added to the waitlist for {event.title}.

📅 EVENT DETAILS:
   Date: {event_date}
   Time: {event_time}
   Venue: {event.venue}
   Current Capacity: {event.capacity} (FULL)

📊 YOUR WAITLIST STATUS:
   Position: #{position}

We'll automatically register you and send a ticket if a spot opens up!

You can check your waitlist status anytime in your account.

- The TerpSpark Team
        """

        if self.mode == "smtp":
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                {content.replace(chr(10), '<br>')}
            </body>
            </html>
            """
            return self._send_smtp_email(user.email, subject, html_content)
        else:
            self._print_mock_email(user.email, subject, content)
            return True

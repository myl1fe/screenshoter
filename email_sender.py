import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
import logging

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self):
        self.smtp_server = None
        self.smtp_port = None
        self.username = None
        self.password = None
        self.from_addr = None
        self.to_addr = None
        self.enabled = False

    def configure(self, smtp_server, smtp_port, username, password, from_addr, to_addr, enabled=False):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.enabled = enabled

    def send_email(self, subject, body, attachments=None):
        if not self.enabled:
            logger.info("Отправка email отключена в настройках")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_addr
            msg['To'] = self.to_addr
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            if attachments:
                for attachment_path in attachments:
                    if os.path.exists(attachment_path):
                        attachment = open(attachment_path, "rb")
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(attachment_path)}")
                        msg.attach(part)
                        attachment.close()

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.from_addr, self.to_addr, text)
            server.quit()

            logger.info(f"Email успешно отправлен: {subject}")
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки email: {e}")
            return False
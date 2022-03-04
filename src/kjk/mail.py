import sendgrid
import os
from pprint import pprint
from sendgrid.helpers.mail import Mail, Email, To, Content
from kjk.logging import clog


class KjKEmailclient:
    def __init__(self):
        self.sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        self.from_email = Email(os.environ.get("MAILER_FROM"))
        self.to_email = To(os.environ.get("MAILER_TO"))
        self.subject = "Indelingsrapportage Kiesjekraam"

    def send_mail(self, message):
        content = Content("text/plain", message)
        mail = Mail(self.from_email, self.to_email, self.subject, content)
        mail_json = mail.get()
        if os.environ.get("MAIL_BACKEND") == "sendgrid":
            try:
                self.sg.client.mail.send.post(request_body=mail_json)
            except Exception:
                clog.error("Kon geen email sturen naar marktbureau.")

        elif os.environ.get("MAIL_BACKEND") == "console":
            pprint(mail_json)

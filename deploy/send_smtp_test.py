"""Send one SMTP test using DB settings (run on server)."""

from app import create_app
from app.services.email_service import EmailService
from app.services.settings_service import SettingsService

app = create_app()
with app.app_context():
    EmailService().send_test_email(SettingsService().get_smtp())
print("Test email sent.")

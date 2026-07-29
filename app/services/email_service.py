from __future__ import annotations

import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.models import SmtpSetting
from app.risk.levels import RiskLevels, format_risk_lines, levels_from_entry
from app.services.base import BaseService
from app.utils.logging_setup import get_logger

logger = get_logger("email")


class EmailService(BaseService[SmtpSetting]):
    def send_signal_alert(
        self,
        smtp: SmtpSetting,
        *,
        signal_type: str,
        symbol: str,
        timeframe: str,
        price: float,
        strategy_name: str,
        candle_time_utc: str,
        levels: RiskLevels | None = None,
    ) -> None:
        subject = smtp.subject_template.format(
            signal_type=signal_type,
            symbol=symbol.replace("/", ""),
        )
        levels = levels or levels_from_entry(signal_type, price)
        body = (
            "--------------------------------\n\n"
            f"{signal_type} Signal\n\n"
            f"Coin:\n{symbol.replace('/', '')}\n\n"
            f"Timeframe:\n{timeframe}\n\n"
            f"Price:\n{price}\n\n"
            f"Risk:\n{format_risk_lines(levels)}\n\n"
            f"Strategy:\n{strategy_name}\n\n"
            f"Time:\n{candle_time_utc}\n\n"
            "--------------------------------"
        )
        self._send(smtp, subject, body)

    def send_test_email(self, smtp: SmtpSetting) -> None:
        subject = "CryptoSignals SMTP test"
        body = (
            "CryptoSignals test email.\n\n"
            "If you received this message, SMTP settings are working."
        )
        self._send(smtp, subject, body)

    def _send(self, smtp: SmtpSetting, subject: str, body: str) -> None:
        if not smtp.smtp_server or not smtp.receiver_email:
            raise ValueError("SMTP server and receiver email are required")

        username = (smtp.username or "").strip()
        password = (smtp.password or "").replace(" ", "")
        if username and not password:
            raise ValueError(
                "SMTP password is empty. Re-enter your Gmail App Password and save."
            )

        message = EmailMessage()
        message["Subject"] = subject
        from_email = (smtp.sender_email or smtp.username or "").strip()
        if smtp.sender_name:
            message["From"] = formataddr((smtp.sender_name, from_email))
        else:
            message["From"] = from_email
        message["To"] = smtp.receiver_email.strip()
        message.set_content(body)

        port = int(smtp.smtp_port or 587)
        use_ssl = bool(smtp.use_ssl) and port == 465

        if use_ssl:
            with smtplib.SMTP_SSL(smtp.smtp_server, port, timeout=30) as server:
                server.ehlo()
                if username:
                    server.login(username, password)
                server.send_message(message)
        else:
            with smtplib.SMTP(smtp.smtp_server, port, timeout=30) as server:
                server.ehlo()
                if smtp.use_tls or port == 587:
                    server.starttls()
                    server.ehlo()
                if username:
                    server.login(username, password)
                server.send_message(message)

        logger.info("Email sent to %s", smtp.receiver_email)

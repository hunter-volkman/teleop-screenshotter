import os
import logging
import asyncio
import smtplib
from email.message import EmailMessage

from playwright.async_api import async_playwright
from google.cloud import secretmanager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# URLs
LOGIN_URL = os.getenv("LOGIN_URL", "https://app.viam.com")
TELEOP_URL = os.getenv("TELEOP_URL", "https://app.viam.com/teleop/your-teleop-id")

# Screenshot settings
SCREENSHOT_DIR = os.getenv("SCREENSHOT_DIR", "screenshots")
SCREENSHOT_FILENAME = os.getenv("SCREENSHOT_FILENAME", "teleop_demo.png")
SCREENSHOT_PATH = os.path.join(SCREENSHOT_DIR, SCREENSHOT_FILENAME)

# Capture interval (default: 30 minutes)
CAPTURE_INTERVAL_SECONDS = int(os.getenv("CAPTURE_INTERVAL_SECONDS", "1800"))

# Google Secret Manager configuration for sensitive data (and credentials)
# Set to "true" to retrieve sender credentials and SMTP config from Secret Manager
USE_SECRETS_MANAGER = os.getenv("USE_SECRETS_MANAGER", "true").lower() == "true"
# Your GCP project ID (required for Secret Manager)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

# Secret names for sender and SMTP credentials (stored securely in GCP Secret Manager)
EMAIL_SENDER_SECRET = os.getenv("EMAIL_SENDER_SECRET", "soleng-sender-email")
EMAIL_SMTP_SERVER_SECRET = os.getenv("EMAIL_SMTP_SERVER_SECRET", "soleng-smtp-server")
EMAIL_SMTP_SERVER_PORT_SECRET = os.getenv("EMAIL_SMTP_SERVER_PORT_SECRET", "soleng-smtp-port")
EMAIL_SMTP_USER_SECRET = os.getenv("EMAIL_SMTP_USER_SECRET", "soleng-smtp-user")
EMAIL_SMTP_PASSWORD_SECRET = os.getenv("EMAIL_SMTP_PASSWORD_SECRET", "soleng-smtp-password")

# For Google login credentials (assumed to be used by the dedicated "soleng" account)
GOOGLE_EMAIL_SECRET = os.getenv("GOOGLE_EMAIL_SECRET", "soleng-google-email")
GOOGLE_PASSWORD_SECRET = os.getenv("GOOGLE_PASSWORD_SECRET", "soleng-google-password")

# If not using Secret Manager, these can be provided via environment variables:
GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")
EMAIL_SMTP_SERVER_PORT = os.getenv("EMAIL_SMTP_SERVER_PORT")
EMAIL_SMTP_USER = os.getenv("EMAIL_SMTP_USER")
EMAIL_SMTP_PASSWORD = os.getenv("EMAIL_SMTP_PASSWORD")

def access_secret(secret_id: str) -> str:
    """
    Retrieves the latest version of a secret from Google Secret Manager.
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(name=name)
    secret_payload = response.payload.data.decode("UTF-8")
    return secret_payload.strip()

def load_recipient_emails(config_file="email_recipients.txt") -> list:
    """
    Loads recipient email addresses from a local file.
    Each non-empty line is treated as an email address.
    If the file is missing, falls back to the EMAIL_RECIPIENT environment variable.
    """
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                recipients = [line.strip() for line in f if line.strip()]
            logging.info("Loaded %d recipient(s) from %s", len(recipients), config_file)
            return recipients
        except Exception as e:
            logging.error("Error reading %s: %s", config_file, e)
    default_recipient = os.getenv("EMAIL_RECIPIENT")
    if default_recipient:
        logging.info("Using default recipient from environment variable.")
        return [default_recipient]
    logging.warning("No recipient emails configured.")
    return []

async def handle_google_login(page, email: str, password: str):
    """
    Automates the Google login flow.
    """
    logging.info("Starting Google login flow...")
    await page.click('button:has-text("Login with Google")')
    await page.wait_for_selector('input[type="email"]')
    await page.fill('input[type="email"]', email)
    await page.click('button:has-text("Next")')
    await page.wait_for_selector('input[type="password"]', timeout=10000)
    await page.fill('input[type="password"]', password)
    await page.click('button:has-text("Next")')
    await page.wait_for_load_state("networkidle", timeout=30000)
    logging.info("Google login completed")

async def capture_screenshot(page, teleop_url: str, output_path: str):
    """
    Navigates to the teleop page and captures a screenshot.
    """
    logging.info("Navigating to teleop URL: %s", teleop_url)
    await page.goto(teleop_url)
    await page.wait_for_selector("body", timeout=10000)
    logging.info("Waiting 3 seconds to ensure page load...")
    await asyncio.sleep(3)
    await page.screenshot(path=output_path)
    logging.info("Screenshot saved to %s", output_path)

def send_email(recipients: list, sender: str, smtp_config: dict, screenshot_path: str):
    """
    Sends an email with the screenshot attached.
    """
    msg = EmailMessage()
    msg["Subject"] = "Teleop Screenshot Demo"
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content("Attached is the teleop screenshot demo.")

    try:
        with open(screenshot_path, "rb") as f:
            msg.add_attachment(f.read(), maintype='image', subtype='png', filename=os.path.basename(screenshot_path))
    except Exception as e:
        logging.error("Failed to read screenshot for email attachment: %s", e)
        return

    try:
        with smtplib.SMTP(smtp_config["server"], int(smtp_config["port"])) as server:
            server.starttls()
            server.login(smtp_config["user"], smtp_config["password"])
            server.send_message(msg)
        logging.info("Email sent to %s", ", ".join(recipients))
    except Exception as e:
        logging.error("Error sending email: %s", e)

async def process_capture_and_email(google_email: str, google_password: str,
                                    teleop_url: str, screenshot_path: str,
                                    email_config: dict = None):
    """
    Runs the browser session to log into Viam via Google login,
    captures a screenshot, and sends an email if configured.
    """
    logging.info("Starting Playwright session...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(LOGIN_URL)
        await handle_google_login(page, google_email, google_password)
        await capture_screenshot(page, teleop_url, screenshot_path)
        await browser.close()

    if email_config:
        send_email(email_config["recipients"], email_config["sender"], email_config, screenshot_path)
    else:
        logging.info("Email not configured; skipping email notification.")

async def main():
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)

    # Load recipient emails from a local configuration file
    recipients = load_recipient_emails("email_recipients.txt")

    # Retrieve credentials from Secret Manager if enabled
    if USE_SECRETS_MANAGER:
        if not GCP_PROJECT_ID:
            logging.error("GCP_PROJECT_ID is not set. Cannot access secrets.")
            return
        try:
            google_email = access_secret(GOOGLE_EMAIL_SECRET)
            google_password = access_secret(GOOGLE_PASSWORD_SECRET)
            logging.info("Retrieved Google credentials from Secret Manager.")

            # Retrieve sender and SMTP credentials from Secret Manager
            sender = access_secret(EMAIL_SENDER_SECRET)
            smtp_server = access_secret(EMAIL_SMTP_SERVER_SECRET)
            smtp_port = access_secret(EMAIL_SMTP_SERVER_PORT_SECRET) if EMAIL_SMTP_SERVER_PORT_SECRET else "587"
            smtp_user = access_secret(EMAIL_SMTP_USER_SECRET)
            smtp_password = access_secret(EMAIL_SMTP_PASSWORD_SECRET)

            # Build email config only if there is at least one recipient
            email_config = {
                "recipients": recipients,
                "sender": sender,
                "server": smtp_server,
                "port": smtp_port,
                "user": smtp_user,
                "password": smtp_password,
            } if recipients else None
        except Exception as e:
            logging.error("Error retrieving secrets: %s", e)
            return
    else:
        # Fall back to using environment variables
        google_email = GOOGLE_EMAIL
        google_password = GOOGLE_PASSWORD
        sender = EMAIL_SENDER
        smtp_server = EMAIL_SMTP_SERVER
        smtp_port = EMAIL_SMTP_SERVER_PORT if EMAIL_SMTP_SERVER_PORT else "587"
        smtp_user = EMAIL_SMTP_USER
        smtp_password = EMAIL_SMTP_PASSWORD
        email_config = {
            "recipients": recipients,
            "sender": sender,
            "server": smtp_server,
            "port": smtp_port,
            "user": smtp_user,
            "password": smtp_password,
        } if recipients else None

    if not google_email or not google_password:
        logging.error("Google credentials are missing. Exiting.")
        return

    while True:
        try:
            logging.info("Starting new capture cycle...")
            await process_capture_and_email(google_email, google_password, TELEOP_URL, SCREENSHOT_PATH, email_config)
            logging.info("Cycle completed. Waiting for %s seconds.", CAPTURE_INTERVAL_SECONDS)
        except Exception as e:
            logging.error("Error during capture cycle: %s", e)
        await asyncio.sleep(CAPTURE_INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Shutting down gracefully...")

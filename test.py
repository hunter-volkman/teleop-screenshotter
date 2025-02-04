import os
import logging
import asyncio
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from viam.app.viam_client import ViamClient
from viam.rpc.dial import Credentials, DialOptions

# Load environment variables from the .env file
load_dotenv()

# Set up logging configuration
# Change to DEBUG for more detailed logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# -------------------------
# Configuration
# -------------------------
# OAuth Login URL for authenticating to the web app
LOGIN_URL = (
    "https://auth.viam.com/admin"
)

# Hardcoded teleop URL
HARDCODED_TELEOP_URL = "https://app.viam.com/teleop/679afa71e0e67e4defcab50c/machine/7ede9f18-88ec-4084-a0b7-ae931a8c90ad"

# URL template for teleop pages
TELEOP_URL_TEMPLATE = "https://app.viam.com/teleop/{teleop_workspace_id}/machine/{machine_id}"

# OAuth credentials (for web login)
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")


# Screenshot settings
# Directory where screenshots will be saved
SCREENSHOT_DIR = "screenshots" 
SCREENSHOT_PATH = os.path.join(SCREENSHOT_DIR, "teleop_demo.png")

# Email configuration (optional)
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER")
EMAIL_SMTP_SERVER_PORT = int(os.getenv("EMAIL_SMTP_SERVER_PORT", "587"))
EMAIL_SMTP_USER = os.getenv("EMAIL_SMTP_USER")
EMAIL_SMTP_PASSWORD = os.getenv("EMAIL_SMTP_PASSWORD")

# Ensure screenshot directory exists
if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

# -------------------------
# Helper Functions
# -------------------------
async def capture_screenshot(page, teleop_url: str, output_path: str):
    """
    Navigates to a given teleop URL using an authenticated Playwright page,
    waits for the page to load, and captures a screenshot.
    """
    logging.info("Navigating to teleop URL: %s", teleop_url)
    await page.goto(teleop_url)
    await page.wait_for_selector("body", timeout=10000)
    logging.info("Waiting for 3 seconds to ensure the teleop page is fully loaded...")
    await asyncio.sleep(3)
    await page.screenshot(path=output_path)
    logging.info("Screenshot saved to %s", output_path)

def send_email(recipient: str, sender: str, smtp_config: dict, screenshot_path: str):
    """
    Sends an email with the screenshot attached.
    """
    msg = EmailMessage()
    msg["Subject"] = "Teleop Screenshot Demo"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content("Attached is the teleop screenshot demo.")

    with open(screenshot_path, "rb") as f:
        msg.add_attachment(f.read(), maintype='image', subtype='png', filename="teleop_demo.png")

    with smtplib.SMTP(smtp_config["server"], smtp_config["port"]) as server:
        server.starttls()
        server.login(smtp_config["user"], smtp_config["password"])
        server.send_message(msg)
    logging.info("Email sent with screenshot attached.")

# -------------------------
# Main Function
# -------------------------
async def main():
    logging.info("Starting Playwright session for OAuth demo...")

    async with async_playwright() as p:
        logging.info("Launching browser...")
        # Set headless to False for debugging
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        logging.info("Navigating to OAuth login URL: %s", LOGIN_URL)
        await page.goto(LOGIN_URL)

        logging.info("Waiting for login form fields to load...")
        await page.wait_for_selector("#loginId", timeout=30000)
        await page.wait_for_selector("#password", timeout=30000)

        logging.info("Filling in the OAuth login form...")
        await page.fill("#loginId", USERNAME)
        await page.fill("#password", PASSWORD)

        logging.info("Clicking the submit button...")
        await page.click("button.blue.button")

        logging.info("Waiting for OAuth login to complete...")
        await page.wait_for_load_state("networkidle", timeout=30000)

        # Capture screenshot of the teleop URL
        await capture_screenshot(page, HARDCODED_TELEOP_URL, SCREENSHOT_PATH)

        logging.info("Closing browser...")
        await browser.close()

    # Optionally send an email with the screenshot
    if EMAIL_RECIPIENT and EMAIL_SENDER and EMAIL_SMTP_SERVER:
        smtp_config = {
            "server": EMAIL_SMTP_SERVER,
            "port": EMAIL_SMTP_SERVER_PORT,
            "user": EMAIL_SMTP_USER,
            "password": EMAIL_SMTP_PASSWORD,
        }
        send_email(EMAIL_RECIPIENT, EMAIL_SENDER, smtp_config, SCREENSHOT_PATH)
    else:
        logging.info("Email settings not fully configured; skipping email.")

if __name__ == "__main__":
    asyncio.run(main())
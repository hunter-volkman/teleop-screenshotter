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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
LOGIN_URL = "https://app.viam.com"
HARDCODED_TELEOP_URL = "https://app.viam.com/teleop/679a4f421d5cd4386e27b964/machine/55200250-4b28-4981-b8eb-bcb10aaf8073"

# Login credentials
GOOGLE_EMAIL = os.getenv("GOOGLE_EMAIL")
GOOGLE_PASSWORD = os.getenv("GOOGLE_PASSWORD")
USE_GOOGLE_LOGIN = os.getenv("USE_GOOGLE_LOGIN", "false").lower() == "true"

# Screenshot settings
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

async def handle_google_login(page):
    """
    Handles the Google login flow
    """
    logging.info("Starting Google login flow...")
    
    # Click the Google login button
    await page.click('button:has-text("Login with Google")')
    
    # Wait for Google login page and enter email
    await page.wait_for_selector('input[type="email"]')
    await page.fill('input[type="email"]', GOOGLE_EMAIL)
    await page.click('button:has-text("Next")')
    
    # Wait for password field and enter password
    await page.wait_for_selector('input[type="password"]', timeout=5000)
    await page.fill('input[type="password"]', GOOGLE_PASSWORD)
    await page.click('button:has-text("Next")')
    
    # Wait for the login to complete
    await page.wait_for_load_state("networkidle", timeout=30000)
    logging.info("Google login completed")

async def handle_direct_login(page):
    """
    Handles the direct username/password login flow
    """
    logging.info("Starting direct login flow...")
    await page.wait_for_selector("#loginId", timeout=30000)
    await page.wait_for_selector("#password", timeout=30000)
    
    await page.fill("#loginId", os.getenv("USERNAME"))
    await page.fill("#password", os.getenv("PASSWORD"))
    await page.click("button.blue.button")
    
    await page.wait_for_load_state("networkidle", timeout=30000)
    logging.info("Direct login completed")

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

async def main():
    logging.info("Starting Playwright session...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(LOGIN_URL)

        # Handle login based on configuration
        if USE_GOOGLE_LOGIN:
            await handle_google_login(page)
        else:
            await handle_direct_login(page)

        # Capture screenshot of the teleop URL
        await capture_screenshot(page, HARDCODED_TELEOP_URL, SCREENSHOT_PATH)

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
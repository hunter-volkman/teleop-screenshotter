# Viam Teleop Screenshot Automation

This project automates the process of capturing screenshots from Viam's teleop interface using Playwright for web automation. It includes features for OAuth authentication (both direct Viam login and Google login), screenshot capture, and optional email notification functionality.

## Features

- Automated login to Viam's web interface using either:
  - Direct Viam credentials
  - Google authentication (with 2FA support)
- Screenshot capture of specified teleop pages
- Optional email notification with screenshot attachment
- Configurable logging levels
- Environment-based configuration

## Prerequisites

- Python 3.7 or higher
- Chrome/Chromium browser installed (required for Playwright)

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```
3. Install Playwright browsers:
```bash
playwright install
```

## Configuration

Create a `.env` file in the project root with the following configuration:

```env
# Required - Choose Authentication Method
USE_GOOGLE_LOGIN=false  # Set to 'true' for Google login, 'false' for direct Viam login

# Direct Viam Login Credentials (Required if USE_GOOGLE_LOGIN=false)
USERNAME=your_viam_username
PASSWORD=your_viam_password

# Google Login Credentials (Required if USE_GOOGLE_LOGIN=true)
GOOGLE_EMAIL=your.email@gmail.com
GOOGLE_PASSWORD=your_google_password

# Optional - Email Configuration
EMAIL_RECIPIENT=recipient@example.com
EMAIL_SENDER=sender@example.com
EMAIL_SMTP_SERVER=smtp.example.com
EMAIL_SMTP_SERVER_PORT=587
EMAIL_SMTP_USER=smtp_username
EMAIL_SMTP_PASSWORD=smtp_password
```

### Required Environment Variables
Based on your chosen authentication method:

For Direct Viam Login (`USE_GOOGLE_LOGIN=false`):
- `USERNAME`: Your Viam platform username
- `PASSWORD`: Your Viam platform password

For Google Login (`USE_GOOGLE_LOGIN=true`):
- `GOOGLE_EMAIL`: Your Google email address
- `GOOGLE_PASSWORD`: Your Google account password

### Optional Email Configuration Variables
- `EMAIL_RECIPIENT`: Email address to receive screenshots
- `EMAIL_SENDER`: Email address sending the screenshots
- `EMAIL_SMTP_SERVER`: SMTP server address
- `EMAIL_SMTP_SERVER_PORT`: SMTP server port (default: 587)
- `EMAIL_SMTP_USER`: SMTP authentication username
- `EMAIL_SMTP_PASSWORD`: SMTP authentication password

## Usage

Run the script using:
```bash
python test.py
```

The script will:
1. Launch a browser session
2. Log in to the Viam platform (using either direct or Google authentication)
3. Navigate to the specified teleop URL
4. Capture a screenshot
5. Save it to the `screenshots` directory
6. Optionally send an email with the screenshot attached

## Google Authentication Notes

When using Google authentication (`USE_GOOGLE_LOGIN=true`):
- If you have 2-Factor Authentication (2FA) enabled on your Google account, you will need to approve the login attempt on your device
- After approving 2FA once, the session should remain authenticated for a while
- The script cannot automatically bypass 2FA as this is a security feature

## Screenshot Storage

Screenshots are stored in the `screenshots` directory, which will be created automatically if it doesn't exist. The default screenshot filename is `teleop_demo.png`.

## Logging

The script includes configurable logging. By default, it's set to INFO level. To enable more detailed logging, modify the logging level in the script to DEBUG.

## Troubleshooting

Common issues and solutions:
- If using direct login and the script fails to log in, verify your Viam credentials in the .env file
- If using Google login and you have 2FA enabled, be ready to approve the login on your device
- For email-related issues, check your SMTP configuration
- For screenshot capture failures, try increasing the wait time in the `capture_screenshot` function

## Notes

- The script includes a hardcoded teleop URL for demonstration purposes
- Browser is launched in non-headless mode by default (visible browser window)
- Contains configurable timeouts for page loading and element detection
- Google login with 2FA requires manual approval on your device
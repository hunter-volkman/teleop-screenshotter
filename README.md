# Viam Teleop Screenshot Automation

This project automates the process of capturing screenshots from Viam's teleop interface using Playwright for web automation. It includes features for OAuth authentication, screenshot capture, and optional email notification functionality.

## Features

- Automated login to Viam's web interface using OAuth credentials
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
# Required - Viam OAuth Credentials
USERNAME=your_viam_username
PASSWORD=your_viam_password

# Optional - Email Configuration
EMAIL_RECIPIENT=recipient@example.com
EMAIL_SENDER=sender@example.com
EMAIL_SMTP_SERVER=smtp.example.com
EMAIL_SMTP_SERVER_PORT=587
EMAIL_SMTP_USER=smtp_username
EMAIL_SMTP_PASSWORD=smtp_password
```

### Required Environment Variables
- `USERNAME`: Your Viam platform username
- `PASSWORD`: Your Viam platform password

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
python3 test.py
```

The script will:
1. Launch a browser session
2. Log in to the Viam platform
3. Navigate to the specified teleop URL
4. Capture a screenshot
5. Save it to the `screenshots` directory
6. Optionally send an email with the screenshot attached

## Screenshot Storage

Screenshots are stored in the `screenshots` directory, which will be created automatically if it doesn't exist. The default screenshot filename is `teleop_demo.png`.

## Logging

The script includes configurable logging. By default, it's set to INFO level. To enable more detailed logging, modify the logging level in the script to DEBUG.

## Troubleshooting

Common issues and solutions:
- If the script fails to log in, verify your OAuth credentials in the .env file
- For email-related issues, check your SMTP configuration
- For screenshot capture failures, try increasing the wait time in the `capture_screenshot` function

## Notes

- The script includes a hardcoded teleop URL for demonstration purposes
- Browser is launched in non-headless mode by default (visible browser window)
- Contains configurable timeouts for page loading and element detection
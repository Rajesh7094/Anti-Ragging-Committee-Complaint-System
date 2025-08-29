from fastapi import FastAPI, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
from datetime import datetime
from typing import List
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========================
# CONFIGURATION SECTION
# ========================
SENDER_EMAIL = "rajesherode2004@gmail.com"
SENDER_PASSWORD = "mkxb cpmb nzio sddl"  # Make sure this is your app password, not regular password
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
COMMITTEE_EMAILS = [
    "gjsabuhurira@gmail.com",
    "abuhurairagjs@gmail.com",
    "rajesherode2004@gmail.com",
    "rajubairajesh5@gmail.com"
]

app = FastAPI(
    title="Anti-Ragging Reporting System API",
    description="API for submitting anti-ragging complaints.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class ComplaintForm(BaseModel):
    register_number: str = Field(..., min_length=1, description="Student's register number.")
    complaint_text: str = Field(..., min_length=1, description="Details of the complaint.")


def send_complaint_email(register_number: str, complaint_text: str, recipients: List[str]):
    """
    Send a complaint email to all committee members.
    """
    try:
        logger.info(f"Starting email sending process for register number: {register_number}")

        # Create message
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['Subject'] = f"Ragging Report from (Register number) {register_number}"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        body = f"""
ANTI-RAGGING COMPLAINT REPORT
=============================

Student Register Number: {register_number}
Complaint Submitted On: {timestamp}

COMPLAINT DETAILS:
{complaint_text}

=============================
This is an automated message from the College Anti-Ragging Reporting System.
Please take immediate action as required.
        """
        msg.attach(MIMEText(body, 'plain'))

        # Create SSL context
        context = ssl.create_default_context()

        logger.info(f"Attempting to connect to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")

        # Connect to server and send emails
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            logger.info("Connected to SMTP server")

            # Enable security
            server.starttls(context=context)
            logger.info("TLS enabled")

            # Login
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            logger.info("Login successful")

            # Send email to each recipient
            successful_sends = 0
            for email in recipients:
                try:
                    # Create a fresh message for each recipient
                    individual_msg = MIMEMultipart()
                    individual_msg['From'] = SENDER_EMAIL
                    individual_msg['To'] = email
                    individual_msg['Subject'] = f"Ragging Report from (Register number) {register_number}"
                    individual_msg.attach(MIMEText(body, 'plain'))

                    # Send the message
                    server.send_message(individual_msg)
                    logger.info(f"Email sent successfully to: {email}")
                    successful_sends += 1

                except Exception as e:
                    logger.error(f"Failed to send email to {email}: {str(e)}")

        logger.info(f"Email sending completed. Successfully sent to {successful_sends}/{len(recipients)} recipients")
        return successful_sends > 0

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Email authentication failed: {str(e)}")
        logger.error("Please check if you're using an App Password instead of your regular Gmail password")
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"Failed to connect to SMTP server: {str(e)}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error occurred: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return False


@app.post("/submit_complaint", status_code=200)
async def submit_complaint(
        background_tasks: BackgroundTasks,
        register_number: str = Form(..., min_length=1),
        complaint_text: str = Form(..., min_length=1),
):
    """
    Endpoint to receive and process a new anti-ragging complaint.
    """
    try:
        logger.info(f"Received complaint from register number: {register_number}")

        # Validate inputs
        if not register_number.strip():
            raise HTTPException(status_code=400, detail="Register number cannot be empty")
        if not complaint_text.strip():
            raise HTTPException(status_code=400, detail="Complaint text cannot be empty")

        # Add the email sending task to the background
        background_tasks.add_task(
            send_complaint_email,
            register_number.strip(),
            complaint_text.strip(),
            COMMITTEE_EMAILS
        )

        logger.info(f"Background task added for sending emails")

        return {
            "status": "success",
            "message": "Complaint received. Email is being sent in the background.",
            "register_number": register_number,
            "complaint_message": complaint_text
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in submit_complaint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# Add a test endpoint to check email functionality
@app.post("/test_email")
async def test_email():
    """
    Test endpoint to check if email configuration is working
    """
    try:
        result = send_complaint_email(
            "TEST123",
            "This is a test email to verify the email configuration is working correctly.",
            [SENDER_EMAIL]  # Send test email to sender's own email
        )

        if result:
            return {"status": "success", "message": "Test email sent successfully"}
        else:
            return {"status": "error", "message": "Failed to send test email"}

    except Exception as e:
        logger.error(f"Test email failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test email failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
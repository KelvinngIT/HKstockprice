import streamlit as st
import resend

# Safer way to get the key
api_key = st.secrets.get("RESEND_API_KEY")

if not api_key:
    st.error("RESEND_API_KEY is missing in Streamlit Secrets!")
    st.stop()

resend.api_key = api_key

def send_otp_email(email: str, otp: str):
    try:
        response = resend.Emails.send({
            "from": "HK Stock Report <onboarding@resend.dev>",
            "to": [email],
            "subject": "Your Verification Code - HK Stock Report",
            "html": f"""
                <h2>Your verification code is:</h2>
                <h1 style="letter-spacing: 8px; color: #2563eb;">{otp}</h1>
                <p>This code will expire in 10 minutes.</p>
            """
        })
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        # Show more debug info (temporary)
        st.write("Debug - API Key starts with:", api_key[:7] + "..." if api_key else "None")
        return False

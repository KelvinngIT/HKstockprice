import streamlit as st
import random
import string
from datetime import datetime, timedelta
import resend
from pathlib import Path

# ================== CONFIG ==================
st.set_page_config(page_title="HK Stock Daily Report", page_icon="📈", layout="wide")

# Put your Resend API key in Streamlit Secrets
# .streamlit/secrets.toml → RESEND_API_KEY = "re_xxxxx"
resend.api_key = st.secrets.get("RESEND_API_KEY")

# ================== HELPER FUNCTIONS ==================
def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def send_otp_email(email: str, otp: str):
    try:
        resend.Emails.send({
            "from": "HK Stock Report <onboarding@resend.dev>",  # change later to your domain
            "to": [email],
            "subject": "Your Verification Code - HK Stock Report",
            "html": f"""
                <h2>Your verification code is:</h2>
                <h1 style="letter-spacing: 8px;">{otp}</h1>
                <p>This code will expire in 10 minutes.</p>
            """
        })
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False

def is_otp_valid():
    if "otp" not in st.session_state or "otp_expiry" not in st.session_state:
        return False
    return datetime.now() < st.session_state.otp_expiry

# ================== SESSION STATE ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# ================== LOGIN PAGE ==================
if not st.session_state.logged_in:
    st.title("🔐 Login with Email")

    with st.form("email_form"):
        email = st.text_input("Email address", placeholder="you@example.com")
        send_btn = st.form_submit_button("Send Verification Code", type="primary")

    if send_btn:
        if not email or "@" not in email:
            st.error("Please enter a valid email address")
        else:
            otp = generate_otp()
            st.session_state.otp = otp
            st.session_state.otp_expiry = datetime.now() + timedelta(minutes=10)
            st.session_state.pending_email = email

            if send_otp_email(email, otp):
                st.success(f"Verification code sent to **{email}**")
                st.info("Please check your inbox (and spam folder).")

    # Verification form
    if "pending_email" in st.session_state:
        st.divider()
        with st.form("otp_form"):
            code = st.text_input("Enter 6-digit code", max_chars=6)
            verify_btn = st.form_submit_button("Verify & Login")

        if verify_btn:
            if not is_otp_valid():
                st.error("Code has expired. Please request a new one.")
            elif code == st.session_state.otp:
                st.session_state.logged_in = True
                st.session_state.user_email = st.session_state.pending_email
                # Clean up
                for key in ["otp", "otp_expiry", "pending_email"]:
                    st.session_state.pop(key, None)
                st.rerun()
            else:
                st.error("Incorrect verification code")

# ================== MAIN APP (After Login) ==================
else:
    st.sidebar.success(f"Logged in as: **{st.session_state.user_email}**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.rerun()

    st.title("📈 Hong Kong Stocks Daily Report")

    data_dir = Path("data")
    if data_dir.exists():
        files = sorted(data_dir.glob("*.xlsx"), reverse=True)
        if files:
            latest = files[0]
            st.info(f"Latest report: **{latest.name}**")

            with open(latest, "rb") as f:
                st.download_button(
                    label="⬇️ Download Latest Excel",
                    data=f,
                    file_name=latest.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            st.subheader("Previous Reports")
            for f in files[1:8]:
                with open(f, "rb") as file:
                    st.download_button(
                        label=f"Download {f.name}",
                        data=file,
                        file_name=f.name,
                        key=str(f)
                    )
        else:
            st.warning("No reports generated yet.")
    else:
        st.warning("Data folder not found. Waiting for the first daily run.")

import streamlit as st
import random
import string
from datetime import datetime, timedelta
from pathlib import Path

# ====================== Page Config ======================
st.set_page_config(
    page_title="HK Stock Daily Report",
    page_icon="📈",
    layout="wide"
)

# ====================== Helper Functions ======================
def generate_otp(length: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=length))


def send_otp_email(email: str, otp: str) -> bool:
    """Send OTP using Resend. Returns True if successful."""
    try:
        import resend
        api_key = st.secrets.get("RESEND_API_KEY")
        
        if not api_key:
            st.error("RESEND_API_KEY is missing in Streamlit Secrets.")
            return False
            
        resend.api_key = api_key

        resend.Emails.send({
            "from": "HK Stock Report <onboarding@resend.dev>",
            "to": [email],
            "subject": "Your Verification Code - HK Stock Report",
            "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 500px;">
                    <h2>Verification Code</h2>
                    <p>Your login code is:</p>
                    <h1 style="letter-spacing: 8px; color: #2563eb;">{otp}</h1>
                    <p>This code will expire in <b>10 minutes</b>.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">If you didn't request this, please ignore this email.</p>
                </div>
            """
        })
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False


def is_otp_valid() -> bool:
    if "otp" not in st.session_state or "otp_expiry" not in st.session_state:
        return False
    return datetime.now() < st.session_state.otp_expiry


# ====================== Session State ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None


# ====================== LOGIN PAGE ======================
if not st.session_state.logged_in:
    st.title("🔐 Login with Email")
    st.write("Enter your email to receive a verification code.")

    with st.form("email_form", clear_on_submit=False):
        email = st.text_input("Email address", placeholder="you@example.com")
        send_clicked = st.form_submit_button("Send Verification Code", type="primary")

    if send_clicked:
        if not email or "@" not in email or "." not in email:
            st.error("Please enter a valid email address.")
        else:
            otp = generate_otp()
            st.session_state.otp = otp
            st.session_state.otp_expiry = datetime.now() + timedelta(minutes=10)
            st.session_state.pending_email = email.strip().lower()

            with st.spinner("Sending verification code..."):
                if send_otp_email(email, otp):
                    st.success(f"✅ Verification code sent to **{email}**")
                    st.info("Please also check your **Spam / Junk** folder.")

    # Show OTP input only after code was sent
    if "pending_email" in st.session_state:
        st.divider()
        st.subheader("Enter Verification Code")

        with st.form("otp_form"):
            code = st.text_input("6-digit code", max_chars=6, placeholder="123456")
            verify_clicked = st.form_submit_button("Verify & Login", type="primary")

        if verify_clicked:
            if not is_otp_valid():
                st.error("⏰ Code has expired. Please request a new one.")
                # Clear expired data
                for key in ["otp", "otp_expiry", "pending_email"]:
                    st.session_state.pop(key, None)
            elif code.strip() == st.session_state.get("otp"):
                # Login successful
                st.session_state.logged_in = True
                st.session_state.user_email = st.session_state.pending_email
                
                # Clean up
                for key in ["otp", "otp_expiry", "pending_email"]:
                    st.session_state.pop(key, None)
                    
                st.success("Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("❌ Incorrect verification code. Please try again.")

# ====================== MAIN APP (After Login) ======================
else:
    # Sidebar
    st.sidebar.success(f"Logged in as:\n**{st.session_state.user_email}**")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.rerun()

    # Main Content
    st.title("📈 Hong Kong Stocks Daily Report")
    st.caption(f"Welcome back, {st.session_state.user_email}")

    data_dir = Path("data")

    if data_dir.exists():
        files = sorted(data_dir.glob("*.xlsx"), reverse=True)

        if files:
            latest = files[0]
            st.info(f"📁 Latest report: **{latest.name}**")

            # Download latest
            with open(latest, "rb") as f:
                st.download_button(
                    label="⬇️ Download Latest Excel",
                    data=f,
                    file_name=latest.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )

            # Previous reports
            if len(files) > 1:
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
            st.warning("No reports have been generated yet.")
    else:
        st.warning("Data folder not found. Waiting for the first daily run.")

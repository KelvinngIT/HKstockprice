import streamlit as st
from pathlib import Path
import random
import string
from datetime import datetime, timedelta

st.set_page_config(page_title="HK Stock Daily Report", page_icon="📈", layout="wide")

# ---------- Safer secrets handling ----------
def get_resend_api_key():
    try:
        return st.secrets["RESEND_API_KEY"]
    except Exception:
        return None

api_key = get_resend_api_key()

if api_key:
    import resend
    resend.api_key = api_key
else:
    st.warning("⚠️ RESEND_API_KEY is not set in Secrets. Email login will not work.")

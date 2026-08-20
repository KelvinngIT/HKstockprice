# app.py
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
from pathlib import Path

st.set_page_config(page_title="HK Stock Daily Report", page_icon="📈", layout="wide")

# Load authentication config
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

authenticator.login(location='main')

if st.session_state.get("authentication_status"):
    st.success(f"Welcome **{st.session_state['name']}**")
    authenticator.logout(location='sidebar')

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
            for f in files[1:10]:
                with open(f, "rb") as file:
                    st.download_button(
                        label=f"Download {f.name}",
                        data=file,
                        file_name=f.name,
                        key=f.name
                    )
        else:
            st.warning("No reports generated yet.")
    else:
        st.warning("Data folder not found.")

elif st.session_state.get("authentication_status") is False:
    st.error("Username / password is incorrect")
elif st.session_state.get("authentication_status") is None:
    st.warning("Please enter your email / username and password")

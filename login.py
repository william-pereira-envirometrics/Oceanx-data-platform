# 📁 login.py
import streamlit as st

def login():
    st.title("🔐 Login to OceanX Dashboard")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if user == "admin" and pwd == "oceanx2025":
            st.session_state["logged_in"] = True
        else:
            st.error("❌ Invalid credentials")

def check_login():
    if "logged_in" not in st.session_state:
        login()
        st.stop()

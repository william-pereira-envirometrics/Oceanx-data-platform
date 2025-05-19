# 📁 login.py
import streamlit as st
from database import verify_user, create_user

def register():
    st.subheader("Create New Account")
    with st.form("register_form"):
        new_username = st.text_input("Choose Username")
        new_password = st.text_input("Choose Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        email = st.text_input("Email (optional)")
        submitted = st.form_submit_button("Register")
        
        if submitted:
            if not new_username or not new_password:
                st.error("❌ Username and password are required")
                return
            if new_password != confirm_password:
                st.error("❌ Passwords do not match")
                return
            if create_user(new_username, new_password, email):
                st.success("✅ Registration successful! Please login.")
                st.session_state["show_login"] = True
            else:
                st.error("❌ Registration failed. Username may already exist.")

def login():
    st.title("🔐 Login to OceanX Dashboard")
    
    # Add a toggle between login and register
    if "show_login" not in st.session_state:
        st.session_state["show_login"] = True
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login", use_container_width=True):
            st.session_state["show_login"] = True
    with col2:
        if st.button("Register", use_container_width=True):
            st.session_state["show_login"] = False
    
    if st.session_state["show_login"]:
        with st.form("login_form"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if verify_user(user, pwd):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = user
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
    else:
        register()

def check_login():
    if "logged_in" not in st.session_state:
        login()
        st.stop()
    return st.session_state.get("username")

import streamlit as st
import os
import json
import base64
import re

AUTHORISED_TENANTS = os.getenv("AUTH_TENANT_IDS")
# 'aa410fd2-904c-402e-a77c-1cf5e826ab63,b'
authorised = False

st.set_page_config(page_title="Auth validation", layout="wide")

def extract_iss_claim(token):
    obj = json.loads(base64.urlsafe_b64decode(token))
    if 'claims' not in obj:
        print("claims not found")
        return None
    for claim in obj['claims']:
        if claim.get('typ') == 'iss':
            return claim.get('val')  # Return the 'val' of the 'iss' claim
    print("iss claim not found")    
    return None

if 'X-Ms-Client-Principal' in st.context.headers:
    url = extract_iss_claim(st.context.headers['X-Ms-Client-Principal'])

    if url is not None:
        match = re.search(r"(?<=login\.microsoftonline\.com/)[a-f0-9\-]+", url)
        authorised = match and match.group(0) in AUTHORISED_TENANTS

# Authorization check at the beginning
if not authorised:
    st.error("Unauthorized", icon="🚫")
    st.stop()  

st.session_state.topic = ""

# # Accept user input
prompt = st.chat_input("Please provide a topic for a blog post:")

# --- Sidebar ---
with st.sidebar:
    st.info("Multi-agent blog writer.")
    title = st.title(f"Topic: {st.session_state.topic}")
    cc = st.columns(1)
    with cc[0]:
        cc[0].container(border=False, height=300)
    buttn_click = st.button("Reset State")
        
# --- Reset state ---
if buttn_click:
    title.title("Topic:")

# --- Process Prompt ---
if prompt:
    st.session_state.topic = prompt
    title.title(f"Topic: {st.session_state.topic}")

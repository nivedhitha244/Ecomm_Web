import streamlit as st
from app_backend import get_rag_chain, generate_response

# 1. Page Configuration
st.set_page_config(
    page_title="Store Assistant", 
    page_icon="💬", 
    layout="centered" # Changed from wide to centered for a clean chat UI
)

# 2. Connect to the AI Backend
@st.cache_resource
def load_backend():
    return get_rag_chain()

rag_chain = load_backend()

# ==========================================
# FULL-SCREEN CHATBOT INTERFACE
# ==========================================
st.title("💬 Store Assistant")
st.caption("Everyday Apparel Customer Support")
st.divider()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi there! I can help you with store policies, shipping, and product information. What do you need help with today?"}
    ]

# Display chat messages from history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# React to user input
if user_input := st.chat_input("E.g., Do you have clothes on sale?"):
    
    # Display user message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Generate and display AI response
    with st.chat_message("assistant"):
        with st.spinner("Checking store info..."):
            answer = generate_response(rag_chain, user_input)
        st.markdown(answer)
        
    st.session_state.messages.append({"role": "assistant", "content": answer})
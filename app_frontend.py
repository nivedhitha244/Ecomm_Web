import base64
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
import app_backend as backend

st.set_page_config(page_title="E-Commerce Assistant", page_icon="🛍️", layout="wide")

# ==========================================
# INITIALIZATION & STATE
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = None
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "feedback_log" not in st.session_state:
    st.session_state.feedback_log = {}
if "show_analytics" not in st.session_state:
    st.session_state.show_analytics = False
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "cart" not in st.session_state:
    st.session_state.cart = []

# ==========================================
# CALLBACK FUNCTIONS
# ==========================================
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.cart = [] 
    st.session_state.current_session_id = None

def set_active_session(session_id):
    st.session_state.current_session_id = session_id
    st.session_state.feedback_log = {}

def start_new_session():
    st.session_state.current_session_id = None
    st.session_state.feedback_log = {}

def remove_session(session_id):
    backend.delete_session(session_id)
    if st.session_state.current_session_id == session_id:
        st.session_state.current_session_id = None
        st.session_state.feedback_log = {}

# ==========================================
# LOGIN / SIGNUP PAGE UI
# ==========================================
def render_auth_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🛍️ Welcome")
        st.markdown("Please sign in or create an account to access the assistant.")
        
        tab1, tab2 = st.tabs(["Log In", "Sign Up"])
        
        with tab1:
            st.subheader("Log In")
            login_user = st.text_input("Username", key="login_user")
            login_pass = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Login", use_container_width=True):
                if backend.authenticate_user(login_user, login_pass):
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.session_state.cart = backend.load_user_cart(login_user)
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
        with tab2:
            st.subheader("Create Account")
            signup_user = st.text_input("Choose a Username", key="signup_user")
            signup_pass = st.text_input("Choose a Password", type="password", key="signup_pass")
            signup_pass_confirm = st.text_input("Confirm Password", type="password", key="signup_pass_confirm")
            
            if st.button("Sign Up", use_container_width=True):
                if signup_pass != signup_pass_confirm:
                    st.error("Passwords do not match!")
                elif len(signup_user) < 3:
                    st.error("Username must be at least 3 characters.")
                elif len(signup_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    success, message = backend.create_user(signup_user, signup_pass)
                    if success:
                        st.success(f"{message} You can now log in.")
                    else:
                        st.error(message)

# ==========================================
# MAIN APP ROUTING
# ==========================================
if not st.session_state.logged_in:
    render_auth_page()
    st.stop() 


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.title("Chat History")
    
    st.button("➕ New Chat", on_click=start_new_session, use_container_width=True)
    
    search_query = st.text_input("🔍 Search chats...", placeholder="Type to search...")
    st.divider()
    
    st.header("⚡ Quick Actions")
    st.metric("🛒 Items in Cart", len(st.session_state.cart))
    
    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("📦 Track", use_container_width=True):
            st.session_state.quick_action_prompt = "Track order #ORD1023"
    with colB:
        if st.button("🛒 Cart", use_container_width=True):
            st.session_state.quick_action_prompt = "View cart"
    with colC:
        if st.button("🔄 Return", use_container_width=True, help="Start a return/refund request"):
            st.session_state.quick_action_prompt = "I need to return an order"
    st.divider()
    
    # UPDATED: Passes the active username to the backend to filter history
    sessions = backend.get_all_sessions(st.session_state.username, search_query)
    
    if not sessions:
        if search_query:
            st.caption("No chats match your search.")
        else:
            st.caption("No past conversations.")
    else:
        for session in sessions:
            col1, col2 = st.columns([5, 1])
            with col1:
                is_active = (session["id"] == st.session_state.current_session_id)
                prefix = "💬" if is_active else "📄"
                st.button(
                    f"{prefix} {session['title']}", 
                    key=f"select_{session['id']}", 
                    on_click=set_active_session, 
                    args=(session["id"],),
                    use_container_width=True
                )
            with col2:
                st.button(
                    "🗑️", 
                    key=f"delete_{session['id']}", 
                    on_click=remove_session, 
                    args=(session["id"],)
                )

    st.divider()
    
    st.header("Session Metrics")
    if st.session_state.feedback_log:
        for index, sentiment in st.session_state.feedback_log.items():
            actual_turn = (index // 2) + 1
            symbol = "👍" if sentiment == "Positive" else "👎"
            st.write(f"Turn {actual_turn}: {sentiment} {symbol}")
    else:
        st.write("No feedback for this chat.")

    st.divider()
    
    st.header("📈 Admin")
    button_label = "⬅️ Back to Chat" if st.session_state.show_analytics else "📊 View Analytics"
    if st.button(button_label, use_container_width=True):
        st.session_state.show_analytics = not st.session_state.show_analytics
        st.rerun()

    st.divider()

    # === PROFILE AVATAR UI ===
    user_initial = st.session_state.username[0].upper() if st.session_state.username else "U"
    
    avatar_html = f"""
    <div style="display: flex; align-items: center; margin-bottom: 15px;">
        <div style="
            width: 42px; 
            height: 42px; 
            border-radius: 50%; 
            background-color: #C2185B; 
            color: white; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            font-size: 22px; 
            font-family: sans-serif;
            margin-right: 12px;
        ">
            {user_initial}
        </div>
        <div style="font-size: 16px; font-weight: bold; color: inherit;">
            {st.session_state.username}
        </div>
    </div>
    """
    st.markdown(avatar_html, unsafe_allow_html=True)
    # ==========================
    
    st.button("🚪 Logout", on_click=logout, use_container_width=True)
    
# ==========================================
# MAIN UI: CHAT OR ANALYTICS
# ==========================================
if st.session_state.show_analytics:
    st.title("📈 Chatbot Usage Analytics")
    st.markdown("Live operational metrics pulled directly from the local SQLite database.")
    
    stats = backend.get_analytics_data()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Conversations", stats["total_sessions"], delta="Active")
    col2.metric("Total Messages Sent", stats["total_messages"])
    col3.metric("Avg Messages / Chat", round(stats["total_messages"] / max(stats["total_sessions"], 1), 1))
    col4.metric("🚨 Fraud Flags", stats["total_fraud_flags"], delta_color="inverse")
    
    st.divider()
    
    st.subheader("Message Volume by Role")
    import pandas as pd
    chart_data = pd.DataFrame(
        {"Messages": [stats["user_messages"], stats["bot_messages"]]},
        index=["User (Human)", "Assistant (AI)"]
    )
    st.bar_chart(chart_data)
    
    st.divider()
    
    st.subheader("🚨 Recent Fraud Alerts")
    fraud_alerts = backend.get_recent_fraud_alerts()
    if fraud_alerts:
        import pandas as pd
        fraud_df = pd.DataFrame(fraud_alerts)
        st.dataframe(fraud_df, use_container_width=True)
    else:
        st.success("No fraudulent activity detected recently.")
    
else:
    st.title("🛍️ E-Commerce Support Assistant")
    st.markdown("Ask me about returns, shipping, orders, or our store policies!")

    chat_history = []
    if st.session_state.current_session_id:
        chat_history = backend.get_session_messages(st.session_state.current_session_id)

    for i, message in enumerate(chat_history):
        role = "user" if isinstance(message, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(message.content)
            
            if role == "assistant":
                feedback = st.feedback("thumbs", key=f"feedback_{st.session_state.current_session_id}_{i}")
                
                if feedback is not None:
                    sentiment = "Positive" if feedback == 1 else "Negative"
                    if i not in st.session_state.feedback_log or st.session_state.feedback_log[i] != sentiment:
                        st.toast("Thanks for your feedback! 🛍️")
                    st.session_state.feedback_log[i] = sentiment

    with st.expander("📸 Visual Search (Upload an image)"):
        uploaded_image = st.file_uploader("Upload a product image", type=["png", "jpg", "jpeg"], key=str(st.session_state.uploader_key))

    user_input_text = st.chat_input("How can I help you today?")

    if st.session_state.get("quick_action_prompt"):
        prompt = st.session_state.quick_action_prompt
        st.session_state.quick_action_prompt = None
    else:
        prompt = user_input_text

    if prompt:
        image_base64 = None
        if uploaded_image:
            image_base64 = base64.b64encode(uploaded_image.read()).decode('utf-8')
        
        if not st.session_state.current_session_id:
            title_text = prompt[:25] + "..." if len(prompt) > 25 else prompt
            # UPDATED: Now passes the logged-in user when creating a new chat
            st.session_state.current_session_id = backend.create_session(username=st.session_state.username, title=title_text)
        
        session_id = st.session_state.current_session_id
        
        with st.chat_message("user"):
            st.markdown(prompt)
            if uploaded_image:
                st.image(uploaded_image, width=200)
            
        backend.save_message(session_id, "user", prompt)
        
        if st.session_state.rag_chain is None:
            with st.spinner("Initializing AI Assistant for the first time..."):
                st.session_state.rag_chain = backend.get_rag_chain()

        with st.spinner("Processing..."):
            response = backend.generate_response(
                rag_chain=st.session_state.rag_chain,
                user_input=prompt,
                chat_history=chat_history,
                image_base64=image_base64,
                cart=st.session_state.cart,
                username=st.session_state.username
    )

        with st.chat_message("assistant"):
            st.markdown(response)

        backend.save_message(session_id, "assistant", response)
        
        if uploaded_image:
            st.session_state.uploader_key += 1
            
        st.rerun()
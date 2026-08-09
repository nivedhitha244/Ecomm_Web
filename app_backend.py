import os
import logging
import sqlite3
import uuid
import pandas as pd
import re
import json 
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st
import hashlib

from langchain_community.document_loaders import DataFrameLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

# Setup Logging
logging.basicConfig(
    filename='chatbot_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

load_dotenv()

# ==========================================
# DATABASE SETUP (SQLite)
# ==========================================
@st.cache_resource
def init_db():
    conn = sqlite3.connect('chat_history.db', check_same_thread=False)
    c = conn.cursor()
    # UPDATED: Added username column to sessions table
    c.execute('''CREATE TABLE IF NOT EXISTS sessions 
                 (id TEXT PRIMARY KEY, username TEXT, title TEXT, created_at DATETIME)''')
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT, created_at DATETIME)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT, created_at DATETIME)''')
                 
    c.execute('''CREATE TABLE IF NOT EXISTS fraud_flags 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, flag_reason TEXT, severity TEXT, created_at DATETIME)''')
                 
    c.execute('''CREATE TABLE IF NOT EXISTS user_carts 
                 (username TEXT PRIMARY KEY, cart_data TEXT)''')
                 
    conn.commit()
    return conn

db_conn = init_db()

# ==========================================
# CART DATABASE LOGIC
# ==========================================
def save_user_cart(username, cart_list):
    if username == "Guest" or not username:
        return
    c = db_conn.cursor()
    cart_json = json.dumps(cart_list)
    c.execute("INSERT OR REPLACE INTO user_carts (username, cart_data) VALUES (?, ?)", (username, cart_json))
    db_conn.commit()

def load_user_cart(username):
    c = db_conn.cursor()
    c.execute("SELECT cart_data FROM user_carts WHERE username = ?", (username,))
    result = c.fetchone()
    if result:
        return json.loads(result[0])
    return []

# ==========================================
# FRAUD DETECTION SYSTEM
# ==========================================
def log_fraud(username, reason, severity="HIGH"):
    c = db_conn.cursor()
    c.execute("INSERT INTO fraud_flags (username, flag_reason, severity, created_at) VALUES (?, ?, ?, ?)", 
              (username, reason, severity, datetime.now()))
    db_conn.commit()

def check_for_fraud(username, user_input, order_id=None):
    user_lower = user_input.lower()
    blacklisted_terms = ["stolen card", "stolen credit card", "fake receipt", "bypass payment", "test cc", "cvv generator"]
    if any(term in user_lower for term in blacklisted_terms):
        log_fraud(username, f"Used suspicious blacklisted term: {user_input}")
        return True, "🚨 **Security Alert:** We have detected a violation of our Terms of Service. Your account activity has been flagged and restricted for manual review."

    if order_id:
        if order_id.endswith("99") or order_id == "ORD0000":
            log_fraud(username, f"Attempted action on high-risk flagged order: {order_id}")
            return True, f"🚨 **Risk Management Alert:** Order {order_id} has been frozen due to suspicious payment or return activity. Automated requests cannot be processed."

    return False, ""

# ==========================================
# USER AUTHENTICATION LOGIC
# ==========================================
def hash_password(password):
    salt = os.urandom(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return (salt + pwd_hash).hex()

def verify_password(password, stored_hex):
    stored_bytes = bytes.fromhex(stored_hex)
    salt = stored_bytes[:32]
    stored_hash = stored_bytes[32:]
    new_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return new_hash == stored_hash

def create_user(username, password):
    try:
        c = db_conn.cursor()
        c.execute("SELECT username FROM users WHERE username = ?", (username,))
        if c.fetchone():
            return False, "Username already exists. Please choose another."

        hashed = hash_password(password)
        c.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)", 
                  (username, hashed, datetime.now()))
        db_conn.commit()
        return True, "Account created successfully!"
    except Exception as e:
        return False, f"Database error: {str(e)}"

def authenticate_user(username, password):
    c = db_conn.cursor()
    c.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    
    if not result:
        return False 
        
    stored_hash = result[0]
    return verify_password(password, stored_hash)

# ==========================================
# SESSION & MESSAGE MANAGEMENT
# ==========================================
# UPDATED: Now requires username to bind the session to the user
def create_session(username, title="New Chat"):
    session_id = str(uuid.uuid4())
    c = db_conn.cursor()
    c.execute("INSERT INTO sessions (id, username, title, created_at) VALUES (?, ?, ?, ?)", 
              (session_id, username, title, datetime.now()))
    db_conn.commit()
    return session_id

# UPDATED: Now filters sessions by username
def get_all_sessions(username, search_query=""):
    c = db_conn.cursor()
    if search_query:
        c.execute("SELECT id, title FROM sessions WHERE username = ? AND title LIKE ? ORDER BY created_at DESC", (username, f"%{search_query}%"))
    else:
        c.execute("SELECT id, title FROM sessions WHERE username = ? ORDER BY created_at DESC", (username,))
    return [{"id": row[0], "title": row[1]} for row in c.fetchall()]

def delete_session(session_id):
    c = db_conn.cursor()
    c.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    db_conn.commit()

def save_message(session_id, role, content):
    c = db_conn.cursor()
    c.execute("INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)", 
              (session_id, role, content, datetime.now()))
    db_conn.commit()

def get_session_messages(session_id):
    c = db_conn.cursor()
    c.execute("SELECT role, content FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
    messages = []
    for row in c.fetchall():
        if row[0] == "user":
            messages.append(HumanMessage(content=row[1]))
        else:
            messages.append(AIMessage(content=row[1]))
    return messages

# ==========================================
# RAG PIPELINE
# ==========================================
@st.cache_resource
def get_rag_chain():
    try:
        print("Loading existing RAG database...")

        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

        vector_store = Chroma(
            persist_directory="chroma_db",
            embedding_function=embeddings
        )

        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        llm = ChatGroq(
            temperature=0.3,
            groq_api_key=api_key,
            model_name="llama-3.1-8b-instant"
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are a helpful e-commerce assistant.

Answer based ONLY on the provided context.

If you don't know the answer, say:
'I cannot find that in our policies.'

Context:
{context}"""
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])

        retriever = vector_store.as_retriever(
            search_kwargs={"k": 2}
        )

        def format_docs(docs):
            return "\n\n".join(
                f"Question: {doc.page_content}\n"
                f"Answer: {doc.metadata.get('answer', '')}"
                for doc in docs
            )

        rag_chain = (
            {
                "context": lambda x: format_docs(
                    retriever.invoke(x["input"])
                ),
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"]
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        logging.info(
            "Backend RAG Pipeline loaded successfully."
        )

        print("RAG pipeline loaded successfully.")

        return rag_chain

    except Exception as e:
        logging.error(
            f"Error loading RAG pipeline: {e}"
        )
        raise
# ==========================================
# BUSINESS LOGIC (Orders & Returns)
# ==========================================
def get_order_details(order_id):
    try:
        df = pd.read_csv("orders.csv")
        df['order_id'] = df['order_id'].astype(str)
        order_row = df[df['order_id'].str.upper() == order_id]
        
        if not order_row.empty:
            row = order_row.iloc[0]
            return f"**📦 Order {row['order_id']}**\n\n**Product:** {row['product']}\n**Status:** {row['status']}\n\n**Ordered:** {row['ordered_date']}\n**Expected delivery:** {row['expected_delivery']}\n\n**Current location:**\n{row['current_location']}"
        else:
            return f"I couldn't find order #{order_id}. Please check your order number and try again."
    except FileNotFoundError:
        return "System Error: orders.csv database is missing."

def process_return(order_id):
    try:
        df = pd.read_csv("orders.csv")
        df['order_id'] = df['order_id'].astype(str)
        order_row = df[df['order_id'].str.upper() == order_id]
        
        if not order_row.empty:
            row = order_row.iloc[0]
            status = row['status'].lower()
            
            if status != "delivered":
                return f"❌ **Return Ineligible:** Order #{order_id} is currently marked as '{row['status']}'. Items can only be returned after they have been delivered."
            
            return (f"🔄 **Return Initiated for Order {order_id}**\n\n"
                    f"**Item:** {row['product']}\n"
                    f"**Return Window:** Eligible (Within 30 days)\n\n"
                    f"To finalize this return, please reply with the reason (e.g., 'Return {order_id} because it was defective').\n\n"
                    f"*Note: If the item arrived damaged or defective, please use the Visual Search uploader to attach a photo of the defect.*")
        else:
            return f"I couldn't find order #{order_id}. Please check your order number."
    except FileNotFoundError:
        return "System Error: orders.csv database is missing."

# ==========================================
# MAIN RESPONSE GENERATOR
# ==========================================
def generate_response(rag_chain, user_input, chat_history=[], image_base64=None, cart=None, username="Guest"):
    if cart is None:
        cart = []
        
    logging.info(f"User Asked: {user_input}")
    try:
        user_lower = user_input.lower()

        # === FRAUD DETECTION ===
        is_fraud, fraud_msg = check_for_fraud(username, user_input)
        if is_fraud:
            return fraud_msg
        
        if user_lower in ["i need to return an order", "return item", "refund order"]:
            return "I can help you with that! Please provide your **Order ID** (e.g., ORD1023) so I can look up your eligibility."
            
        return_match = re.search(r'(return|refund).*?(ORD\d+)', user_lower, re.IGNORECASE)
        if return_match:
            order_id = return_match.group(2).upper()
            is_fraud, fraud_msg = check_for_fraud(username, user_input, order_id=order_id)
            if is_fraud: return fraud_msg
            return process_return(order_id)

        # === CART ACTIONS ===
        if user_lower in ["view cart", "show cart", "what is in my cart", "cart"]:
            if not cart:
                return "🛒 **Your cart is currently empty.**\n\nAsk me to find products for you, and tell me to *'add [item] to cart'* when you are ready!"
            else:
                cart_items = "\n".join([f"{i+1}. {item}" for i, item in enumerate(cart)])
                return f"🛒 **Your Cart contains {len(cart)} item(s):**\n\n{cart_items}\n\n*Type 'clear cart' to empty it.*"
                
        if user_lower in ["clear cart", "empty cart"]:
            cart.clear()
            save_user_cart(username, cart) 
            st.session_state.pop("last_inquired_item", None)
            return "🗑️ **Your cart has been emptied.**"

        confirm_add_match = re.search(r'(?:add\s+it|yes.*add|sure.*add|thats fine.*add|please add|ok.*add)', user_lower, re.IGNORECASE)
        if confirm_add_match and st.session_state.get("last_inquired_item"):
            item_to_add = st.session_state.pop("last_inquired_item")
            cart.append(item_to_add)
            save_user_cart(username, cart)
            return f"✅ **Added to Cart!**\n\n**{item_to_add}** is now in your cart. You have {len(cart)} item(s) total.\n\nType *'view cart'* to see them."

        buy_match = re.search(r'(?:i want to buy|i want to purchase|buy|purchase)\s+(.+)', user_lower, re.IGNORECASE)
        if buy_match and not ("add" in user_lower):
            item_inquiry = buy_match.group(1).strip().title()
            st.session_state.last_inquired_item = item_inquiry
            try:
                advisor_prompt = ChatPromptTemplate.from_messages([
                    ("system", "You are a smart E-commerce Assistant. The user's current cart contains: {cart_items}. The user just said they want to buy: '{item_inquiry}'. Acknowledge what is currently in their cart, point out any potential brand/compatibility mismatch if they are asking for a different brand (like asking for a Samsung product when they have a Redmi product in the cart), and ask if they would like you to add it anyway. Do not add it to the cart automatically."),
                    ("human", "{user_input}")
                ])
                advisor_chain = advisor_prompt | ChatGroq(temperature=0.3, groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama-3.1-8b-instant") | StrOutputParser()
                return advisor_chain.invoke({
                    "cart_items": ", ".join(cart) if cart else "Empty", "item_inquiry": item_inquiry, "user_input": user_input
                })
            except Exception as e:
                logging.error(f"Buy inquiry error: {e}")
            
        add_match = re.search(r'^(?:add\s+)?(.*?)\s+(?:to|in|into)\s+(?:the\s+|my\s+|a\s+)*\s*(?:cart|csrt|crt|crat|bag)', user_lower, re.IGNORECASE)
        if not add_match:
            add_match = re.search(r'^add\s+(.+)', user_lower, re.IGNORECASE)
            
        if add_match:
            raw_item = add_match.group(1).strip()
            clean_item = re.sub(r'\s+(?:to|in|into)\s+(?:the\s+|my\s+|a\s+)*\s*(?:cart|csrt|crt|crat|bag).*$', '', raw_item, flags=re.IGNORECASE)
            item = clean_item.strip().title()
            item = item.rstrip('.')
            if not item: item = "Product"
                
            cart.append(item)
            save_user_cart(username, cart) 
            st.session_state.pop("last_inquired_item", None)
            return f"✅ **Added to Cart!**\n\n**{item}** is now in your cart. You have {len(cart)} item(s) total.\n\nType *'view cart'* to see them."

        remove_match = re.search(r'^remove\s+(.+?)(?:\s+from\s+(?:the\s+|my\s+|a\s+)*\s*(?:cart|csrt|crt|crat|bag))?$', user_lower, re.IGNORECASE)
        if not remove_match:
            remove_match = re.search(r'remove\s+(.+)', user_lower, re.IGNORECASE)
            
        if remove_match:
            raw_target = remove_match.group(1).strip()
            clean_target = re.sub(r'\s+from\s+(?:the\s+|my\s+|a\s+)*\s*(?:cart|csrt|crt|crat|bag).*$', '', raw_target, flags=re.IGNORECASE).strip().lower()
            
            found_index = -1
            for i, cart_item in enumerate(cart):
                if clean_target in cart_item.lower() or cart_item.lower() in clean_target:
                    found_index = i
                    break
            
            if found_index != -1:
                removed_item = cart.pop(found_index)
                save_user_cart(username, cart) 
                return f"🗑️ **Removed from Cart!**\n\n**{removed_item}** has been removed. You have {len(cart)} item(s) total. Type *'view cart'* to see them."
            else:
                return f"⚠️ **Item not found.** I couldn't find '{raw_target.title()}' in your cart. Type *'view cart'* to see what's currently in there."

        # --- ORDER TRACKING INTERCEPTOR ---
        order_match = re.search(r'ORD\d+', user_input, re.IGNORECASE)
        if order_match and ("track" in user_lower or "where" in user_lower):
            order_id = order_match.group(0).upper()
            is_fraud, fraud_msg = check_for_fraud(username, user_input, order_id=order_id)
            if is_fraud: return fraud_msg
            return get_order_details(order_id)
        
        query_text = user_input
        
        # --- VISION LOGIC ---
        if image_base64:
            api_key = os.getenv("GROQ_API_KEY")
            mime_type = "image/png" if image_base64.startswith("iVBORw0KGgo") else "image/jpeg"
            vision_llm = ChatGroq(temperature=0.1, groq_api_key=api_key, model_name="qwen/qwen3.6-27b")
            vision_msg = HumanMessage(content=[
                {"type": "text", "text": "Describe the main product or defect in this image in 3-5 keywords."},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}},
            ])
            vision_response = vision_llm.invoke([vision_msg])
            image_keywords = vision_response.content
            query_text = f"{user_input}\n[Visual Context: The user uploaded an image showing: {image_keywords}. Account for this in your response.]"

        answer = rag_chain.invoke({"input": query_text, "chat_history": chat_history})
        return answer
        
    except Exception as e:
        logging.error(f"Error generating response: {str(e)}")
        return f"⚠️ **Backend Error:** {str(e)}"

# ==========================================
# ANALYTICS & ADMIN
# ==========================================
def get_analytics_data():
    c = db_conn.cursor()
    c.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM messages")
    total_messages = c.fetchone()[0]
    
    c.execute("SELECT role, COUNT(*) FROM messages GROUP BY role")
    role_counts = dict(c.fetchall())
    
    c.execute("SELECT COUNT(*) FROM fraud_flags")
    total_fraud_flags = c.fetchone()[0]
    
    return {
        "total_sessions": total_sessions,
        "total_messages": total_messages,
        "user_messages": role_counts.get("user", 0),
        "bot_messages": role_counts.get("assistant", 0),
        "total_fraud_flags": total_fraud_flags
    }

def get_recent_fraud_alerts():
    c = db_conn.cursor()
    c.execute("SELECT username, flag_reason, severity, created_at FROM fraud_flags ORDER BY created_at DESC LIMIT 5")
    return [{"User": row[0], "Reason": row[1], "Severity": row[2], "Timestamp": row[3]} for row in c.fetchall()]
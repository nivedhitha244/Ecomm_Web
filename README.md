# 🛍️ E-Commerce AI Assistant

An AI-powered **E-Commerce Customer Support Assistant** built with **Python and Streamlit**, combining Retrieval-Augmented Generation (RAG), multimodal vision, secure authentication, persistent chat sessions, and rule-based e-commerce workflows.

The assistant can answer questions from FAQ/policy documents, analyze uploaded product or defect images, manage cart operations, track orders, process returns, and provide administrators with usage analytics.

---

## 🚀 Key Features

### 🔐 1. Secure User Authentication

* User signup and login system.
* Passwords are securely **salted and hashed** using Python's `hashlib`.
* User credentials are stored in a local **SQLite database**.
* Authentication prevents unauthorized access to user-specific chat sessions and features.

### 💬 2. Persistent Chat Sessions

Users can maintain multiple conversations with the AI assistant.

* Automatically saves conversations to SQLite.
* View previous chat sessions.
* Resume existing conversations.
* Delete unwanted conversations.
* Maintains conversation state using Streamlit session state.

This allows users to return to previous customer-support conversations without losing their chat history.

---

### 📚 3. Retrieval-Augmented Generation (RAG)

The assistant uses RAG to provide answers based on the application's FAQ and policy data.

#### RAG Pipeline

```text
FAQ CSV
   ↓
Document Loading
   ↓
Text Processing
   ↓
HuggingFace Embeddings
   ↓
ChromaDB Vector Store
   ↓
Similarity Search
   ↓
Relevant Context
   ↓
LLaMA 3.1 8B
   ↓
Final Answer
```

The system uses:

* **LangChain** for the RAG pipeline.
* **HuggingFace `all-MiniLM-L6-v2`** for text embeddings.
* **ChromaDB** as the vector database.
* **LLaMA 3.1 8B Instant** for response generation.

This reduces the possibility of the LLM generating answers that are unrelated to the application's actual policies.

---

### 🖼️ 4. Multimodal Vision Search

The assistant supports image uploads for product-related queries and defect detection.

Users can upload an image of:

* A damaged product
* A defective product
* A product they want to identify
* A visible product issue

The uploaded image is processed by a vision-capable model to extract useful keywords or descriptions.

```text
User uploads image
        ↓
Vision Model
        ↓
Extract product/defect keywords
        ↓
Add information to chat context
        ↓
RAG / AI processing
        ↓
Relevant response
```

This allows the chatbot to handle both **text and image-based customer queries**.

---

### 🛒 5. Rule-Based Cart Management

Important e-commerce operations are handled using deterministic Python logic instead of relying completely on the LLM.

The application supports:

* Add items to cart
* Remove items from cart
* View cart
* Clear cart

Regex-based interceptors identify specific user commands and route them to the appropriate backend function.

Example:

```text
User:
"Add iPhone 15 to my cart"

        ↓

Regex Interceptor

        ↓

Cart Management Function

        ↓

Database / Cart State

        ↓

Confirmation to User
```

This approach helps prevent the LLM from incorrectly modifying cart information.

---

### 📦 6. Order Tracking

Users can ask about their orders and receive order information from the application's order database.

The system can retrieve information such as:

* Order ID
* Order status
* Delivery information
* Expected delivery date

Example:

```text
User: Where is my order ORD1001?

        ↓

Order Interceptor

        ↓

Search orders.csv / database

        ↓

Retrieve order status

        ↓

Return accurate information
```

Because order information comes from structured data rather than an LLM's generated response, the system avoids hallucinating order details.

---

### 🔄 7. Return and Refund Processing

The assistant also supports return-related workflows.

Before initiating a return, the application checks the order status.

Example workflow:

```text
User requests return
        ↓
Identify Order ID
        ↓
Check Order Status
        ↓
Verify Delivery Status
        ↓
Check Return Eligibility
        ↓
Initiate Refund / Return Flow
        ↓
Show Confirmation
```

This ensures that business rules are checked before performing the operation.

---

### 📊 8. Admin Analytics Dashboard

The application includes an analytics dashboard for monitoring chatbot usage.

The dashboard can display metrics such as:

* Total chat sessions
* Total messages
* Human interactions
* AI interactions
* Session activity

Example:

```text
             Admin Dashboard

       ┌─────────────────────────┐
       │ Total Sessions     120   │
       ├─────────────────────────┤
       │ Total Messages    1,250  │
       ├─────────────────────────┤
       │ Human Messages      620  │
       ├─────────────────────────┤
       │ AI Messages          630 │
       └─────────────────────────┘
```

These metrics help administrators understand how the chatbot is being used.

---

# 🏗️ System Architecture

The overall application follows this architecture:

```text
                         ┌─────────────────┐
                         │      User       │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │    Streamlit    │
                         │   Frontend UI   │
                         └────────┬────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   Python        │
                         │    Backend      │
                         └────────┬────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
              ▼                   ▼                   ▼
       ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
       │ Interceptor │     │     RAG     │     │   Vision    │
       │   Logic     │     │   Pipeline  │     │    Model    │
       └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
              │                   │                   │
              ▼                   ▼                   ▼
       ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
       │ Cart /      │     │  ChromaDB   │     │   Image     │
       │ Orders /    │     │ + Embeddings│     │ Processing   │
       │ Returns     │     └──────┬──────┘     └─────────────┘
       └──────┬──────┘            │
              │                   ▼
              │            ┌─────────────┐
              │            │ LLaMA 3.1   │
              │            │     8B      │
              │            └──────┬──────┘
              │                   │
              └─────────┬─────────┘
                        ▼
                ┌───────────────┐
                │     SQLite    │
                │   Database    │
                └───────────────┘
```

---

# 🛠️ Tech Stack

| Category              | Technology                     |
| --------------------- | ------------------------------ |
| Frontend              | Streamlit                      |
| Backend               | Python 3                       |
| Relational Database   | SQLite                         |
| Vector Database       | ChromaDB                       |
| AI Framework          | LangChain                      |
| Embeddings            | HuggingFace `all-MiniLM-L6-v2` |
| LLM                   | LLaMA 3.1 8B Instant           |
| Vision Model          | Qwen Vision Model              |
| API Provider          | Groq                           |
| Data Processing       | Pandas                         |
| Authentication        | Python `hashlib`               |
| Environment Variables | `.env`                         |

---

# 📂 Project Structure

```text
ecommerce-assistant/
│
├── app.py
│   └── Streamlit frontend, UI, routing, and session state
│
├── app_backend.py
│   └── Database logic, RAG pipeline, AI/API calls,
│       authentication, cart/order/return processing
│
├── .env
│   └── Environment variables and API keys
│
├── requirements.txt
│   └── Python dependencies
│
├── data/
│   │
│   ├── faq_data_2.csv
│   │   └── FAQ/policy dataset
│   │
│   └── orders.csv
│       └── Order tracking information
│
└── chat_history.db
    └── SQLite database generated automatically
```

> **Note:** `chat_history.db` does not need to be manually created. The application generates it when the project is run for the first time.

---

# 📄 Dataset Requirements

## `faq_data_2.csv`

The FAQ dataset should contain at least the following columns:

```text
question,answer
```

Example:

```csv
question,answer
What is the return policy?,Products can be returned within the specified return period.
How long does delivery take?,Standard delivery usually takes several business days.
```

This data is used by the RAG pipeline to retrieve relevant information.

---

## `orders.csv`

The order dataset contains information required for order tracking and return processing.

Example structure:

```csv
order_id,status,delivery_date
ORD1001,Delivered,2026-08-05
ORD1002,Shipped,2026-08-10
ORD1003,Processing,2026-08-12
```

> The exact columns should match the fields expected by the backend implementation.

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone <your-repository-url>
```

Navigate into the project:

```bash
cd ecommerce-assistant
```

---

## 2. Create a Virtual Environment

It is recommended to use a virtual environment.

### Windows

```bash
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create a `.env` file in the project root directory.

Example:

```env
GROQ_API_KEY=your_groq_api_key
```

Replace the placeholder with your actual API key.

### ⚠️ Security

Never commit your API key to GitHub.

Add `.env` to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
chat_history.db
```

---

# ▶️ Running the Application

After activating the virtual environment and installing the dependencies, run:

```bash
streamlit run app.py
```

Streamlit will start the application and provide a local URL, usually similar to:

```text
http://localhost:8501
```

Open the URL in your browser.

---

# 🔄 Application Workflow

The application determines how to process a user's request based on the type of query.

```text
                    User Query
                        │
                        ▼
                ┌───────────────┐
                │ Query Analysis │
                └───────┬───────┘
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼
    Cart/Order       FAQ/Policy       Image Query
      Query             Query             Query
        │               │                │
        ▼               ▼                ▼
   Rule-Based          RAG            Vision Model
   Interceptor        Pipeline             │
        │               │                  ▼
        │               │             Extract Context
        │               │                  │
        │               ▼                  │
        │            ChromaDB              │
        │               │                  │
        │               ▼                  │
        │          LLaMA 3.1 8B            │
        │               │                  │
        └───────────────┼──────────────────┘
                        ▼
                  Final Response
                        │
                        ▼
                 Save Chat History
```

---

# 🧠 Why RAG?

A normal LLM may answer based on information learned during its training.

However, an e-commerce assistant needs to answer questions using the **specific policies and information of the application**.

RAG solves this by retrieving relevant information before generating the response.

For example:

```text
User:
"Can I return a product after 15 days?"

        ↓

Search FAQ / Policy Documents

        ↓

Retrieve relevant return-policy information

        ↓

Provide retrieved information to LLaMA

        ↓

AI generates answer based on the policy
```

This makes the chatbot more suitable for domain-specific customer support.

---

# 🛡️ Why Rule-Based Interceptors?

Not every operation should be handled by an LLM.

Operations such as:

* Adding an item to a cart
* Removing an item
* Checking an order
* Processing a return

require deterministic behavior.

For example, an LLM should **not invent an order status**.

Instead:

```text
User → "Where is order ORD1001?"

       ↓

Rule-Based Interceptor

       ↓

Search Order Data

       ↓

Actual Status

       ↓

Response
```

This provides greater reliability for business-critical operations.

---

# 🔐 Authentication Flow

```text
Signup
  │
  ▼
Create Salt
  │
  ▼
Hash Password
  │
  ▼
Store Hash + Salt
  │
  ▼
SQLite Database
```

During login:

```text
User enters password
        ↓
Retrieve stored salt
        ↓
Hash entered password
        ↓
Compare hashes
        ↓
Authentication successful / failed
```

Plain-text passwords are not stored.

---

# 🗃️ Database

The application uses **SQLite** for persistent application data.

SQLite can store information such as:

* User accounts
* Chat sessions
* Chat messages
* Interaction metrics
* Other application state

The database file is generated automatically:

```text
chat_history.db
```

ChromaDB is used separately for vector-based document retrieval.

### SQLite vs ChromaDB

| SQLite                  | ChromaDB          |
| ----------------------- | ----------------- |
| Relational database     | Vector database   |
| Stores structured data  | Stores embeddings |
| Users                   | FAQ embeddings    |
| Chat history            | Semantic search   |
| Orders/application data | RAG retrieval     |
| Authentication data     | Document context  |

---

# 📈 Admin Analytics

The analytics dashboard provides an overview of chatbot usage.

Possible metrics include:

```text
Total Sessions
       ↓
Total Messages
       ↓
Human Messages
       ↓
AI Messages
       ↓
Interaction Analysis
```

This helps administrators understand user engagement and chatbot activity.

---

# 💡 Example Queries

Users can interact with the assistant using natural language.

### FAQ / Policy

```text
What is your return policy?
```

### Order Tracking

```text
Where is my order ORD1001?
```

### Cart

```text
Add the laptop to my cart.
```

```text
Show my cart.
```

```text
Remove the laptop from my cart.
```

### Returns

```text
I want to return order ORD1001.
```

### Image-Based Query

Upload an image of a damaged product and ask:

```text
What is wrong with this product?
```

---

# 🎯 Project Objectives

The main objectives of this project are to demonstrate how Generative AI can be integrated with traditional software engineering and e-commerce business logic.

The project combines:

* Generative AI
* Retrieval-Augmented Generation
* Vector databases
* Embeddings
* Multimodal AI
* Authentication
* Relational databases
* Rule-based processing
* Persistent memory
* Analytics
* Streamlit UI

Rather than relying entirely on an LLM, the application combines **AI + deterministic backend logic** to create a more reliable e-commerce assistant.

---

# 🌟 Key Highlights

### Generative AI

Uses LLaMA to generate natural-language responses.

### RAG

Retrieves relevant FAQ and policy information before generating answers.

### Multimodal AI

Processes product/defect images using a vision model.

### Persistent Memory

Stores previous conversations in SQLite.

### Business Logic

Uses deterministic Python functions for cart, order, and return operations.

### Secure Authentication

Uses salted password hashing rather than storing plain-text passwords.

### Analytics

Provides administrators with chatbot usage metrics.

---

# 🔮 Future Enhancements

Potential improvements include:

* 💳 Payment gateway integration
* 📧 Email notifications for orders and returns
* 🚚 Real-time shipping API integration
* 📦 Product recommendation system
* ⭐ Product review analysis
* 🎙️ Voice-based customer support
* 🌐 Multi-language support
* 🧠 Long-term personalized user memory
* 📊 Advanced admin analytics
* 🔔 Order status notifications
* 🛒 AI-powered product recommendations
* 🔍 Semantic product search
* 📱 Mobile-responsive interface
* 👨‍💼 Human-agent escalation for complex queries

---

# 🧪 Testing

Before deployment, test the following workflows:

### Authentication

* [ ] User signup
* [ ] Valid login
* [ ] Invalid login
* [ ] Password verification

### Chat

* [ ] New conversation
* [ ] Continue previous conversation
* [ ] Delete conversation
* [ ] Chat history persistence

### RAG

* [ ] FAQ retrieval
* [ ] Policy questions
* [ ] Irrelevant questions
* [ ] Missing information handling

### Cart

* [ ] Add item
* [ ] Remove item
* [ ] View cart
* [ ] Clear cart

### Orders

* [ ] Valid order lookup
* [ ] Invalid order ID
* [ ] Delivery status
* [ ] Delivery date

### Returns

* [ ] Eligible order
* [ ] Ineligible order
* [ ] Return request

### Vision

* [ ] Upload image
* [ ] Extract image information
* [ ] Use extracted information in chatbot context

### Admin

* [ ] Session count
* [ ] Message count
* [ ] Human/AI interaction metrics

---

# ⚠️ Important Notes

1. Keep API keys inside `.env`.
2. Never upload `.env` to GitHub.
3. Ensure the required files exist inside the `data/` directory.
4. Make sure the CSV column names match the backend implementation.
5. The SQLite database is generated automatically.
6. Internet access is required for API-based AI model calls.
7. ChromaDB must be initialized/populated before performing RAG queries if your implementation does not build the vector store automatically.

---

# 👩‍💻 Author

**K.S. Nivedhitha**

Computer Science Engineering
St. Joseph's College of Engineering, Chennai

---

# 📜 License

This project is developed for educational and demonstration purposes.

If you plan to publish or distribute the project, add an appropriate open-source license such as MIT based on your intended usage.

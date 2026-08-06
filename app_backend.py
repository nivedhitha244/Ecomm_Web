import os
import logging
import pandas as pd
from dotenv import load_dotenv
from langchain_community.document_loaders import DataFrameLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Setup Logging (Creates chatbot_activity.log automatically)
logging.basicConfig(
    filename='chatbot_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load hidden API keys from .env
load_dotenv()

def get_rag_chain():
    try:
        df = pd.read_csv("faq_data_2.csv")
        loader = DataFrameLoader(df, page_content_column="question")
        docs = loader.load()
        
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store = Chroma.from_documents(docs, embeddings)
        
        # Pulls key securely from the environment
        api_key = os.getenv("GROQ_API_KEY")
        llm = ChatGroq(temperature=0.3, groq_api_key=api_key, model_name="llama-3.1-8b-instant")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful e-commerce assistant. Answer based ONLY on the provided context. If you don't know, say 'I cannot find that in our policies.'\n\nContext: {context}"),
            ("human", "{input}")
        ])
        
        retriever = vector_store.as_retriever(search_kwargs={"k": 2})
        
        # THE FIX: Now we pull the question AND the answer from the metadata!
        def format_docs(docs):
            return "\n\n".join(f"Question: {doc.page_content}\nAnswer: {doc.metadata['answer']}" for doc in docs)
            
        rag_chain = (
            {"context": retriever | format_docs, "input": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        logging.info("Backend RAG Pipeline initialized successfully.")
        return rag_chain
    except Exception as e:
        logging.error(f"Error initializing pipeline: {e}")
        raise e

def generate_response(rag_chain, user_input):
    logging.info(f"User Asked: {user_input}")
    try:
        answer = rag_chain.invoke(user_input)
        logging.info(f"Bot Answered: {answer}")
        return answer
    except Exception as e:
        logging.error(f"Error generating response: {e}")
        return "I'm sorry, I encountered an error."
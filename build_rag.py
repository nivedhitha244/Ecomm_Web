import os
os.environ["HF_HOME"] = "/app/hf_cache"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
import pandas as pd
from langchain_community.document_loaders import DataFrameLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

print("Building RAG database...")

df = pd.read_csv("faq_data_2.csv")
df.columns = df.columns.str.lower()

loader = DataFrameLoader(
    df,
    page_content_column="question"
)

docs = loader.load()

print(f"Loaded {len(docs)} FAQ documents.")

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

Chroma.from_documents(
    documents=docs,
    embedding=embeddings,
    persist_directory="chroma_db"
)

print("RAG database created successfully.")
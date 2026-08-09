FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app_backend.py .
COPY app_frontend.py .
COPY faq_data_2.csv .
COPY orders.csv .
COPY build_rag.py .
COPY .streamlit .streamlit

# Build the RAG database during Docker image creation
RUN python build_rag.py && chmod -R 777 /app

EXPOSE 8501

CMD ["sh", "-c", "streamlit run app_frontend.py --server.port=$PORT --server.address=0.0.0.0"]
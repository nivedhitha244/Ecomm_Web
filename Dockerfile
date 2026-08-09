FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app_backend.py .
COPY app_frontend.py .
COPY faq_data_2.csv .
COPY orders.csv .
COPY .streamlit .streamlit

# Verify that the backend contains get_rag_chain
RUN python -c "import app_backend; print('SUCCESS: get_rag_chain =', app_backend.get_rag_chain)"

EXPOSE 8501

CMD ["sh", "-c", "streamlit run app_frontend.py --server.port=$PORT --server.address=0.0.0.0"]
FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

CMD ["sh", "-c", "streamlit run app_frontend.py --server.port=$PORT --server.address=0.0.0.0"]
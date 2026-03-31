FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sp500_tickers.py .
COPY reddit_producer.py .

CMD ["python", "reddit_producer.py"]

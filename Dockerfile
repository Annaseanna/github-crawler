FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY github-crawler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY github-crawler/. .

# Copy shared modules
COPY shared ./shared

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]


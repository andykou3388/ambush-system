FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app .

EXPOSE 8000

# 開發環境使用 volume 掛載，main.py 在 /app/app/main.py
CMD ["python", "app/main.py"]

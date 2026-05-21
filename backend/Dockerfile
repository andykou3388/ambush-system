FROM python:3.9-slim

WORKDIR /app

# 先複製 requirements.txt 並安裝依賴（利用 Docker cache）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製原始碼（僅供建置用，開發時會被 volume 覆蓋）
COPY ./app ./app

EXPOSE 8000

# 開發環境下 command 會被 docker-compose 的 command 覆蓋
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM node:18-alpine

WORKDIR /app

# 先複製 package.json 並安裝依賴
COPY package.json .
RUN npm install

# 複製所有源代碼
COPY . .

EXPOSE 3000

# 開發環境使用 Vite 開發服務器
CMD ["npm", "run", "dev"]
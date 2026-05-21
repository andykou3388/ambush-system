FROM node:16-alpine

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

EXPOSE 3000

# 開發環境使用 volume 掛載 src/，server.js 在 /app/src/server.js
CMD ["node", "src/server.js"]

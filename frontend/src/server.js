const express = require('express');
const axios = require('axios');
const app = express();
const PORT = process.env.FRONTEND_PORT || 3000;

app.use(express.json());

// 簡單的首頁路由
app.get('/', (req, res) => {
  res.json({ message: 'Welcome to Ambush System Frontend' });
});

// 代理後端 API 請求
app.get('/api/test', async (req, res) => {
  try {
    const response = await axios.get('http://backend:8000/');
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch from backend' });
  }
});

app.listen(PORT, () => {
  console.log(`Frontend server running on port ${PORT}`);
});
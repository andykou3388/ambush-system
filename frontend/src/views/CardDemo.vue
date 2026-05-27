<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">股票卡片展示</h1>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <StockCard 
        v-for="stock in demoStocks" 
        :key="stock.symbol" 
        :stock="stock" 
      />
    </div>
  </div>
</template>

<script setup>
import StockCard from '../components/StockCard.vue'

const demoStocks = [
  { symbol: 'AAPL', name: 'Apple Inc.', price: 175.50, changePct: 2.3,
    zone: 'buy', ma10: 170.20, ma30: 165.80, score: 85.5 },
  { symbol: 'MSFT', name: 'Microsoft', price: 330.20, changePct: -0.5,
    zone: 'hold', ma10: 325.40, ma30: 320.10, score: 65.2 },
  { symbol: 'TSLA', name: 'Tesla Inc.', price: 245.80, changePct: -3.2,
    zone: 'sell', ma10: 260.30, ma30: 270.50, score: 35.8 },
]
</script>
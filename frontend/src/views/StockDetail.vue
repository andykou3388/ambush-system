<template>
  <div class="stock-detail p-8">
    <div class="max-w-4xl mx-auto">
      <div class="mb-6">
        <router-link to="/" class="text-blue-600 hover:text-blue-800">
          &larr; 返回看板
        </router-link>
      </div>
      
      <div class="bg-white rounded-lg shadow p-6">
        <h1 class="text-3xl font-bold mb-2">{{ stock.symbol }}</h1>
        <p class="text-gray-500 mb-6">{{ stock.name }}</p>
        
        <div class="grid grid-cols-2 gap-4">
          <div class="p-4 bg-gray-50 rounded">
            <div class="text-sm text-gray-500">當前價格</div>
            <div class="text-2xl font-bold">${{ stock.price.toFixed(2) }}</div>
          </div>
          <div class="p-4 bg-gray-50 rounded">
            <div class="text-sm text-gray-500">漲跌幅</div>
            <div class="text-2xl font-bold" :class="stock.changePct >= 0 ? 'text-green-600' : 'text-red-600'">
              {{ stock.changePct > 0 ? '+' : '' }}{{ stock.changePct.toFixed(2) }}%
            </div>
          </div>
          <div class="p-4 bg-gray-50 rounded">
            <div class="text-sm text-gray-500">MA10</div>
            <div class="text-xl font-semibold">${{ stock.ma10.toFixed(2) }}</div>
          </div>
          <div class="p-4 bg-gray-50 rounded">
            <div class="text-sm text-gray-500">MA30</div>
            <div class="text-xl font-semibold">${{ stock.ma30.toFixed(2) }}</div>
          </div>
        </div>
        
        <div class="mt-6">
          <span class="inline-block px-3 py-1 rounded-full text-sm font-medium"
            :class="zoneBadgeClass">
            {{ zoneLabels[stock.zone] }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const zoneLabels = { buy: '買入區', hold: '持有區', sell: '賣出區' }

// 使用路由參數獲取股票代碼
const stockSymbol = route.params.symbol

// 模擬股票數據 - 實際應用中應從 API 獲取
const stock = computed(() => {
  const demoStocks = {
    'AAPL': { symbol: 'AAPL', name: 'Apple Inc.', price: 175.50, changePct: 2.3, zone: 'buy', ma10: 170.20, ma30: 165.80, score: 85.5 },
    'MSFT': { symbol: 'MSFT', name: 'Microsoft', price: 330.20, changePct: -0.5, zone: 'hold', ma10: 325.40, ma30: 320.10, score: 65.2 },
    'TSLA': { symbol: 'TSLA', name: 'Tesla Inc.', price: 245.80, changePct: -3.2, zone: 'sell', ma10: 260.30, ma30: 270.50, score: 35.8 },
  }
  return demoStocks[stockSymbol] || { symbol: stockSymbol, name: '未知股票', price: 0, changePct: 0, zone: 'hold', ma10: 0, ma30: 0, score: 0 }
})

const zoneBadgeClass = computed(() => {
  const zone = stock.value.zone
  return {
    'bg-green-100 text-green-800': zone === 'buy',
    'bg-yellow-100 text-yellow-800': zone === 'hold',
    'bg-red-100 text-red-800': zone === 'sell'
  }
})
</script>
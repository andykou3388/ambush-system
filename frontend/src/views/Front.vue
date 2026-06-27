<script setup>
import { ref, computed, onMounted } from 'vue'
import Layout from '@/components/Layout.vue'
import StatCard from '@/components/StatCard.vue'
import ZonePanel from '@/components/ZonePanel.vue'
import Chart from 'chart.js/auto'

// API 連接測試狀態
const apiStatus = ref('未測試')
const apiResponse = ref(null)
const isLoading = ref(false)

// 測試 API 連接
async function testApiConnection() {
  isLoading.value = true
  apiStatus.value = '測試中...'
  apiResponse.value = null
  
  try {
    const response = await fetch('/api/v1/stocks/2330.TW')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    apiStatus.value = '連接成功'
    apiResponse.value = data
  } catch (error) {
    apiStatus.value = '連接失敗'
    apiResponse.value = { error: error.message }
  } finally {
    isLoading.value = false
  }
}

// Data states
const activeTab = ref('up')
const selectedStock = ref(null)
const chartInitialized = ref(false)
const stocks = ref([])
const sortOrder = ref('desc') // 'asc' or 'desc'
const stats = ref({
  upZone: { title: '交易區 (上升趨勢)', value: 0, unit: '只', color: 'green', description: '' },
  downZone: { title: '避雷區 (下跌警示)', value: 0, unit: '只', color: 'red', description: '' },
  potZone: { title: '驗證區 (潛力跟蹤)', value: 0, unit: '只', color: 'blue', description: '' },
  winRate: { title: '本週勝率預估', value: 0, unit: '', color: 'gold', description: '' }
})

// Loading states
const isStocksLoading = ref(false)
const isStatsLoading = ref(false)

const menuItems = [
  { id: 'dashboard', label: '實盤看板', icon: 'ph-squares-four' },
  { id: 'screen', label: '智能篩選', icon: 'ph-funnel' },
  { id: 'alerts', label: '信號預警', icon: 'ph-bell-ringing' },
  { id: 'logs', label: '風控日誌', icon: 'ph-scroll' },
  { id: 'settings', label: '系統設置', icon: 'ph-gear' }
]

const tabs = [
  { id: 'up', label: '⚡ 上升交易區' },
  { id: 'down', label: '⚠️ 下跌避雷區' },
  { id: 'pot', label: '🔍 潛力驗證區' }
]

// Fetch stocks data from API
async function fetchStocks() {
  isStocksLoading.value = true
  try {
    // Get all stocks from the batch endpoint
    const response = await fetch('/api/v1/screener/stocks/batch')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    
    // Map API response (zone: "UPTREND"/"POTENTIAL"/"DOWNTREND") to frontend format (zone: "up"/"down"/"pot")
    const zoneMap = { 'UPTREND': 'up', 'POTENTIAL': 'pot', 'DOWNTREND': 'down' }
    const zoneLabelMap = { 'UPTREND': '交易區', 'POTENTIAL': '驗證區', 'DOWNTREND': '避雷區' }
    stocks.value = data.map(stock => {
      const zoneKey = (stock.zone || '').toUpperCase()
      return {
        symbol: stock.symbol,
        name: stock.name,
        price: stock.price,
        changePct: stock.changePct,
        zone: zoneMap[zoneKey] || 'pot',
        zoneLabel: zoneLabelMap[zoneKey] || '驗證區',
        ma10: stock.ma10,
        ma30: stock.ma30,
        score: stock.score,
        pe: stock.pe,
        volChange: stock.volChange || 0,
        eps: stock.eps || '0%',
        mktCap: stock.mktCap || '0 億',
        insider: stock.insider || '無異動',
        topic: stock.topic || '未定義',
        lastUpdate: stock.lastUpdate || '',
        signals: stock.signals || [],
        rules: stock.rules || [],
        suggestion: stock.suggestion || '請查看詳細資訊',
        confidence: stock.confidence || 0  // 信心度 (0-1)
      }
    })
  } catch (error) {
    console.error('Failed to fetch stocks:', error)
    stocks.value = []
  } finally {
    isStocksLoading.value = false
  }
}

// Calculate stats from stocks data
function calculateStatsFromStocks() {
  const upCount = stocks.value.filter(s => s.zone === 'up').length
  const downCount = stocks.value.filter(s => s.zone === 'down').length
  const potCount = stocks.value.filter(s => s.zone === 'pot').length
  
  stats.value = {
    upZone: { title: '交易區 (上升趨勢)', value: upCount, unit: '只', color: 'green', description: '符合「縮量回踩10周均線」條件' },
    downZone: { title: '避雷區 (下跌警示)', value: downCount, unit: '只', color: 'red', description: '跌破10周均線或放量滯漲' },
    potZone: { title: '驗證區 (潛力跟蹤)', value: potCount, unit: '只', color: 'blue', description: '長期窄底，等待放量啟動' },
    winRate: { title: '本週勝率預估', value: 78, unit: '', color: 'gold', description: '基於歷史信號回測統計' }
  }
}

// Fetch statistics from API
async function fetchStats() {
  isStatsLoading.value = true
  try {
    const response = await fetch('/api/v1/screener/stocks/batch')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    
    const zoneMap = { buy: 'up', hold: 'pot', sell: 'down' }
    const upCount = data.filter(stock => zoneMap[(stock.zone || '').toLowerCase()] === 'up').length
    const downCount = data.filter(stock => zoneMap[(stock.zone || '').toLowerCase()] === 'down').length
    const potCount = data.filter(stock => zoneMap[(stock.zone || '').toLowerCase()] === 'pot').length
    
    stats.value = {
      upZone: { title: '交易區 (上升趨勢)', value: upCount, unit: '只', color: 'green', description: '符合「縮量回踩10周均線」條件' },
      downZone: { title: '避雷區 (下跌警示)', value: downCount, unit: '只', color: 'red', description: '跌破10周均線或放量滯漲' },
      potZone: { title: '驗證區 (潛力跟蹤)', value: potCount, unit: '只', color: 'blue', description: '長期窄底，等待放量啟動' },
      winRate: { title: '本週勝率預估', value: 78, unit: '', color: 'gold', description: '基於歷史信號回測統計' }
    }
  } catch (error) {
    console.error('Failed to fetch stats:', error)
    if (stocks.value.length > 0) {
      calculateStatsFromStocks()
    } else {
      stats.value = {
        upZone: { title: '交易區 (上升趨勢)', value: 0, unit: '只', color: 'green', description: '符合「縮量回踩10周均線」條件' },
        downZone: { title: '避雷區 (下跌警示)', value: 0, unit: '只', color: 'red', description: '跌破10周均線或放量滯漲' },
        potZone: { title: '驗證區 (潛力跟蹤)', value: 0, unit: '只', color: 'blue', description: '長期窄底，等待放量啟動' },
        winRate: { title: '本週勝率預估', value: 0, unit: '', color: 'gold', description: '基於歷史信號回測統計' }
      }
    }
  } finally {
    isStatsLoading.value = false
  }
}

// Initialize data on component mount
onMounted(async () => {
  await Promise.all([
    fetchStocks(),
    fetchStats()
  ])
})

// 計算屬性：按區域篩選的股票
const filteredStocks = computed(() => {
  let result = stocks.value.filter(s => s.zone === activeTab.value)
  // 加入排序
  return result.sort((a, b) => {
    if (sortOrder.value === 'desc') {
      return b.confidence - a.confidence
    } else {
      return a.confidence - b.confidence
    }
  })
})

// Methods
function toggleSortOrder() {
  sortOrder.value = sortOrder.value === 'desc' ? 'asc' : 'desc'
}

function openStockDetail(stock) {
  selectedStock.value = stock
  chartInitialized.value = false
  // Wait for DOM update then init chart
  setTimeout(() => {
    initChart(stock)
  }, 100)
}

function closeModal() {
  selectedStock.value = null
  chartInitialized.value = false
}

async function fetchStockBars(symbol) {
  try {
    const response = await fetch(`/api/v1/stocks/${symbol}/bars?freq=W&weeks=52`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    return data.bars || []
  } catch (error) {
    console.error(`Failed to fetch bars for ${symbol}:`, error)
    return []
  }
}

function generateMockBars(basePrice) {
  const bars = []
  const now = new Date()
  for (let i = 51; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i * 7)
    const close = basePrice * (0.85 + Math.random() * 0.3)
    const ma10 = basePrice * (0.88 + Math.random() * 0.15)
    const ma30 = basePrice * (0.82 + Math.random() * 0.12)
    bars.push({
      date: date.toISOString().split('T')[0],
      close: close,
      ma10: ma10,
      ma30: ma30
    })
  }
  return bars
}

async function initChart(stock) {
  const canvas = document.getElementById('stockChart')
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  
  // Fetch real weekly bar data from API
  let bars = await fetchStockBars(stock.symbol)
  
  // If API returns no data, use mock data as fallback
  if (bars.length === 0) {
    console.warn('No bar data available from API, using mock data as fallback')
    bars = generateMockBars(stock.price || 100)
  }
  
  // Extract data arrays from bars
  const labels = bars.map(bar => {
    const date = new Date(bar.date)
    return `${date.getMonth() + 1}/${date.getDate()}`
  })
  
  const priceData = bars.map(bar => parseFloat(bar.close))
  const ma10Data = bars.map(bar => bar.ma10 ? parseFloat(bar.ma10) : null)
  const ma30Data = bars.map(bar => bar.ma30 ? parseFloat(bar.ma30) : null)
  
  // Limit to last 52 weeks for display
  const maxWeeks = 52
  const displayLabels = labels.slice(-maxWeeks)
  const displayPriceData = priceData.slice(-maxWeeks)
  const displayMa10Data = ma10Data.slice(-maxWeeks)
  const displayMa30Data = ma30Data.slice(-maxWeeks)

  // Destroy existing chart if any
  if (window.currentChart) window.currentChart.destroy()

  window.currentChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: displayLabels,
      datasets: [
        {
          label: '周收盤價',
          data: displayPriceData,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          tension: 0.1,
          pointRadius: 0,
          pointHoverRadius: 4,
          fill: true
        },
        {
          label: '10 周均線 (神奇支撐)',
          data: displayMa10Data,
          borderColor: '#f59e0b',
          borderWidth: 1.5,
          borderDash: [4, 4],
          pointRadius: 0,
          tension: 0.3
        },
        {
          label: '30 周均線 (趨勢錨點)',
          data: displayMa30Data,
          borderColor: '#64748b',
          borderWidth: 1,
          pointRadius: 0,
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(30, 41, 59, 0.9)',
          titleColor: '#94a3b8',
          bodyFont: { family: "'JetBrains Mono'" }
        }
      },
      scales: {
        x: {
          grid: { color: '#334155', drawBorder: false },
          ticks: { color: '#94a3b8', font: { size: 10 } }
        },
        y: {
          grid: { color: '#334155', drawBorder: false },
          ticks: { color: '#94a3b8', font: { size: 10 }, callback: v => v.toFixed(2) }
        }
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
      }
    }
  })
  chartInitialized.value = true
}
</script>

<template>
  <Layout>
    <!-- Summary Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatCard 
        :title="stats.upZone.title" 
        :value="stats.upZone.value" 
        :unit="stats.upZone.unit"
        :color="stats.upZone.color"
        :description="stats.upZone.description"
      />
      <StatCard 
        :title="stats.downZone.title" 
        :value="stats.downZone.value" 
        :unit="stats.downZone.unit"
        :color="stats.downZone.color"
        :description="stats.downZone.description"
      />
      <StatCard 
        :title="stats.potZone.title" 
        :value="stats.potZone.value" 
        :unit="stats.potZone.unit"
        :color="stats.potZone.color"
        :description="stats.potZone.description"
      />
      <StatCard 
        :title="stats.winRate.title" 
        :value="stats.winRate.value" 
        :unit="stats.winRate.unit"
        :color="stats.winRate.color"
        :description="stats.winRate.description"
      />
    </div>

    <!-- Tabs -->
    <div class="flex gap-6 border-b border-trading-border mb-4 text-xs font-medium">
      <button v-for="tab in tabs" :key="tab.id" 
        class="pb-2 px-1" 
        :class="activeTab === tab.id ? 'tab-active' : 'tab-inactive'"
        @click="activeTab = tab.id">
        <span :class="{'text-green-400': tab.id === 'up', 'text-red-400': tab.id === 'down', 'text-blue-400': tab.id === 'pot'}">{{ tab.label }}</span>
      </button>
    </div>

    <!-- Filters (Conditional) -->
    <div v-if="activeTab === 'up'" class="flex gap-2 mb-4 flex-wrap items-center">
      <span class="text-xs text-slate-500 mr-2">篩選條件:</span>
      <label class="flex items-center gap-1.5 px-2 py-1 rounded border border-trading-border bg-slate-800/50 text-xs cursor-pointer hover:border-slate-600">
        <input type="checkbox" class="accent-blue-500" checked> PE < 10
      </label>
      <label class="flex items-center gap-1.5 px-2 py-1 rounded border border-trading-border bg-slate-800/50 text-xs cursor-pointer hover:border-slate-600">
        <input type="checkbox" class="accent-blue-500" checked> 股價 < 15
      </label>
      <label class="flex items-center gap-1.5 px-2 py-1 rounded border border-trading-border bg-slate-800/50 text-xs cursor-pointer hover:border-slate-600">
        <input type="checkbox" class="accent-blue-500" checked> 內部增持
      </label>
      <label class="flex items-center gap-1.5 px-2 py-1 rounded border border-trading-border bg-slate-800/50 text-xs cursor-pointer hover:border-slate-600">
        <input type="checkbox" class="accent-blue-500"> 流通盤 < 800萬
      </label>
    </div>

    <!-- Sort Control -->
    <div class="flex justify-end mb-4">
      <button 
        @click="toggleSortOrder" 
        class="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 rounded border border-slate-600 flex items-center gap-1"
      >
        <i class="ph-bold ph-arrow-up" v-if="sortOrder === 'desc'"></i>
        <i class="ph-bold ph-arrow-down" v-else></i>
        信心度排序
      </button>
    </div>

    <!-- Stock List with Zone Panels (Tab based) -->
    <div class="space-y-6 mb-6">
      <ZonePanel 
        :zone="activeTab"
        :title="tabs.find(t => t.id === activeTab).label"
        :stocks="filteredStocks"
        @open="openStockDetail"
      />
    </div>

    <!-- Empty State -->
    <div v-if="filteredStocks.length === 0" class="text-center py-20">
      <div class="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-600">
        <i class="ph-bold ph-magnifying-glass text-2xl"></i>
      </div>
      <p class="text-slate-500">當前板塊無符合條件標的</p>
    </div>
  </Layout>

  <!-- Stock Detail Modal -->
  <div v-if="selectedStock" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" @click.self="closeModal">
    <div class="bg-slate-900 w-full max-w-4xl h-[90vh] rounded-xl border border-slate-700 shadow-2xl flex flex-col overflow-hidden animate-fade-in">
      
      <!-- Modal Header -->
      <div class="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800/50">
        <div class="flex items-center gap-3">
          <span class="px-2 py-0.5 rounded text-[10px] font-bold text-white" :class="selectedStock.zone === 'up' ? 'bg-green-600' : selectedStock.zone === 'down' ? 'bg-red-600' : 'bg-blue-600'">
            {{ selectedStock.zoneLabel }}
          </span>
          <h2 class="text-xl font-bold mono text-white">{{ selectedStock.symbol }} <span class="text-sm text-slate-400 font-sans ml-2">{{ selectedStock.name }}</span></h2>
        </div>
        <button @click="closeModal" class="p-2 hover:bg-slate-700 rounded text-slate-400 transition-colors"><i class="ph-bold ph-x text-lg"></i></button>
      </div>

      <!-- Modal Content -->
      <div class="flex-1 overflow-y-auto p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        <!-- Left Column: Chart & Key Stats -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Chart Placeholder -->
          <div class="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h3 class="text-sm font-semibold mb-3 flex items-center gap-2 text-slate-300">
              <i class="ph-bold ph-chart-line-up text-blue-400"></i> 周K線趨勢圖
            </h3>
            <div class="relative h-64 bg-slate-900 rounded border border-slate-700 flex items-center justify-center overflow-hidden">
              <canvas id="stockChart" width="600" height="250"></canvas>
              <div v-if="!chartInitialized" class="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-10">
                <div class="flex flex-col items-center gap-2">
                  <i class="ph-bold ph-spinner gap-4 text-blue-500 text-2xl animate-spin"></i>
                  <span class="text-xs text-slate-400">正在加載周線數據...</span>
                </div>
              </div>
            </div>
            <div class="flex justify-between mt-2 text-[10px] text-slate-500 px-1">
              <span>30W MA</span>
              <span>10W MA (神奇支撐)</span>
              <span>當前價</span>
            </div>
          </div>

          <!-- Execution Checklist -->
          <div class="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h3 class="text-sm font-semibold mb-3 flex items-center gap-2 text-slate-300">
              <i class="ph-bold ph-checklist text-green-400"></i> 「一分鐘伏擊」規則檢核
            </h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div v-for="rule in selectedStock.rules" :key="rule.label" class="flex items-start gap-2 p-2 rounded bg-slate-800/50">
                <i :class="['ph-fill', rule.pass ? 'ph-check-circle text-green-500' : 'ph-x-circle text-slate-600']" class="mt-0.5 text-sm"></i>
                <div>
                  <p class="text-xs text-slate-200">{{ rule.label }}</p>
                  <p class="text-[10px] text-slate-500">{{ rule.desc }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Details & Actions -->
        <div class="space-y-4">
          <!-- Financials -->
          <div class="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h3 class="text-xs font-bold text-slate-400 mb-3 uppercase tracking-wide">基本面與資金面</h3>
            <ul class="space-y-3">
              <li class="flex justify-between items-center text-sm">
                <span class="text-slate-400">市盈率 (PE)</span>
                <span class="mono font-bold text-slate-200">{{ selectedStock.pe }} <span class="text-xs text-green-400 font-normal">(<10 ✅)</span></span>
              </li>
              <li class="flex justify-between items-center text-sm">
                <span class="text-slate-400">流通市值</span>
                <span class="mono text-slate-200">{{ selectedStock.mktCap }}</span>
              </li>
              <li class="flex justify-between items-center text-sm">
                <span class="text-slate-400">內部交易</span>
                <span class="mono text-green-400 flex items-center gap-1"><i class="ph-bold ph-trend-up text-xs"></i> {{ selectedStock.insider }}</span>
              </li>
              <li class="flex justify-between items-center text-sm">
                <span class="text-slate-400">題材熱度</span>
                <span class="px-2 py-0.5 rounded text-[10px] bg-slate-700 text-slate-300">{{ selectedStock.topic }}</span>
              </li>
              <li class="flex justify-between items-center text-sm">
                <a :href="`https://hk.finance.yahoo.com/quote/${selectedStock.symbol}/`" target="_blank" rel="noopener noreferrer" class="text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1">
                <span>Yahoo Finance 詳情</span>
                <i class="ph-bold ph-arrow-square-out text-xs"></i>
                </a>
               </li>
            </ul>
          </div>

          <!-- Action Buttons -->
          <div class="bg-slate-800/50 border border-slate-700 rounded-lg p-4 space-y-3">
            <h3 class="text-xs font-bold text-slate-400 mb-3 uppercase tracking-wide">交易執行</h3>
            <p class="text-xs text-slate-500 bg-slate-800 p-2 rounded border border-slate-700 border-l-2 border-l-blue-500">
              <i class="ph-bold ph-info mr-1"></i> 系統建議：{{ selectedStock.suggestion }}
            </p>
            
            <button class="w-full py-2 rounded bg-green-600 hover:bg-green-500 text-white font-bold text-sm transition-colors flex items-center justify-center gap-2" v-if="selectedStock.zone === 'up'">
              <i class="ph-bold ph-hand-buying"></i> 加入買入清單
            </button>
            <button class="w-full py-2 rounded bg-red-900/50 hover:bg-red-900 text-red-400 border border-red-800 hover:text-red-200 font-bold text-sm transition-colors flex items-center justify-center gap-2" v-else-if="selectedStock.zone === 'down'">
              <i class="ph-bold ph-skull"></i> 確認清倉記錄
            </button>
            <button class="w-full py-2 rounded bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm transition-colors flex items-center justify-center gap-2" v-else>
              <i class="ph-bold ph-plus"></i> 加入驗證池跟蹤
            </button>

            <div class="pt-2 border-t border-slate-700">
              <label class="flex items-center gap-2 cursor-pointer group">
                <div class="w-4 h-4 border border-slate-600 rounded flex items-center justify-center group-hover:border-blue-500">
                  <i class="ph-bold ph-check text-[10px] text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity"></i>
                </div>
                <span class="text-xs text-slate-400">我已閱讀並理解報告風險提示</span>
              </label>
            </div>
          </div>

          <!-- Log -->
          <div class="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
            <h3 class="text-xs font-bold text-slate-400 mb-3 uppercase tracking-wide">風控日誌</h3>
            <div class="space-y-2 text-xs text-slate-500">
              <div class="flex gap-2"><span class="mono text-slate-600">05-17</span> <span>周線突破30W均線，量價共振</span></div>
              <div class="flex gap-2"><span class="mono text-slate-600">05-19</span> <span>縮量回踩10W均線，信號確認</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mono { 
  font-family: 'JetBrains Mono', monospace; 
}

/* Custom Scrollbar */
::-webkit-scrollbar { 
  width: 6px; 
  height: 6px; 
}
::-webkit-scrollbar-track { 
  background: #1e293b; 
}
::-webkit-scrollbar-thumb { 
  background: #475569; 
  border-radius: 4px; 
}
::-webkit-scrollbar-thumb:hover { 
  background: #64748b; 
}

/* Animations */
@keyframes pulse-ring {
  0% { transform: scale(0.8); opacity: 0.5; }
  100% { transform: scale(1.2); opacity: 0; }
}
.alert-ring { 
  position: absolute; 
  inset: -2px; 
  border-radius: 50%; 
  border: 2px solid #ef4444; 
  animation: pulse-ring 2s infinite; 
}

.tab-active { border-bottom: 2px solid #3b82f6; color: #60a5fa; }
.tab-inactive { border-bottom: 2px solid transparent; color: #94a3b8; transition: all 0.2s; }
.tab-inactive:hover { color: #cbd5e1; border-color: #475569; }

.stock-card { transition: transform 0.2s, box-shadow 0.2s; }
.stock-card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); border-color: #475569; }
</style>
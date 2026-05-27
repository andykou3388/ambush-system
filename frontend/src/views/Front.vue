<script setup>
import { ref, computed } from 'vue'

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

// Demo page data
const activeMenu = ref('dashboard')
const activeTab = ref('up')
const showNotifications = ref(false)
const unreadCount = ref(3)
const selectedStock = ref(null)
const chartInitialized = ref(false)

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

const notifications = [
  { id: 1, type: 'sell', time: '16:05', title: 'XX科技 離場信號', desc: '連續兩周收於10W均線下方，且放量，建議清倉。' },
  { id: 2, type: 'buy', time: '15:58', title: 'YY生醫 伏擊確認', desc: '縮量回踩10W均線，PE 6.5，符合買入條件。' },
  { id: 3, type: 'info', time: '12:00', title: '週報生成完畢', desc: '本週共篩選出 12 只交易區標的，已發送至郵箱。' }
]

const stocks = [
  // UP ZONE (Trading)
  { ticker: '603123', name: '翠微股份', price: '12.45', change: 1.2, zone: 'up', zoneLabel: '交易區', pe: 8.2, ma10: 11.8, volChange: -45, eps: '15%', mktCap: '32億', insider: '增持', topic: '新零售', lastUpdate: '05/19', 
    signals: [
      { type: 'success', text: '收於10W均線之上' },
      { type: 'success', text: '周量萎縮，浮籌清洗' },
      { type: 'success', text: 'EPS增長 > 10%' }
    ],
    rules: [
      { label: '神奇支撐', desc: '價格 12.45 > MA10 11.8，支撐有效', pass: true },
      { label: '縮量確認', desc: '周量低於突破周 50%', pass: true },
      { label: '估值安全', desc: 'PE 8.2 < 10，安全墊厚', pass: true },
      { label: '內部資金', desc: '高管近30日增持', pass: true }
    ],
    suggestion: '縮量回踩10周均線確認，可分批建倉，嚴守11.0止損。'
  },
  { ticker: '00258', name: '綠心集團', price: '14.20', change: 0.5, zone: 'up', zoneLabel: '交易區', pe: 9.1, ma10: 13.5, volChange: -60, eps: '22%', mktCap: '45億', insider: '無異動', topic: '環保', lastUpdate: '05/19',
    signals: [
      { type: 'success', text: '站上30W均線' },
      { type: 'success', text: '缺口未補' },
      { type: 'warning', text: '媒體關注度上升' }
    ],
    rules: [
      { label: '趨勢錨點', desc: 'MA30向上，角度45°', pass: true },
      { label: '量價配合', desc: '缺口後縮量', pass: true },
      { label: '風險點', desc: '留言板討論增多，需警惕', pass: false }
    ],
    suggestion: '形態標準，但注意媒體熱度，若放量滯漲需離場。'
  },
  // DOWN ZONE (Warning)
  { ticker: '88211', name: '瑞風數據', price: '18.50', change: -12.5, zone: 'down', zoneLabel: '避雷區', pe: 45, ma10: 22.0, volChange: 350, eps: '-10%', mktCap: '80億', insider: '減持', topic: 'AI概念', lastUpdate: '05/19',
    signals: [
      { type: 'warning', text: '跌破10W均線超15%' },
      { type: 'warning', text: '高位放巨量陰線' },
      { type: 'warning', text: '高管減持' }
    ],
    rules: [
      { label: '生命線', desc: '價格 < MA10 22.0，破位嚴重', pass: false },
      { label: '量價異常', desc: '周量激增，價格下跌', pass: false },
      { label: '基本面惡化', desc: '業績不及預期', pass: false }
    ],
    suggestion: '鐵律觸發：跌破均線+放量+內部減持。堅決清倉，不可補倉！'
  },
  // POTENTIAL ZONE
  { ticker: '300421', name: '力源信息', price: '6.80', change: 0.0, zone: 'pot', zoneLabel: '驗證區', pe: 8.5, ma10: 6.9, volChange: 5, eps: '8%', mktCap: '20億', insider: '回購', topic: '芯片分銷', lastUpdate: '05/19',
    signals: [
      { type: 'info', text: '窄幅震盪 > 6個月' },
      { type: 'info', text: '內部人士持續回購' },
      { type: 'info', text: '等待放量突破' }
    ],
    rules: [
      { label: '底部結構', desc: '長期橫盤，波幅收窄', pass: true },
      { label: '籌碼結構', desc: '流通盤小，易撬動', pass: true },
      { label: '啟動信號', desc: '尚未放量，需跟蹤', pass: false }
    ],
    suggestion: '列入觀察池。設置價格提醒：周量放大300%且站上MA30時通知。'
  }
]

const filteredStocks = computed(() => {
  return stocks.filter(s => s.zone === activeTab.value)
})

// Methods
function toggleNotifications() {
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) unreadCount.value = 0
}

function markAllRead() {
  notifications.splice(0, notifications.length)
}

function openStockDetail(stock) {
  selectedStock.value = stock
  chartInitialized.value = false
  // In a real app, we would initialize the chart here
}

function closeModal() {
  selectedStock.value = null
  chartInitialized.value = false
}
</script>

<template>
  <div class="h-screen flex overflow-hidden text-sm bg-slate-900">
    <!-- Sidebar -->
    <aside class="w-16 lg:w-64 flex-shrink-0 bg-trading-dark border-r border-trading-border flex flex-col transition-all duration-300">
      <div class="h-14 flex items-center justify-center lg:justify-start lg:px-4 border-b border-trading-border">
        <div class="flex items-center gap-2 font-bold text-lg tracking-wider text-trading-green">
          <i class="ph-bold ph-trend-up text-xl"></i>
          <span class="hidden lg:block">伏擊系統</span>
        </div>
      </div>

      <nav class="flex-1 py-4 space-y-1 px-2">
        <a v-for="item in menuItems" :key="item.id" href="#" 
           class="flex items-center gap-3 px-3 py-2 rounded-md text-slate-400 hover:text-white hover:bg-trading-panel transition-colors group"
           :class="{'bg-trading-panel text-white': activeMenu === item.id}">
          <i :class="['ph-bold', item.icon, 'text-lg', 'group-hover:text-blue-400']"></i>
          <span class="hidden lg:block text-xs font-medium">{{ item.label }}</span>
        </a>
      </nav>

      <div class="p-4 border-t border-trading-border">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs">
            交
          </div>
          <div class="hidden lg:block overflow-hidden">
            <p class="text-xs font-medium text-white truncate">波段交易員 01</p>
            <p class="text-[10px] text-slate-400">權限：全權限</p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col min-w-0 bg-slate-900">
      <!-- Header -->
      <header class="h-14 bg-trading-dark border-b border-trading-border flex items-center justify-between px-6 shadow-md z-10">
        <h1 class="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-trading-green animate-pulse"></span>
          實盤監控看板 <span class="text-xs text-slate-500 font-normal mono">2026-05-19 週五 16:00 UTC+8</span>
        </h1>

        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 px-3 py-1 rounded bg-slate-800 border border-trading-border text-xs">
            <span class="w-2 h-2 rounded-full bg-blue-500"></span>
            <span class="text-slate-400">數據源：</span>
            <span class="text-white font-mono">AKShare / Polygon</span>
          </div>

          <button @click="toggleNotifications" class="relative p-2 text-slate-400 hover:text-white transition-colors">
            <i class="ph-bold ph-bell text-lg"></i>
            <span v-if="unreadCount > 0" class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>
        </div>
      </header>

      <!-- Notification Panel (Slide Over) -->
      <div v-if="showNotifications" class="absolute top-14 right-0 w-80 bg-trading-dark border border-trading-border shadow-2xl z-50 rounded-bl-lg overflow-hidden transition-all">
        <div class="p-3 bg-slate-800 flex justify-between items-center border-b border-trading-border">
          <span class="font-semibold text-xs">即時信號通知</span>
          <button @click="markAllRead" class="text-[10px] text-blue-400 hover:text-blue-300">全部已讀</button>
        </div>
        <div class="h-64 overflow-y-auto divide-y divide-trading-border bg-slate-900/50">
          <div v-for="n in notifications" :key="n.id" class="p-3 hover:bg-slate-800 transition-colors group">
            <div class="flex justify-between items-start mb-1">
              <span class="text-[10px] mono text-slate-500">{{ n.time }}</span>
              <span :class="{'bg-red-900 text-red-300': n.type==='sell', 'bg-green-900 text-green-300': n.type==='buy', 'bg-blue-900 text-blue-300': n.type==='info'}" class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase">{{ n.type === 'sell' ? '⚠️ 賣出' : n.type === 'buy' ? '✅ 買點' : 'ℹ️ 週報' }}</span>
            </div>
            <p class="text-xs text-slate-300 mb-0.5">{{ n.title }}</p>
            <p class="text-[11px] text-slate-500">{{ n.desc }}</p>
          </div>
          <div v-if="notifications.length === 0" class="p-8 text-center text-slate-500 text-xs">暫無新通知</div>
        </div>
      </div>

      <!-- Scrollable Content -->
      <div class="flex-1 overflow-y-auto p-4 lg:p-6 scroll-smooth">
        
        <!-- Summary Cards -->
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div class="bg-trading-panel p-4 rounded-lg border border-trading-border">
            <div class="flex justify-between items-start">
              <div>
                <p class="text-slate-400 text-xs mb-1">交易區 (上升趨勢)</p>
                <h3 class="text-2xl font-bold text-trading-green mono">12 <span class="text-xs font-normal text-slate-500">只</span></h3>
              </div>
              <div class="p-2 bg-green-900/30 rounded text-trading-green"><i class="ph-bold ph-chart-line-up text-lg"></i></div>
            </div>
            <p class="text-[10px] text-slate-500 mt-2">符合「縮量回踩10周均線」條件</p>
          </div>
          <div class="bg-trading-panel p-4 rounded-lg border border-trading-border">
            <div class="flex justify-between items-start">
              <div>
                <p class="text-slate-400 text-xs mb-1">避雷區 (下跌警示)</p>
                <h3 class="text-2xl font-bold text-trading-red mono">5 <span class="text-xs font-normal text-slate-500">只</span></h3>
              </div>
              <div class="p-2 bg-red-900/30 rounded text-trading-red"><i class="ph-bold ph-shield-warning text-lg"></i></div>
            </div>
            <p class="text-[10px] text-slate-500 mt-2">跌破10周均線或放量滯漲</p>
          </div>
          <div class="bg-trading-panel p-4 rounded-lg border border-trading-border">
            <div class="flex justify-between items-start">
              <div>
                <p class="text-slate-400 text-xs mb-1">驗證區 (潛力跟蹤)</p>
                <h3 class="text-2xl font-bold text-trading-blue mono">28 <span class="text-xs font-normal text-slate-500">只</span></h3>
              </div>
              <div class="p-2 bg-blue-900/30 rounded text-trading-blue"><i class="ph-bold ph-eye text-lg"></i></div>
            </div>
            <p class="text-[10px] text-slate-500 mt-2">長期窄底，等待放量啟動</p>
          </div>
          <div class="bg-trading-panel p-4 rounded-lg border border-trading-border">
            <div class="flex justify-between items-start">
              <div>
                <p class="text-slate-400 text-xs mb-1">本週勝率預估</p>
                <h3 class="text-2xl font-bold text-trading-gold mono">78% <span class="text-xs font-normal text-slate-500">↑</span></h3>
              </div>
              <div class="p-2 bg-yellow-900/30 rounded text-trading-gold"><i class="ph-bold ph-target text-lg"></i></div>
            </div>
            <p class="text-[10px] text-slate-500 mt-2">基於歷史信號回測統計</p>
          </div>
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

        <!-- Stock List Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
          
          <!-- Stock Cards -->
          <div v-for="stock in filteredStocks" :key="stock.ticker" 
               class="stock-card bg-trading-panel rounded-lg border border-trading-border p-4 relative overflow-hidden cursor-pointer group"
               @click="openStockDetail(stock)">
              
            <!-- Zone Badge -->
            <div class="absolute top-0 right-0 px-2 py-0.5 text-[10px] font-bold text-white rounded-bl-lg z-10"
                 :class="{'bg-green-600': stock.zone==='up', 'bg-red-600': stock.zone==='down', 'bg-blue-600': stock.zone==='pot'}">
              {{ stock.zoneLabel }}
            </div>

            <!-- Header -->
            <div class="flex items-center justify-between mb-3">
              <div>
                <h3 class="text-base font-bold text-white mono">{{ stock.ticker }}</h3>
                <p class="text-[11px] text-slate-400 truncate max-w-[120px]">{{ stock.name }}</p>
              </div>
              <div class="text-right">
                <p class="text-lg font-bold text-white mono">{{ stock.price }}</p>
                <p class="text-xs mono flex items-center justify-end" :class="stock.change >= 0 ? 'text-green-400' : 'text-red-400'">
                  <i :class="['ph-bold', stock.change >= 0 ? 'ph-caret-up' : 'ph-caret-down', 'mr-0.5']"></i>
                  {{ Math.abs(stock.change) }}%
                </p>
              </div>
            </div>

            <!-- Key Metrics -->
            <div class="grid grid-cols-2 gap-y-2 gap-x-1 text-xs mb-3">
              <div class="flex justify-between px-2 py-1 rounded bg-slate-800/30">
                <span class="text-slate-500">PE (TTM)</span>
                <span class="mono font-bold text-slate-200">{{ stock.pe }}</span>
              </div>
              <div class="flex justify-between px-2 py-1 rounded bg-slate-800/30">
                <span class="text-slate-500">10W MA</span>
                <span class="mono font-bold text-slate-200">{{ stock.ma10 }}</span>
              </div>
              <div class="flex justify-between px-2 py-1 rounded bg-slate-800/30">
                <span class="text-slate-500">周量變幅</span>
                <span class="mono font-bold" :class="stock.volChange > 100 ? 'text-green-400' : 'text-slate-200'">{{ stock.volChange }}%</span>
              </div>
              <div class="flex justify-between px-2 py-1 rounded bg-slate-800/30">
                <span class="text-slate-500">EPS 增長</span>
                <span class="mono font-bold text-slate-200">{{ stock.eps }}</span>
              </div>
            </div>

            <!-- Signals / Checklist -->
            <div class="space-y-1.5 mb-3">
              <div v-for="(signal, idx) in stock.signals" :key="idx" class="flex items-center gap-1.5 text-xs">
                <i v-if="signal.type === 'success'" class="ph-bold ph-check-circle text-green-500"></i>
                <i v-else-if="signal.type === 'warning'" class="ph-bold ph-warning text-yellow-500"></i>
                <i v-else class="ph-bold ph-info text-blue-500"></i>
                <span class="text-slate-300">{{ signal.text }}</span>
              </div>
            </div>

            <!-- Action Hint -->
            <div class="pt-2 border-t border-slate-700 flex justify-between items-center">
              <span class="text-[10px] text-slate-500 mono">收盤更新: {{ stock.lastUpdate }}</span>
              <span class="text-[10px] font-bold text-blue-400 group-hover:text-blue-300 flex items-center gap-1">
                查看詳情 <i class="ph-bold ph-arrow-right"></i>
              </span>
            </div>
          </div>

        </div>

        <!-- Empty State -->
        <div v-if="filteredStocks.length === 0" class="text-center py-20">
          <div class="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-600">
            <i class="ph-bold ph-magnifying-glass text-2xl"></i>
          </div>
          <p class="text-slate-500">當前板塊無符合條件標的</p>
        </div>

      </div>
    </main>

    <!-- Stock Detail Modal -->
    <div v-if="selectedStock" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4" @click.self="closeModal">
      <div class="bg-slate-900 w-full max-w-4xl h-[90vh] rounded-xl border border-slate-700 shadow-2xl flex flex-col overflow-hidden animate-fade-in">
        
        <!-- Modal Header -->
        <div class="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800/50">
          <div class="flex items-center gap-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold text-white" :class="selectedStock.zone === 'up' ? 'bg-green-600' : selectedStock.zone === 'down' ? 'bg-red-600' : 'bg-blue-600'">
              {{ selectedStock.zoneLabel }}
            </span>
            <h2 class="text-xl font-bold mono text-white">{{ selectedStock.ticker }} <span class="text-sm text-slate-400 font-sans ml-2">{{ selectedStock.name }}</span></h2>
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
                <!-- Mock Chart Canvas -->
                <div class="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-10">
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
  </div>
    <router-view />
</template>

<style scoped>
/* Import the necessary styles from the demo */
@import url('https://cdn.jsdelivr.net/npm/@fontsource/noto-sans-tc@5.0.0/latin-400.css');
@import url('https://cdn.jsdelivr.net/npm/@fontsource/noto-sans-tc@5.0.0/latin-600.css');
@import url('https://cdn.jsdelivr.net/npm/@fontsource/jetbrains-mono@5.0.0/latin-400.css');

body { 
  font-family: 'Noto Sans TC', sans-serif; 
  background-color: #0f172a; 
  color: #e2e8f0; 
}

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

.tab-active { 
  border-bottom: 2px solid #3b82f6; 
  color: #60a5fa; 
}
.tab-inactive { 
  border-bottom: 2px solid transparent; 
  color: #94a3b8; 
  transition: all 0.2s; 
}
.tab-inactive:hover { 
  color: #cbd5e1; 
  border-color: #475569; 
}

.stock-card { 
  transition: transform 0.2s, box-shadow 0.2s; 
}
.stock-card:hover { 
  transform: translateY(-2px); 
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); 
  border-color: #475569; 
}

/* Trading colors */
.trading-dark { background-color: #0b1120; }
.trading-panel { background-color: #1e293b; }
.trading-border { border-color: #334155; }
.trading-red { color: #ef4444; }
.trading-red-bg { background-color: #450a0a; }
.trading-green { color: #10b981; }
.trading-green-bg { background-color: #064e3b; }
.trading-blue { color: #3b82f6; }
.trading-blue-bg { background-color: #1e3a8a; }
.trading-gold { color: #f59e0b; }
</style>
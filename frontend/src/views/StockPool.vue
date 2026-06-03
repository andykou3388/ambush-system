<template>
  <Layout>
    <!-- 頂部標題列 -->
    <div class="flex flex-col md:flex-row items-start md:items-center justify-between mb-6 gap-4">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 bg-gradient-to-br from-amber-400 to-amber-600 rounded-lg flex items-center justify-center text-2xl shadow-lg">
          📊
        </div>
        <div>
          <h1 class="text-2xl font-bold text-amber-400">股票池瀏覽器</h1>
          <p class="text-sm text-slate-400">跨市場基本面掃描 · 快速篩選超級強勢股</p>
        </div>
      </div>
      
      <!-- Watchlist 摘要卡 -->
      <div class="bg-slate-800/80 backdrop-blur border border-slate-700 rounded-lg px-5 py-3 flex items-center gap-4">
        <div class="text-center">
          <div class="text-xs text-slate-400">關注股票</div>
          <div class="flex items-baseline gap-1">
            <span class="text-2xl font-bold text-amber-400 font-mono">{{ watchlist.length }}</span>
            <span class="text-xs text-slate-500">/{{ stocks.length }}</span>
          </div>
        </div>
        <div class="h-10 w-px bg-slate-700"></div>
        <div class="text-center">
          <div class="text-xs text-slate-400">符合伏擊</div>
          <div class="flex items-baseline gap-1">
            <span class="text-2xl font-bold text-green-400 font-mono">{{ ambushCount }}</span>
            <span class="text-xs text-slate-500">隻</span>
          </div>
        </div>
        <div class="h-10 w-px bg-slate-700"></div>
        <div class="text-center">
          <div class="text-xs text-slate-400">虧損警示</div>
          <div class="flex items-baseline gap-1">
            <span class="text-2xl font-bold text-red-400 font-mono">{{ lossCount }}</span>
            <span class="text-xs text-slate-500">隻</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 篩選控制列 -->
    <div class="bg-slate-800/80 backdrop-blur border border-slate-700 rounded-lg p-4 mb-4">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        
        <!-- 搜索 -->
        <div>
          <label class="text-xs text-slate-400 mb-1 block flex items-center gap-1">
            <span>🔍</span> 搜索代碼
          </label>
          <input 
            v-model="searchQuery" 
            type="text"
            placeholder="例：2330, AAPL, 0700"
            class="w-full bg-slate-900 border border-slate-600 text-white px-3 py-2 rounded text-sm focus:outline-none focus:border-amber-400 transition"
          />
        </div>
        
        <!-- 市場 -->
        <div>
          <label class="text-xs text-slate-400 mb-1 block flex items-center gap-1">
            <span>🌐</span> 市場
          </label>
          <select 
            v-model="filterMarket"
            class="w-full bg-slate-900 border border-slate-600 text-white px-3 py-2 rounded text-sm focus:outline-none focus:border-amber-400"
          >
            <option value="ALL">全部市場</option>
            <option value="TW">🇹🇼 台股</option>
            <option value="US">🇺🇸 美股</option>
            <option value="HK">🇭🇰 港股</option>
          </select>
        </div>

        <!-- PE -->
        <div>
          <label class="text-xs text-slate-400 mb-1 block flex items-center gap-1">
            <span>📊</span> PE (TTM) 篩選
          </label>
          <select 
            v-model="filterPE"
            class="w-full bg-slate-900 border border-slate-600 text-white px-3 py-2 rounded text-sm focus:outline-none focus:border-amber-400"
          >
            <option value="ALL">不限</option>
            <option value="LOW">PE < 10 (低估值)</option>
            <option value="MID">PE 10-25 (合理)</option>
            <option value="HIGH">PE > 25 (高成長)</option>
            <option value="NEG">虧損 (PE 為空)</option>
          </select>
        </div>

        <!-- EPS -->
        <div>
          <label class="text-xs text-slate-400 mb-1 block flex items-center gap-1">
            <span>💰</span> EPS 狀態
          </label>
          <select 
            v-model="filterEPS"
            class="w-full bg-slate-900 border border-slate-600 text-white px-3 py-2 rounded text-sm focus:outline-none focus:border-amber-400"
          >
            <option value="ALL">不限</option>
            <option value="POS">EPS > 0 (盈利)</option>
            <option value="NEG">EPS < 0 (虧損)</option>
          </select>
        </div>
      </div>

      <!-- 排序 + 伏擊篩選 -->
      <div class="flex flex-wrap items-center gap-3 mt-4 pt-4 border-t border-slate-700">
        <span class="text-xs text-slate-400">排序：</span>
        <button 
          v-for="s in sortOptions" 
          :key="s.key"
          @click="setSort(s.key)"
          :class="[
            'px-3 py-1.5 text-xs rounded transition',
            currentSort === s.key 
              ? 'bg-amber-500 text-slate-900 font-bold shadow-lg' 
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          ]"
        >
          {{ s.label }}
        </button>
        
        <div class="flex-1"></div>
        
        <!-- 伏擊快捷篩選 -->
        <button 
          @click="ambushOnly = !ambushOnly"
          :class="[
            'px-3 py-1.5 text-xs rounded transition flex items-center gap-1',
            ambushOnly 
              ? 'bg-green-600 text-white font-bold' 
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          ]"
        >
          <span>✅</span> 只看「一分鐘伏擊」
        </button>
        
        <button 
          @click="clearFilters"
          class="text-xs text-slate-400 hover:text-amber-400 transition px-2"
        >
          🔄 清除
        </button>
      </div>
    </div>

    <!-- 統計列 -->
    <div class="flex items-center justify-between mb-3 px-2">
      <span class="text-sm text-slate-400">
        顯示 <span class="text-amber-400 font-bold font-mono">{{ filteredStocks.length }}</span> / {{ stocks.length }} 隻
      </span>
      <div class="text-xs text-slate-500">
        資料日期：{{ stocks[0] ? stocks[0].report_date : '-' }}
      </div>
    </div>

    <!-- 股票列表 -->
    <div class="space-y-2">
      <div 
        v-for="(stock, idx) in filteredStocks" 
        :key="stock.id"
        :class="[
          'bg-slate-800/80 backdrop-blur border rounded-lg p-4 transition-all duration-300 hover:shadow-lg slide-in',
          isInWatchlist(stock.code) 
            ? 'border-amber-500/60 bg-slate-800' 
            : checkAmbushRule(stock) 
              ? 'border-green-700/40 hover:border-green-500/60 ambush-glow'
              : 'border-slate-700 hover:border-slate-600'
        ]"
        :style="{ animationDelay: (idx % 20) * 30 + 'ms' }"
      >
        <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          
          <!-- 左側：股票資訊 -->
          <div class="flex items-center gap-3 lg:gap-4 flex-1 min-w-0">
            <!-- 市場徽章 -->
            <div :class="marketBadgeClass(stock.market)" class="text-xs font-bold px-2 py-1 rounded min-w-[44px] text-center">
              {{ stock.market }}
            </div>
            
            <!-- 代碼與日期 -->
            <div class="min-w-0 flex-1 lg:flex-none lg:w-40">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-mono font-bold text-white text-lg">{{ stock.code }}</span>
                <span v-if="isInWatchlist(stock.code)" class="text-amber-400 text-xs pulse-amber bg-amber-500/10 px-2 py-0.5 rounded">⭐ 已關注</span>
              </div>
              <div class="text-xs text-slate-500 mt-0.5">{{ stock.report_date }}</div>
            </div>

            <!-- 核心指標 -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-8 flex-1">
              <div class="text-center">
                <div class="text-xs text-slate-500 mb-1">PE (TTM)</div>
                <div :class="peColor(stock.pe_ttm)" class="font-mono font-bold text-lg">
                  {{ formatPE(stock.pe_ttm) }}
                </div>
              </div>
              <div class="text-center">
                <div class="text-xs text-slate-500 mb-1">EPS</div>
                <div :class="epsColor(stock.eps_ttm)" class="font-mono font-bold text-lg">
                  {{ formatEPS(stock.eps_ttm) }}
                </div>
              </div>
              <div class="text-center">
                <div class="text-xs text-slate-500 mb-1">流通股(億)</div>
                <div class="font-mono text-base text-slate-200">
                  {{ formatShares(stock.float_shares) }}
                </div>
              </div>
              <div class="text-center">
                <div class="text-xs text-slate-500 mb-1">負債率</div>
                <div :class="debtColor(stock.debt_ratio)" class="font-mono text-base">
                  {{ formatDebt(stock.debt_ratio) }}
                </div>
              </div>
            </div>
          </div>

          <!-- 右側：操作按鈕 -->
          <div class="flex items-center gap-2 lg:ml-4">
            <button 
              v-if="!isInWatchlist(stock.code)"
              @click="addToWatchlist(stock)"
              class="bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-4 py-2 rounded text-sm transition flex items-center gap-1 shadow hover:shadow-amber-500/30"
            >
              <span>⭐</span> 加入關注
            </button>
            <button 
              v-else
              @click="removeFromWatchlist(stock.code)"
              class="bg-red-600/80 hover:bg-red-600 text-white font-bold px-4 py-2 rounded text-sm transition flex items-center gap-1"
            >
              <span>✕</span> 移除
            </button>
            <button 
              @click="viewDetail(stock)"
              class="bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-2 rounded text-sm transition"
              title="查看詳情"
            >
              🔎
            </button>
          </div>
        </div>

        <!-- 伏擊規則提示 -->
        <div v-if="checkAmbushRule(stock)" class="mt-3 pt-3 border-t border-slate-700/50">
          <div class="flex items-center gap-2 text-xs flex-wrap">
            <span class="bg-green-900/50 text-green-400 border border-green-700/60 px-2 py-0.5 rounded">
              ✅ 符合「一分鐘伏擊」基本條件
            </span>
            <span class="text-slate-500">
              PE={{ formatPE(stock.pe_ttm) }} < 10 · 
              EPS={{ formatEPS(stock.eps_ttm) }} > 0
              <template v-if="stock.debt_ratio && stock.debt_ratio < 0.3"> · 低負債</template>
            </span>
          </div>
        </div>

        <!-- 虧損警示 -->
        <div v-else-if="stock.eps_ttm < 0" class="mt-3 pt-3 border-t border-slate-700/50">
          <div class="flex items-center gap-2 text-xs">
            <span class="bg-red-900/50 text-red-400 border border-red-700/60 px-2 py-0.5 rounded">
              ⚠️ 虧損中 (EPS 為負)
            </span>
          </div>
        </div>
      </div>

      <!-- 空狀態 -->
      <div v-if="filteredStocks.length === 0" class="text-center py-16 text-slate-500">
        <div class="text-6xl mb-4">🔍</div>
        <div class="text-lg mb-2">沒有符合條件的股票</div>
        <div class="text-sm">請嘗試調整篩選條件</div>
      </div>
    </div>

    <!-- Toast 提示 -->
    <transition name="toast">
      <div v-if="toast.show" :class="toastClass" class="fixed bottom-6 right-6 px-5 py-3 rounded-lg shadow-2xl z-50 flex items-center gap-2 border">
        <span>{{ toast.icon }}</span>
        <span>{{ toast.message }}</span>
      </div>
    </transition>

    <!-- 詳情彈窗 -->
    <transition name="modal">
      <div v-if="detailStock" class="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" @click.self="detailStock=null">
        <div class="bg-slate-800 border border-slate-700 rounded-lg max-w-lg w-full p-6 shadow-2xl">
          <div class="flex items-start justify-between mb-4">
            <div>
              <div class="flex items-center gap-2">
                <span :class="marketBadgeClass(detailStock.market)" class="text-xs font-bold px-2 py-1 rounded">{{ detailStock.market }}</span>
                <h3 class="text-xl font-bold text-white font-mono">{{ detailStock.code }}</h3>
              </div>
              <div class="text-sm text-slate-400 mt-1">報告日：{{ detailStock.report_date }}</div>
            </div>
            <button @click="detailStock=null" class="text-slate-400 hover:text-white text-2xl leading-none">&times;</button>
          </div>
          
          <div class="grid grid-cols-2 gap-4 mb-4">
            <div class="bg-slate-900/50 p-3 rounded">
              <div class="text-xs text-slate-500">PE (TTM)</div>
              <div :class="peColor(detailStock.pe_ttm)" class="font-mono font-bold text-xl mt-1">{{ formatPE(detailStock.pe_ttm) }}</div>
            </div>
            <div class="bg-slate-900/50 p-3 rounded">
              <div class="text-xs text-slate-500">EPS</div>
              <div :class="epsColor(detailStock.eps_ttm)" class="font-mono font-bold text-xl mt-1">{{ formatEPS(detailStock.eps_ttm) }}</div>
            </div>
            <div class="bg-slate-900/50 p-3 rounded">
              <div class="text-xs text-slate-500">流通股</div>
              <div class="font-mono text-xl mt-1">{{ formatShares(detailStock.float_shares) }} 億</div>
            </div>
            <div class="bg-slate-900/50 p-3 rounded">
              <div class="text-xs text-slate-500">負債率</div>
              <div :class="debtColor(detailStock.debt_ratio)" class="font-mono text-xl mt-1">{{ formatDebt(detailStock.debt_ratio) }}</div>
            </div>
          </div>

          <div v-if="checkAmbushRule(detailStock)" class="bg-green-900/30 border border-green-700/50 text-green-300 text-sm p-3 rounded mb-4">
            ✅ 此股票符合「一分鐘伏擊」基本面基本條件，可進入下一步技術面檢核。
          </div>

          <div class="flex gap-2">
            <button 
              v-if="!isInWatchlist(detailStock.code)"
              @click="addToWatchlist(detailStock); detailStock=null"
              class="flex-1 bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold py-2 rounded transition"
            >
              ⭐ 加入關注
            </button>
            <button 
              v-else
              @click="removeFromWatchlist(detailStock.code); detailStock=null"
              class="flex-1 bg-red-600 hover:bg-red-500 text-white font-bold py-2 rounded transition"
            >
              ✕ 移除關注
            </button>
          </div>
        </div>
      </div>
    </transition>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Layout from '@/components/Layout.vue'

// 股票數據
const stocks = ref([])
const loading = ref(false)
const error = ref(null)

// 從 API 獲取數據
async function fetchStocks() {
  loading.value = true
  error.value = null
  try {
    const response = await fetch('/api/v1/stock-fundamental/list')
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    stocks.value = await response.json()
  } catch (err) {
    error.value = err.message
    console.error('獲取股票數據失敗:', err)
  } finally {
    loading.value = false
  }
}

// 狀態
const watchlist = ref([])
const searchQuery = ref('')
const filterMarket = ref('ALL')
const filterPE = ref('ALL')
const filterEPS = ref('ALL')
const currentSort = ref('pe_asc')
const ambushOnly = ref(false)
const toast = ref({ show: false, message: '', type: 'success', icon: '✅' })
const detailStock = ref(null)

const sortOptions = [
  { key: 'pe_asc', label: 'PE 由低到高' },
  { key: 'pe_desc', label: 'PE 由高到低' },
  { key: 'eps_desc', label: 'EPS 最高' },
  { key: 'shares_desc', label: '流通股最大' },
  { key: 'code_asc', label: '代碼 A-Z' }
]

// 初始化
onMounted(() => {
  fetchStocks()
  const saved = localStorage.getItem('my_watchlist_v2')
  if (saved) {
    try { watchlist.value = JSON.parse(saved) } catch(e) {}
  }
})

// 計算屬性
const ambushCount = computed(() => stocks.value.filter(s => checkAmbushRule(s)).length)
const lossCount = computed(() => stocks.value.filter(s => s.eps_ttm !== null && s.eps_ttm < 0).length)

const filteredStocks = computed(() => {
  let result = [...stocks.value]

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toUpperCase()
    result = result.filter(s => s.code.toUpperCase().includes(q))
  }

  if (filterMarket.value !== 'ALL') {
    result = result.filter(s => s.market === filterMarket.value)
  }

  if (filterPE.value === 'LOW') result = result.filter(s => s.pe_ttm !== null && s.pe_ttm < 10)
  else if (filterPE.value === 'MID') result = result.filter(s => s.pe_ttm !== null && s.pe_ttm >= 10 && s.pe_ttm <= 25)
  else if (filterPE.value === 'HIGH') result = result.filter(s => s.pe_ttm !== null && s.pe_ttm > 25)
  else if (filterPE.value === 'NEG') result = result.filter(s => s.pe_ttm === null)

  if (filterEPS.value === 'POS') result = result.filter(s => s.eps_ttm > 0)
  else if (filterEPS.value === 'NEG') result = result.filter(s => s.eps_ttm < 0)

  if (ambushOnly.value) result = result.filter(s => checkAmbushRule(s))

  // 排序
  result.sort((a, b) => {
    switch(currentSort.value) {
      case 'pe_asc': return (a.pe_ttm ?? 9999) - (b.pe_ttm ?? 9999)
      case 'pe_desc': return (b.pe_ttm ?? 0) - (a.pe_ttm ?? 0)
      case 'eps_desc': return (b.eps_ttm ?? 0) - (a.eps_ttm ?? 0)
      case 'shares_desc': return (b.float_shares ?? 0) - (a.float_shares ?? 0)
      case 'code_asc': return a.code.localeCompare(b.code)
    }
    return 0
  })

  return result
})

// 方法
const isInWatchlist = (code) => watchlist.value.some(s => s.code === code)

const addToWatchlist = (stock) => {
  if (isInWatchlist(stock.code)) return
  watchlist.value.push({
    code: stock.code,
    market: stock.market,
    addedAt: new Date().toISOString(),
    pe_ttm: stock.pe_ttm
  })
  syncStorage()
  showToast(`已加入關注：${stock.code}`, 'success', '✅')
}

const removeFromWatchlist = (code) => {
  watchlist.value = watchlist.value.filter(s => s.code !== code)
  syncStorage()
  showToast(`已移除：${code}`, 'info', 'ℹ️')
}

const viewDetail = (stock) => {
  detailStock.value = stock
}

const syncStorage = () => {
  localStorage.setItem('my_watchlist_v2', JSON.stringify(watchlist.value))
}

const setSort = (key) => {
  currentSort.value = key
}

const clearFilters = () => {
  searchQuery.value = ''
  filterMarket.value = 'ALL'
  filterPE.value = 'ALL'
  filterEPS.value = 'ALL'
  currentSort.value = 'pe_asc'
  ambushOnly.value = false
}

const showToast = (message, type = 'success', icon = '✅') => {
  toast.value = { show: true, message, type, icon }
  setTimeout(() => { toast.value.show = false }, 2500)
}

// 伏擊規則
const checkAmbushRule = (stock) => {
  return stock.pe_ttm !== null && stock.pe_ttm < 10 && stock.eps_ttm > 0
}

// 格式化
const formatPE = (v) => v === null || v === undefined ? 'N/A' : Number(v).toFixed(2)
const formatEPS = (v) => v === null || v === undefined ? 'N/A' : Number(v).toFixed(2)
const formatShares = (v) => v ? (Number(v) / 1e8).toFixed(2) : 'N/A'
const formatDebt = (v) => v === null || v === undefined ? 'N/A' : (Number(v) * 100).toFixed(1) + '%'

// 顏色
const peColor = (v) => {
  if (v === null || v === undefined) return 'text-slate-500'
  if (v < 10) return 'text-green-400'
  if (v < 25) return 'text-amber-400'
  return 'text-red-400'
}
const epsColor = (v) => v > 0 ? 'text-green-400' : v < 0 ? 'text-red-400' : 'text-slate-500'
const debtColor = (v) => {
  if (v === null || v === undefined) return 'text-slate-500'
  if (v < 0.3) return 'text-green-400'
  if (v < 0.6) return 'text-amber-400'
  return 'text-red-400'
}
const marketBadgeClass = (m) => ({
  'TW': 'bg-red-900/50 text-red-400 border border-red-700/60',
  'US': 'bg-blue-900/50 text-blue-400 border border-blue-700/60',
  'HK': 'bg-amber-900/50 text-amber-400 border border-amber-700/60'
}[m])

const toastClass = computed(() => ({
  'success': 'bg-green-900/90 text-green-100 border-green-600',
  'info': 'bg-blue-900/90 text-blue-100 border-blue-600',
  'error': 'bg-red-900/90 text-red-100 border-red-600'
}[toast.value.type]))
</script>

<style scoped>
body {
  font-family: 'Noto Sans TC', sans-serif;
  background: #0f172a;
  color: #e2e8f0;
}
.font-mono { font-family: 'JetBrains Mono', monospace; }

/* 滾動條 */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #1e293b; }
::-webkit-scrollbar-thumb { background: #475569; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #64748b; }

/* 動畫 */
@keyframes slideIn {
  from { opacity: 0; transform: translateX(20px); }
  to { opacity: 1; transform: translateX(0); }
}
.slide-in { animation: slideIn 0.3s ease-out; }

@keyframes pulse-amber {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.4); }
  50% { box-shadow: 0 0 0 6px rgba(245, 158, 11, 0); }
}
.pulse-amber { animation: pulse-amber 2s infinite; }

.ambush-glow {
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.15);
}

.toast-enter-active, .toast-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateX(100px);
}
.modal-enter-active, .modal-leave-active {
  transition: all 0.25s ease;
}
.modal-enter-from, .modal-leave-to {
  opacity: 0;
}
</style>
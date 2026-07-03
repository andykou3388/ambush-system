<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import Layout from '@/components/Layout.vue'
import { useRamStopLossData } from '@/composables/useRamStopLossData'

// 使用止損數據 composable，設定 60 秒自動刷新間隔
const {
  positions,
  loading,
  error,
  trackingCount,
  monitoringCount,
  triggeredCount,
  totalPositions,
  activePositions,
  fetchPositions,
  activateStopLoss,
  getPositionStatus,
  checkStopLoss,
  checkAllStopLoss,
  closePosition,
  formatPrice,
  formatPct,
  getPriceClass,
  getDrawdownPercent,
  getStatusText,
  getStatusColorClass,
  clearAll,
  
  // 自動刷新相關
  isAutoRefreshing,
  lastRefreshTime,
  timeSinceLastRefresh,
  startAutoRefresh,
  stopAutoRefresh,
  toggleAutoRefresh,
  setupVisibilityHandling,
  cleanup
} = useRamStopLossData({
  interval: 60000 // 設定 60 秒刷新間隔
})

// 買入價輸入（用於追蹤中狀態）
const buyPriceInput = ref({})

/**
 * 啟用止損監控
 */
const handleActivateMonitoring = async (code) => {
  const buyPrice = buyPriceInput.value[code]
  
  if (!buyPrice || buyPrice <= 0) {
    alert('請輸入有效的買入價格')
    return
  }
  
  try {
    await activateStopLoss(code, buyPrice)
    // 清空輸入框
    buyPriceInput.value[code] = ''
    // 重新獲取數據
    await fetchPositions()
  } catch (err) {
    alert('啟動監控失敗：' + err.message)
  }
}

// 手動檢查止損
const handleCheckStopLoss = async (code) => {
  try {
    await checkStopLoss(code)
    await fetchPositions()
  } catch (err) {
    alert('檢查止損失敗：' + err.message)
  }
}

// 關閉止損部位
const handleClosePosition = async (code) => {
  if (!confirm(`確定要關閉 ${code} 的止損追蹤嗎？`)) {
    return
  }
  
  try {
    await closePosition(code)
  } catch (err) {
    alert('關閉部位失敗：' + err.message)
  }
}

// 批量檢查所有活躍部位
const handleCheckAll = async () => {
  if (!confirm('確定要檢查所有活躍部位的止損嗎？')) {
    return
  }
  
  try {
    await checkAllStopLoss()
  } catch (err) {
    alert('批量檢查失敗：' + err.message)
  }
}

// 統計數據對象（保持與原模板相容）
const stats = computed(() => ({
  tracking: trackingCount.value,
  monitoring: monitoringCount.value,
  triggered: triggeredCount.value
}))

// 狀態文字映射（保持與原模板相容）
const statusText = {
  tracking: '追蹤中',
  monitoring: '監控中',
  triggered: '已觸發'
}

// 狀態顏色（保持與原模板相容）
const statusColors = {
  tracking: 'bg-blue-600',
  monitoring: 'bg-green-600',
  triggered: 'bg-red-600'
}

// 計算屬性：處理 is_active 字段映射（API 返回的是 is_active，前端需要 isActive）
const getPositionData = (pos) => {
  return {
    ...pos,
    // API 返回 snake_case，這裡統一為 camelCase 供模板使用
    isActive: pos.is_active || false,
    isTriggered: pos.is_triggered || false
  }
}

// 初始化加載
onMounted(() => {
  fetchPositions()
  setupVisibilityHandling()
  startAutoRefresh() // 預設啟用自動刷新
})

onUnmounted(() => {
  cleanup()
})
</script>

<template>
  <Layout>
    <!-- 頁面標題區域 -->
    <div class="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
      <h1 class="text-xl font-bold text-white flex items-center gap-2">
        <i class="ph-bold ph-shield-check text-trading-green"></i>
        實時動態止損追蹤
      </h1>
      
      <!-- Header 控制區 -->
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-sm text-slate-400" v-if="timeSinceLastRefresh">
          最後更新：{{ timeSinceLastRefresh }}
        </span>
        
        <button 
          @click="toggleAutoRefresh" 
          :class="{ 'bg-green-600': isAutoRefreshing, 'bg-gray-700': !isAutoRefreshing }"
          class="px-3 py-1.5 text-sm rounded-lg transition-colors flex items-center gap-2 whitespace-nowrap"
          :title="isAutoRefreshing ? '停用自動刷新' : '啟用自動刷新'"
        >
          <i :class="['ph-bold', isAutoRefreshing ? 'ph-pause-circle' : 'ph-play-circle']"></i>
          {{ isAutoRefreshing ? '停用自動刷新' : '啟用自動刷新' }}
        </button>
        
        <button 
          @click="() => fetchPositions()" 
          :class="{ 'cursor-wait': loading }"
          class="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 text-white rounded-lg flex items-center gap-2 transition-colors whitespace-nowrap"
          :disabled="loading"
        >
          <i :class="['ph-bold', loading ? 'ph-spinner animate-spin' : 'ph-arrows-clockwise']"></i>
          {{ loading ? '載入中...' : '刷新' }}
        </button>
      </div>
    </div>

    <!-- 統計摘要區域 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <!-- 追蹤中 -->
      <div class="bg-slate-800/50 border border-trading-border rounded-lg p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs text-slate-400 mb-1">追蹤中</p>
            <p class="text-2xl font-bold text-blue-400">{{ stats.tracking }}</p>
            <p class="text-[10px] text-slate-500 mt-1">未設定買入價</p>
          </div>
          <div class="w-12 h-12 rounded-full bg-blue-600/20 flex items-center justify-center">
            <i class="ph-bold ph-magnifying-glass text-blue-400 text-xl"></i>
          </div>
        </div>
      </div>

      <!-- 監控中 -->
      <div class="bg-slate-800/50 border border-trading-border rounded-lg p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs text-slate-400 mb-1">監控中</p>
            <p class="text-2xl font-bold text-green-400">{{ stats.monitoring }}</p>
            <p class="text-[10px] text-slate-500 mt-1">正常運行中</p>
          </div>
          <div class="w-12 h-12 rounded-full bg-green-600/20 flex items-center justify-center">
            <i class="ph-bold ph-eye text-green-400 text-xl"></i>
          </div>
        </div>
      </div>

      <!-- 已觸發 -->
      <div class="bg-slate-800/50 border border-trading-border rounded-lg p-4">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs text-slate-400 mb-1">已觸發</p>
            <p class="text-2xl font-bold text-red-400">{{ stats.triggered }}</p>
            <p class="text-[10px] text-slate-500 mt-1">止損條件觸發</p>
          </div>
          <div class="w-12 h-12 rounded-full bg-red-600/20 flex items-center justify-center">
            <i class="ph-bold ph-warning-circle text-red-400 text-xl"></i>
          </div>
        </div>
      </div>
    </div>

    <!-- 資料載入狀態 -->
    <div v-if="loading && !isAutoRefreshing" class="flex flex-col items-center justify-center py-20">
      <i class="ph-bold ph-spinner animate-spin text-blue-500 text-4xl mb-4"></i>
      <p class="text-slate-400">正在載入止損追蹤數據...</p>
    </div>

    <!-- 錯誤提示 -->
    <div v-else-if="error" class="bg-red-900/20 border border-red-800 rounded-lg p-6 text-center">
      <i class="ph-bold ph-warning text-red-500 text-4xl mb-4"></i>
      <p class="text-red-400 mb-2">載入失敗</p>
      <p class="text-sm text-slate-400">{{ error }}</p>
        <button 
          @click="() => fetchPositions()" 
          class="mt-4 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg"
        >
          重試
        </button>
    </div>

    <!-- 空狀態 -->
    <div v-else-if="positions.length === 0" class="text-center py-20">
      <div class="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-600">
        <i class="ph-bold ph-shield-check text-2xl"></i>
      </div>
      <p class="text-slate-500">目前沒有追蹤的止損部位</p>
    </div>

    <!-- 部位列表 - 3 欄網格布局 (響應式) -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="pos in positions" :key="pos.code" 
        class="bg-slate-800/50 border border-trading-border rounded-lg overflow-hidden"
        :class="{ 'opacity-50': pos.isTriggered }"
      >
        <!-- 卡片頭部 -->
        <div class="p-4 border-b border-trading-border flex justify-between items-start">
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="text-lg font-bold text-white mono">{{ pos.code }}</h3>
        <!-- 狀態判斷邏輯修正：buyPrice=0 視為追蹤中 -->
        <span :class="['px-2 py-0.5 rounded text-[10px] font-bold text-white', statusColors[pos.isTriggered ? 'triggered' : (pos.buyPrice && pos.buyPrice > 0 ? 'monitoring' : 'tracking')]]">
          {{ statusText[pos.isTriggered ? 'triggered' : (pos.buyPrice && pos.buyPrice > 0 ? 'monitoring' : 'tracking')] }}
        </span>
            </div>
            <p class="text-sm text-slate-400">{{ pos.name || '股票名稱待定' }}</p>
          </div>
          <div class="text-right">
            <p class="text-xs text-slate-500">買入日期</p>
            <p class="text-sm text-slate-300 mono">{{ pos.buyDate }}</p>
          </div>
        </div>

        <!-- 內容區域 -->
        <div class="p-4">
          <!-- 追蹤中狀態 - 輸入買入價 -->
          <div v-if="!pos.buyPrice || pos.buyPrice === 0" class="flex items-center gap-4">
            <div class="flex-1">
              <label class="block text-xs text-slate-400 mb-1">輸入買入價格</label>
              <input 
                type="number" 
                v-model="buyPriceInput[pos.code]"
                step="0.01" 
                min="0"
                placeholder="輸入買入價"
                class="w-full px-3 py-2 bg-slate-900 border border-trading-border rounded-lg text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            <button 
              @click="handleActivateMonitoring(pos.code)"
              class="px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium flex items-center gap-2 whitespace-nowrap"
            >
              <i class="ph-bold ph-play"></i>
              啟用止損監控
            </button>
          </div>

          <!-- 監控中狀態 - 顯示詳細資訊 (有買入價且大於 0) -->
          <div v-else-if="!pos.isTriggered && pos.buyPrice && pos.buyPrice > 0 && pos.isActive" class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p class="text-xs text-slate-500 mb-1">買入價格</p>
              <p class="text-lg font-bold text-white mono">{{ formatPrice(pos.buyPrice) }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">當前價格</p>
              <p class="text-lg font-bold mono" :class="getPriceClass(pos.currentPrice, pos.buyPrice)">
                {{ formatPrice(pos.currentPrice) }}
                <i v-if="parseFloat(pos.currentPrice) >= parseFloat(pos.buyPrice)" class="ph-bold ph-arrow-up-circle ml-1 text-green-400"></i>
                <i v-else class="ph-bold ph-arrow-down-circle ml-1 text-red-400"></i>
              </p>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">最高價格</p>
              <p class="text-lg font-bold text-yellow-400 mono">{{ formatPrice(pos.highestPrice) }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-500 mb-1">止損價格</p>
              <p class="text-lg font-bold text-red-400 mono">{{ formatPrice(pos.stopLossPrice) }}</p>
            </div>
          </div>

          <!-- 回撤進度條 -->
          <div v-else-if="!pos.isTriggered && pos.buyPrice && pos.buyPrice > 0 && pos.isActive" class="mt-4 pt-4 border-t border-trading-border">
            <div class="flex justify-between items-center mb-2">
              <span class="text-xs text-slate-400">回撤幅度</span>
              <span :class="['text-xs font-bold', parseFloat(getDrawdownPercent(pos)) > 7 ? 'text-red-400' : 'text-yellow-400']">
                {{ getDrawdownPercent(pos) }}%
              </span>
            </div>
            <div class="w-full bg-slate-900 rounded-full h-2 overflow-hidden">
              <div 
                class="h-full rounded-full transition-all duration-300"
                :class="parseFloat(getDrawdownPercent(pos)) > 7 ? 'bg-red-600' : 'bg-yellow-600'"
                :style="{ width: Math.min(parseFloat(getDrawdownPercent(pos)), 100) + '%' }"
              ></div>
            </div>
            <p class="text-[10px] text-slate-500 mt-1">止損閾值：8% 從最高點回撤</p>
          </div>

          <!-- 已觸發狀態 -->
          <div v-else class="bg-red-900/20 border border-red-800 rounded-lg p-4">
            <div class="flex items-center gap-2 mb-2">
              <i class="ph-bold ph-warning-circle text-red-500 text-xl"></i>
              <span class="font-bold text-red-400">止損條件已觸發</span>
            </div>
            <p class="text-sm text-slate-400">
              買入價：{{ formatPrice(pos.buyPrice) }} | 
              觸發價：{{ formatPrice(pos.stopLossPrice) }} | 
              回撤：{{ formatPct(pos.drawdownPct) }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </Layout>
</template>

<style scoped>
.mono {
  font-family: 'JetBrains Mono', monospace;
}

/* 自動化刷新指示器動畫 */
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.live-indicator {
  animation: pulse-dot 2s ease-in-out infinite;
}
</style>
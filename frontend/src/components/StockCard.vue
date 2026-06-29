<template>
  <div 
    class="stock-card bg-trading-panel rounded-lg border border-trading-border p-4 relative overflow-hidden cursor-pointer group"
    @click="goToDetail"
  >
    <!-- Zone Badge -->
    <div class="absolute top-0 right-0 px-2 py-0.5 text-[10px] font-bold text-white rounded-bl-lg z-10"
         :class="zoneBadgeClass">
      {{ stock.zoneLabel }}
    </div>

    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <div>
        <h3 class="text-base font-bold text-white mono">{{ stock.symbol }}</h3>
        <p class="text-[11px] text-slate-400 truncate max-w-[120px]">{{ stock.name }}</p>
      </div>
      <div class="text-right">
        <p class="text-lg font-bold text-white mono">{{ stock.price.toFixed(2) }}</p>
        <p class="text-xs mono flex items-center justify-end" :class="changeClass">
          <i :class="['ph-bold', stock.changePct >= 0 ? 'ph-caret-up' : 'ph-caret-down', 'mr-0.5']"></i>
          {{ Math.abs(stock.changePct) }}%
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
        <span class="text-slate-500">信心度</span>
        <span class="mono font-bold" :class="confidenceClass">{{ (stock.confidence * 100).toFixed(0) }}%</span>
      </div>
      <div class="flex justify-between px-2 py-1 rounded bg-slate-800/30">
        <span class="text-slate-500">10W MA</span>
        <span class="mono font-bold text-slate-200">{{ stock.ma10.toFixed(1) }}</span>
      </div>
      <div class="flex justify-between px-2 py-1 rounded bg-slate-800/30">
        <span class="text-slate-500">周量變幅</span>
        <span class="mono font-bold" :class="stock.volChange > 100 ? 'text-green-400' : 'text-slate-200'">{{ (stock.volChange || 0).toFixed(2) }}%</span>
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

    <!-- Action Hint / Track Button -->
    <div class="pt-2 border-t border-slate-700 flex justify-between items-center">
      <span class="text-[10px] text-slate-500 mono">收盤更新：{{ stock.lastUpdate }}</span>
      
      <!-- 加入追蹤按鈕 -->
      <button 
        v-if="!isTracked"
        @click.stop="toggleTracking"
        class="text-[10px] font-bold text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors"
      >
        <i class="ph-bold ph-plus-circle"></i>
        加入追蹤
      </button>
      
      <!-- 追蹤中徽章 -->
      <span v-else class="text-[10px] font-bold text-green-400 flex items-center gap-1">
        <i class="ph-bold ph-check-circle"></i>
        追蹤中
      </span>
      
      <span class="text-[10px] font-bold text-blue-400 group-hover:text-blue-300 flex items-center gap-1 ml-2">
        查看詳情 <i class="ph-bold ph-arrow-right"></i>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  stock: { type: Object, required: true }
})

const emit = defineEmits(['open', 'tracking-change'])

const isTracked = ref(false)
const loading = ref(false)

// 本地維護已追蹤股票集合
const trackedSymbols = ref(new Set())

// 加載已追蹤的股票代碼
const loadTrackedSymbols = async () => {
  try {
    const response = await fetch('/api/ram-stop-loss/positions')
    if (response.ok) {
      const data = await response.json()
      data.forEach(pos => {
        trackedSymbols.value.add(pos.code)
      })
    }
  } catch (error) {
    console.error('獲取追蹤列表失敗:', error)
  }
}

// 切換追蹤狀態
const toggleTracking = async () => {
  if (loading.value) return
  
  loading.value = true
  
  try {
    // 檢查是否已追蹤
    if (trackedSymbols.value.has(props.stock.symbol)) {
      // 已追蹤，移除（可選擴展功能）
      // 這裡可以實現取消追蹤功能
      alert(`${props.stock.symbol} 已在追蹤清單中`)
    } else {
      // 新增追蹤
      const response = await fetch('/api/ram-stop-loss/positions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          code: props.stock.symbol,
          market: 'TW',
          buy_date: new Date().toISOString().split('T')[0],
          buy_price: null  // 先創建，之後再設定買入價
        })
      })
      
      if (response.ok) {
        trackedSymbols.value.add(props.stock.symbol)
        isTracked.value = true
        emit('tracking-change', { symbol: props.stock.symbol, tracked: true })
        alert(`✅ 已將 ${props.stock.symbol} 加入實時追蹤\n請前往「實時追蹤」頁面設定買入價格`)
      } else {
        throw new Error('加入追蹤失敗')
      }
    }
  } catch (error) {
    console.error('追蹤操作失敗:', error)
    alert('❌ 追蹤操作失敗，請稍後再試')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTrackedSymbols()
})

const zoneBadgeClass = computed(() => ({
  'bg-green-600': props.stock.zone === 'up',
  'bg-red-600': props.stock.zone === 'down',
  'bg-blue-600': props.stock.zone === 'pot'
}))

const changeClass = computed(() => ({
  'text-green-400': props.stock.changePct >= 0,
  'text-red-400': props.stock.changePct < 0
}))

const confidenceClass = computed(() => {
  const conf = props.stock.confidence || 0
  if (conf >= 0.8) return 'text-green-400'      // 高信心 (≥80%)
  if (conf >= 0.6) return 'text-blue-400'       // 中信心 (60%-79%)
  return 'text-yellow-400'                      // 低信心 (<60%)
})

function goToDetail() {
  emit('open', props.stock)
}
</script>

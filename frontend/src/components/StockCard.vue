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
        <span class="text-slate-500">10W MA</span>
        <span class="mono font-bold text-slate-200">{{ stock.ma10.toFixed(1) }}</span>
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
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  stock: { type: Object, required: true }
})

const router = useRouter()

const zoneBadgeClass = computed(() => ({
  'bg-green-600': props.stock.zone === 'up',
  'bg-red-600': props.stock.zone === 'down',
  'bg-blue-600': props.stock.zone === 'pot'
}))

const changeClass = computed(() => ({
  'text-green-400': props.stock.changePct >= 0,
  'text-red-400': props.stock.changePct < 0
}))

function goToDetail() {
  router.push(`/stocks/${props.stock.symbol}`)
}
</script>

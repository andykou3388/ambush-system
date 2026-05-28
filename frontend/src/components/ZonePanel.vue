<template>
  <div>
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-slate-200">{{ title }}</h3>
      <span class="text-xs text-slate-500">{{ stocks.length }} 檔</span>
    </div>
    <div v-if="stocks.length === 0" class="text-center py-8 text-slate-500 text-xs">
      暫無股票
    </div>
    <StockCardList v-else :stocks="stocks" />
  </div>
</template>

<script setup>
import StockCardList from './StockCardList.vue'

defineProps({
  zone: { type: String, required: true },
  title: { type: String, required: true },
  stocks: { type: Array, default: () => [] }
})
</script>

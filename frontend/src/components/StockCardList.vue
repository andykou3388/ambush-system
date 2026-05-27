<template>
  <div class="stock-card-list">
    <StockCard 
      v-for="stock in stocks" 
      :key="stock.symbol" 
      :stock="stock" 
    />
    <div v-if="stocks.length === 0" class="empty-state">
      暫無股票數據
    </div>
  </div>
</template>

<script setup>
import StockCard from './StockCard.vue'

defineProps({
  stocks: { type: Array, default: () => [] }
})
</script>

<style scoped>
.stock-card-list {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4;
}

.empty-state {
  @apply col-span-full text-center py-8 text-gray-500;
}
</style>
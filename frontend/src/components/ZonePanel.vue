<template>
  <div class="zone-panel bg-white rounded-lg shadow">
    <div class="zone-header p-4 border-b">
      <div class="flex justify-between items-center">
        <h2 class="text-lg font-semibold">{{ title }}</h2>
        <span class="stock-count text-sm text-gray-500">{{ stocks.length }} 檔</span>
      </div>
    </div>
    <div class="stock-list p-4">
      <!-- 使用新的股票卡片組件 -->
      <div v-if="stocks.length === 0" class="text-center py-8 text-gray-500">
        暫無股票
      </div>
      <StockCardList v-else :stocks="stocks" />
    </div>
  </div>
</template>

<script setup>
import StockCardList from './StockCardList.vue'

defineProps({
  zone: {
    type: String,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  stocks: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.zone-panel {
  border-top: 4px solid;
}

.zone-panel.zone-buy {
  border-top-color: #22c55e;
}

.zone-panel.zone-hold {
  border-top-color: #eab308;
}

.zone-panel.zone-sell {
  border-top-color: #ef4444;
}
</style>
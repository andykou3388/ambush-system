<template>
  <div class="dashboard min-h-screen bg-gray-50 p-4 md:p-6">
    <!-- 頂部統計卡片 -->
    <div class="stats-grid grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatCard title="總標的數" :value="stats.total" />
      <StatCard title="買入區" :value="stats.buy" color="buy-zone" />
      <StatCard title="持有區" :value="stats.hold" color="hold-zone" />
      <StatCard title="賣出區" :value="stats.sell" color="sell-zone" />
    </div>

    <!-- 三區佈局 -->
    <div class="zones-grid grid grid-cols-1 md:grid-cols-3 gap-4">
      <ZonePanel zone="buy" title="買入區" :stocks="buyStocks" />
      <ZonePanel zone="hold" title="持有區" :stocks="holdStocks" />
      <ZonePanel zone="sell" title="賣出區" :stocks="sellStocks" />
    </div>
  </div>
</template>

<script setup>
import StatCard from '../components/StatCard.vue'
import ZonePanel from '../components/ZonePanel.vue'
import { useApiData } from '../composables/useApiData'

// 使用API數據
const { stats, buyStocks, holdStocks, sellStocks, loading, error } = useApiData()
</script>

<style scoped>
.dashboard {
  padding-top: 1rem;
}

.stats-grid {
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}

.zones-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

@media (max-width: 768px) {
  .zones-grid {
    grid-template-columns: 1fr;
  }
}
</style>
<template>
  <div 
    class="stock-card" 
    :class="[`zone-${stock.zone}`, { 'is-hovered': isHovered }]"
    @click="goToDetail"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
  >
    <!-- 頂部：股票代碼與名稱 -->
    <div class="card-header">
      <div class="stock-symbol">{{ stock.symbol }}</div>
      <div class="stock-name">{{ stock.name }}</div>
    </div>

    <!-- 中間：價格與漲跌幅 -->
    <div class="card-price">
      <span class="price">${{ stock.price.toFixed(2) }}</span>
      <span class="change" :class="changeClass">
        {{ stock.changePct > 0 ? '+' : '' }}{{ stock.changePct.toFixed(2) }}%
      </span>
    </div>

    <!-- 底部：技術指標摘要 -->
    <div class="card-indicators">
      <div class="indicator">
        <span class="label">MA10</span>
        <span class="value">${{ stock.ma10.toFixed(2) }}</span>
      </div>
      <div class="indicator">
        <span class="label">MA30</span>
        <span class="value">${{ stock.ma30.toFixed(2) }}</span>
      </div>
      <div class="indicator">
        <span class="label">評分</span>
        <span class="value">{{ stock.score.toFixed(1) }}</span>
      </div>
    </div>

    <!-- 區域標籤 -->
    <div class="zone-badge" :class="`badge-${stock.zone}`">
      {{ zoneLabels[stock.zone] }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  stock: { type: Object, required: true }
})

const router = useRouter()
const isHovered = ref(false)

const zoneLabels = { buy: '買入區', hold: '持有區', sell: '賣出區' }

const changeClass = computed(() => ({
  'text-green-500': props.stock.changePct >= 0,
  'text-red-500': props.stock.changePct < 0
}))

function goToDetail() {
  router.push(`/stocks/${props.stock.symbol}`)
}
</script>

<style scoped>
.stock-card {
  @apply bg-white rounded-lg shadow-sm p-4 cursor-pointer
         border-l-4 transition-all duration-200;
}
.stock-card.zone-buy { @apply border-l-green-500; }
.stock-card.zone-hold { @apply border-l-yellow-500; }
.stock-card.zone-sell { @apply border-l-red-500; }
.stock-card.is-hovered { @apply shadow-md transform -translate-y-0.5; }
</style>

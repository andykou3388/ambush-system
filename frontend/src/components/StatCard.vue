<template>
  <div class="stat-card bg-white rounded-lg shadow p-4 transition-all duration-200 hover:shadow-md">
    <div class="stat-label text-gray-500 text-sm font-medium">{{ title }}</div>
    <div class="stat-value text-2xl font-bold mt-1">{{ value }}</div>
    <div v-if="change" class="stat-change mt-2 text-sm" :class="changeClass">
      <span v-if="change > 0">↑</span>
      <span v-else-if="change < 0">↓</span>
      <span>{{ Math.abs(change) }}%</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: Number,
    required: true
  },
  color: {
    type: String,
    default: 'default'
  },
  change: {
    type: Number,
    default: null
  }
})

const changeClass = computed(() => {
  if (props.change === null) return ''
  return props.change >= 0 ? 'text-green-600' : 'text-red-600'
})
</script>

<style scoped>
.stat-card {
  border-left: 4px solid;
}

.stat-card.buy-zone {
  border-left-color: #22c55e;
}

.stat-card.hold-zone {
  border-left-color: #eab308;
}

.stat-card.sell-zone {
  border-left-color: #ef4444;
}
</style>
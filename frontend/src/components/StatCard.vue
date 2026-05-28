<template>
  <div class="bg-trading-panel p-4 rounded-lg border border-trading-border">
    <div class="flex justify-between items-start">
      <div>
        <p class="text-slate-400 text-xs mb-1">{{ title }}</p>
        <h3 class="text-2xl font-bold mono" :class="valueColor">
          {{ displayValue }} <span class="text-xs font-normal text-slate-500">{{ unit }}</span>
        </h3>
      </div>
      <div class="p-2 rounded" :class="iconBgClass">
        <i :class="['ph-bold', icon, 'text-lg', iconColorClass]"></i>
      </div>
    </div>
    <p class="text-[10px] text-slate-500 mt-2">{{ description }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  value: { type: Number, required: true },
  unit: { type: String, default: '' },
  color: { type: String, default: 'default' },
  change: { type: Number, default: null },
  description: { type: String, default: '' },
  icon: { type: String, default: 'ph-chart-line-up' }
})

const displayValue = computed(() => {
  if (props.color === 'gold') return `${props.value}%`
  return props.value
})

const valueColor = computed(() => {
  const colors = {
    green: 'text-trading-green',
    red: 'text-trading-red',
    blue: 'text-trading-blue',
    gold: 'text-trading-gold'
  }
  return colors[props.color] || 'text-white'
})

const iconBgClass = computed(() => {
  const bg = {
    green: 'bg-green-900/30',
    red: 'bg-red-900/30',
    blue: 'bg-blue-900/30',
    gold: 'bg-yellow-900/30'
  }
  return bg[props.color] || 'bg-slate-800/30'
})

const iconColorClass = computed(() => {
  const colors = {
    green: 'text-trading-green',
    red: 'text-trading-red',
    blue: 'text-trading-blue',
    gold: 'text-trading-gold'
  }
  return colors[props.color] || 'text-slate-400'
})

const icon = computed(() => {
  const icons = {
    green: 'ph-chart-line-up',
    red: 'ph-shield-warning',
    blue: 'ph-eye',
    gold: 'ph-target'
  }
  return icons[props.color] || 'ph-chart-line-up'
})
</script>

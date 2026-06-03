<template>
  <div class="h-screen flex overflow-hidden text-sm bg-slate-900">
    <!-- Sidebar -->
    <aside class="w-16 lg:w-64 flex-shrink-0 bg-trading-dark border-r border-trading-border flex flex-col transition-all duration-300">
      <div class="h-14 flex items-center justify-center lg:justify-start lg:px-4 border-b border-trading-border">
        <div class="flex items-center gap-2 font-bold text-lg tracking-wider text-trading-green">
          <i class="ph-bold ph-trend-up text-xl"></i>
          <span class="hidden lg:block">伏擊系統</span>
        </div>
      </div>

      <nav class="flex-1 py-4 space-y-1 px-2">
        <router-link v-for="item in menuItems" :key="item.id" 
           :to="item.id === 'dashboard' ? '/' : `/${item.id}`"
           class="flex items-center gap-3 px-3 py-2 rounded-md text-slate-400 hover:text-white hover:bg-trading-panel transition-colors group"
           :class="{'bg-trading-panel text-white': activeMenu === item.id}">
          <i :class="['ph-bold', item.icon, 'text-lg', 'group-hover:text-blue-400']"></i>
          <span class="hidden lg:block text-xs font-medium">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="p-4 border-t border-trading-border">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs">
            交
          </div>
          <div class="hidden lg:block overflow-hidden">
            <p class="text-xs font-medium text-white truncate">波段交易員 01</p>
            <p class="text-[10px] text-slate-400">權限：全權限</p>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col min-w-0 bg-slate-900">
      <!-- Header -->
      <header class="h-14 bg-trading-dark border-b border-trading-border flex items-center justify-between px-6 shadow-md z-10">
        <h1 class="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <span class="w-2 h-2 rounded-full bg-trading-green animate-pulse"></span>
          <span v-if="$route.path === '/'">實盤監控看板</span>
          <span v-else-if="$route.path === '/stockpool'">股票池瀏覽器</span>
          <span v-else>伏擊系統</span>
          <span class="text-xs text-slate-500 font-normal mono">2026-05-19 週五 16:00 UTC+8</span>
        </h1>

        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 px-3 py-1 rounded bg-slate-800 border border-trading-border text-xs">
            <span class="w-2 h-2 rounded-full bg-blue-500"></span>
            <span class="text-slate-400">數據源：</span>
            <span class="text-white font-mono">AKShare / Polygon</span>
          </div>

          <button @click="toggleNotifications" class="relative p-2 text-slate-400 hover:text-white transition-colors">
            <i class="ph-bold ph-bell text-lg"></i>
            <span v-if="unreadCount > 0" class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>
        </div>
      </header>

      <!-- Notification Panel (Slide Over) -->
      <div v-if="showNotifications" class="absolute top-14 right-0 w-80 bg-trading-dark border border-trading-border shadow-2xl z-50 rounded-bl-lg overflow-hidden transition-all">
        <div class="p-3 bg-slate-800 flex justify-between items-center border-b border-trading-border">
          <span class="font-semibold text-xs">即時信號通知</span>
          <button @click="markAllRead" class="text-[10px] text-blue-400 hover:text-blue-300">全部已讀</button>
        </div>
        <div class="h-64 overflow-y-auto divide-y divide-trading-border bg-slate-900/50">
          <div v-for="n in notifications" :key="n.id" class="p-3 hover:bg-slate-800 transition-colors group">
            <div class="flex justify-between items-start mb-1">
              <span class="text-[10px] mono text-slate-500">{{ n.time }}</span>
              <span :class="{'bg-red-900 text-red-300': n.type==='sell', 'bg-green-900 text-green-300': n.type==='buy', 'bg-blue-900 text-blue-300': n.type==='info'}" class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase">{{ n.type === 'sell' ? '⚠️ 賣出' : n.type === 'buy' ? '✅ 買點' : 'ℹ️ 週報' }}</span>
            </div>
            <p class="text-xs text-slate-300 mb-0.5">{{ n.title }}</p>
            <p class="text-[11px] text-slate-500">{{ n.desc }}</p>
          </div>
          <div v-if="notifications.length === 0" class="p-8 text-center text-slate-500 text-xs">暫無新通知</div>
        </div>
      </div>

      <!-- Scrollable Content -->
      <div class="flex-1 overflow-y-auto p-4 lg:p-6 scroll-smooth">
        <slot></slot>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// Navigation items
const menuItems = [
  { id: 'dashboard', label: '實盤看板', icon: 'ph-squares-four' },
  { id: 'stockpool', label: '篩選器', icon: 'ph-funnel' },
  { id: 'screen', label: '智能篩選', icon: 'ph-funnel' },
  { id: 'alerts', label: '信號預警', icon: 'ph-bell-ringing' },
  { id: 'logs', label: '風控日誌', icon: 'ph-scroll' },
  { id: 'settings', label: '系統設置', icon: 'ph-gear' }
]

// Notification state
const showNotifications = ref(false)
const unreadCount = ref(3)
const notifications = ref([
  { id: 1, type: 'sell', time: '16:05', title: 'XX科技 離場信號', desc: '連續兩周收於10W均線下方，且放量，建議清倉。' },
  { id: 2, type: 'buy', time: '15:58', title: 'YY生醫 伏擊確認', desc: '縮量回踩10W均線，PE 6.5，符合買入條件。' },
  { id: 3, type: 'info', time: '12:00', title: '週報生成完畢', desc: '本週共篩選出 12 只交易區標的，已發送至郵箱。' }
])

// Methods
const toggleNotifications = () => {
  showNotifications.value = !showNotifications.value
  if (showNotifications.value) unreadCount.value = 0
}

const markAllRead = () => {
  notifications.value = []
}

// Active menu state (for demonstration purposes)
const activeMenu = ref('dashboard')
</script>

<style scoped>
.mono { 
  font-family: 'JetBrains Mono', monospace; 
}

/* Custom Scrollbar */
::-webkit-scrollbar { 
  width: 6px; 
  height: 6px; 
}
::-webkit-scrollbar-track { 
  background: #1e293b; 
}
::-webkit-scrollbar-thumb { 
  background: #475569; 
  border-radius: 4px; 
}
::-webkit-scrollbar-thumb:hover { 
  background: #64748b; 
}

/* Animations */
@keyframes pulse-ring {
  0% { transform: scale(0.8); opacity: 0.5; }
  100% { transform: scale(1.2); opacity: 0; }
}
.alert-ring { 
  position: absolute; 
  inset: -2px; 
  border-radius: 50%; 
  border: 2px solid #ef4444; 
  animation: pulse-ring 2s infinite; 
}

.tab-active { border-bottom: 2px solid #3b82f6; color: #60a5fa; }
.tab-inactive { border-bottom: 2px solid transparent; color: #94a3b8; transition: all 0.2s; }
.tab-inactive:hover { color: #cbd5e1; border-color: #475569; }

.stock-card { transition: transform 0.2s, box-shadow 0.2s; }
.stock-card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); border-color: #475569; }
</style>
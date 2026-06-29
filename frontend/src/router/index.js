import { createRouter, createWebHistory } from 'vue-router'
import Front from '../views/Front.vue'
import Dashboard from '../views/Dashboard.vue'
import CardDemo from '../views/CardDemo.vue'
import StockDetail from '../views/StockDetail.vue'
import StockPool from '../views/StockPool.vue'

const routes = [
  {
    path: '/',
    name: 'Front',
    component: Front
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,

  },
  {
    path: '/card-demo',
    name: 'CardDemo',
    component: CardDemo
  },
  {
    path: '/stocks/:symbol',
    name: 'StockDetail',
    component: StockDetail
  },
  {
    path: '/stockpool',
    name: 'StockPool',
    component: StockPool
  },
  {
    path: '/ram-stop-loss',
    name: 'RamStopLossTracker',
    component: () => import('@/views/RamStopLossTracker.vue'),
    meta: { 
      requiresAuth: true,
      title: '實時動態止損追蹤'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
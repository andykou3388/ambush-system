import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import CardDemo from '../views/CardDemo.vue'
import StockDetail from '../views/StockDetail.vue'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: Dashboard
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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
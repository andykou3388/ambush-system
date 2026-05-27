import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import CardDemo from '../views/CardDemo.vue'

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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
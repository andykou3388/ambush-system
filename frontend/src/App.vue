<script setup>
import { ref } from 'vue'

// API 連接測試狀態
const apiStatus = ref('未測試')
const apiResponse = ref(null)
const isLoading = ref(false)

// 測試 API 連接
async function testApiConnection() {
  isLoading.value = true
  apiStatus.value = '測試中...'
  apiResponse.value = null
  
  try {
    const response = await fetch('/api/v1/stocks/2330.TW')
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    apiStatus.value = '連接成功'
    apiResponse.value = data
  } catch (error) {
    apiStatus.value = '連接失敗'
    apiResponse.value = { error: error.message }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center">
          <h1 class="text-3xl font-bold text-gray-900">Ambush System</h1>
          <nav class="flex space-x-4">
            <router-link to="/" class="text-blue-600 hover:text-blue-800">看板</router-link>
            <router-link to="/card-demo" class="text-blue-600 hover:text-blue-800">卡片展示</router-link>
          </nav>
        </div>
      </div>
    </header>
    
    <main>
      <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div class="px-4 py-6 sm:px-0">
          <!-- API 連接測試區塊 -->
          <div class="bg-white shadow rounded-lg p-6 mb-6">
            <h2 class="text-xl font-semibold mb-4">API 連接測試</h2>
            <div class="flex items-center space-x-4 mb-4">
              <button 
                @click="testApiConnection"
                :disabled="isLoading"
                class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {{ isLoading ? '測試中...' : '測試 API 連接' }}
              </button>
              <span class="px-3 py-1 rounded-full text-sm font-medium"
                :class="apiStatus === '連接成功' ? 'bg-green-100 text-green-800' : 
                        apiStatus === '連接失敗' ? 'bg-red-100 text-red-800' : 
                        'bg-gray-100 text-gray-800'">
                {{ apiStatus }}
              </span>
            </div>
            
            <div v-if="apiResponse" class="mt-4">
              <h3 class="font-medium mb-2">API 回應:</h3>
              <pre class="bg-gray-100 p-4 rounded overflow-auto text-sm">{{ JSON.stringify(apiResponse, null, 2) }}</pre>
            </div>
          </div>
          
          <!-- 路由視圖 -->
          <router-view />
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
</style>
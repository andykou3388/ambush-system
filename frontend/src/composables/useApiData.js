// API數據獲取組合式函數
import { ref, onMounted } from 'vue'

export function useApiData() {
  // 定義響應式數據
  const stats = ref({
    total: 0,
    buy: 0,
    hold: 0,
    sell: 0
  })
  
  const buyStocks = ref([])
  const holdStocks = ref([])
  const sellStocks = ref([])
  
  const loading = ref(false)
  const error = ref(null)
  
  // 從API獲取數據
  const fetchData = async () => {
    loading.value = true
    error.value = null
    
    try {
      // 這裡使用相對路徑，實際部署時會根據API_BASE_URL進行調整
      const response = await fetch('/api/v1/dashboard/stats')
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      
      // 設置統計數據
      stats.value = {
        total: data.total || 0,
        buy: data.buy || 0,
        hold: data.hold || 0,
        sell: data.sell || 0
      }
      
      // 設置股票數據
      buyStocks.value = data.buy_stocks || []
      holdStocks.value = data.hold_stocks || []
      sellStocks.value = data.sell_stocks || []
      
    } catch (err) {
      error.value = err.message
      console.error('獲取數據失敗:', err)
      
      // 如果API調用失敗，使用預設數據
      stats.value = {
        total: 150,
        buy: 45,
        hold: 70,
        sell: 35
      }
      
      buyStocks.value = [
        { symbol: 'AAPL', name: 'Apple Inc.', price: 175.50, change: 2.3 },
        { symbol: 'MSFT', name: 'Microsoft', price: 330.20, change: 1.8 },
        { symbol: 'GOOGL', name: 'Alphabet Inc.', price: 138.21, change: -0.5 }
      ]
      
      holdStocks.value = [
        { symbol: 'TSLA', name: 'Tesla Inc.', price: 248.50, change: 3.2 },
        { symbol: 'AMZN', name: 'Amazon.com Inc.', price: 145.80, change: -1.2 },
        { symbol: 'NVDA', name: 'NVIDIA Corporation', price: 450.75, change: 5.7 }
      ]
      
      sellStocks.value = [
        { symbol: 'META', name: 'Meta Platforms Inc.', price: 325.60, change: -2.1 },
        { symbol: 'JPM', name: 'JPMorgan Chase & Co.', price: 158.30, change: 0.8 },
        { symbol: 'V', name: 'Visa Inc.', price: 235.40, change: 1.5 }
      ]
    } finally {
      loading.value = false
    }
  }
  
  // 組件掛載時獲取數據
  onMounted(() => {
    fetchData()
  })
  
  // 返回數據和方法
  return {
    stats,
    buyStocks,
    holdStocks,
    sellStocks,
    loading,
    error,
    refresh: fetchData // 提供手動刷新數據的方法
  }
}
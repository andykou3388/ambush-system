/**
 * useRamStopLossData - 止損追蹤資料組合式函數
 * 
 * 封裝止損追蹤相關的 API 調用邏輯，提供給其他組件複用
 * @author Frontend Developer
 * @task RAM-05, RAM-06
 */
import { ref, computed } from 'vue'

/**
 * 止損追蹤資料 composable
 * @param {Object} options - 配置選項
 * @param {number} options.interval - 自動刷新間隔（毫秒），預設 60000
 * @returns {Object} 止損追蹤相關的状态、方法和計算屬性
 */
export function useRamStopLossData(options = {}) {
  // ========================================
  // 自動刷新配置
  // ========================================
  
  const AUTO_REFRESH_INTERVAL = options.interval || 60000 // 預設 60 秒
  
  let refreshIntervalId = null
  let isAutoRefreshing = ref(false)
  let lastRefreshTime = ref(null)
  
  // ========================================
  // 狀態定義
  // ========================================
  
  /** 所有止損部位列表 */
  const positions = ref([])
  
  /** 載入狀態 */
  const loading = ref(false)
  
  /** 錯誤信息 */
  const error = ref(null)
  
  /** API 基礎路徑 */
  const API_BASE = '/api/ram-stop-loss'

  // ========================================
  // 計算屬性 - 統計數據
  // ========================================
  
  /** 追蹤中的股票數量（未設定買入價） */
  const trackingCount = computed(() => {
    return positions.value.filter(p => !p.buyPrice).length
  })
  
  /** 監控中的股票數量（已設定買入價且正常運行中） */
  const monitoringCount = computed(() => {
    return positions.value.filter(p => 
      p.buyPrice && !p.isTriggered && p.isActive
    ).length
  })
  
  /** 已觸發的股票數量 */
  const triggeredCount = computed(() => {
    return positions.value.filter(p => p.isTriggered).length
  })
  
  /** 總部位數量 */
  const totalPositions = computed(() => {
    return positions.value.length
  })
  
  /** 活躍部位數量 */
  const activePositions = computed(() => {
    return positions.value.filter(p => p.isActive).length
  })
  
  /** 計算距離上次刷新的時間 */
  const timeSinceLastRefresh = computed(() => {
    if (!lastRefreshTime.value) return '尚未刷新'
    
    const seconds = Math.floor((Date.now() - lastRefreshTime.value.getTime()) / 1000)
    
    if (seconds < 60) return `${seconds}秒前`
    const minutes = Math.floor(seconds / 60)
    return `${minutes}分鐘前`
  })

  // ========================================
  // 核心方法 - API 調用
  // ========================================
  
  /**
   * 獲取所有止損追蹤部位狀態
   * @param {boolean} activeOnly - 僅返回活躍部位
   * @returns {Promise<Array>} 部位列表
   */
  const fetchPositions = async (activeOnly = true) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch(
        `${API_BASE}/positions?active_only=${activeOnly}`
      )
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      positions.value = data || []
      
      // 更新最後刷新時間（手動刷新才記錄）
      if (!isAutoRefreshing.value) {
        lastRefreshTime.value = new Date()
      }
      
      return positions.value
    } catch (err) {
      error.value = err.message
      console.error('獲取止損數據失敗:', err)
      
      // 使用預設空數據避免組件崩潰
      positions.value = []
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 啟用止損監控（設定買入價）
   * @param {string} code - 股票代碼
   * @param {number} buyPrice - 買入價格
   * @returns {Promise<Object>} API 響應結果
   */
  const activateStopLoss = async (code, buyPrice) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch(`${API_BASE}/activate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          code: code,
          buy_price: parseFloat(buyPrice)
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail?.message || errorData.message || '啟動監控失敗')
      }
      
      const result = await response.json()
      
      // 立即更新本地狀態（適配新 response 格式：{ success, message, data: {...} }）
      const positionData = result.data || result
      const existingIndex = positions.value.findIndex(p => p.code === code)
      if (existingIndex >= 0) {
        positions.value[existingIndex] = {
          ...positions.value[existingIndex],
          ...positionData,
          isActive: true
        }
      } else {
        positions.value.unshift(positionData)
      }
      
      return result
    } catch (err) {
      error.value = err.message
      console.error('啟用止損監控失敗:', err)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 查詢單一股票的止損狀態
   * @param {string} code - 股票代碼
   * @returns {Promise<Object>} 止損狀態
   */
  const getPositionStatus = async (code) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch(`${API_BASE}/positions/${code}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (err) {
      error.value = err.message
      console.error('查詢止損狀態失敗:', err)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 手動檢查指定股票的止損
   * @param {string} code - 股票代碼
   * @returns {Promise<Object>} 檢查結果
   */
  const checkStopLoss = async (code) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch(`${API_BASE}/check/${code}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || '檢查止損失敗')
      }
      
      const result = await response.json()
      
      // 如果止損被觸發，立即刷新列表
      if (result.status === 'triggered') {
        await fetchPositions(true)
      }
      
      return result
    } catch (err) {
      error.value = err.message
      console.error('手動檢查止損失敗:', err)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 檢查所有活躍部位的止損
   * @returns {Promise<Object>} 批量檢查結果
   */
  const checkAllStopLoss = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch(`${API_BASE}/check-all`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || '批量檢查失敗')
      }
      
      const result = await response.json()
      
      // 刷新列表以獲取最新狀態
      await fetchPositions(true)
      
      return result
    } catch (err) {
      error.value = err.message
      console.error('批量檢查止損失敗:', err)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 關閉止損部位（例如賣出股票時）
   * @param {string} code - 股票代碼
   * @returns {Promise<Object>} 關閉結果
   */
  const closePosition = async (code) => {
    loading.value = true
    error.value = null
    
    try {
      const response = await fetch(`${API_BASE}/positions/${code}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `關閉部位失敗：${code}`)
      }
      
      const result = await response.json()
      
      // 從列表中移除該部位
      positions.value = positions.value.filter(p => p.code !== code)
      
      return result
    } catch (err) {
      error.value = err.message
      console.error('關閉止損部位失敗:', err)
      throw err
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 批量檢查多個股票的止損狀態
   * @param {string[]} codes - 股票代碼數組
   * @returns {Promise<Object[]>} 檢查結果數組
   */
  const checkMultipleStopLoss = async (codes) => {
    const results = []
    
    for (const code of codes) {
      try {
        const result = await checkStopLoss(code)
        results.push({ code, success: true, result })
      } catch (err) {
        results.push({ code, success: false, error: err.message })
      }
    }
    
    return results
  }

  // ========================================
  // 自動刷新功能
  // ========================================
  
  /**
   * 啟動自動刷新
   */
  const startAutoRefresh = () => {
    if (refreshIntervalId) return
    
    isAutoRefreshing.value = true
    
    // 立即執行一次
    fetchPositions().catch(err => {
      console.error('自動刷新初始獲取失敗:', err)
      isAutoRefreshing.value = false
    })
    
    // 設置定時器
    refreshIntervalId = setInterval(async () => {
      try {
        await fetchPositions()
        lastRefreshTime.value = new Date()
      } catch (error) {
        console.error('自動刷新失敗:', error)
        // 不中斷自動刷新，繼續下一輪
      }
    }, AUTO_REFRESH_INTERVAL)
  }
  
  /**
   * 停止自動刷新
   */
  const stopAutoRefresh = () => {
    if (refreshIntervalId) {
      clearInterval(refreshIntervalId)
      refreshIntervalId = null
      isAutoRefreshing.value = false
    }
  }
  
  /**
   * 切換自動刷新狀態
   */
  const toggleAutoRefresh = () => {
    if (isAutoRefreshing.value) {
      stopAutoRefresh()
    } else {
      startAutoRefresh()
    }
  }
  
  /**
   * 根據視圖可見性自動調整刷新
   * @returns {Function} 清理函數
   */
  const setupVisibilityHandling = () => {
    const handleChange = () => {
      if (document.hidden) {
        // 頁面隱藏時暫停刷新
        stopAutoRefresh()
      } else {
        // 頁面重新顯示時恢復刷新
        startAutoRefresh()
        // 立即刷新一次獲取最新數據
        fetchPositions().catch(err => {
          console.error('可見性恢復後獲取失敗:', err)
        })
      }
    }
    
    document.addEventListener('visibilitychange', handleChange)
    
    // 返回清理函數
    return () => {
      document.removeEventListener('visibilitychange', handleChange)
    }
  }
  
  /**
   * 組件卸載時的清理方法
   */
  const cleanup = () => {
    stopAutoRefresh()
  }

  // ========================================
  // 工具方法
  // ========================================
  
  /**
   * 檢查股票是否已被追蹤
   * @param {string} code - 股票代碼
   * @returns {boolean} 是否已被追蹤
   */
  const isTracked = (code) => {
    return positions.value.some(p => p.code === code)
  }
  
  /**
   * 獲取特定股票的資訊
   * @param {string} code - 股票代碼
   * @returns {Object|undefined} 部位資訊
   */
  const getPositionByCode = (code) => {
    return positions.value.find(p => p.code === code)
  }
  
  /**
   * 清除所有追蹤狀態
   */
  const clearAll = () => {
    positions.value = []
    error.value = null
  }
  
  /**
   * 從緩存恢復數據
   * @param {Object} cachedData - 緩存的數據對象
   */
  const restoreFromCache = (cachedData) => {
    if (cachedData && Array.isArray(cachedData.positions)) {
      positions.value = cachedData.positions
    }
  }
  
  /**
   * 將當前數據保存到緩存
   * @returns {Object} 緩存數據
   */
  const saveToCache = () => {
    return {
      positions: positions.value,
      timestamp: Date.now()
    }
  }
  
  /**
   * 格式化價格
   * @param {number} price - 價格
   * @returns {string} 格式化後的價格字符串
   */
  const formatPrice = (price) => {
    return price ? parseFloat(price).toFixed(2) : '-'
  }
  
  /**
   * 格式化百分比
   * @param {number} pct - 百分比值
   * @returns {string} 格式化後的百分比字符串
   */
  const formatPct = (pct) => {
    return pct ? (pct * 100).toFixed(2) + '%' : '0%'
  }
  
  /**
   * 判斷漲跌樣式類名
   * @param {number} currentPrice - 當前價格
   * @param {number} buyPrice - 買入價格
   * @returns {string} CSS 類名
   */
  const getPriceClass = (currentPrice, buyPrice) => {
    if (!buyPrice) return ''
    const change = currentPrice - buyPrice
    return change >= 0 ? 'text-green-400' : 'text-red-400'
  }
  
  /**
   * 計算回撤幅度百分比
   * @param {Object} position - 部位物件
   * @returns {number} 回撤百分比
   */
  const getDrawdownPercent = (position) => {
    if (!position.highestPrice || !position.currentPrice) return 0
    return ((position.highestPrice - position.currentPrice) / position.highestPrice * 100)
  }
  
  /**
   * 獲取狀態文字
   * @param {Object} position - 部位物件
   * @returns {string} 狀態文字
   */
  const getStatusText = (position) => {
    if (position.isTriggered) return '已觸發'
    if (position.buyPrice && position.isActive) return '監控中'
    return '追蹤中'
  }
  
  /**
   * 獲取狀態顏色類名
   * @param {Object} position - 部位物件
   * @returns {string} 顏色類名
   */
  const getStatusColorClass = (position) => {
    if (position.isTriggered) return 'bg-red-600'
    if (position.buyPrice && position.isActive) return 'bg-green-600'
    return 'bg-blue-600'
  }

  // ========================================
  // 返回公共 API
  // ========================================
  
  return {
    // ======================================
    // 狀態
    // ======================================
    positions,
    loading,
    error,
    
    // ======================================
    // 計數器（統計數據）
    // ======================================
    trackingCount,
    monitoringCount,
    triggeredCount,
    totalPositions,
    activePositions,
    
    // ======================================
    // 自動刷新狀態
    // ======================================
    isAutoRefreshing,
    lastRefreshTime,
    timeSinceLastRefresh,
    
    // ======================================
    // 主要 API 方法
    // ======================================
    fetchPositions,
    activateStopLoss,
    getPositionStatus,
    checkStopLoss,
    checkAllStopLoss,
    closePosition,
    checkMultipleStopLoss,
    
    // ======================================
    // 自動刷新控制方法
    // ======================================
    startAutoRefresh,
    stopAutoRefresh,
    toggleAutoRefresh,
    setupVisibilityHandling,
    cleanup,
    
    // ======================================
    // 工具函數
    // ======================================
    isTracked,
    getPositionByCode,
    clearAll,
    restoreFromCache,
    saveToCache,
    refresh: fetchPositions, // 提供別名以便於組件使用
    
    // ======================================
    // 輔助格式化函數
    // ======================================
    formatPrice,
    formatPct,
    getPriceClass,
    getDrawdownPercent,
    getStatusText,
    getStatusColorClass
  }
}
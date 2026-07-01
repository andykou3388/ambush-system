/**
 * RAM Stop Loss Tracker - 單元測試
 * 
 * 測試範圍：
 * 1. useRamStopLossData composable 方法
 * 2. RamStopLossTracker 組件渲染
 * 3. Integration 場景
 * 
 * @author Frontend Developer
 * @task RAM-08
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick, ref } from 'vue'

// ========================================
// Mock setup
// ========================================

const mockPositions = [
  {
    code: '2330.TW',
    name: '台積電',
    status: 'monitoring',
    buyPrice: 580,
    currentPrice: 595,
    highestPrice: 602,
    stopLossPrice: 553.84,
    drawdownPct: 1.16,
    buyDate: '2024-01-15',
    isActive: true,
    isTriggered: false
  },
  {
    code: '2317.TW',
    name: '鴻海',
    status: 'tracking',
    buyPrice: null,
    currentPrice: 105,
    highestPrice: null,
    stopLossPrice: null,
    drawdownPct: 0,
    buyDate: null,
    isActive: true,
    isTriggered: false
  }
]

const mockTriggeredPosition = {
  code: '2454.TW',
  name: '聯發科',
  status: 'triggered',
  buyPrice: 1200,
  currentPrice: 1080,
  highestPrice: 1250,
  stopLossPrice: 1150,
  drawdownPct: 8.5,
  buyDate: '2024-02-01',
  isActive: true,
  isTriggered: true
}

// ========================================
// useRamStopLossData Composable 測試
// ========================================

describe('useRamStopLossData', () => {
  let useRamStopLossData

  beforeAll(async () => {
    // Dynamic import the composable
    const module = await import('@/composables/useRamStopLossData')
    useRamStopLossData = module.useRamStopLossData
  })

  beforeEach(() => {
    // Mock global fetch
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should initialize with empty positions', () => {
    const { positions, loading, error } = useRamStopLossData()
    expect(positions.value).toEqual([])
    expect(loading.value).toBe(false)
    expect(error.value).toBeNull()
  })

  it('should handle API errors gracefully', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))
    
    const { positions, error, fetchPositions } = useRamStopLossData()
    
    await expect(fetchPositions()).rejects.toThrow('Network error')
    expect(error.value).toBeTruthy()
    expect(positions.value).toEqual([])
  })

  it('should fetch positions successfully', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockPositions)
    })
    
    const { positions, fetchPositions } = useRamStopLossData()
    await fetchPositions()
    
    expect(positions.value.length).toBe(2)
    expect(positions.value[0].code).toBe('2330.TW')
    expect(positions.value[1].code).toBe('2317.TW')
  })

  it('should handle HTTP error responses', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ detail: 'Internal server error' })
    })
    
    const { positions, error, fetchPositions } = useRamStopLossData()
    await expect(fetchPositions()).rejects.toThrow()
    expect(positions.value).toEqual([])
  })

  it('should track symbols correctly', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPositions)
      })
    
    const { positions, fetchPositions, isTracked } = useRamStopLossData()
    
    // Before fetch, no symbols tracked
    expect(isTracked('2330.TW')).toBe(false)
    
    // After fetch
    await fetchPositions()
    expect(isTracked('2330.TW')).toBe(true)
    expect(isTracked('2317.TW')).toBe(true)
    expect(isTracked('9999.TW')).toBe(false)
  })

  it('should activate stop loss monitoring', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPositions[0])
      })
    
    const { positions, activateStopLoss } = useRamStopLossData()
    const result = await activateStopLoss('2330.TW', 580)
    
    expect(result.code).toBe('2330.TW')
    expect(result.name).toBe('台積電')
  })

  it('should close position correctly', async () => {
    // First fetch positions
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPositions)
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ status: 'closed' })
      })
    
    const { positions, fetchPositions, closePosition } = useRamStopLossData()
    
    await fetchPositions()
    expect(positions.value.length).toBe(2)
    
    await closePosition('2330.TW')
    expect(positions.value.length).toBe(1)
    expect(positions.value[0].code).toBe('2317.TW')
  })

  it('should compute counts correctly', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([...mockPositions, mockTriggeredPosition])
      })
    
    const { 
      fetchPositions, 
      trackingCount, 
      monitoringCount, 
      triggeredCount, 
      totalPositions 
    } = useRamStopLossData()
    
    await fetchPositions()
    
    expect(totalPositions.value).toBe(3)
    expect(trackingCount.value).toBe(1)  // 2317.TW has no buyPrice
    expect(monitoringCount.value).toBe(1) // 2330.TW is monitoring
    expect(triggeredCount.value).toBe(1)  // 2454.TW is triggered
  })
})

// ========================================
// RamStopLossTracker 組件測試
// ========================================

describe('RamStopLossTracker', () => {
  let RamStopLossTracker

  beforeAll(async () => {
    const module = await import('@/views/RamStopLossTracker.vue')
    RamStopLossTracker = module.default
  })

  beforeEach(() => {
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should display empty state when no positions', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([])
    })
    
    const wrapper = mount(RamStopLossTracker, {
      global: {
        stubs: {
          Layout: { template: '<div><slot /></div>' },
          'router-view': true
        }
      }
    })
    
    // Wait for mount fetch
    await nextTick()
    await nextTick()
    
    const emptyState = wrapper.find('.text-slate-500')
    expect(emptyState.exists()).toBe(true)
    expect(emptyState.text()).toContain('目前沒有追蹤的止損部位')
  })

  it('should display error state on API failure', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Connection failed'))
    
    const wrapper = mount(RamStopLossTracker, {
      global: {
        stubs: {
          Layout: { template: '<div><slot /></div>' },
          'router-view': true
        }
      }
    })
    
    // Wait for mount fetch to reject
    await nextTick()
    await nextTick()
    await nextTick()
    
    // Should show error text
    const errorText = wrapper.text()
    expect(errorText).toContain('Connection failed')
  })

  it('should render position cards correctly', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockPositions)
    })
    
    const wrapper = mount(RamStopLossTracker, {
      global: {
        stubs: {
          Layout: { template: '<div><slot /></div>' }
        }
      }
    })
    
    await nextTick()
    await nextTick()
    
    // Wait for component to process fetched data
    await new Promise(resolve => setTimeout(resolve, 100))
    await nextTick()
    
    // Check stats cards exist (tracking, monitoring, triggered)
    const statValues = wrapper.findAll('.text-2xl.font-bold')
    expect(statValues.length).toBeGreaterThanOrEqual(3)
  })

  it('should have manual refresh button visible', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([])
    })
    
    const wrapper = mount(RamStopLossTracker, {
      global: {
        stubs: {
          Layout: { template: '<div><slot /></div>' }
        }
      }
    })
    
    await nextTick()
    
    const refreshButton = wrapper.find('button')
    const allButtons = wrapper.findAll('button')
    
    // Find the refresh button by text content
    const hasRefreshButton = allButtons.some(btn => btn.text().includes('刷新'))
    expect(hasRefreshButton).toBe(true)
  })
})

// ========================================
// Integration Tests
// ========================================

describe('End to End Scenarios', () => {
  it('should handle full tracking workflow', async () => {
    // Mock the initial fetch - empty positions
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve([])
    })
    
    const { useRamStopLossData } = await import('@/composables/useRamStopLossData')
    const { positions, fetchPositions, activateStopLoss, closePosition, isTracked } = useRamStopLossData()
    
    // Step 1: Initial state - empty
    await fetchPositions()
    expect(positions.value.length).toBe(0)
    expect(isTracked('2330.TW')).toBe(false)
    
    // Step 2: Add stock to tracking (activate stop loss)
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockPositions[0])
    })
    
    await activateStopLoss('2330.TW', 580)
    
    // Step 3: Fetch updated positions
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockPositions)
    })
    
    await fetchPositions()
    expect(isTracked('2330.TW')).toBe(true)
    
    // Step 4: Close position
    global.fetch = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ status: 'closed' })
    })
    
    await closePosition('2330.TW')
    expect(positions.value.length).toBe(1)
  })
})
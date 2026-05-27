// 股票數據接口定義
export const stockSchema = {
  symbol: String,      // 股票代碼
  name: String,        // 股票名稱
  price: Number,       // 當前價格
  change: Number,      // 漲跌金額
  changePct: Number,   // 漲跌幅百分比
  zone: String,        // 所屬區域 (buy/hold/sell)
  ma10: Number,        // MA10
  ma30: Number,        // MA30
  volume: Number,      // 成交量
  score: Number,       // 綜合評分
}
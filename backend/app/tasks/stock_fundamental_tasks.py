"""
通用股票基本面數據獲取任務
從 YFinance 獲取股票基本面數據並保存到 stock_fundamental 表
V2.0 優化：同時寫入 stock_fundamental_latest 緩存表
"""
from celery import shared_task
from yfinance import Ticker
from datetime import datetime
import time
import logging
import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from app.database import SessionLocal
from app.models.stock_fundamental import StockFundamental
from app.models.stock_fundamental_latest import StockFundamentalLatest

logger = logging.getLogger(__name__)


def _safe_numeric(value):
    """
    將 YFinance 回傳的值轉為安全的數值，過濾 Infinity/NaN 等非數值
    
    Args:
        value: 原始值（可能是 None, str, int, float）
        
    Returns:
        float 或 None（當值為 Infinity/NaN 時回傳 None）
    """
    if value is None:
        return None
    if isinstance(value, str) and value.lower() in ("infinity", "-infinity", "nan", "inf", "-inf"):
        return None
    try:
        v = float(value)
        if v == float('inf') or v == float('-inf') or v != v:  # v != v 檢測 NaN
            return None
        return v
    except (ValueError, TypeError):
        return None


def get_insider_net_buy_3m(ticker):
    """
    從 Ticker 的 insider_transactions 中計算過去 3 個月 (90 天) 的內部人淨買入股數。
    """
    try:
        df = ticker.insider_transactions
        
        # 1. 檢查數據是否存在
        if df is None or df.empty or 'Start Date' not in df.columns:
            return None

        # 2. 確保日期格式正確
        df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
        
        # 3. 計算 3 個月 (90 天) 前的截止時間
        cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=90)
        
        # 4. 篩選出過去 3 個月內的交易
        recent_tx = df[df['Start Date'] >= cutoff_date]
        
        # 如果過去 3 個月沒有任何交易，淨買入為 0
        if recent_tx.empty:
            return 0 

        net_shares = 0
        net_value = 0
        
        # 5. 遍歷明細，判斷買賣方向並加總
        for _, row in recent_tx.iterrows():
            shares = row.get('Shares', 0)
            value = row.get('Value', 0)
            
            # 處理 NaN 值
            shares = shares if pd.notna(shares) else 0
            value = value if pd.notna(value) else 0
            
            # 從 'Text' 欄位判斷交易方向 (因為 'Transaction' 欄位有時為空)
            text = str(row.get('Text', '')).lower()
            
            # 定義買入與賣出的關鍵字
            is_buy = any(kw in text for kw in ['purchase', 'acquisition', 'buy', 'grant', 'award'])
            is_sell = any(kw in text for kw in ['sale', 'sell', 'disposition'])
            
            # 根據方向加減股數與金額
            if is_buy and not is_sell:
                net_shares += shares
                net_value += value
            elif is_sell and not is_buy:
                net_shares -= shares
                net_value -= value
                
        # 根據您的資料庫需求，這裡返回「淨股數」。
        # 如果您的欄位需要的是「淨金額」，請改為 return net_value
        return net_shares 

    except Exception as e:
        logger.warning(f"計算 {ticker.ticker} 內部人淨買入失敗：{e}")
        return None


def save_to_database(data_list: list):
    """
    批量保存基本面數據到資料庫（雙表寫入）
    
    Args:
        data_list: 基本面數據列表
    """
    db = SessionLocal()
    try:
        for data in data_list:
            # 1. 寫入歷史表（原有邏輯，使用 UPSERT 避免唯一約束衝突）
            stmt = insert(StockFundamental).values(**data)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_code_report",
                set_={
                    "pe_ttm": data["pe_ttm"],
                    "eps_ttm": data["eps_ttm"],
                    "float_shares": data["float_shares"],
                    "debt_ratio": data["debt_ratio"],
                    "insider_net_buy_3m": data["insider_net_buy_3m"],
                    "pb": data["pb"],
                    "dividend_yield": data["dividend_yield"],
                    "total_market_cap": data["total_market_cap"],
                    "net_profit_ttm": data["net_profit_ttm"],
                    "updated_at": data["updated_at"],
                },
            )
            db.execute(stmt)
            
            # 2. 寫入最新緩存表（新增邏輯）
            # 只保留 latest 表需要的字段
            latest_data = {
                "code": data["code"],
                "market": data["market"],
                "report_date": data["report_date"],
                "pe_ttm": data["pe_ttm"],
                "eps_ttm": data["eps_ttm"],
                "float_shares": data["float_shares"],
                "debt_ratio": data["debt_ratio"],
                "insider_net_buy_3m": data["insider_net_buy_3m"],
                "pb": data["pb"],
                "dividend_yield": data["dividend_yield"],
                "total_market_cap": data["total_market_cap"],
                "net_profit_ttm": data["net_profit_ttm"],
                "updated_at": data["updated_at"],
            }
            upsert_latest = insert(StockFundamentalLatest).values(**latest_data)
            upsert_latest = upsert_latest.on_conflict_do_update(
                constraint="stock_fundamental_latest_pkey",
                set_=latest_data
            )
            db.execute(upsert_latest)
            
        db.commit()
        logger.info(f"批量保存 {len(data_list)} 條基本面數據（含 latest 緩存表）")
    except Exception as e:
        db.rollback()
        logger.error(f"保存數據失敗：{e}")
        raise
    finally:
        db.close()


def _fetch_stock_fundamentals_impl(stock_codes: list):
    """
    批量獲取股票基本面數據的通用實現（非 Celery 任務版本）
    供 Celery 任務和一次性初始化任務直接調用
    
    Args:
        stock_codes: 股票代碼列表，例如 ['2330.TW', '2317.TW', '0700.HK']
        
    Returns:
        dict: 包含處理結果的字典
    """
    logger.info(f"開始獲取 {len(stock_codes)} 隻股票的基本面數據")
    
    batch_fundamental_data = []
    failed_symbols = []
    success_count = 0
    
    # 分批處理避免過於頻繁的 API 請求
    batch_size = 5
    total_batches = (len(stock_codes) + batch_size - 1) // batch_size
    
    for i in range(0, len(stock_codes), batch_size):
        batch = stock_codes[i : i + batch_size]
        current_batch = i // batch_size + 1
        logger.info(f"處理批次 {current_batch}/{total_batches}: {batch}")
        
        for symbol in batch:
            try:
                # 添加延遲避免過於頻繁的 API 請求
                time.sleep(0.5)
                
                ticker = Ticker(symbol)
                info = ticker.info
                
                # 提取基本面數據
                # 注意：YFinance 的 debtToEquity 返回的是百分比值（如 140.542），
                # 需要轉換為小數（如 1.40542）以符合資料庫 NUMERIC(6,4) 的精度
                debt_to_equity = info.get("debtToEquity")
                if debt_to_equity is not None:
                    debt_to_equity = round(debt_to_equity / 100, 4)
                
                # 判斷市場
                if "." in symbol:
                    suffix = symbol.split(".")[-1]
                    if suffix == "TW":
                        market = "TW"
                    elif suffix == "HK":
                        market = "HK"
                    else:
                        market = suffix
                else:
                    market = "US"
                
                # ==========================================
                # 新增：處理您提到的 4 個特定欄位
                # ==========================================
                
                # 1. pb (市淨率 Price-to-Book)
                pb = info.get('priceToBook') 
                
                # 2. dividend_yield (股息收益率)
                div_yield_raw = info.get('dividendYield')
                if div_yield_raw is not None:
                    dividend_yield = (div_yield_raw * 100) if div_yield_raw < 1 else div_yield_raw
                else:
                    dividend_yield = None

                # 3. total_market_cap (總市值)
                total_market_cap = info.get('marketCap')
                
                # 4. net_profit_ttm (最近四季淨利潤 / TTM Net Income)
                net_profit_ttm = info.get('netIncomeToCommon')
                
                # 備用方案：如果 info 中沒有，則從年度財報 (income_stmt) 中獲取最新一期的 Net Income
                if net_profit_ttm is None:
                    try:
                        income_stmt = ticker.income_stmt
                        if income_stmt is not None and not income_stmt.empty:
                            # 取第一列（最新一期）的 Net Income
                            net_profit_ttm = income_stmt.iloc[0].get('Net Income')
                    except Exception:
                        pass

                fundamental_data = {
                    "code": symbol,
                    "market": market,
                    "report_date": datetime.now().date(),
                    "pe_ttm": _safe_numeric(info.get("trailingPE")),
                    "eps_ttm": _safe_numeric(info.get("trailingEps")),
                    "float_shares": info.get("floatShares"),
                    "debt_ratio": debt_to_equity,
                    "insider_net_buy_3m": get_insider_net_buy_3m(ticker) or 0,
                    "pb": pb,
                    "dividend_yield": dividend_yield,
                    "total_market_cap": total_market_cap,
                    "net_profit_ttm": net_profit_ttm,
                    "updated_at": datetime.now(),
                }
                logger.info(f"成功獲取 {symbol} 的基本面數據")
                batch_fundamental_data.append(fundamental_data)
                success_count += 1
                
            except Exception as e:
                logger.error(f"獲取 {symbol} 數據失敗：{e}")
                failed_symbols.append(symbol)
                continue
        
        # 每批次後稍作休息
        time.sleep(2)
    
    # 保存數據到資料庫
    if batch_fundamental_data:
        save_to_database(batch_fundamental_data)
        logger.info(f"成功保存 {len(batch_fundamental_data)} 條數據到資料庫")
    
    if failed_symbols:
        logger.warning(f"有 {len(failed_symbols)} 隻股票獲取失敗：{failed_symbols}")
    
    return {
        "status": "success",
        "total": len(stock_codes),
        "success": success_count,
        "failed": len(failed_symbols),
        "failed_symbols": failed_symbols,
    }


# ==========================================
# Celery 任務：批量獲取股票基本面數據
# 支援兩種調用方式：
#   1. 有參數：使用傳入的 stock_codes（向後相容）
#   2. 無參數：自動從 monitored_stocks 表讀取待監控股票清單
# ==========================================

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def fetch_stock_fundamentals(self, stock_codes: list = None):
    """
    批量獲取股票基本面數據的通用任務（支援自動從 monitored_stocks 讀取）
    """
    try:
        if not stock_codes:
            from app.utils.stock_utils import get_tracked_stock_codes
            stock_codes = get_tracked_stock_codes()
            logger.info(f"自動從 monitored_stocks 讀取股票清單，共 {len(stock_codes)} 隻")

        if not stock_codes:
            logger.warning("股票清單為空，跳過本次基本面抓取")
            return {"status": "skipped", "reason": "股票清單為空"}

        return _fetch_stock_fundamentals_impl(stock_codes)
    except Exception as exc:
        logger.error(f"獲取股票數據失敗：{exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=1)
def fetch_single_stock_fundamental(self, symbol: str):
    """
    獲取單一股票基本面數據
    
    Args:
        symbol: 股票代碼，例如 '2330.TW'
        
    Returns:
        dict: 股票基本面數據
    """
    try:
        logger.info(f"獲取單一股票 {symbol} 的基本面數據")
        ticker = Ticker(symbol)
        info = ticker.info
        
        debt_to_equity = info.get("debtToEquity")
        if debt_to_equity is not None:
            debt_to_equity = round(debt_to_equity / 100, 4)
        
        if "." in symbol:
            suffix = symbol.split(".")[-1]
            if suffix == "TW":
                market = "TW"
            elif suffix == "HK":
                market = "HK"
            else:
                market = suffix
        else:
            market = "US"
        
        pb = info.get('priceToBook') 
        
        div_yield_raw = info.get('dividendYield')
        if div_yield_raw is not None:
            dividend_yield = (div_yield_raw * 100) if div_yield_raw < 1 else div_yield_raw
        else:
            dividend_yield = None

        total_market_cap = info.get('marketCap')
        
        net_profit_ttm = info.get('netIncomeToCommon')
        
        if net_profit_ttm is None:
            try:
                income_stmt = ticker.income_stmt
                if income_stmt is not None and not income_stmt.empty:
                    net_profit_ttm = income_stmt.iloc[0].get('Net Income')
            except Exception:
                pass

        fundamental_data = {
            "code": symbol,
            "market": market,
            "report_date": datetime.now().date(),
            "pe_ttm": _safe_numeric(info.get("trailingPE")),
            "eps_ttm": _safe_numeric(info.get("trailingEps")),
            "float_shares": info.get("floatShares"),
            "debt_ratio": debt_to_equity,
            "insider_net_buy_3m": get_insider_net_buy_3m(ticker) or 0,
            "pb": pb,
            "dividend_yield": dividend_yield,
            "total_market_cap": total_market_cap,
            "net_profit_ttm": net_profit_ttm,
            "updated_at": datetime.now(),
        }
        
        save_to_database([fundamental_data])
        logger.info(f"成功獲取並保存 {symbol} 的基本面數據")
        return fundamental_data
        
    except Exception as exc:
        logger.error(f"獲取 {symbol} 數據失敗：{exc}")
        raise self.retry(exc=exc)
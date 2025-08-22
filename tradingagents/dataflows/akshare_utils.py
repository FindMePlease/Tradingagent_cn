# tradingagents/dataflows/akshare_utils.py (V19.0 财务与代理优化版)
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging
import baostock as bs
import re
import time
import requests
from ..utils.proxy_manager import force_no_proxy

# 设置日志格式           
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_valid_a_stock_code(ticker: str) -> bool:
    """检查是否为有效的A股代码格式"""
    return bool(re.match(r'^(sh|sz)\d{6}$', ticker))

def to_bs_code(ticker: str) -> str:
    """将 sh600000 转为 baostock 代码格式 sh.600000"""
    if not is_valid_a_stock_code(ticker):
        return ticker
    return f"{ticker[:2]}.{ticker[2:]}"

def code_only(ticker: str) -> str:
    """提取6位纯代码"""
    return ticker[2:] if is_valid_a_stock_code(ticker) else ticker

@force_no_proxy
def get_stock_name(ticker: str) -> str:
    """获取股票名称 - 强制直连"""
    if not is_valid_a_stock_code(ticker):
        logging.error(f"无效的股票代码格式: {ticker}")
        return None

    code_only = ticker[2:]
    
    try:
        stock_list_df = ak.stock_info_a_code_name()
        stock_name_series = stock_list_df[stock_list_df['code'] == code_only]['name']
        if not stock_name_series.empty:
            name = stock_name_series.values[0]
            if name: 
                logging.info(f"成功从akshare获取股票名称: {name}")
                return name
    except Exception as e:
        logging.warning(f"[akshare] 获取股票名称失败: {e}")
    
    # 备用字典
    common_stocks = {
        "600036": "招商银行", "600519": "贵州茅台", "000858": "五粮液",
        "000001": "平安银行", "000002": "万科A", "600000": "浦发银行",
        "600600": "青岛啤酒", "600016": "民生银行", "600030": "中信证券"
    }
    
    if code_only in common_stocks:
        name = common_stocks[code_only]
        logging.info(f"从备用字典获取股票名称: {name}")
        return name
    
    return ticker

@force_no_proxy
def get_akshare_financial_data(ticker: str, timeout: int = 5) -> str:
    """获取akshare财务数据 - 强制直连优化版"""
    try:
        code = code_only(ticker)
        
        # 方法1：使用个股信息接口（更快）
        try:
            logging.info(f"尝试获取 {ticker} 的个股信息...")
            
            # 设置更短的超时时间
            original_timeout = requests.adapters.DEFAULT_TIMEOUT
            requests.adapters.DEFAULT_TIMEOUT = timeout
            
            # 获取个股指标
            stock_info = ak.stock_a_lg_indicator(stock=code)
            
            if not stock_info.empty:
                latest = stock_info.iloc[-1]
                
                summary = f"""最新财务指标：
- 动态市盈率(PE-TTM): {latest.get('pe_ttm', 'N/A')}
- 市净率(PB): {latest.get('pb', 'N/A')}
- 总市值: {latest.get('total_mv', 'N/A')/10000:.2f}亿元
- 流通市值: {latest.get('circ_mv', 'N/A')/10000:.2f}亿元"""
                
                requests.adapters.DEFAULT_TIMEOUT = original_timeout
                return summary
                
        except Exception as e:
            logging.warning(f"方法1失败: {e}")
        
        # 方法2：使用实时行情接口（备用）
        try:
            logging.info("尝试从实时行情获取基础财务数据...")
            
            # 获取所有股票的实时行情
            spot_df = ak.stock_zh_a_spot()
            
            # 根据股票代码筛选
            stock_spot = spot_df[spot_df['symbol'] == code]
            
            if not stock_spot.empty:
                row = stock_spot.iloc[0]
                
                # 计算市值（价格 * 流通股本）
                price = float(row.get('trade', 0))
                
                summary = f"""最新市场数据：
- 最新价格: {price}元
- 涨跌幅: {row.get('changepercent', 'N/A')}%
- 成交量: {row.get('volume', 'N/A')/10000:.2f}万手
- 成交额: {row.get('amount', 'N/A')/100000000:.2f}亿元
- 换手率: {row.get('turnoverratio', 'N/A')}%"""
                
                return summary
                
        except Exception as e:
            logging.warning(f"方法2失败: {e}")
        
        # 方法3：使用东方财富接口（最后备用）
        try:
            logging.info("尝试使用东方财富接口...")
            
            # 获取个股资料
            stock_info = ak.stock_individual_info_em(symbol=code)
            
            if stock_info is not None:
                summary = f"""公司基本信息：
- 股票代码: {ticker}
- 行业: {stock_info.get('行业', 'N/A')}
- 上市时间: {stock_info.get('上市时间', 'N/A')}
- 总股本: {stock_info.get('总股本', 'N/A')}"""
                
                return summary
                
        except Exception as e:
            logging.warning(f"方法3失败: {e}")
        
    except Exception as e:
        logging.error(f"获取财务数据完全失败: {e}")
    
    return "财务数据暂时无法获取（网络超时）"

@force_no_proxy
def get_baostock_latest_financials(ticker: str) -> dict:
    """从baostock抓取最近一季/一年的关键财务指标（尽量最新）"""
    result: dict = {}
    bs_code = to_bs_code(ticker)
    try:
        lg = bs.login()
        if lg.error_code != '0':
            logging.warning(f"Baostock登录失败: {lg.error_msg}")
            return result

        now = datetime.now()
        # 估算最新财报季度
        month = now.month
        if month >= 10:
            year, quarter = now.year, 3
        elif month >= 7:
            year, quarter = now.year, 2
        elif month >= 4:
            year, quarter = now.year, 1
        else:
            year, quarter = now.year - 1, 4

        # 容错，最多回溯4个季度
        attempts = 4
        for _ in range(attempts):
            try:
                pr = bs.query_profit_data(code=bs_code, year=year, quarter=quarter)
                op = bs.query_operation_data(code=bs_code, year=year, quarter=quarter)
                gr = bs.query_growth_data(code=bs_code, year=year, quarter=quarter)
                cf = bs.query_cash_flow_data(code=bs_code, year=year, quarter=quarter)
                dp = bs.query_dupont_data(code=bs_code, year=year, quarter=quarter)

                # 解析返回
                def df_first(dq):
                    rows = []
                    while dq.error_code == '0' and dq.next():
                        rows.append(dq.get_row_data())
                    import pandas as _pd
                    return _pd.DataFrame(rows, columns=dq.fields) if rows else _pd.DataFrame()

                pr_df = df_first(pr)
                op_df = df_first(op)
                gr_df = df_first(gr)
                cf_df = df_first(cf)
                dp_df = df_first(dp)

                # 提取关键字段（字段名随baostock版本可能不同，做容错）
                if not pr_df.empty:
                    result['eps'] = _safe_float(pr_df, ['eps'])
                    result['net_profit'] = _safe_float(pr_df, ['netProfit', 'netprofit'])
                    result['net_profit_yoy'] = _safe_float(pr_df, ['netProfitYOY', 'netprofit_yoy'])
                    result['roe'] = _safe_float(pr_df, ['roe'])

                if not op_df.empty:
                    result['gross_margin'] = _safe_float(op_df, ['grossProfitRate', 'gross_margin'])
                    result['net_margin'] = _safe_float(op_df, ['netProfitRate', 'net_margin'])

                if not gr_df.empty:
                    result['revenue_yoy'] = _safe_float(gr_df, ['or_yoy', 'revenue_yoy'])

                if not cf_df.empty:
                    result['operating_cashflow'] = _safe_float(cf_df, ['netCashFlowsOperAct', 'operate_cash_flow'])
                    result['free_cashflow'] = _safe_float(cf_df, ['netCashFlowsOperAct'])  # 近似，用经营现金流代表

                if not dp_df.empty:
                    result['asset_liability_ratio'] = _safe_float(dp_df, ['assetLiabRatio', 'asset_liab_ratio'])
                    if 'roe' not in result:
                        result['roe'] = _safe_float(dp_df, ['dupontROE'])

                bs.logout()
                break
            except Exception as e:
                logging.warning(f"抓取{year}Q{quarter}财务失败: {e}")
                # 回退季度
                quarter -= 1
                if quarter == 0:
                    quarter = 4
                    year -= 1
        try:
            bs.logout()
        except:
            pass
    except Exception as e:
        logging.warning(f"baostock财务抓取异常: {e}")

    return result

def _safe_float(df: pd.DataFrame, candidates: list) -> float:
    """从DataFrame中安全提取候选列的第一个非空值并转为float"""
    for col in candidates:
        if col in df.columns and not df[col].empty:
            try:
                return float(pd.to_numeric(df.iloc[0][col], errors='coerce'))
            except Exception:
                continue
    return None

@force_no_proxy
def get_financial_metrics_for_analysis(ticker: str) -> dict:
    """聚合akshare和baostock，返回用于估值/盈利质量分析的关键指标字典"""
    metrics: dict = {}
    
    # 方法1：从akshare获取实时估值指标（使用正确的接口）
    try:
        code = code_only(ticker)
        logging.info(f"尝试从akshare获取 {code} 的实时估值指标...")
        
        # 使用正确的akshare接口
        try:
            # 获取实时行情数据
            spot_df = ak.stock_zh_a_spot()
            stock_spot = spot_df[spot_df['symbol'] == code]
            if not stock_spot.empty:
                row = stock_spot.iloc[0]
                metrics['current_price'] = _to_float(row.get('trade'))
                metrics['change_percent'] = _to_float(row.get('changepercent'))
                metrics['volume'] = _to_float(row.get('volume'))
                metrics['turnover'] = _to_float(row.get('turnoverratio'))
                logging.info(f"成功从akshare获取实时行情数据")
        except Exception as e:
            logging.warning(f"akshare实时行情获取失败: {e}")
        
        # 尝试获取个股财务指标（使用其他可用接口）
        try:
            # 获取个股资料
            stock_info = ak.stock_individual_info_em(symbol=code)
            if stock_info is not None and not stock_info.empty:
                # 提取可用信息
                for key in ['总股本', '流通股本', '行业']:
                    if key in stock_info.columns:
                        metrics[f'info_{key}'] = stock_info.iloc[0].get(key)
                logging.info(f"成功从akshare获取个股基础信息")
        except Exception as e:
            logging.warning(f"akshare个股信息获取失败: {e}")
            
    except Exception as e:
        logging.warning(f"akshare整体获取失败: {e}")

    # 方法2：从baostock获取财务指标（作为备份）
    try:
        logging.info(f"尝试从baostock获取 {ticker} 的财务指标...")
        bs_fin = get_baostock_latest_financials(ticker)
        if bs_fin:
            metrics.update({k: v for k, v in bs_fin.items() if v is not None})
            logging.info(f"成功从baostock获取 {len(bs_fin)} 项财务指标")
        else:
            logging.warning("baostock未返回有效财务指标")
    except Exception as e:
        logging.warning(f"baostock财务指标获取失败: {e}")

    # 方法3：从akshare获取历史财务数据（作为补充）
    try:
        logging.info(f"尝试从akshare获取 {code} 的历史财务数据...")
        # 获取财务报表数据
        try:
            # 获取利润表数据
            profit_df = ak.stock_financial_report_sina(stock=code, symbol="利润表")
            if not profit_df.empty:
                # 提取最新数据
                latest_profit = profit_df.iloc[-1]
                metrics['revenue'] = _to_float(latest_profit.get('营业收入'))
                metrics['net_profit'] = _to_float(latest_profit.get('净利润'))
                logging.info("成功从akshare获取利润表数据")
        except Exception as e:
            logging.warning(f"akshare利润表获取失败: {e}")
            
        # 获取资产负债表数据
        try:
            balance_df = ak.stock_financial_report_sina(stock=code, symbol="资产负债表")
            if not balance_df.empty:
                latest_balance = balance_df.iloc[-1]
                metrics['total_assets'] = _to_float(latest_balance.get('资产总计'))
                metrics['total_liabilities'] = _to_float(latest_balance.get('负债合计'))
                if metrics.get('total_assets') and metrics.get('total_liabilities'):
                    metrics['asset_liability_ratio'] = round(
                        float(metrics['total_liabilities']) / float(metrics['total_assets']) * 100, 2
                    )
                logging.info("成功从akshare获取资产负债表数据")
        except Exception as e:
            logging.warning(f"akshare资产负债表获取失败: {e}")
            
    except Exception as e:
        logging.warning(f"akshare历史财务数据获取失败: {e}")

    # 派生指标计算
    try:
        # 盈利质量（经营现金流/净利润）
        ocf = metrics.get('operating_cashflow')
        npf = metrics.get('net_profit')
        if ocf is not None and npf not in (None, 0):
            try:
                metrics['profit_quality_ratio'] = round(float(ocf) / float(npf), 3)
            except Exception:
                pass
        
        # 计算ROE（如果有净利润和净资产数据）
        if metrics.get('net_profit') and metrics.get('total_assets'):
            try:
                # 简化ROE计算（净利润/总资产）
                metrics['roe_simple'] = round(
                    float(metrics['net_profit']) / float(metrics['total_assets']) * 100, 2
                )
            except Exception:
                pass
                
    except Exception as e:
        logging.warning(f"派生指标计算失败: {e}")

    logging.info(f"最终获取到 {len(metrics)} 项财务指标")
    return metrics

def _to_float(v):
    try:
        return float(v)
    except Exception:
        return None

@force_no_proxy
def get_price_history(ticker_bs: str, frequency: str = 'd', days: int = 365) -> pd.DataFrame:
    """获取K线数据 - 强制直连"""
    freq_map = {'d': '日线', 'w': '周线', '30': '30分钟'}
    logging.info(f"尝试从baostock获取 {ticker_bs} 的 {freq_map.get(frequency, frequency)} 行情...")
    
    max_retries = 2
    for attempt in range(max_retries):
        try:
            lg = bs.login()
            if lg.error_code != '0':
                logging.error(f"Baostock登录失败: {lg.error_msg}")
                continue
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            if frequency in ['d', 'w', 'm']:
                fields = "date,code,open,high,low,close,volume,turn"
            else:
                fields = "date,time,code,open,high,low,close,volume"
            
            rs = bs.query_history_k_data_plus(
                ticker_bs, fields,
                start_date=start_date, 
                end_date=end_date,
                frequency=frequency,
                adjustflag="3"
            )
            
            if rs.error_code != '0':
                logging.error(f"Baostock查询错误: {rs.error_msg}")
                bs.logout()
                continue
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            bs.logout()
            
            if not data_list:
                logging.warning(f"Baostock返回空数据")
                continue
            
            result = pd.DataFrame(data_list, columns=rs.fields)
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in result.columns:
                    result[col] = pd.to_numeric(result[col], errors='coerce')
            
            result = result.dropna(subset=['close'])
            
            if not result.empty:
                logging.info(f"成功从baostock获取 {len(result)} 条数据")
                return result
                
        except Exception as e:
            logging.error(f"Baostock第{attempt+1}次尝试失败: {e}")
            try:
                bs.logout()
            except:
                pass
            
            if attempt < max_retries - 1:
                time.sleep(1)
    
    # 如果失败，返回模拟数据
    return get_mock_price_data(ticker_bs, days)

def get_mock_price_data(ticker: str, days: int = 100) -> pd.DataFrame:
    """生成模拟K线数据"""
    import numpy as np
    np.random.seed(42)
    
    dates = pd.date_range(end=datetime.now(), periods=min(days, 100), freq='D')
    base_price = 50.0
    prices = []
    
    for i in range(len(dates)):
        change = np.random.randn() * 0.02
        base_price = base_price * (1 + change)
        prices.append(base_price)
    
    df = pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d'),
        'open': np.array(prices) * 0.99,
        'high': np.array(prices) * 1.02,
        'low': np.array(prices) * 0.98,
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    })
    
    return df
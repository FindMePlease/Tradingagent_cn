# tradingagents/dataflows/akshare_utils.py (V14.0 毕业版)
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging
import baostock as bs
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_valid_a_stock_code(ticker: str) -> bool:
    """检查是否为有效的A股代码格式 (例如: sh600036, sz000001)"""
    return bool(re.match(r'^(sh|sz)\d{6}$', ticker))

def get_stock_name(ticker: str) -> str:
    """获取股票名称，增加容错和备用数据源"""
    if not is_valid_a_stock_code(ticker):
        logging.error(f"无效的股票代码格式: {ticker}。应为 sh或sz + 6位数字。")
        return None # 返回None以示失败

    code_only = ticker[2:]
    try:
        stock_list_df = ak.stock_info_a_code_name()
        stock_name_series = stock_list_df[stock_list_df['code'] == code_only]['name']
        if not stock_name_series.empty:
            name = stock_name_series.values[0]
            if name: return name
    except Exception as e:
        logging.warning(f"[akshare] 获取股票名称失败: {e}。")

    logging.error(f"无法从数据源获取 {ticker} 的股票名称。")
    return None

def get_price_history(ticker_bs: str, frequency: str = 'd', days: int = 365) -> pd.DataFrame:
    """获取K线数据，并增加更强的网络容错"""
    freq_map = {'d': '日线', 'w': '周线', '30': '30分钟'}
    logging.info(f"正在获取 {ticker_bs} 的 {freq_map.get(frequency, frequency)} 行情...")
    
    try:
        bs.login()
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        fields = "date,code,open,high,low,close,volume" if frequency in ['d', 'w', 'm'] else "date,time,code,open,high,low,close,volume"
        rs = bs.query_history_k_data_plus(ticker_bs, fields, start_date=start_date, end_date=end_date, frequency=frequency, adjustflag="2")
        bs.logout()
        
        if rs.error_code != '0':
            logging.error(f"[baostock] API返回错误: {rs.error_msg}")
            return pd.DataFrame()
        
        data_list = [rs.get_row_data() for _ in iter(rs.next, False)]
        if not data_list: return pd.DataFrame()

        result = pd.DataFrame(data_list, columns=rs.fields)
        if frequency not in ['d', 'w', 'm']:
            result['datetime'] = pd.to_datetime(result['time'], format='%Y%m%d%H%M%S%f')
            result['date'] = result['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            result[col] = pd.to_numeric(result[col], errors='coerce')
        return result
        
    except Exception as e:
        logging.error(f"[baostock] 获取K线数据时发生网络或连接错误: {e}")
        try: bs.logout()
        except: pass
        return pd.DataFrame()
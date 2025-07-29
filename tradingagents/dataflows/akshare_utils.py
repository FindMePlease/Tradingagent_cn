# tradingagents/dataflows/akshare_utils.py (V4.2 终极修正版)
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging
import baostock as bs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_stock_name(ticker: str) -> str:
    if len(ticker) > 6: ticker = ticker[2:]
    try:
        stock_list_df = ak.stock_info_a_code_name()
        stock_name = stock_list_df[stock_list_df['code'] == ticker]['name'].values
        if len(stock_name) > 0: return stock_name[0]
        return ticker
    except Exception:
        return ticker

def get_company_profile(ticker: str) -> str:
    stock_code = ticker[2:] if len(ticker) > 6 else ticker
    stock_name_val = get_stock_name(ticker)
    profile_text = f"--- {stock_name_val} ({ticker}) 公司概况 ---\n\n"
    try:
        logging.info(f"正在获取 {ticker} 的公司概况 (来源: AkShare)...")
        profile_df = ak.stock_individual_info_em(symbol=stock_code)
        if not profile_df.empty:
            profile_dict = dict(zip(profile_df['item'], profile_df['value']))
            for key, value in profile_dict.items(): profile_text += f"{key}: {value}\n"
        return profile_text
    except Exception as e:
        return f"获取 {ticker} 公司概况时出错: {e}"

def get_price_history(ticker_bs: str, frequency: str = 'd', days: int = 365) -> pd.DataFrame:
    """[核心修正] 根据不同的K线周期，请求正确的字段"""
    freq_map = {'d': '日线', 'w': '周线', '30': '30分钟'}
    logging.info(f"正在获取 {ticker_bs} 的 {freq_map.get(frequency, frequency)} 行情 (来源: baostock)...")
    bs.login()
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # [核心修正] 针对不同周期，定义不同的请求字段
    if frequency in ['d', 'w', 'm']: # 日、周、月线
        fields = "date,code,open,high,low,close,volume"
    else: # 分钟线
        fields = "date,time,code,open,high,low,close,volume"

    rs = bs.query_history_k_data_plus(
        ticker_bs, fields,
        start_date=start_date, end_date=end_date,
        frequency=frequency, adjustflag="2"
    )
    bs.logout()
    if rs.error_code != '0':
        logging.error(f"[baostock] 获取 {freq_map.get(frequency, frequency)} 行情失败: {rs.error_msg}")
        return pd.DataFrame()
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
        
    result = pd.DataFrame(data_list, columns=rs.fields)
    if frequency not in ['d', 'w', 'm']:
        result['datetime'] = pd.to_datetime(result['time'], format='%Y%m%d%H%M%S%f')
        result['date'] = result['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    for col in ['open', 'high', 'low', 'close', 'volume']:
        result[col] = pd.to_numeric(result[col], errors='coerce')
    
    logging.info(f"成功获取 {ticker_bs} 的 {len(result)} 条 {freq_map.get(frequency, frequency)} 价格数据。")
    return result
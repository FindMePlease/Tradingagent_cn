# tradingagents/dataflows/akshare_utils.py (最终版)
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import logging
import baostock as bs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def format_ticker_for_akshare(ticker: str) -> str:
    if isinstance(ticker, str) and len(ticker) == 8:
        return ticker[2:]
    return ticker

def get_stock_name(ticker: str) -> str:
    try:
        stock_code = format_ticker_for_akshare(ticker)
        stock_list_df = ak.stock_info_a_code_name()
        stock_name = stock_list_df[stock_list_df['code'] == stock_code]['name'].values
        if len(stock_name) > 0:
            return stock_name[0]
        return ticker
    except Exception:
        return ticker

def get_company_profile(ticker: str) -> str:
    stock_code = format_ticker_for_akshare(ticker)
    stock_name_val = get_stock_name(ticker)
    profile_text = f"--- {stock_name_val} ({ticker}) 公司概况 ---\n\n"
    try:
        logging.info(f"正在获取 {ticker} 的公司概况 (来源: AkShare)...")
        profile_df = ak.stock_individual_info_em(symbol=stock_code)
        if not profile_df.empty:
            profile_dict = dict(zip(profile_df['item'], profile_df['value']))
            for key, value in profile_dict.items():
                profile_text += f"{key}: {value}\n"
        return profile_text
    except Exception as e:
        return f"获取 {ticker} 公司概况时出错。"

def get_price_history(ticker: str, days: int = 365) -> pd.DataFrame:
    logging.info(f"正在获取 {ticker} 的日线行情 (来源: baostock)...")
    bs.login()
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    rs = bs.query_history_k_data_plus(
        ticker, "date,code,open,high,low,close,volume,amount",
        start_date=start_date, end_date=end_date, frequency="d", adjustflag="2"
    )
    bs.logout()
    if rs.error_code != '0':
        logging.error(f"[baostock] 获取行情失败: {rs.error_msg}")
        return pd.DataFrame()
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    result = pd.DataFrame(data_list, columns=rs.fields)
    for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
        result[col] = pd.to_numeric(result[col], errors='coerce')
    logging.info(f"成功获取 {ticker} 的 {len(result)} 条价格数据。")
    return result

def get_financial_reports(ticker: str) -> str:
    logging.info(f"正在获取 {ticker} 的财务数据 (来源: baostock)...")
    bs.login()
    stock_name_val = get_stock_name(ticker.replace('.', ''))
    report_text = f"--- {stock_name_val} ({ticker}) 财务报告摘要 (来源: baostock) ---\n\n"
    try:
        profit_list = []
        for year in range(datetime.now().year - 2, datetime.now().year + 1):
            for quarter in range(1, 5):
                rs = bs.query_profit_data(code=ticker, year=year, quarter=quarter)
                while (rs.error_code == '0') & rs.next():
                    profit_list.append(rs.get_row_data())
        if profit_list:
            profit_df = pd.DataFrame(profit_list, columns=rs.fields)
            profit_df_subset = profit_df[['statDate', 'roeAvg', 'npMargin', 'gpMargin', 'netProfit', 'epsTTM']]
            profit_df_subset.columns = ['财报日期', '净资产收益率ROE(%)', '净利率(%)', '毛利率(%)', '净利润(元)', '每股收益TTM(元)']
            report_text += "### 1. 核心盈利能力指标 ###\n" + profit_df_subset.to_markdown(index=False) + "\n\n"
        else:
            report_text += "未能获取核心盈利能力指标。\n\n"
        growth_list = []
        for year in range(datetime.now().year - 2, datetime.now().year + 1):
            for quarter in range(1, 5):
                rs = bs.query_growth_data(code=ticker, year=year, quarter=quarter)
                while (rs.error_code == '0') & rs.next():
                    growth_list.append(rs.get_row_data())
        if growth_list:
            growth_df = pd.DataFrame(growth_list, columns=rs.fields)
            growth_df_subset = growth_df[['statDate', 'YOYEquity', 'YOYAsset', 'YOYNI', 'YOYEPSBasic']]
            growth_df_subset.columns = ['财报日期', '净资产同比增长率(%)', '总资产同比增长率(%)', '净利润同比增长率(%)', '每股收益同比增长率(%)']
            report_text += "### 2. 核心成长能力指标 ###\n" + growth_df_subset.to_markdown(index=False) + "\n\n"
        else:
            report_text += "未能获取核心成长能力指标。\n\n"
    except Exception as e:
        logging.error(f"财务报告 [baostock]: 获取数据时发生严重错误: {e}")
        report_text += "获取财务数据时发生未知错误。\n"
    finally:
        bs.logout()
    return report_text
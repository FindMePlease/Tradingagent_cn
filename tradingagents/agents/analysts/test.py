import baostock as bs
import pandas as pd
from datetime import datetime, timedelta

def verify_latest_kline_data(stock_code: str):
    """
    一个独立的验证函数，用于抓取并打印指定股票最新的日线行情数据。

    Args:
        stock_code (str): 需要查询的股票代码, 格式为 'sh.xxxxxx' 或 'sz.xxxxxx'。
    """
    print("="*60)
    print(f"正在为您验证股票 {stock_code} 的最新日线数据...")
    print("="*60)

    # 1. 登录 baostock
    lg = bs.login()
    if lg.error_code != '0':
        print(f"登录失败: {lg.error_msg}")
        return
    print(f"Baostock 登录成功！(返回信息: {lg.error_msg})")

    # 2. 设置查询日期范围（我们只关心最近5个交易日）
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d') # 查询过去10天，确保能覆盖5个交易日
    
    print(f"查询日期范围: {start_date} 到 {end_date}")

    # 3. 准备查询参数
    # 我们需要'date', 'open', 'high', 'low', 'close', 'volume'
    # adjustflag="2" 代表后复权
    fields = "date,code,open,high,low,close,volume,preclose"
    
    # 4. 执行查询
    rs = bs.query_history_k_data_plus(
        stock_code,
        fields,
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="2"
    )

    if rs.error_code != '0':
        print(f"\n查询K线数据失败: {rs.error_msg}")
        bs.logout()
        return
    
    # 5. 处理并打印结果
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    if not data_list:
        print("\n在指定日期范围内未能获取到任何数据。")
    else:
        result = pd.DataFrame(data_list, columns=rs.fields)
        print("\n--- 获取到的最新K线数据如下 ---")
        print(result.tail(5)) # 打印最近5条记录
        print("\n请将上面表格中的最后一行数据的'date'与当前市场的最新交易日进行核对。")

    # 6. 登出 baostock
    bs.logout()
    print("\nBaostock 已成功登出。")
    print("="*60)


if __name__ == '__main__':
    # 将这里替换为您想验证的任何股票代码
    target_stock = 'sh.601068'  # 中铝国际
    verify_latest_kline_data(target_stock)
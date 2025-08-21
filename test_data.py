#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据获取测试脚本
用于验证各个数据源是否正常工作
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_stock_name():
    """测试股票名称获取"""
    print("\n" + "="*60)
    print("测试1：获取股票名称")
    print("="*60)
    
    from tradingagents.dataflows.akshare_utils import get_stock_name
    
    test_stocks = ["sh600600", "sz000858", "sh600036"]
    for ticker in test_stocks:
        name = get_stock_name(ticker)
        print(f"{ticker}: {name}")

def test_price_history():
    """测试K线数据获取"""
    print("\n" + "="*60)
    print("测试2：获取K线数据")
    print("="*60)
    
    from tradingagents.dataflows.akshare_utils import get_price_history
    
    ticker_bs = "sh.600600"
    
    # 测试日线
    print("\n获取日线数据...")
    df_daily = get_price_history(ticker_bs, 'd', 30)
    if not df_daily.empty:
        print(f"✅ 成功获取 {len(df_daily)} 条日线数据")
        print(df_daily.tail(5))
    else:
        print("❌ 日线数据获取失败")
    
    # 测试30分钟线
    print("\n获取30分钟线数据...")
    df_30m = get_price_history(ticker_bs, '30', 10)
    if not df_30m.empty:
        print(f"✅ 成功获取 {len(df_30m)} 条30分钟线数据")
        print(df_30m.tail(5))
    else:
        print("⚠️ 30分钟线数据获取失败（使用备用数据）")

def test_financial_data():
    """测试财务数据获取"""
    print("\n" + "="*60)
    print("测试3：获取财务数据")
    print("="*60)
    
    from tradingagents.dataflows.ai_research_assistant import get_financial_data_from_akshare
    
    ticker = "sh600600"
    financial_summary = get_financial_data_from_akshare(ticker)
    print(financial_summary)

def test_capital_flow():
    """测试资金流向数据"""
    print("\n" + "="*60)
    print("测试4：获取资金流向")
    print("="*60)
    
    from tradingagents.dataflows.ai_research_assistant import get_capital_flow_from_akshare
    
    ticker = "sh600600"
    capital_summary = get_capital_flow_from_akshare(ticker)
    print(capital_summary)

def test_ai_assistant():
    """测试AI研究助理"""
    print("\n" + "="*60)
    print("测试5：AI研究助理综合分析")
    print("="*60)
    
    from tradingagents.dataflows.ai_research_assistant import get_data_by_ai_assistant
    
    ticker = "sh600600"
    stock_name = "青岛啤酒"
    
    try:
        report = get_data_by_ai_assistant(ticker, stock_name)
        print(f"✅ AI分析报告生成成功")
        print(f"- 新闻条数: {len(report.analyzed_news_and_sentiment)}")
        print(f"- 政策分析: {report.analyzed_policy[:100]}...")
        print(f"- 财务摘要: {report.financial_metrics_summary[:100]}...")
        print(f"- 资金流向: {report.capital_flow_summary[:100]}...")
    except Exception as e:
        print(f"❌ AI分析失败: {e}")

def test_llm_connection():
    """测试LLM连接"""
    print("\n" + "="*60)
    print("测试6：LLM连接测试")
    print("="*60)
    
    from tradingagents.llms import llm_client_factory
    
    # 测试千问
    try:
        print("测试千问连接...")
        llm = llm_client_factory("qwen")
        response = llm.invoke("你好，请回复'测试成功'")
        print(f"✅ 千问连接成功: {response.content}")
    except Exception as e:
        print(f"❌ 千问连接失败: {e}")
    
    # 测试Gemini（如果配置了）
    try:
        print("\n测试Gemini连接...")
        llm = llm_client_factory("gemini")
        response = llm.invoke("Hello, please reply 'test successful'")
        print(f"✅ Gemini连接成功: {response.content}")
    except Exception as e:
        print(f"⚠️ Gemini连接失败: {e}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("A股多智能体投研系统 - 数据获取测试")
    print("="*60)
    
    # 运行所有测试
    try:
        test_stock_name()
        test_price_history()
        test_financial_data()
        test_capital_flow()
        test_llm_connection()
        test_ai_assistant()
        
        print("\n" + "="*60)
        print("测试完成！请检查上述结果")
        print("="*60)
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
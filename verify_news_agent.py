import argparse
import logging
import os
import requests
from bs4 import BeautifulSoup
from typing import List
from datetime import datetime, timedelta

# --- [核心修正] 在所有网络操作之前，强制设置代理 ---
# 我们假设您的代理服务器在本地运行 (127.0.0.1)
# 并且同时支持 http 和 https
proxy_address = "http://127.0.0.1:7897"
os.environ['HTTP_PROXY'] = proxy_address
os.environ['HTTPS_PROXY'] = proxy_address
print(f"--- [诊断信息]：已为当前程序设置网络代理: {proxy_address} ---")
# --- 1. 配置日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 2. 导入我们项目的核心功能 ---
try:
    # [最终修正] 确保从 smart_news_agent 导入
    from tradingagents.dataflows.smart_news_agent import get_smart_news
    # [最终修正] 使用了绝对正确的变量名 Google Search_CONFIG
    from tradingagents.default_config import LLM_PROVIDER, QWEN_CONFIG, Google_Search_CONFIG
    print("--- [诊断脚本]：成功从项目中导入核心模块 ---")
except ImportError as e:
    print(f"\n[严重错误] 导入核心模块失败: {e}")
    print("请确保您的文件结构正确，并且您正从项目根目录运行此脚本。")
    exit()

# --- 3. 复制 Pydantic 和 LangChain 定义 ---
try:
    from pydantic import BaseModel, Field
    from langchain.prompts import ChatPromptTemplate
    from langchain_community.chat_models import ChatTongyi
    from langchain.output_parsers import PydanticOutputParser
    print("--- [诊断脚本]：成功导入 langchain 和 pydantic ---")
except ImportError:
    print("[错误] 核心库未安装。请在终端运行: pip install pydantic langchain langchain-community dashscope")
    exit()

def setup_environment():
    """
    一个辅助函数，用于检查和配置运行所需的环境。
    """
    print("\n--- 正在为您配置和检查运行环境 ---")
    
    # 检查千问API Key
    try:
        qwen_api_key = QWEN_CONFIG.get("api_key")
        if not qwen_api_key or "your_qwen_api_key" in qwen_api_key or "在这里粘贴" in qwen_api_key:
             print("\n[严重错误] 通义千问API Key未配置！")
             print("请先打开 tradingagents/default_config.py 文件，设置您的 QWEN_CONFIG。")
             return False
        os.environ["DASHSCOPE_API_KEY"] = qwen_api_key
        print(f"[成功] 已加载 '{LLM_PROVIDER}' 的配置。")
    except (ImportError, KeyError):
        print("\n[严重错误] 无法加载配置文件中的 QWEN_CONFIG。")
        return False

    # 检查Google Search API Key
    try:
        # [最终修正] 使用了绝对正确的变量名 Google_Search_CONFIG
        google_api_key = Google_Search_CONFIG.get("api_key")
        google_cx_id = Google_Search_CONFIG.get("cx_id")
        if not google_api_key or "在这里粘贴" in google_api_key or not google_cx_id:
            print("\n[严重错误] Google Search API Key 或 CX ID 未配置！")
            print("请先打开 tradingagents/default_config.py 文件，设置您的 Google_Search_CONFIG。")
            return False
        print("[成功] 已加载 Google Search API 的配置。")
    except (ImportError, KeyError):
        # [最终修正] 使用了绝对正确的变量名 Google_Search_CONFIG
        print("\n[严重错误] 无法加载配置文件中的 Google_Search_CONFIG。")
        return False
        
    return True

def run_verification(ticker: str, stock_name: str, num_articles: int):
    """
    执行验证流程。
    """
    print("\n" + "="*80)
    print(f"    开始为「{stock_name} ({ticker})」执行【Google API版】AI新闻智能体验证流程")
    print("="*80)
    
    # 调用我们想要验证的核心功能
    report = get_smart_news(ticker=ticker, stock_name=stock_name, num_articles=num_articles)
    
    print("\n" + "="*80)
    print("                 验证完成 - 最终生成的报告")
    print("="*80)
    print(report)
    print("="*80)
    print("\n请检查以上报告，确认AI新闻智能体是否成功从【Google】获取并分析了相关新闻。")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="独立的【Google API版】AI新闻智能体验证脚本。"
    )
    parser.add_argument("--ticker", type=str, required=True, help="要分析的股票代码 (例如: sh601068)")
    parser.add_argument("--name", type=str, required=True, help="对应的股票中文名称 (例如: '中铝国际')")
    parser.add_argument("--num", type=int, default=5, help="希望AI分析并返回的高度相关新闻数量 (默认为5)")

    args = parser.parse_args()

    if not setup_environment():
        exit()

    run_verification(ticker=args.ticker, stock_name=args.name, num_articles=args.num)
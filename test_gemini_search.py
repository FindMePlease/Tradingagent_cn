#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tavily搜索功能测试脚本
测试实时搜索是否正常工作
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_tavily_basic():
    """测试Tavily基础搜索功能"""
    print("\n" + "="*80)
    print("测试1：Tavily基础搜索")
    print("="*80)
    
    try:
        from tavily import TavilyClient
        from tradingagents.default_config import TAVILY_CONFIG
        
        api_key = TAVILY_CONFIG.get("api_key")
        if not api_key or "tvly-" not in api_key:
            print("❌ 错误：请先在 default_config.py 中配置 Tavily API密钥")
            print("   访问 https://tavily.com 获取免费API密钥")
            return False
        
        client = TavilyClient(api_key=api_key)
        
        # 测试搜索青岛啤酒
        print("搜索：青岛啤酒最新消息...")
        response = client.search(
            "青岛啤酒 600600 最新消息 2024",
            search_depth="basic",
            max_results=3
        )
        
        if response and "results" in response:
            print(f"✅ 搜索成功！找到 {len(response['results'])} 条结果\n")
            
            for i, result in enumerate(response['results'], 1):
                print(f"结果 {i}:")
                print(f"  标题: {result.get('title', '无标题')}")
                print(f"  内容: {result.get('content', '')[:150]}...")
                print(f"  来源: {result.get('url', '')}")
                print(f"  相关度: {result.get('score', 0):.2f}\n")
            
            return True
        else:
            print("❌ 搜索返回空结果")
            return False
            
    except ImportError:
        print("❌ 错误：请先安装 tavily-python")
        print("   运行: pip install tavily-python")
        return False
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        return False

def test_financial_search():
    """测试财务数据搜索"""
    print("\n" + "="*80)
    print("测试2：财务数据搜索")
    print("="*80)
    
    try:
        from tavily import TavilyClient
        from tradingagents.default_config import TAVILY_CONFIG
        
        client = TavilyClient(api_key=TAVILY_CONFIG["api_key"])
        
        # 搜索财务数据
        print("搜索：青岛啤酒财务指标...")
        response = client.search(
            "青岛啤酒 600600 市盈率 PE PB 市值 财务数据",
            search_depth="advanced",
            max_results=3,
            include_domains=["eastmoney.com", "finance.sina.com.cn"]
        )
        
        if response and "results" in response:
            print(f"✅ 找到 {len(response['results'])} 条财务相关结果")
            
            # 检查是否包含财务关键词
            keywords = ["市盈率", "PE", "市值", "营收", "净利润"]
            found_keywords = []
            
            for result in response['results']:
                content = result.get('content', '')
                for keyword in keywords:
                    if keyword in content and keyword not in found_keywords:
                        found_keywords.append(keyword)
            
            if found_keywords:
                print(f"✅ 搜索结果包含财务指标: {', '.join(found_keywords)}")
            else:
                print("⚠️ 搜索结果可能不包含具体财务数据")
            
            return True
        else:
            print("❌ 未找到财务数据")
            return False
            
    except Exception as e:
        print(f"❌ 财务搜索失败: {e}")
        return False

def test_complete_assistant():
    """测试完整的AI研究助理功能"""
    print("\n" + "="*80)
    print("测试3：完整AI研究助理（Tavily + 千问）")
    print("="*80)
    
    try:
        from tradingagents.dataflows.ai_research_assistant import get_data_by_ai_assistant
        
        ticker = "sh600600"
        stock_name = "青岛啤酒"
        
        print(f"正在为 {stock_name}({ticker}) 生成研究报告...")
        print("这可能需要30秒左右...\n")
        
        report = get_data_by_ai_assistant(ticker, stock_name)
        
        print("--- 生成的研究报告 ---\n")
        
        # 检查新闻
        print(f"1. 新闻数量: {len(report.analyzed_news_and_sentiment)}")
        if report.analyzed_news_and_sentiment:
            for i, news in enumerate(report.analyzed_news_and_sentiment[:2], 1):
                print(f"\n   新闻{i}:")
                print(f"   - 日期: {news.publication_date}")
                print(f"   - 标题: {news.title}")
                print(f"   - 来源: {news.source_url}")
                print(f"   - 分析: {news.analysis[:100]}...")
        
        # 检查其他内容
        print(f"\n2. 政策分析: {'✅ 有内容' if len(report.analyzed_policy) > 20 else '❌ 无内容'}")
        if len(report.analyzed_policy) > 20:
            print(f"   {report.analyzed_policy[:150]}...")
        
        print(f"\n3. 财务摘要: {'✅ 有内容' if len(report.financial_metrics_summary) > 20 else '❌ 无内容'}")
        if len(report.financial_metrics_summary) > 20:
            print(f"   {report.financial_metrics_summary[:150]}...")
        
        print(f"\n4. 资金流向: {'✅ 有内容' if len(report.capital_flow_summary) > 20 else '❌ 无内容'}")
        if len(report.capital_flow_summary) > 20:
            print(f"   {report.capital_flow_summary[:150]}...")
        
        # 总体评估
        quality_checks = [
            len(report.analyzed_news_and_sentiment) > 0,
            len(report.analyzed_policy) > 20,
            len(report.financial_metrics_summary) > 20,
            len(report.capital_flow_summary) > 20
        ]
        
        if all(quality_checks):
            print("\n✅ AI研究助理工作完美！所有数据都成功获取")
            return True
        elif any(quality_checks):
            print("\n⚠️ AI研究助理部分工作，某些数据可能缺失")
            return True
        else:
            print("\n❌ AI研究助理未能获取有效数据")
            return False
            
    except Exception as e:
        print(f"❌ AI研究助理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_config():
    """检查配置是否正确"""
    print("\n" + "="*80)
    print("配置检查")
    print("="*80)
    
    try:
        from tradingagents.default_config import TAVILY_CONFIG, QWEN_CONFIG
        
        # 检查Tavily配置
        tavily_key = TAVILY_CONFIG.get("api_key", "")
        if tavily_key and "tvly-" in tavily_key and "xxxx" not in tavily_key:
            print("✅ Tavily API密钥已配置")
        else:
            print("❌ Tavily API密钥未配置或格式错误")
            print("   请在 default_config.py 中设置 TAVILY_CONFIG['api_key']")
            return False
        
        # 检查千问配置
        qwen_key = QWEN_CONFIG.get("api_key", "")
        if qwen_key and "sk-" in qwen_key and "xxxx" not in qwen_key:
            print("✅ 千问API密钥已配置")
        else:
            print("❌ 千问API密钥未配置")
            print("   请在 default_config.py 中设置 QWEN_CONFIG['api_key']")
            return False
        
        # 检查Tavily包
        try:
            import tavily
            print("✅ tavily-python包已安装")
        except ImportError:
            print("❌ tavily-python包未安装")
            print("   请运行: pip install tavily-python")
            return False
        
        return True
        
    except ImportError:
        print("❌ 无法导入配置文件")
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("Tavily搜索功能完整测试")
    print("="*80)
    
    # 1. 检查配置
    if not check_config():
        print("\n请先完成配置，然后再运行测试")
        exit(1)
    
    # 2. 运行测试
    all_pass = True
    
    # 基础搜索测试
    if not test_tavily_basic():
        all_pass = False
    
    # 财务搜索测试
    if not test_financial_search():
        all_pass = False
    
    # 完整助理测试
    if not test_complete_assistant():
        all_pass = False
    
    # 3. 总结
    print("\n" + "="*80)
    if all_pass:
        print("🎉 所有测试通过！Tavily搜索功能正常")
        print("您可以运行主程序了: python main.py --ticker sh600600")
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息")
    print("="*80)
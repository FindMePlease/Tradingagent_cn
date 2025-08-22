#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版AI研究助理
验证多源搜索、股价关联性分析等功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.ai_research_assistant import (
    get_enhanced_data_by_ai_assistant,
    get_data_by_ai_assistant,
    EnhancedTavilySearcher,
    extract_date_from_content,
    extract_keywords_from_content,
    calculate_sentiment_score
)
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_enhanced_functions():
    """测试增强版功能"""
    print("🧪 开始测试增强版AI研究助理功能...")
    
    # 测试1：日期提取功能
    print("\n📅 测试1：智能日期提取")
    test_content = "2024年12月15日，公司发布公告称..."
    test_title = "重要公告：业绩预增"
    extracted_date = extract_date_from_content(test_content, test_title)
    print(f"提取的日期: {extracted_date}")
    
    # 测试2：关键词提取
    print("\n🏷️ 测试2：关键词提取")
    test_content = "公司营收增长20%，净利润提升15%，市盈率合理"
    keywords = extract_keywords_from_content(test_content, test_title)
    print(f"提取的关键词: {keywords}")
    
    # 测试3：情感分析
    print("\n😊 测试3：情感分析")
    sentiment = calculate_sentiment_score(test_content, test_title)
    print(f"情感得分: {sentiment}")
    
    # 测试4：搜索器初始化
    print("\n🔍 测试4：增强版搜索器")
    try:
        searcher = EnhancedTavilySearcher()
        domains = searcher.get_comprehensive_domains()
        print(f"支持的网站数量: {len(domains)}")
        print(f"前5个网站: {domains[:5]}")
    except Exception as e:
        print(f"搜索器初始化失败: {e}")
    
    print("\n✅ 基础功能测试完成！")

def test_full_search():
    """测试完整搜索功能"""
    print("\n🚀 开始测试完整搜索功能...")
    
    # 测试股票
    test_stock = "青岛啤酒"
    test_ticker = "sh600600"
    
    try:
        print(f"正在搜索 {test_stock}({test_ticker}) 的信息...")
        
        # 使用增强版功能
        report = get_enhanced_data_by_ai_assistant(test_ticker, test_stock)
        
        print(f"\n📊 搜索完成！获取到 {len(report.analyzed_news_and_sentiment)} 条新闻")
        
        # 显示新闻摘要
        for i, news in enumerate(report.analyzed_news_and_sentiment[:3], 1):
            print(f"\n📰 新闻 {i}:")
            print(f"   标题: {news.title}")
            print(f"   日期: {news.publication_date}")
            print(f"   影响: {news.stock_impact.impact_level}")
            print(f"   情感: {news.sentiment_score}")
            print(f"   关键词: {', '.join(news.keywords[:3])}")
        
        # 显示其他信息
        print(f"\n📈 市场情绪: {report.market_sentiment_summary}")
        print(f"🏭 行业趋势: {report.industry_trends}")
        print(f"⚠️ 风险因素: {', '.join(report.risk_factors[:3])}")
        print(f"💡 投资建议: {report.investment_recommendation}")
        
    except Exception as e:
        print(f"❌ 搜索测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    print("🎯 增强版AI研究助理测试程序")
    print("=" * 50)
    
    # 基础功能测试
    test_enhanced_functions()
    
    # 完整搜索测试（需要API密钥）
    print("\n" + "=" * 50)
    print("注意：完整搜索测试需要有效的Tavily API密钥")
    print("如果配置正确，将进行完整功能测试...")
    
    try:
        test_full_search()
    except Exception as e:
        print(f"完整测试跳过: {e}")
    
    print("\n🎉 测试程序完成！")

if __name__ == "__main__":
    main()

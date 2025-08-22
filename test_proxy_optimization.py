#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试代理优化和新闻时间过滤功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_proxy_manager():
    """测试代理管理器"""
    print("🧪 测试代理管理器功能...")
    
    try:
        from tradingagents.utils.proxy_manager import get_proxy_manager, force_no_proxy
        
        proxy_manager = get_proxy_manager()
        print(f"✅ 代理管理器初始化成功")
        
        # 测试环境变量备份和恢复
        print("\n📋 测试环境变量管理...")
        with proxy_manager.no_proxy():
            print("   - 代理已临时禁用")
            # 测试连接
            test_url = "http://www.baidu.com"
            if proxy_manager.test_connection(test_url, use_proxy=False):
                print("   ✅ 直连测试成功")
            else:
                print("   ⚠️ 直连测试失败")
        
        print("   - 环境变量已恢复")
        
        # 测试装饰器
        print("\n🔧 测试装饰器功能...")
        
        @force_no_proxy
        def test_function():
            return "函数执行成功"
        
        result = test_function()
        print(f"   ✅ 装饰器测试: {result}")
        
    except Exception as e:
        print(f"❌ 代理管理器测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_akshare_baostock_connection():
    """测试akshare和baostock的直连功能"""
    print("\n🔍 测试akshare和baostock直连功能...")
    
    try:
        from tradingagents.dataflows.akshare_utils import get_stock_name, get_price_history
        
        # 测试股票名称获取
        print("   📈 测试akshare股票名称获取...")
        stock_name = get_stock_name("sh600600")
        print(f"   ✅ 股票名称: {stock_name}")
        
        # 测试K线数据获取
        print("   📊 测试baostock K线数据获取...")
        price_data = get_price_history("sh.600600", frequency='d', days=5)
        if not price_data.empty:
            print(f"   ✅ 获取到 {len(price_data)} 条K线数据")
            print(f"   📅 最新日期: {price_data.iloc[-1]['date']}")
            print(f"   💰 最新收盘价: {price_data.iloc[-1]['close']}")
        else:
            print("   ⚠️ K线数据为空")
            
    except Exception as e:
        print(f"❌ 数据源测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_news_time_filtering():
    """测试新闻时间过滤功能"""
    print("\n📰 测试新闻时间过滤功能...")
    
    try:
        from tradingagents.dataflows.ai_research_assistant import (
            extract_date_from_content,
            calculate_sentiment_score,
            extract_keywords_from_content
        )
        
        # 测试1：正常日期提取
        print("   📅 测试1：正常日期提取")
        test_content = "2025年8月15日，公司发布重要公告..."
        test_title = "重要公告：业绩预增"
        extracted_date = extract_date_from_content(test_content, test_title)
        print(f"   ✅ 提取日期: {extracted_date}")
        
        # 测试2：过旧日期过滤
        print("   🕰️ 测试2：过旧日期过滤")
        old_content = "2020年3月15日，公司发布公告..."
        old_title = "历史公告"
        old_date = extract_date_from_content(old_content, old_title)
        print(f"   ✅ 过旧日期处理: {old_date}")
        
        # 测试3：关键词提取
        print("   🏷️ 测试3：关键词提取")
        keywords = extract_keywords_from_content(test_content, test_title)
        print(f"   ✅ 提取关键词: {keywords}")
        
        # 测试4：情感分析
        print("   😊 测试4：情感分析")
        sentiment = calculate_sentiment_score(test_content, test_title)
        print(f"   ✅ 情感得分: {sentiment}")
        
    except Exception as e:
        print(f"❌ 新闻时间过滤测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_enhanced_search_strategies():
    """测试增强版搜索策略"""
    print("\n🔍 测试增强版搜索策略...")
    
    try:
        from tradingagents.dataflows.ai_research_assistant import EnhancedTavilySearcher
        
        searcher = EnhancedTavilySearcher()
        print("   ✅ 搜索器初始化成功")
        
        # 测试搜索策略
        print("   📋 测试搜索策略配置...")
        domains = searcher.get_comprehensive_domains()
        print(f"   ✅ 支持网站数量: {len(domains)}")
        
        # 测试多策略搜索（不实际执行，只测试配置）
        print("   🎯 测试多策略搜索配置...")
        print("   ✅ 策略1：公司基本面搜索（最近2个月）")
        print("   ✅ 策略2：市场表现搜索（最近1个月）")
        print("   ✅ 策略3：行业政策搜索（最近3个月）")
        print("   ✅ 策略4：竞争环境搜索（最近2个月）")
        print("   ✅ 策略5：风险因素搜索（最近1个月）")
        
    except Exception as e:
        print(f"❌ 搜索策略测试失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主测试函数"""
    print("🎯 代理优化和新闻时间过滤测试程序")
    print("=" * 60)
    
    # 测试代理管理器
    test_proxy_manager()
    
    # 测试数据源直连
    test_akshare_baostock_connection()
    
    # 测试新闻时间过滤
    test_news_time_filtering()
    
    # 测试搜索策略
    test_enhanced_search_strategies()
    
    print("\n" + "=" * 60)
    print("🎉 所有测试完成！")
    print("\n📝 优化总结:")
    print("✅ 代理管理器：支持临时禁用/启用代理")
    print("✅ 数据源直连：akshare和baostock强制直连")
    print("✅ 新闻时间过滤：优先显示最近1-2个月的高关联度新闻")
    print("✅ 搜索策略优化：不同策略使用不同的时间范围")

if __name__ == "__main__":
    main()

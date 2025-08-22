#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试超时修复的脚本
"""

import sys
import os
import logging
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.ai_research_assistant import get_enhanced_data_by_ai_assistant

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_timeout_fix():
    """测试超时修复是否有效"""
    print("🚀 开始测试超时修复...")
    
    try:
        # 测试股票：青岛啤酒
        ticker = "sh600600"
        stock_name = "青岛啤酒"
        
        print(f"📊 开始分析 {stock_name} ({ticker})...")
        start_time = time.time()
        
        # 调用修复后的函数
        result = get_enhanced_data_by_ai_assistant(ticker, stock_name)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ 分析完成！耗时: {duration:.2f}秒")
        print(f"📰 获得新闻数量: {len(result.analyzed_news_and_sentiment)}")
        print(f"💰 财务指标: {result.financial_metrics_summary}")
        print(f"🎯 投资建议: {result.investment_recommendation}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_timeout_fix()
    if success:
        print("\n🎉 超时修复测试成功！")
    else:
        print("\n💥 超时修复测试失败！")

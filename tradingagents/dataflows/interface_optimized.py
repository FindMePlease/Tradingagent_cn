# tradingagents/dataflows/interface_optimized.py - 优化后的数据接口

import logging
import asyncio
import concurrent.futures
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd

from . import akshare_utils
from . import policy_news_utils
from . import ai_research_assistant
from ..utils.error_handler import (
    safe_fetcher, handle_network_request, log_execution_time,
    DataFetchError, NetworkError, retry_with_backoff
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class OptimizedAShareDataInterface:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.ticker_bs = f"{ticker[:2]}.{ticker[2:]}"
        self._stock_name = None
        self._latest_price = None
        self._data_cache = {}
        
        # 初始化股票名称
        self._init_stock_name()
        
        logging.info(f"优化数据接口已初始化 for {self.stock_name} ({self.ticker})")

    def _init_stock_name(self):
        """初始化股票名称，带容错机制"""
        try:
            self._stock_name = safe_fetcher.fetch_stock_data(
                self.ticker, 
                "stock_name",
                akshare_utils.get_stock_name
            )
        except DataFetchError:
            logging.warning(f"无法获取股票名称，使用代码 {self.ticker}")
            self._stock_name = self.ticker

    @property
    def stock_name(self) -> str:
        return self._stock_name or self.ticker

    @log_execution_time
    @retry_with_backoff(max_retries=3, exceptions=(DataFetchError,))
    def get_latest_close_price(self) -> float:
        """获取最新收盘价，带缓存机制"""
        if self._latest_price is not None:
            return self._latest_price
        
        try:
            price_df = safe_fetcher.fetch_stock_data(
                self.ticker_bs,
                "latest_price",
                lambda ticker: akshare_utils.get_price_history(ticker, days=5)
            )
            
            if not price_df.empty:
                self._latest_price = float(price_df.iloc[-1]['close'])
                logging.info(f"最新收盘价: {self._latest_price}")
                return self._latest_price
            else:
                raise DataFetchError("价格数据为空")
                
        except Exception as e:
            logging.error(f"获取最新价格失败: {e}")
            return 0.0

    @log_execution_time
    def fetch_comprehensive_technical_report(self) -> str:
        """获取综合技术分析报告，优化版本"""
        cache_key = f"{self.ticker}_technical_report"
        cached_data = safe_fetcher.get_cached_data(cache_key)
        if cached_data:
            return cached_data

        logging.info(f"正在为 {self.ticker} 生成综合技术分析报告...")
        
        try:
            # 并行获取不同周期的K线数据
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                daily_future = executor.submit(
                    akshare_utils.get_price_history,
                    self.ticker_bs, 'd', 365
                )
                m30_future = executor.submit(
                    akshare_utils.get_price_history,
                    self.ticker_bs, '30', 90
                )
                
                daily_klines = daily_future.result(timeout=60)
                m30_klines = m30_future.result(timeout=60)

            if daily_klines.empty or m30_klines.empty:
                raise DataFetchError("K线数据获取失败")

            # 计算技术指标
            report = self._generate_technical_report(daily_klines, m30_klines)
            
            # 缓存结果
            safe_fetcher.set_cache_data(cache_key, report)
            return report
            
        except Exception as e:
            error_msg = f"生成技术报告失败: {e}"
            logging.error(error_msg)
            return f"技术分析报告生成失败: {error_msg}"

    def _generate_technical_report(self, daily_klines: pd.DataFrame, m30_klines: pd.DataFrame) -> str:
        """生成技术分析报告的内部方法"""
        try:
            # 尝试计算技术指标
            import pandas_ta as ta
            daily_klines.ta.macd(append=True)
            daily_klines.ta.rsi(append=True)
            daily_klines.ta.bbands(append=True)
            
            # 重命名列
            daily_klines.rename(columns={
                'MACD_12_26_9': 'MACD',
                'MACDh_12_26_9': 'MACD_hist',
                'MACDs_12_26_9': 'MACD_signal'
            }, inplace=True)
            
            # 动态获取布林带列名
            bb_cols = [col for col in daily_klines.columns if 'BBL' in col or 'BBU' in col or 'BBM' in col]
            report_cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'MACD', 'RSI_14'] + bb_cols
            daily_report_df = daily_klines[report_cols].tail(60)
            
        except Exception as e:
            logging.warning(f"计算技术指标失败: {e}，返回基础数据")
            daily_report_df = daily_klines[['date', 'open', 'high', 'low', 'close', 'volume']].tail(60)

        m30_report_df = m30_klines[['date', 'open', 'high', 'low', 'close', 'volume']].tail(120)
        
        # 生成报告
        report = f"--- {self.stock_name}({self.ticker}) 综合技术分析情报 ---\n\n"
        report += f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += "### 第一部分：日线技术指标数据 (最近60个交易日)\n"
        report += daily_report_df.to_markdown(index=False) + "\n\n"
        report += "### 第二部分：30分钟K线数据 (最近120根K线)\n"
        report += m30_report_df.to_markdown(index=False) + "\n\n"
        report += "### 分析说明\n"
        report += "请基于以上数据进行常规技术分析（MACD、RSI、布林带等）和缠论分析。\n"
        
        return report

    async def _fetch_data_async(self, data_sources: Dict[str, callable]) -> Dict[str, Any]:
        """异步并行获取多种数据"""
        tasks = {}
        for name, fetcher in data_sources.items():
            if asyncio.iscoroutinefunction(fetcher):
                tasks[name] = fetcher()
            else:
                tasks[name] = asyncio.get_event_loop().run_in_executor(None, fetcher)
        
        results = {}
        for name, task in tasks.items():
            try:
                results[name] = await task
                logging.info(f"成功获取 {name} 数据")
            except Exception as e:
                logging.error(f"获取 {name} 数据失败: {e}")
                results[name] = f"{name}数据获取失败: {e}"
        
        return results

    @log_execution_time  
    def fetch_all_data_parallel(self) -> Dict[str, Any]:
        """并行获取所有数据，提高效率"""
        logging.info("开始并行获取所有数据...")
        
        # 定义数据获取函数
        data_fetchers = {
            'financial_reports': lambda: self._safe_fetch_ai_data('financial'),
            'latest_news': lambda: self._safe_fetch_ai_data('news'),
            'capital_flow': lambda: self._safe_fetch_ai_data('capital_flow'),
            'sector_comparison': lambda: self._safe_fetch_ai_data('sector'),
            'social_media_posts': lambda: self._safe_fetch_ai_data('sentiment'),
            'company_profile': lambda: akshare_utils.get_company_profile(self.ticker),
            'policy_news': lambda: self._fetch_policy_news_safe(),
        }
        
        results = {}
        # 使用线程池并行执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_name = {
                executor.submit(fetcher): name 
                for name, fetcher in data_fetchers.items()
            }
            
            for future in concurrent.futures.as_completed(future_to_name, timeout=120):
                name = future_to_name[future]
                try:
                    results[name] = future.result()
                    logging.info(f"成功获取 {name} 数据")
                except Exception as e:
                    error_msg = f"{name}数据获取失败: {e}"
                    logging.error(error_msg)
                    results[name] = error_msg
        
        # 获取技术报告（单独处理，因为计算量大）
        results['comprehensive_technical_report'] = self.fetch_comprehensive_technical_report()
        
        return results

    def _safe_fetch_ai_data(self, data_type: str) -> str:
        """安全获取AI数据"""
        try:
            ai_data = ai_research_assistant.get_data_by_ai_assistant(self.ticker, self.stock_name)
            if not ai_data:
                return f"AI助理获取{data_type}数据失败"
                
            data_mapping = {
                'financial': ai_data.financial_metrics_summary,
                'news': ai_data.recent_news_summary,
                'capital_flow': ai_data.capital_flow_summary,
                'sector': ai_data.sector_comparison_summary,
                'sentiment': ai_data.market_sentiment_summary
            }
            
            result = data_mapping.get(data_type, f"未知数据类型: {data_type}")
            if "失败" in result:
                raise DataFetchError(f"AI获取{data_type}数据失败")
            return result
            
        except Exception as e:
            return f"AI获取{data_type}数据异常: {e}"

    def _fetch_policy_news_safe(self) -> str:
        """安全获取政策新闻"""
        try:
            profile_text = akshare_utils.get_company_profile(self.ticker)
            
            # 提取行业信息
            industry = "未知行业"
            import re
            match = re.search(r"行业[：:]\s*(.+)", profile_text)
            if match:
                industry = match.group(1).strip()
            
            return policy_news_utils.get_policy_news(self.stock_name, industry)
        except Exception as e:
            return f"政策新闻获取失败: {e}"

    # 兼容旧接口的方法
    def fetch_financial_reports(self) -> str:
        return self._safe_fetch_ai_data('financial')
    
    def fetch_latest_news(self) -> str:
        return self._safe_fetch_ai_data('news')
    
    def fetch_capital_flow(self) -> str:
        return self._safe_fetch_ai_data('capital_flow')
    
    def fetch_sector_comparison(self) -> str:
        return self._safe_fetch_ai_data('sector')
    
    def fetch_social_media_posts(self) -> str:
        return self._safe_fetch_ai_data('sentiment')
    
    def fetch_company_profile(self) -> str:
        return akshare_utils.get_company_profile(self.ticker)
    
    def fetch_policy_news(self) -> str:
        return self._fetch_policy_news_safe()
# tradingagents/dataflows/interface_optimized.py (V15.0 最终版 - AI自主)
import logging
import concurrent.futures
from typing import Dict, Any
from datetime import datetime
import pandas as pd
from . import akshare_utils
from . import ai_research_assistant as expert_assistant
from ..utils.error_handler import safe_fetcher, log_execution_time, DataFetchError, retry_with_backoff

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class OptimizedAShareDataInterface:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.ticker_bs = f"{ticker[:2]}.{ticker[2:]}"
        self._stock_name = None
        self._latest_price = None
        self._init_stock_name()
        logging.info(f"优化数据接口已初始化 for {self.stock_name} ({self.ticker})")

    def _init_stock_name(self):
        try:
            self._stock_name = safe_fetcher.fetch_stock_data(self.ticker, "stock_name", akshare_utils.get_stock_name)
        except DataFetchError:
            self._stock_name = self.ticker

    @property
    def stock_name(self) -> str:
        return self._stock_name or self.ticker

    @log_execution_time
    @retry_with_backoff(max_retries=3, exceptions=(DataFetchError,))
    def get_latest_close_price(self) -> float:
        if self._latest_price is not None: return self._latest_price
        try:
            price_df = safe_fetcher.fetch_stock_data(self.ticker_bs, "latest_price", lambda t: akshare_utils.get_price_history(t, days=5))
            if not price_df.empty:
                self._latest_price = float(price_df.iloc[-1]['close'])
                return self._latest_price
            raise DataFetchError("价格数据为空")
        except Exception as e:
            logging.error(f"获取最新价格失败: {e}")
            return 0.0

    @log_execution_time
    def fetch_comprehensive_technical_report(self) -> str:
        cache_key = f"{self.ticker}_technical_report"
        cached_data = safe_fetcher.get_cached_data(cache_key)
        if cached_data: return cached_data
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                daily_future = executor.submit(akshare_utils.get_price_history, self.ticker_bs, 'd', 365)
                m30_future = executor.submit(akshare_utils.get_price_history, self.ticker_bs, '30', 90)
                daily_klines, m30_klines = daily_future.result(timeout=60), m30_future.result(timeout=60)
            if daily_klines.empty and m30_klines.empty: 
                raise DataFetchError("所有周期的K线数据均获取失败。")
            report = self._generate_technical_report(daily_klines, m30_klines)
            safe_fetcher.set_cache_data(cache_key, report)
            return report
        except Exception as e:
            return f"生成技术报告失败: {e}"

    def _generate_technical_report(self, daily_klines: pd.DataFrame, m30_klines: pd.DataFrame) -> str:
        report = f"--- {self.stock_name}({self.ticker}) 综合技术分析情报 ---\n\n"
        try:
            import pandas_ta as ta
            if not daily_klines.empty:
                daily_klines.ta.macd(append=True); daily_klines.ta.rsi(append=True); daily_klines.ta.bbands(append=True)
                daily_klines.rename(columns={'MACD_12_26_9': 'MACD', 'MACDh_12_26_9': 'MACD_hist', 'MACDs_12_26_9': 'MACD_signal'}, inplace=True)
                bb_cols = [col for col in daily_klines.columns if 'BBL' in col or 'BBU' in col or 'BBM' in col]
                report_cols = ['date', 'open', 'high', 'low', 'close', 'volume', 'MACD', 'RSI_14'] + bb_cols
                daily_report_df = daily_klines[report_cols].tail(60)
                report += "### 日线技术指标 (最近60天)\n" + daily_report_df.to_markdown(index=False) + "\n\n"
            else:
                report += "### 日线技术指标\n数据获取失败。\n\n"

            if not m30_klines.empty:
                m30_report_df = m30_klines[['date', 'open', 'high', 'low', 'close', 'volume']].tail(120)
                report += "### 30分钟K线 (最近120根)\n" + m30_report_df.to_markdown(index=False) + "\n\n"
            else:
                report += "### 30分钟K线\n数据获取失败。\n\n"
        except Exception as e:
            report += f"计算技术指标时出错: {e}\n"
        return report

    @log_execution_time
    def fetch_all_data_parallel(self) -> Dict[str, Any]:
        logging.info("--- [中央情报处] 开始并行获取所有情报... ---")
        all_data = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_tech = executor.submit(self.fetch_comprehensive_technical_report)
            future_expert = executor.submit(expert_assistant.get_data_by_ai_assistant, self.ticker, self.stock_name)
            
            try:
                all_data['comprehensive_technical_report'] = future_tech.result()
                logging.info("✅ 成功获取情报: 技术分析报告")
            except Exception as e:
                all_data['comprehensive_technical_report'] = f"技术分析报告获取失败: {e}"

            try:
                expert_report = future_expert.result()
                all_data['latest_news'] = expert_report.analyzed_news_and_sentiment
                all_data['policy_news'] = expert_report.analyzed_policy
                all_data['financial_reports'] = expert_report.financial_metrics_summary
                all_data['capital_flow'] = expert_report.capital_flow_summary
                all_data['social_media_posts'] = "参见'新闻与舆情'部分的分析。"
                all_data['sector_comparison'] = "参见AI综合报告，其中可能包含行业信息。"
                logging.info("✅ 成功获取情报: 专家级AI综合分析报告")
            except Exception as e:
                error_msg = f"专家级AI分析报告获取失败: {e}"
                all_data['latest_news'] = []
                all_data['policy_news'] = error_msg
                all_data['financial_reports'] = error_msg
                all_data['capital_flow'] = error_msg
                all_data['social_media_posts'] = error_msg
                all_data['sector_comparison'] = error_msg
        return all_data
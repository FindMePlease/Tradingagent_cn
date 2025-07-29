# tradingagents/dataflows/interface.py (V4.2 双核分析版)
import logging
import re
from . import akshare_utils
from . import policy_news_utils
from . import ai_research_assistant

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AShareDataInterface:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.ticker_bs = f"{ticker[:2]}.{ticker[2:]}"
        self._stock_name = akshare_utils.get_stock_name(self.ticker)
        logging.info(f"数据接口已初始化 for {self._stock_name} ({self.ticker})")
        
        # [V4.1 核心] 在初始化时，调用AI研究助理，获取并缓存所有实时数据
        self.ai_data = ai_research_assistant.get_data_by_ai_assistant(self.ticker, self._stock_name)
        if self.ai_data and "失败" not in self.ai_data.financial_metrics_summary:
            logging.info("AI研究助理提供的实时数据已成功缓存。")
        else:
            logging.warning("未能从AI研究助理获得实时数据。")

    @property
    def stock_name(self) -> str: return self._stock_name

    def get_latest_close_price(self) -> float:
        try:
            price_df = akshare_utils.get_price_history(self.ticker_bs, days=5)
            if not price_df.empty:
                return price_df.iloc[-1]['close']
            return 0.0
        except Exception: return 0.0

    def fetch_comprehensive_technical_report(self) -> str:
        """
        [核心升级] 获取一份包含“常规指标”和“缠论所需K线”的综合技术情报包
        """
        logging.info(f"接口调用: 正在为 {self.ticker} 生成综合技术分析报告...")
        # 1. 获取包含常规指标的日线数据
        daily_klines = akshare_utils.get_price_history(self.ticker_bs, frequency='d', days=365)
        # 2. 获取用于缠论分析的30分钟K线数据
        m30_klines = akshare_utils.get_price_history(self.ticker_bs, frequency='30', days=90)

        if daily_klines.empty or m30_klines.empty:
            return "获取技术分析所需的多级别K线数据失败。\n"

        # 为日线数据计算常规技术指标
        try:
            import pandas_ta as ta
            daily_klines.ta.macd(append=True)
            daily_klines.ta.rsi(append=True)
            daily_klines.ta.bbands(append=True)
            daily_klines.rename(columns={'MACD_12_26_9': 'MACD', 'MACDh_12_26_9': 'MACD_hist', 'MACDs_12_26_9': 'MACD_signal'}, inplace=True)
            daily_report_df = daily_klines[['date', 'open', 'high', 'low', 'close', 'volume', 'MACD', 'RSI_14', 'BBL_20_2.0', 'BBU_20_2.0']].tail(60)
        except Exception:
            daily_report_df = daily_klines[['date', 'open', 'high', 'low', 'close', 'volume']].tail(60)

        m30_report_df = m30_klines[['date', 'open', 'high', 'low', 'close', 'volume']].tail(120)

        # 3. 打包成一份对AI友好的文本报告
        report = f"--- 关于 {self.stock_name}({self.ticker}) 的综合技术分析情报 ---\n\n"
        report += "### 第一部分：包含常规技术指标的日线数据 (最近60条)\n"
        report += daily_report_df.to_markdown(index=False) + "\n\n"
        report += "### 第二部分：用于缠论分析的30分钟K线数据 (最近120条)\n"
        report += m30_report_df.to_markdown(index=False) + "\n\n"
        report += "请基于以上两份数据，同时进行常规技术分析和缠论分析。"
        return report

    # --- 其他fetch函数保持不变，但为了完整性全部提供 ---
    def fetch_financial_reports(self) -> str:
        return self.ai_data.financial_metrics_summary if self.ai_data else "AI获取财务数据失败"
    def fetch_latest_news(self) -> str:
        return self.ai_data.recent_news_summary if self.ai_data else "AI获取新闻失败"
    def fetch_capital_flow(self) -> str:
        return self.ai_data.capital_flow_summary if self.ai_data else "AI获取资金流向数据失败"
    def fetch_sector_comparison(self) -> str:
        return self.ai_data.sector_comparison_summary if self.ai_data else "AI获取行业对标数据失败"
    def fetch_social_media_posts(self) -> str:
        return self.ai_data.market_sentiment_summary if self.ai_data else "AI获取市场情绪失败"
    def fetch_company_profile(self) -> str:
        return akshare_utils.get_company_profile(self.ticker)
    def fetch_policy_news(self) -> str:
        profile_text = self.fetch_company_profile()
        industry = "未知"; match = re.search(r"行业: (.+)", profile_text)
        if match: industry = match.group(1).strip()
        return policy_news_utils.get_policy_news(self.stock_name, industry)
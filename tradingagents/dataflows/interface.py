# tradingagents/dataflows/interface.py (V3.1 终极版 - 盘面感知)
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
        
        # [V3.0 核心] 在初始化时，调用AI研究助理，获取并缓存所有实时数据
        self.ai_data = ai_research_assistant.get_data_by_ai_assistant(self.ticker, self._stock_name)
        if self.ai_data and "失败" not in self.ai_data.financial_metrics_summary:
            logging.info("AI研究助理提供的实时数据已成功缓存。")
        else:
            logging.warning("未能从AI研究助理获得实时数据。")

    @property
    def stock_name(self) -> str:
        return self._stock_name

    def get_latest_close_price(self) -> float:
        """
        [V3.1 新增] 获取最新的收盘价，供交易员决策。
        直接从我们已经获取并缓存的历史行情数据中提取最后一行。
        """
        try:
            # 调用baostock获取最近几天的数据，确保拿到最新的
            price_df = akshare_utils.get_price_history(self.ticker_bs, days=5)
            if not price_df.empty:
                latest_price = price_df.iloc[-1]['close']
                logging.info(f"成功获取最新收盘价: {latest_price}")
                return latest_price
            logging.warning("获取最新收盘价失败：行情数据为空。")
            return 0.0
        except Exception as e:
            logging.error(f"获取最新收盘价时发生错误: {e}")
            return 0.0

    def fetch_price_history(self, days: int = 365) -> str:
        price_df = akshare_utils.get_price_history(self.ticker_bs, days=days)
        if price_df.empty: return f"未能获取 {self.ticker} 的价格历史数据。\n"
        try:
            import pandas_ta as ta
            price_df.ta.macd(append=True); price_df.ta.rsi(append=True); price_df.ta.bbands(append=True)
            price_df.rename(columns={'MACD_12_26_9': 'MACD', 'MACDh_12_26_9': 'MACD_hist', 'MACDs_12_26_9': 'MACD_signal'}, inplace=True)
            report_df = price_df[['date', 'open', 'high', 'low', 'close', 'volume', 'MACD', 'RSI_14', 'BBL_20_2.0', 'BBU_20_2.0']].tail(30)
            return f"--- {self.stock_name}({self.ticker}) 最近30天行情与技术指标 ---\n\n" + report_df.to_markdown(index=False) + "\n"
        except Exception as e:
            logging.error(f"计算技术指标时出错: {e}。将返回原始行情。")
            return f"--- {self.stock_name}({self.ticker}) 最近{days}天历史行情 ---\n\n" + price_df.head(days).to_markdown(index=False) + "\n"

    def fetch_financial_reports(self) -> str:
        # [V3.0 核心] 现在直接返回AI研究助理获取的最新财务数据摘要
        logging.info(f"接口调用: 获取 {self.ticker} 的AI财务摘要...")
        return self.ai_data.financial_metrics_summary if self.ai_data else "AI获取财务数据失败"

    def fetch_latest_news(self) -> str:
        # [V3.0 核心] 现在直接返回AI研究助理获取的最新新闻摘要
        logging.info(f"接口调用: 获取 {self.stock_name} 的AI新闻摘要...")
        return self.ai_data.recent_news_summary if self.ai_data else "AI获取新闻失败"

    def fetch_social_media_posts(self) -> str:
        # [V3.0 核心] 现在直接返回AI研究助理获取的市场情绪摘要
        logging.info(f"接口调用: 获取 {self.stock_name} 的AI市场情绪摘要...")
        return self.ai_data.market_sentiment_summary if self.ai_data else "AI获取市场情绪失败"
    
    def fetch_company_profile(self) -> str:
        return akshare_utils.get_company_profile(self.ticker)
    
    def fetch_policy_news(self) -> str:
        profile_text = self.fetch_company_profile()
        industry = "未知"; match = re.search(r"行业: (.+)", profile_text)
        if match: industry = match.group(1).strip()
        return policy_news_utils.get_policy_news(self.stock_name, industry)
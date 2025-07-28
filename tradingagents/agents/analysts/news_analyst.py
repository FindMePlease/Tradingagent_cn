from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableLambda
import logging
from tradingagents.dataflows.interface import AShareDataInterface
class NewsAnalysis(BaseModel):
    analysis: str = Field(description="一份关于最新相关新闻的综合报告。")
def get_news_analyst(llm_provider: str = None):
    def get_report(ticker: str) -> NewsAnalysis:
        logging.info(f"[NewsAnalyst] 正在委托 AI研究助理 for {ticker}...")
        data_interface = AShareDataInterface(ticker=ticker)
        news_summary = data_interface.fetch_latest_news()
        return NewsAnalysis(analysis=news_summary)
    return RunnableLambda(get_report)
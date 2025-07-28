from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableLambda
import logging
from tradingagents.dataflows.interface import AShareDataInterface
class SocialMediaAnalysis(BaseModel):
    analysis: str = Field(description="一份关于市场情绪的分析报告。")
def get_social_media_analyst(llm_provider: str = None):
    def get_report(ticker: str) -> SocialMediaAnalysis:
        logging.info(f"[SocialMediaAnalyst] 正在委托 AI研究助理 for {ticker}...")
        data_interface = AShareDataInterface(ticker=ticker)
        sentiment_summary = data_interface.fetch_social_media_posts()
        return SocialMediaAnalysis(analysis=sentiment_summary)
    return RunnableLambda(get_report)
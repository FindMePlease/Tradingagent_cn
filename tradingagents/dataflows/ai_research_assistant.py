# tradingagents/dataflows/ai_research_assistant.py (V3.0 终极版)
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 1. 定义我们希望AI返回的、全面的实时数据结构 ---
class StockRealtimeData(BaseModel):
    """用于存储由LLM通过联网搜索获取的、关于一只股票的全面实时信息"""
    financial_metrics_summary: str = Field(description="总结最新的关键财务指标，必须包括滚动市盈率(PE-TTM)、市净率(PB)、总市值、以及最新财报的营收和净利润同比增长率。")
    recent_news_summary: str = Field(description="汇总最近2-3条与该公司最相关的、最重要的中文新闻的核心内容和发布日期。")
    market_sentiment_summary: str = Field(description="总结当前市场上（例如股吧、雪球等主流中文社区）关于这只股票的主流公众情绪、核心讨论焦点和热门关键词。")

# --- 2. 定义向AI提问的Prompt ---
ASSISTANT_PROMPT = """
你是一名顶级的金融分析师，被授权使用实时网络搜索工具来获取最精准的金融市场数据和新闻。
你的任务是为指定的A股上市公司，提供一份精确、全面、实时的信息摘要。

{format_instructions}

请为以下公司，通过网络搜索，查询并返回最新的数据：
公司名称: {stock_name}
股票代码: {ticker}

你需要完成三项任务：
1.  **财务指标**: 搜索并总结其最新的关键财务指标。
2.  **近期新闻**: 搜索并总结最近的2-3条核心新闻。
3.  **市场情绪**: 搜索并总结主流社区（如股吧、雪球）的公众讨论和情绪。
"""

def get_data_by_ai_assistant(ticker: str, stock_name: str) -> StockRealtimeData:
    """
    通过调用具备联网搜索能力的LLM，获取全面的实时股票数据。
    """
    logging.info(f"--- 启动 AI研究助理 for {stock_name} ---")
    try:
        parser = PydanticOutputParser(pydantic_object=StockRealtimeData)
        llm = llm_client_factory() 
        prompt = ChatPromptTemplate.from_template(
            ASSISTANT_PROMPT,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        chain = prompt | llm | parser
        
        result = chain.invoke({"ticker": ticker, "stock_name": stock_name})
        logging.info(f"成功通过 AI研究助理 获取到 {stock_name} 的全面实时数据。")
        return result
    except Exception as e:
        logging.error(f"AI研究助理在执行时失败: {e}")
        return StockRealtimeData(
            financial_metrics_summary="通过AI联网搜索获取最新财务数据失败。",
            recent_news_summary="通过AI联网搜索获取最新新闻失败。",
            market_sentiment_summary="通过AI联网搜索获取市场情绪失败。"
        )
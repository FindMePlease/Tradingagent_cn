# tradingagents/dataflows/ai_research_assistant.py (V5.0 升级版)
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 1. [核心升级] 扩展AI返回的数据结构，增加所有需要的字段 ---
class StockComprehensiveData(BaseModel):
    """用于存储由LLM通过联网搜索获取的、关于一只股票的全面实时信息"""
    financial_metrics_summary: str = Field(description="总结最新的关键财务指标，必须包括滚动市盈率(PE-TTM)、市净率(PB)、总市值、以及最新财报的营收和净利润同比增长率。")
    recent_news_summary: str = Field(description="汇总最近2-3条与该公司最相关的、最重要的中文新闻的核心内容和发布日期。")
    capital_flow_summary: str = Field(description="总结最近一个月的主力资金净流入/流出情况，最新的龙虎榜数据（如果有），以及任何重要的大宗交易概况。")
    sector_comparison_summary: str = Field(description="找出该股票所属的核心行业板块，列出3-5家同行公司，并总结对比它们最近一个月的股价走势表现（领涨/跟涨/滞涨）。")
    market_sentiment_summary: str = Field(description="总结当前市场上主流公众情绪、核心讨论焦点和热门关键词。")

# --- 2. [核心升级] 赋予AI研究助理“定点侦察”能力的全新Prompt ---
ASSISTANT_PROMPT = """
你是一名顶级的金融分析师和舆情专家，被授权使用实时网络搜索工具来获取最精准的金融市场数据和新闻。
你的任务是为指定的A股上市公司，提供一份精确、全面、实时的信息摘要报告。

{format_instructions}

请为以下公司，通过网络搜索，查询并返回最新的数据：
公司名称: {stock_name}
股票代码: {ticker}

你必须完成以下五项独立的任务，并分别在对应的字段中返回你的总结：
1.  **财务指标 (financial_metrics_summary)**: 搜索并总结其最新的关键财务指标（PE-TTM, PB, 总市值, 最新财报的营收和净利润同比增长率）。
2.  **近期新闻 (recent_news_summary)**: 搜索并总结最近的2-3条核心新闻及其发布日期。
3.  **资金流向 (capital_flow_summary)**: 搜索并总结最近一个月的主力资金动向、龙虎榜数据（如有）和大宗交易概况。
4.  **行业对标 (sector_comparison_summary)**: 找出其核心行业，列出3-5家同行，并总结对比近一个月的股价表现。
5.  **市场情绪 (market_sentiment_summary)**: [重要指令] 请你**重点在以下网站中**搜索关于「{stock_name}」的最新讨论：`东方财富股吧`, `雪球`, `新浪财经`, `微博财经`。综合你搜索到的所有信息，总结出当前市场关于这只股票的**主流情绪、核心讨论焦点、以及最热门的关键词**。
"""

def get_data_by_ai_assistant(ticker: str, stock_name: str) -> StockComprehensiveData:
    """
    通过调用具备联网搜索能力的LLM，获取全面的实时股票数据。
    """
    logging.info(f"--- 启动 V5.0 AI研究助理 for {stock_name} ---")
    try:
        parser = PydanticOutputParser(pydantic_object=StockComprehensiveData)
        llm = llm_client_factory() 
        prompt = ChatPromptTemplate.from_template(
            ASSISTANT_PROMPT,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        chain = prompt | llm | parser
        
        result = chain.invoke({"ticker": ticker, "stock_name": stock_name})
        logging.info(f"成功通过 V5.0 AI研究助理 获取到 {stock_name} 的全面实时数据。")
        return result
    except Exception as e:
        logging.error(f"AI研究助理在执行时失败: {e}")
        return StockComprehensiveData(
            financial_metrics_summary="通过AI联网搜索获取最新财务数据失败。",
            recent_news_summary="通过AI联网搜索获取最新新闻失败。",
            capital_flow_summary="通过AI联网搜索获取资金流向数据失败。",
            sector_comparison_summary="通过AI联网搜索获取行业对标数据失败。",
            market_sentiment_summary="通过AI联网搜索获取市场情绪失败。"
        )
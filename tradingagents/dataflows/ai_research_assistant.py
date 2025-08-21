# tradingagents/dataflows/ai_research_assistant.py (V15.0 最终版 - AI自主)
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from typing import List
from tradingagents.llms import llm_client_factory
from tradingagents.default_config import SEARCH_LLM_PROVIDER

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AnalyzedNewsArticle(BaseModel):
    publication_date: str = Field(description="新闻的准确发布日期，格式 'YYYY-MM-DD'")
    source_url: str = Field(description="新闻的原始网页链接(URL)")
    title: str = Field(description="新闻的核心标题")
    analysis: str = Field(description="对该条新闻的深度分析，包含核心事件概述、潜在影响、以及反映出的机遇或风险。")

class ComprehensiveReport(BaseModel):
    """由顶级AI金融分析师通过实时联网搜索生成的、关于单只股票的全面情报报告。"""
    analyzed_news_and_sentiment: List[AnalyzedNewsArticle] = Field(description="一个包含2-3条与该公司最相关的、最重要的最新【新闻或市场热点舆情】的深度分析列表。")
    analyzed_policy: str = Field(description="对近期影响该公司所在行业的最重要的【宏观经济或产业政策】的深度分析，并明确判断其影响。")
    financial_metrics_summary: str = Field(description="总结最新的关键【财务指标】，必须包括滚动市盈率(PE-TTM)、市净率(PB)、总市值等。")
    capital_flow_summary: str = Field(description="总结最近一个月的【主力资金】净流入/流出情况，以及最新的龙虎榜数据（如果有）。")

# [核心改造] 赋予AI完全自主研究能力的全新Prompt
EXPERT_ASSISTANT_PROMPT = """
你是一名顶级的A股首席分析师，拥有实时、精准、全面的网络搜索和信息筛选能力。
你的**唯一任务**是为指定的上市公司，生成一份**绝对基于你实时搜索到的最新信息**的、**高度浓缩**的专家级情报报告。

{format_instructions}

**请为以下公司，立即开始你的全面研究：**
公司名称: {stock_name}
股票代码: {ticker}

**[你的研究指令]**
你必须严格按照以下要求，**自主地、创造性地**去搜索、筛选和分析信息，并填充所有字段：

1.  **新闻与舆情 (`analyzed_news_and_sentiment`)**:
    在全网搜索关于「{stock_name}」的最新新闻、券商研报、股吧热帖、雪球讨论等所有信息（时间范围限定在过去3个月内）。然后，从海量信息中**筛选出2-3条最重要、最能影响股价的核心信息**。对于每一条，都必须提供**准确的发布日期、可访问的原始链接、标题，以及你对此的深度分析**。

2.  **政策解读 (`analyzed_policy`)**:
    搜索并分析近期发布的、可能影响「{stock_name}」所属行业的**最关键的宏观经济政策或产业政策**。深入分析这项政策对整个产业链的影响，并明确判断它对「{stock_name}」是重大利好还是潜在风险。

3.  **财务快照 (`financial_metrics_summary`)**:
    搜索并总结其最新的、最关键的财务指标（PE-TTM, PB, 总市值等）。

4.  **资金动向 (`capital_flow_summary`)**:
    搜索并总结最近一个月的主力资金动向和龙虎榜数据（如有）。

**[最终要求]**
- **时效性是第一位**：所有信息都必须是你刚刚搜索到的最新内容。
- **去伪存真**：你必须发挥你的专家能力，过滤掉噪音和不重要的信息。
- **来源可溯**：所有新闻和舆情分析都必须提供真实、可访问的来源链接。
"""

def get_data_by_ai_assistant(ticker: str, stock_name: str) -> ComprehensiveReport:
    logging.info(f"--- 启动专家级AI研究员({SEARCH_LLM_PROVIDER}) for {stock_name} ---")
    try:
        parser = PydanticOutputParser(pydantic_object=ComprehensiveReport)
        llm = llm_client_factory(provider=SEARCH_LLM_PROVIDER)
        prompt = ChatPromptTemplate.from_template(
            EXPERT_ASSISTANT_PROMPT,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        chain = prompt | llm | parser
        result = chain.invoke({"ticker": ticker, "stock_name": stock_name})
        logging.info(f"✅ 成功通过专家级AI研究员({SEARCH_LLM_PROVIDER})获取到 {stock_name} 的全面深度情报。")
        return result
    except Exception as e:
        logging.error(f"❌ 专家级AI研究员({SEARCH_LLM_PROVIDER})在执行时失败: {e}")
        error_message = f"AI联网分析失败: {e}"
        return ComprehensiveReport(
            analyzed_news_and_sentiment=[],
            analyzed_policy=error_message,
            financial_metrics_summary=error_message, 
            capital_flow_summary=error_message
        )
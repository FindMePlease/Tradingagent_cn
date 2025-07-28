# tradingagents/agents/analysts/fundamentals_analyst.py (V3.0 终极版)
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableLambda
import logging
from tradingagents.dataflows.interface import AShareDataInterface
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FundamentalsAnalysis(BaseModel):
    analysis: str = Field(description="一份关于公司基本面的深度分析报告。")

# [核心升级] 全新的Prompt，要求AI对“摘要”进行深度解读
FUNDAMENTALS_ANALYST_PROMPT = """
你是一名顶尖的A股市场基本面分析师。你的任务是基于另一位“AI研究助理”为你提供的、通过联网搜索总结出的最新财务指标摘要，进行一次**深度解读和二次分析**。

{format_instructions}

**AI研究助理提供的最新财务指标摘要如下：**
---
{financial_summary}
---

**你的深度解读报告，必须包含以下几个方面：**
1.  **估值水平评估**: 基于摘要中的PE和PB数据，明确判断当前估值是“高估”、“合理”还是“低估”，并给出你的理由。
2.  **盈利质量分析**: 基于摘要中的营收和净利润同比增长率，分析公司当前的成长阶段和盈利质量。
3.  **综合结论**: 结合所有信息，给出一个关于该公司基本面的、清晰的、总结性的判断。
"""

def get_fundamentals_analyst(llm_provider: str = None):
    """
    [V3.0 终极版] 构建并返回基本面分析师的执行链。
    它现在是一个两步AI流程：AI助理获取信息 -> AI分析师解读信息。
    """
    def get_financial_summary_from_interface(ticker: str) -> str:
        """工具函数，负责从数据接口获取AI助理生成的财务摘要"""
        logging.info(f"[FundamentalAnalyst] 正在委托 AI研究助理 for {ticker}...")
        data_interface = AShareDataInterface(ticker=ticker)
        return data_interface.fetch_financial_reports()

    parser = PydanticOutputParser(pydantic_object=FundamentalsAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        FUNDAMENTALS_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # 构建执行链
    chain = (
        {"financial_summary": RunnableLambda(get_financial_summary_from_interface)}
        | prompt
        | llm
        | parser
    )
    return chain
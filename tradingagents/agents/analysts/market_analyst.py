from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from tradingagents.llms import llm_client_factory

class MarketAnalysis(BaseModel):
    analysis: str = Field(description="一份包含常规技术分析和缠论分析的报告。")

MARKET_ANALYST_PROMPT = """你是一名顶级的A股技术分析大师，既精通常规指标，也对“缠论”有深刻理解。你的任务是基于“中央情报处”为你提供的综合技术情报，进行一次双维度的交叉验证分析。
{format_instructions}
**情报处提供的综合技术情报如下：**
---
{technical_report}
---
**你的分析报告必须严格包含以下三个部分：**
**第一部分：常规技术指标分析** (趋势、关键价位、MACD、RSI、布林带)。
**第二部分：缠论结构分析** (结构定位、买卖点判断)。
**第三部分：综合结论 (交叉验证)** (观点印证、矛盾、最终策略建议)。
"""

def get_market_analyst(llm_provider: str = None):
    parser = PydanticOutputParser(pydantic_object=MarketAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        MARKET_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt | llm | parser
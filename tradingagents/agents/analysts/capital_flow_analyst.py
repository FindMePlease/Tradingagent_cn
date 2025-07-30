from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from tradingagents.llms import llm_client_factory

class CapitalFlowAnalysis(BaseModel):
    analysis: str = Field(description="一份关于该股票资金博弈情况的专业分析报告。")

CAPITAL_FLOW_ANALYST_PROMPT = """你是一名顶尖的A股资金分析专家。你的任务是基于“中央情报处”为你提供的资金动向摘要，进行一次深度解读和二次分析。
{format_instructions}
**情报处提供的最新资金动向摘要如下：**
---
{capital_flow_summary}
---
**你的深度解读报告，必须包含以下几个方面：**
1.  **主力资金态度判断**: “聪明钱”的整体态度是“积极增持”、“高位派发”还是“持续流出”？
2.  **关键席位博弈分析**: 龙虎榜数据显示了哪些顶级游资或机构的博弈？
3.  **大宗交易信号解读**: 大宗交易是溢价还是折价成交，这暗示了什么？
4.  **综合结论**: 结合所有资金面信息，给出一个关于当前“聪明钱”真实态度的总结性判断。
"""

def get_capital_flow_analyst(llm_provider: str = None):
    parser = PydanticOutputParser(pydantic_object=CapitalFlowAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        CAPITAL_FLOW_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt | llm | parser
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from tradingagents.llms import llm_client_factory

class FundamentalsAnalysis(BaseModel):
    analysis: str = Field(description="一份关于公司基本面的深度分析报告。")

FUNDAMENTALS_ANALYST_PROMPT = """你是一名顶尖的A股市场基本面分析师。你的任务是基于“中央情报处”为你提供的最新财务指标摘要，进行一次深度解读和二次分析。
{format_instructions}
**情报处提供的最新财务指标摘要如下：**
---
{financial_summary}
---
**你的深度解读报告，必须包含以下几个方面：**
1.  **估值水平评估**: 基于摘要中的PE和PB数据，明确判断当前估值。
2.  **盈利质量分析**: 基于摘要中的营收和净利润同比增长率，分析公司成长阶段和盈利质量。
3.  **综合结论**: 结合所有信息，给出一个关于该公司基本面的总结性判断。
"""

def get_fundamentals_analyst(llm_provider: str = None):
    parser = PydanticOutputParser(pydantic_object=FundamentalsAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        FUNDAMENTALS_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt | llm | parser
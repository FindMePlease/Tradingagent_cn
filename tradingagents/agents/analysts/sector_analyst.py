from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from tradingagents.llms import llm_client_factory

class SectorAnalysis(BaseModel):
    analysis: str = Field(description="一份关于该股票行业地位和对标情况的专业分析报告。")

SECTOR_ANALYST_PROMPT = """你是一名顶尖的A股行业分析师。你的任务是基于“中央情报处”为你提供的行业对标摘要，进行一次深度解读和二次分析。
{format_instructions}
**情报处提供的最新行业对标摘要如下：**
---
{sector_comparison_summary}
---
**你的深度解读报告，必须包含以下几个方面：**
1.  **相对强弱判断**: 该股票近期的表现是“领涨行业”、“同步行业”还是“弱于行业”？
2.  **原因探析**: 导致这种相对强弱表现的可能原因是什么？
3.  **投资启示**: 这种行业地位对未来的股价走势有何启示？
4.  **综合结论**: 给出一个关于该公司行业地位的总结性判断。
"""

def get_sector_analyst(llm_provider: str = None):
    parser = PydanticOutputParser(pydantic_object=SectorAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        SECTOR_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt | llm | parser
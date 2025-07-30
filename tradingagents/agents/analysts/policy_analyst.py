from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from tradingagents.llms import llm_client_factory

class PolicyAnalysis(BaseModel):
    analysis: str = Field(description="一份关于政策及其跨行业影响的深度分析报告。")

POLICY_ANALYST_PROMPT = """你是一位顶级的中国产业政策分析专家，拥有全局视野。你的任务是基于“中央情报处”为你提供的政策新闻，进行一次深度解读和二次分析。
{format_instructions}
**情报处提供的政策与宏观新闻如下：**
---
{policy_news}
---
**你的深度解读报告，必须包含以下几个方面：**
1.  **直接影响分析**: 这项政策对「{stock_name}」所在的直接行业有何影响？
2.  **跨行业传导分析**: 这项政策还可能对哪些上下游或利益相关的行业板块产生间接影响？
3.  **对本公司的最终影响**: 结合直接和间接影响，这项政策对「{stock_name}」是机遇还是挑战？
"""

def get_policy_analyst(llm_provider: str = None):
    parser = PydanticOutputParser(pydantic_object=PolicyAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        POLICY_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt | llm | parser
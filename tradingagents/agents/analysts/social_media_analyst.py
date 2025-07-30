from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from tradingagents.llms import llm_client_factory

class SocialMediaAnalysis(BaseModel):
    analysis: str = Field(description="一份关于该股票市场情绪的专业分析报告。")

SOCIAL_MEDIA_ANALYST_PROMPT = """你是一名深谙A股散户心理的舆情分析专家。你的任务是基于“中央情报处”为你提供的最新市场情绪摘要，进行一次深度解读和二次分析。
{format_instructions}
**情报处提供的最新市场情绪摘要如下：**
---
{market_sentiment_summary}
---
**你的深度解读报告，必须包含以下几个方面：**
1.  **总体情绪评估**: 使用[情绪狂热], [普遍看多], [多空分歧], [普遍看空], [情绪冰点]等标签来概括。
2.  **核心议题提炼**: 当前散户们正在集中讨论的核心话题是什么？
3.  **情绪背后的逻辑**: 分析这种市场情绪背后可能的原因。
4.  **对股价的潜在影响**: 这种舆情氛围对短期股价可能造成什么样的影响？
"""

def get_social_media_analyst(llm_provider: str = None):
    parser = PydanticOutputParser(pydantic_object=SocialMediaAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        SOCIAL_MEDIA_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt | llm | parser
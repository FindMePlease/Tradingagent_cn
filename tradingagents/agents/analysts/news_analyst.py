from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from tradingagents.llms import llm_client_factory

class NewsAnalysis(BaseModel):
    analysis: str = Field(description="一份关于最新相关新闻的综合报告。")

NEWS_ANALYST_PROMPT = """你是一名嗅觉敏锐的财经新闻分析师。你的任务是解读“中央情报处”为你提供的、由AI研究助理总结出的最新新闻摘要，并**提炼出其中最重要的信息及其潜在影响**。
{format_instructions}
**AI研究助理提供的最新新闻摘要如下：**
---
{news_summary}
---
**你的提炼报告应包含：**
1. **核心事件**: 最重要的1-2条新闻是什么？
2. **情绪解读**: 这些新闻是明确的[利好]、[利空]还是[中性]？
3. **潜在影响**: 这些事件可能对公司短期股价和长期发展产生什么影响？
"""

def get_news_analyst(llm_provider: str = None):
    parser = PydanticOutputParser(pydantic_object=NewsAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        NEWS_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt | llm | parser
# tradingagents/agents/analysts/social_media_analyst.py (V4.1 终极版)
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from tradingagents.llms import llm_client_factory
from tradingagents.dataflows.interface import AShareDataInterface
from langchain_core.runnables import RunnableLambda

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SocialMediaAnalysis(BaseModel):
    analysis: str = Field(description="一份关于该股票市场情绪的专业分析报告。")

# [核心升级] 全新的Prompt，要求AI对“摘要”进行深度解读
SOCIAL_MEDIA_ANALYST_PROMPT = """
你是一名深谙A股散户心理的舆情分析专家。
你的任务是基于“AI研究助理”为你提供的、通过联网搜索总结出的最新市场情绪摘要，进行一次**深度解读和二次分析**。

{format_instructions}

**AI研究助理提供的最新市场情绪摘要如下：**
---
{market_sentiment_summary}
---

**你的深度解读报告，必须包含以下几个方面：**
1.  **总体情绪评估**: 基于摘要，给出一个关于当前社区总体情绪的定性判断。使用如：**[情绪狂热]**, **[普遍看多]**, **[多空分歧]**, **[普遍看空]**, **[情绪冰点]** 这样的标签来概括。
2.  **核心议题提炼**: 当前散户们正在集中讨论的核心话题是什么？是业绩？是概念？还是某个事件？
3.  **情绪背后的逻辑**: 分析这种市场情绪背后可能的原因是什么？是理性的价值发现，还是非理性的情绪宣泄？
4.  **对股价的潜在影响**: 这种舆情氛围，对短期股价可能造成什么样的影响（例如：助涨杀跌、高位派发风险、底部关注度提升等）？
"""

def get_social_media_analyst(llm_provider: str = None):
    def get_summary_from_interface(ticker: str) -> str:
        logging.info(f"[SocialMediaAnalyst] 正在委托 AI研究助理 for {ticker}...")
        data_interface = AShareDataInterface(ticker=ticker)
        return data_interface.fetch_social_media_posts()
    parser = PydanticOutputParser(pydantic_object=SocialMediaAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        SOCIAL_MEDIA_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = (
        {"market_sentiment_summary": RunnableLambda(get_summary_from_interface)}
        | prompt
        | llm
        | parser
    )
    return chain
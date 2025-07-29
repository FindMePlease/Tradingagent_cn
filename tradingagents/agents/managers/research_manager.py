# tradingagents/agents/managers/research_manager.py (V5.0 升级版)
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- [核心升级] 全新的Prompt，现在可以接收和理解全部7份报告 ---
RESEARCH_MANAGER_PROMPT = """
你是一位极其敏锐和深刻的A股投资研究主管，擅长从看似无关的信息中发现核心的逻辑关联。你的任务是审查和整合你团队中**所有7位专业分析师**提交的报告，形成一份直指核心的“投研会议纪要”。

{format_instructions}

**你的团队成员提交了以下七份独立的分析报告：**
---
**1. 基本面分析师报告 (关注内在价值与估值):**
{fundamentals_analysis}
---
**2. "双核"技术分析师报告 (结合常规指标与缠论):**
{market_analysis}
---
**3. AI新闻智能体报告 (关注最新事件催化剂):**
{news_analysis}
---
**4. 资金流向分析师报告 (关注“聪明钱”的动向):**
{capital_flow_analysis}
---
**5. 行业对标分析师报告 (关注股票在行业中的相对强弱):**
{sector_analysis}
---
**6. 政策分析师报告 (关注宏观与跨行业驱动力):**
{policy_analysis}
---
**7. 情绪分析师报告 (关注市场人气与散户动向):**
{social_media_analysis}
---

**你的核心任务是进行深度“交叉验证”，并完成以下所有部分：**
1.  **发现关键的【共识点】(key_confirmations)**: 找出不同维度之间相互印证的观点。
2.  **发现关键的【矛盾点】(key_contradictions)**: 找出不同维度之间相互矛盾、需要警惕的信号。
3.  **提炼核心看多逻辑 (bull_case)**: 基于以上发现，提炼出最核心的看多理由。
4.  **提炼核心看空逻辑 (bear_case)**: 基于以上发现，提炼出最核心的看空理由。
5.  **总结与展望 (summary)**: 对当前多空力量进行最终总结。

**[最终指令]**: 你必须严格按照格式要求，完整地输出包含`key_confirmations`, `key_contradictions`, `bull_case`, `bear_case`, `summary` 这五个字段的JSON对象。**任何字段都不能缺失。**
"""

# --- 输出模型 ---
class ResearchSummary(BaseModel):
    key_confirmations: str = Field(description="不同分析报告之间，最重要的1-2个相互印证的【共识点】。")
    key_contradictions: str = Field(description="不同分析报告之间，最重要的1-2个相互矛盾的【矛盾点】。")
    bull_case: str = Field(description="基于所有分析，提炼出的核心看多理由。")
    bear_case: str = Field(description="基于所有分析，提炼出的核心看空理由。")
    summary: str = Field(description="对当前多空力量的最终总结与展望。")

# --- Agent的核心实现 ---
def get_research_manager(llm_provider: str = None):
    parser = PydanticOutputParser(pydantic_object=ResearchSummary)
    llm = llm_client_factory()
    prompt_template = ChatPromptTemplate.from_template(
        RESEARCH_MANAGER_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = (prompt_template | llm | parser)
    return chain
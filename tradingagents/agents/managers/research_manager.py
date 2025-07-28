# tradingagents/agents/managers/research_manager.py (V2.0 升级版)

from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging

from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- [核心升级] 全新的、更深刻的Prompt ---
RESEARCH_MANAGER_PROMPT = """
你是一位极其敏锐和深刻的A股投资研究主管，擅长从看似无关的信息中发现核心的逻辑关联。你的任务是审查和整合你团队中所有分析师的报告，形成一份直指核心的“投研会议纪要”。

{format_instructions}

**你的团队成员提交了以下五份独立的分析报告：**
---
**1. 基本面分析师报告 (关注内在价值与估值):**
{fundamentals_analysis}
---
**2. 技术分析师报告 (关注价格行为与市场心理):**
{market_analysis}
---
**3. AI新闻智能体报告 (关注最新事件催化剂):**
{news_analysis}
---
**4. 政策分析师报告 (关注宏观与行业驱动力):**
{policy_analysis}
---
**5. 情绪分析师报告 (关注市场人气与散户动向):**
{social_media_analysis}
---

**你的核心任务不再是简单总结，而是进行深度“交叉验证”，找出报告之间的逻辑联系：**

1.  **发现关键的【共识点】(Confirmations):**
    * 找出不同维度之间相互印证的观点。
    * **示例**: “技术面的放量上涨（技术分析），是否得到了公司发布重大利好公告（新闻分析）的确认？” 或者 “基本面的盈利能力改善（基本面分析），是否得到了股价突破关键阻力位（技术分析）的验证？”

2.  **发现关键的【矛盾点】(Contradictions):**
    * 找出不同维度之间相互矛盾、需要警惕的信号。
    * **示例**: “基本面报告显示公司估值合理（基本面分析），但技术面却显示股价处于破位下跌的趋势（技术分析），这是为什么？” 或者 “政策面出现重大利好（政策分析），但市场情绪却异常悲观（情绪分析），这暗示了什么？”

3.  **提炼核心多空逻辑 (Bull & Bear Case):**
    * 基于以上发现的【共识点】和【矛盾点】，提炼出当前市场对这只股票最主要的“看多逻辑”和“看空逻辑”。

**输出要求:**
你必须输出一份结构清晰的“**投研会议纪要**”，其中必须包含【共识点】、【矛盾点】、以及最终的核心多空理由。
"""

# --- [核心升级] 全新的输出模型 ---
class ResearchSummary(BaseModel):
    """研究主管的最终输出，一份包含深度洞察的会议纪要"""
    key_confirmations: str = Field(description="不同分析报告之间，最重要的1-2个相互印证的【共识点】。")
    key_contradictions: str = Field(description="不同分析报告之间，最重要的1-2个相互矛盾的【矛盾点】。")
    bull_case: str = Field(description="基于所有分析，提炼出的核心看多理由。")
    bear_case: str = Field(description="基于所有分析，提炼出的核心看空理由。")
    summary: str = Field(description="对当前多空力量的最终总结与展望。")

# --- Agent的核心实现 ---
def get_research_manager(llm_provider: str = None):
    """
    [V2.0 升级版] 构建并返回研究主管的执行链。
    """
    parser = PydanticOutputParser(pydantic_object=ResearchSummary)
    llm = llm_client_factory()
    prompt_template = ChatPromptTemplate.from_template(
        RESEARCH_MANAGER_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    # 这里的 chain 输入是一个包含了所有分析师报告文本的字典
    chain = (
        prompt_template
        | llm
        | parser
    )
    return chain

if __name__ == '__main__':
    # ... (独立的测试脚本) ...
    pass
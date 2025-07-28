# tradingagents/agents/researchers/bear_researcher.py (V2.0 升级版)

from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging

from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- [核心升级] 全新的、更深刻的Prompt ---
BEAR_RESEARCHER_PROMPT = """
你是一名顶尖的A股“空头辩手”，你的任务是基于研究主管的“投研会议纪要”，构建一份逻辑严密、揭示所有风险的最终看空报告。

{format_instructions}

**你收到的“投研会议纪要”核心内容如下：**
---
**核心看空理由 (Bear Case):**
{bear_case_points}
---
**关键的【共识点】(Confirmations):**
{key_confirmations}
---
**关键的【矛盾点】(Contradictions):**
{key_contradictions}
---

**你的最终看空报告必须完成以下任务：**

1.  **利用【矛盾点】**: 将“矛盾点”作为你最强有力的攻击点。详细阐述为什么这些跨维度的矛盾信号，揭示了公司潜在的巨大风险。

2.  **反驳【共识点】**: **这是你辩论的核心**。你必须对“共识点”提出质疑。尝试从一个悲观的角度去解读这些共识，或者论证为什么这些看似利好的信号是暂时的、具有误导性的、甚至是陷阱。**你不能对利好视而不见。**

3.  **构建空头脚本 (Short Thesis)**: 将所有对你有利的证据（包括你对共识点的反驳）串联起来，形成一个令人警醒的、统一的“空头脚本”。

**输出要求:**
* 输出一份结构清晰的“**最终看空报告**”，包含对矛盾的利用、对共识的反驳，以及最终的空头脚本。
* 你的语气必须**审慎、批判、富有逻辑**。
"""

# --- [核心升级] 全新的输入输出模型 ---
class BearishArgumentInput(BaseModel):
    """看空研究员接收的输入，来自研究主管的会议纪要"""
    ticker: str = Field()
    stock_name: str = Field()
    bear_case_points: str = Field()
    key_confirmations: str = Field()
    key_contradictions: str = Field()

class BearishReport(BaseModel):
    """看空研究员的最终输出"""
    report: str = Field(description="一份结构化的、包含对共识点反驳的最终看空报告。")

# --- Agent的核心实现 ---
def get_bear_researcher(llm_provider: str = None):
    """
    [V2.0 升级版] 构建并返回看空研究员的执行链。
    """
    parser = PydanticOutputParser(pydantic_object=BearishReport)
    llm = llm_client_factory()
    prompt_template = ChatPromptTemplate.from_template(
        BEAR_RESEARCHER_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = (
        prompt_template
        | llm
        | parser
    )
    return chain

if __name__ == '__main__':
    # ... (独立的测试脚本) ...
    pass
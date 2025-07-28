# tradingagents/agents/researchers/bull_researcher.py (V2.0 升级版)

from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging

from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- [核心升级] 全新的、更深刻的Prompt ---
BULL_RESEARCHER_PROMPT = """
你是一名顶尖的A股“多头辩手”，你的任务是基于研究主管的“投研会议纪要”，构建一份逻辑无懈可击、极具说服力的最终看多报告。

{format_instructions}

**你收到的“投研会议纪要”核心内容如下：**
---
**核心看多理由 (Bull Case):**
{bull_case_points}
---
**关键的【共识点】(Confirmations):**
{key_confirmations}
---
**关键的【矛盾点】(Contradictions):**
{key_contradictions}
---

**你的最终看多报告必须完成以下任务：**

1.  **强化【共识点】**: 将“共识点”作为你最强有力的证据。详细阐述为什么这些跨维度的一致信号，极大地增强了看多的确定性。

2.  **回应【矛盾点】**: **这是你辩论的核心**。你必须正面回应“矛盾点”。尝试从一个乐观的角度去解读这些矛盾，或者论证为什么这些矛盾点是次要的、暂时的、可以被克服的。**你不能回避问题。**

3.  **构建投资叙事 (Investment Narrative)**: 将所有对你有利的证据（包括你对矛盾点的解释）串联起来，形成一个引人入胜的、统一的投资故事。

**输出要求:**
* 输出一份结构清晰的“**最终看多报告**”，包含对共识的强化、对矛盾的回应，以及最终的投资故事。
* 你的语气必须**充满信心、逻辑严密、富有洞察力**。
"""

# --- [核心升级] 全新的输入输出模型 ---
class BullishArgumentInput(BaseModel):
    """看多研究员接收的输入，来自研究主管的会议纪要"""
    ticker: str = Field()
    stock_name: str = Field()
    bull_case_points: str = Field()
    key_confirmations: str = Field()
    key_contradictions: str = Field()

class BullishReport(BaseModel):
    """看多研究员的最终输出"""
    report: str = Field(description="一份结构化的、包含对矛盾点回应的最终看多报告。")

# --- Agent的核心实现 ---
def get_bull_researcher(llm_provider: str = None):
    """
    [V2.0 升级版] 构建并返回看多研究员的执行链。
    """
    parser = PydanticOutputParser(pydantic_object=BullishReport)
    llm = llm_client_factory()
    prompt_template = ChatPromptTemplate.from_template(
        BULL_RESEARCHER_PROMPT,
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
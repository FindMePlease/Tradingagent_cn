from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BEAR_RESEARCHER_PROMPT = """你是一名顶尖的A股“空头辩手”，你的任务是基于研究主管的“投研会议纪要”，构建一份逻辑严密、揭示所有风险的最终看空报告。
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
1.  **利用【矛盾点】**: 将“矛盾点”作为你最强有力的攻击点。
2.  **反驳【共识点】**: **这是你辩论的核心**。你必须对“共识点”提出质疑。
3.  **构建空头脚本 (Short Thesis)**: 将所有对你有利的证据串联起来，形成一个令人警醒的“空头脚本”。
**输出要求:**
* 输出一份结构清晰的“**最终看空报告**”。
* 你的语气必须**审慎、批判、富有逻辑**。
"""

class BearishArgumentInput(BaseModel):
    ticker: str = Field()
    stock_name: str = Field()
    bear_case_points: str = Field()
    key_confirmations: str = Field()
    key_contradictions: str = Field()

class BearishReport(BaseModel):
    # [核心修正] 将字段名从 report 修改为 analysis，与其他分析师统一
    analysis: str = Field(description="一份结构化的、包含对共识点反驳的最终看空报告。")

def get_bear_researcher(llm_provider: str = None):
    parser = PydanticOutputParser(pydantic_object=BearishReport)
    llm = llm_client_factory()
    prompt_template = ChatPromptTemplate.from_template(
        BEAR_RESEARCHER_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt_template | llm | parser
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BULL_RESEARCHER_PROMPT = """你是一名坚定、乐观且逻辑严密的A股“多头论证官”。你的任务是基于研究主管的“投研会议纪要”，构建一份详尽且极具说服力的最终看多报告。
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
1.  **强化【共识点】**: 将“共识点”作为你最强有力的证据。
2.  **回应【矛盾点】**: **这是你辩论的核心**。你必须正面回应“矛盾点”。
3.  **构建投资叙事**: 将所有对你有利的证据串联起来，形成一个统一的投资故事。
**输出要求:**
* 输出一份结构清晰的“**最终看多报告**”。
* 你的语气必须**充满信心、逻辑严密、富有洞察力**。
"""

class BullishArgumentInput(BaseModel):
    ticker: str = Field()
    stock_name: str = Field()
    bull_case_points: str = Field()
    key_confirmations: str = Field()
    key_contradictions: str = Field()

class BullishReport(BaseModel):
    # [核心修正] 将字段名从 report 修改为 analysis，与其他分析师统一
    analysis: str = Field(description="一份结构化的、包含对矛盾点回应的最终看多报告。")

def get_bull_researcher(llm_provider: str = None):
    parser = PydanticOutputParser(pydantic_object=BullishReport)
    llm = llm_client_factory()
    prompt_template = ChatPromptTemplate.from_template(
        BULL_RESEARCHER_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt_template | llm | parser
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

RISK_MANAGER_PROMPT = """你是一名极其审慎和专业的A股风险管理经理。你的任务是基于“投研会议纪要”，识别所有潜在风险，并对即将形成的交易策略进行压力测试。
{format_instructions}
**你收到的“投研会议纪要”核心内容如下：**
---
**关键的【共识点】(Confirmations):**
{key_confirmations}
---
**关键的【矛盾点】(Contradictions):**
{key_contradictions}
---
**核心看多理由 (Bull Case):**
{bull_case}
---
**核心看空理由 (Bear Case):**
{bear_case}
---
**你的风险审查报告必须完成以下任务：**
1.  **评估【矛盾点】中的核心风险**: “矛盾点”往往是最大的风险来源。
2.  **质疑【共识点】的脆弱性**: 即使是“共识点”，也可能存在被市场过度解读或证伪的风险。
3.  **量化关键风险与管理建议**: 识别出当前最主要的2-3个风险，并提出具体的管理建议。
4.  **给出总体风险评级**: 给出 **[低风险]**, **[中等风险]**, 或 **[高风险]** 的最终评级。
**输出要求:**
* 输出一份结构清晰的“**最终风险审查报告**”。
"""

class RiskManagerInput(BaseModel):
    key_confirmations: str
    key_contradictions: str
    bull_case: str
    bear_case: str

class RiskAnalysis(BaseModel):
    # [核心修正] 将多个字段合并为一个 analysis 字段，与其他所有智能体保持绝对一致
    analysis: str = Field(description="一份完整的、结构化的最终风险审查报告，必须包含风险评级和具体的风险点分析。")

def get_risk_manager(llm_provider: str = None):
    parser = PydanticOutputParser(pydantic_object=RiskAnalysis)
    llm = llm_client_factory()
    prompt_template = ChatPromptTemplate.from_template(
        RISK_MANAGER_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt_template | llm | parser
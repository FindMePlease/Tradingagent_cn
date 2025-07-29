# tradingagents/agents/managers/risk_manager.py (V5.0 终极版)
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')# --- [核心升级] 全新的Prompt，要求对“会议纪要”进行压力测试 ---
RISK_MANAGER_PROMPT = """
你是一名极其审慎和专业的A股风险管理经理。你的任务是基于“投研会议纪要”，识别所有潜在风险，并对即将形成的交易策略进行压力测试。

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

1.  **评估【矛盾点】中的核心风险**: “矛盾点”往往是最大的风险来源。请深入分析这些矛盾信号背后可能隐藏的、最致命的风险是什么？
2.  **质疑【共识点】的脆弱性**: 即使是“共识点”，也可能存在被市场过度解读或证伪的风险。请评估这些共识是否已经过热，或者它们成立的条件是否足够稳固？
3.  **量化关键风险与管理建议**: 基于所有信息，识别出当前最主要的2-3个风险，并为每一个风险，提出具体的、可操作的风险管理建议。
4.  **给出总体风险评级**: 给出 **[低风险]**, **[中等风险]**, 或 **[高风险]** 的最终评级。

**输出要求:**
* 输出一份结构清晰的“**最终风险审查报告**”。
"""

# --- [核心升级] 全新的输入输出模型 ---
class RiskManagerInput(BaseModel):
    """风险管理经理接收的输入"""
    key_confirmations: str
    key_contradictions: str
    bull_case: str
    bear_case: str

class RiskAnalysis(BaseModel):
    """风险管理经理的最终输出"""
    risk_level: str = Field(description="总体的风险等级评估 ([低风险]/[中等风险]/[高风险])")
    key_risks_and_suggestions: str = Field(description="对2-3个最主要风险点的分析，以及相应的管理建议。")
    # 为了兼容旧版 setup.py 中的打印逻辑，我们保留一个 report 字段来汇总所有信息
    report: str = Field(description="一份完整的、结构化的最终风险审查报告。")
# --- Agent的核心实现 ---
def get_risk_manager(llm_provider: str = None):
    """
    [V5.0 终极版] 构建并返回风险管理经理的执行链。
    """
    parser = PydanticOutputParser(pydantic_object=RiskAnalysis)
    llm = llm_client_factory()
    prompt_template = ChatPromptTemplate.from_template(
        RISK_MANAGER_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = (
        prompt_template
        | llm
        | parser
    )
    return chain

if __name__ == '__main__':
    # 独立的测试脚本
    # ... (为了保持文件简洁，测试脚本可以暂时省略) ...
    pass
# tradingagents/agents/trader/trader.py (V2.0 终极版 - 交易策略师)

from pydantic import BaseModel, Field
from typing import Literal
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging

# 从我们项目的llms模块导入LLM客户端工厂
from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- [核心升级] 最终的、可执行的输出模型 ---
class TradeOrder(BaseModel):
    """一份完整的、可执行的交易计划"""
    action: Literal["买入", "卖出", "保持观察"] = Field(description="核心交易动作：'买入', '卖出', 或 '保持观察'")
    confidence: int = Field(description="对该决策的信心指数（1-5分）", ge=1, le=5)
    rationale: str = Field(description="做出该决策的核心权衡理由。必须详细解释你是如何权衡多空报告的观点，并考虑了风险报告的警告。")
    entry_condition: str = Field(description="具体的入场条件。如果动作为'买入'或'保持观察'后可能转为买入，则必须提供。例如：'股价放量突破16.50元阻力位时'或'股价回踩至15.00元均线支撑位企稳时'。")
    stop_loss: str = Field(description="明确的止损条件。如果动作为'买入'，则必须提供。例如：'有效跌破14.38元前期低点时'。")
    position_sizing: str = Field(description="仓位管理建议。例如：'初始仓位不超过总资金的10%'或'采用金字塔式加仓法'。")# --- [核心升级] 最终的、专业的Prompt ---
TRADER_PROMPT = """
你是一名纪律严明、经验丰富的A股交易策略师。现在是最终决策时刻。你的任务是综合所有情报，形成一份**完整、严谨、可执行**的交易计划。

{format_instructions}

**你的决策依据是以下三份最终报告：**
---
**1. 最终看多报告 (多头辩手陈词):**
{bull_report}
---
**2. 最终看空报告 (空头辩手陈词):**
{bear_report}
---
**3. 最终风险审查报告 (风险管理经理):**
{risk_report}
---

**你的任务：**
1.  **权衡利弊**: 深入分析多空双方的辩论，评估哪一方的逻辑链更强、证据更足。
2.  **整合风险**: **必须**将风险报告中提出的【高风险】警告作为核心决策约束。
3.  **制定计划**: 基于你的最终判断，制定一份包含所有必要元素的交易计划。

**输出要求:**
你必须输出一个唯一的、结构化的交易计划，严格包含`action`, `confidence`, `rationale`, `entry_condition`, `stop_loss`, `position_sizing` 六个部分。**所有部分都必须被填充，不允许留空。**
"""

class TradeDecisionInput(BaseModel):
    ticker: str = Field()
    stock_name: str = Field()
    bull_report: str = Field()
    bear_report: str = Field()
    risk_report: str = Field()
    
def get_trader_agent(llm_provider: str = None):
    """
    [V2.0 终极版] 构建并返回交易策略师的执行链。
    """
    parser = PydanticOutputParser(pydantic_object=TradeOrder)
    llm = llm_client_factory()
    prompt_template = ChatPromptTemplate.from_template(
        TRADER_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = (
        prompt_template
        | llm
        | parser
    )
    return chain

if __name__ == '__main__':
    # ... 独立的测试脚本 ...
    pass
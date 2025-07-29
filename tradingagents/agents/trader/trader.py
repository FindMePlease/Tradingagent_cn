# tradingagents/agents/trader/trader.py (V5.0 首席投资官)
from pydantic import BaseModel, Field
from typing import Literal
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradePlan(BaseModel):
    action: Literal["买入", "卖出", "保持观察"] = Field(description="核心交易动作")
    confidence: int = Field(description="对该决策的信心指数（1-5分）", ge=1, le=5)
    rationale: str = Field(description="做出该决策的核心权衡理由。必须详细解释你是如何权衡所有信息，并形成自己独立判断的。")
    entry_price: str = Field(description="具体的建议入场价格区间。")
    stop_loss_price: str = Field(description="明确的建议止损价格。")
    target_price: str = Field(description="明确的建议目标价格区间。")
    position_sizing: str = Field(description="仓位管理建议。")

# --- [核心升级] 全新的、赋予独立思考能力的Prompt ---
TRADER_PROMPT = """
你是一名以实现最终盈利为唯一目标的A股首席投资官(CIO)。你的桌上现在有关于「{stock_name}」({ticker})的**全部情报**，包括一份包含7位专家报告的《投研简报》，一份《多空辩论纪要》，以及一份《最终风险评估》。

{format_instructions}

**[当前盘面]**
* **最新收盘价**: **{latest_close_price}元**

**[情报汇总]**
---
**1. 完整的《投研简报》(包含全部7份原始分析报告):**
{full_briefing_book}
---
**2. 《多空辩论纪要》:**
* **多头最终陈词:** {bull_report}
* **空头最终陈词:** {bear_report}
---
**3. 《最终风险评估》:**
{risk_report}
---

**你的任务：**
1.  **独立思考**: 你不需要简单地听从任何一方。你的职责是穿透所有信息，**找出当前最核心的交易机会点（Alpha）或最致命的风险点**。
2.  **形成观点**: 基于你的独立思考，形成自己对后市的独特判断。
3.  **制定计划**: 将你的观点，转化为一个**具体、完整、可执行**的交易计划。

**输出要求:**
你必须输出一个唯一的、结构化的交易计划，严格包含所有字段。你的`rationale`(决策理由)部分，必须体现出你**权衡了所有信息**后的**独立思考**过程。
"""

def get_trader_agent(llm_provider: str = None):
    parser = PydanticOutputParser(pydantic_object=TradePlan)
    llm = llm_client_factory()
    prompt_template = ChatPromptTemplate.from_template(
        TRADER_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = (prompt_template | llm | parser)
    return chain
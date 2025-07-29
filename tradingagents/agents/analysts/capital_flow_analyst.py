# tradingagents/agents/analysts/capital_flow_analyst.py (V4.1 新增)
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging

from tradingagents.llms import llm_client_factory
from tradingagents.dataflows.interface import AShareDataInterface
from langchain_core.runnables import RunnableLambda

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 1. 定义分析师的输出格式 ---
class CapitalFlowAnalysis(BaseModel):
    analysis: str = Field(description="一份关于该股票资金博弈情况的专业分析报告。")

# --- 2. 定义分析师的Prompt ---
CAPITAL_FLOW_ANALYST_PROMPT = """
你是一名顶尖的A股资金分析专家，擅长从繁杂的资金数据中解读出主力资金的真实意图。
你的任务是基于“AI研究助理”为你提供的资金动向摘要，进行一次**深度解读和二次分析**。

{format_instructions}

**AI研究助理提供的最新资金动向摘要如下：**
---
{capital_flow_summary}
---

**你的深度解读报告，必须包含以下几个方面：**
1.  **主力资金态度判断**: 基于主力资金净流入/流出的数据，判断近一个月来，“聪明钱”的整体态度是“积极增持”、“高位派发”、“持续流出”还是“增减不明”？
2.  **关键席位博弈分析**: 如果摘要中提到了龙虎榜数据，请分析上榜的营业部或机构席位，是顶级游资在短线博弈，还是机构在进行中长线布局？
3.  **大宗交易信号解读**: 如果摘要中提到了大宗交易，请分析其成交价相对于当日收盘价是“溢价”、“折价”还是“平价”成交？这通常暗示了什么信号？
4.  **综合结论**: 结合所有资金面信息，给出一个关于当前“聪明钱”对这只股票真实态度的、清晰的、总结性的判断。
"""

# --- 3. 定义Agent的实现 ---
def get_capital_flow_analyst(llm_provider: str = None):
    """
    构建并返回资金流向分析师的执行链。
    这是一个两步AI流程：AI助理获取信息 -> AI分析师解读信息。
    """
    def get_summary_from_interface(ticker: str) -> str:
        """工具函数，负责从数据接口获取AI助理生成的资金流向摘要"""
        logging.info(f"[CapitalFlowAnalyst] 正在委托 AI研究助理 for {ticker}...")
        # 注意：每次调用AShareDataInterface都会重新触发一次AI助理的数据获取
        # 在完整的图中，我们会优化为只调用一次
        data_interface = AShareDataInterface(ticker=ticker)
        return data_interface.ai_data.capital_flow_summary if data_interface.ai_data else "AI获取资金流向数据失败"

    parser = PydanticOutputParser(pydantic_object=CapitalFlowAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        CAPITAL_FLOW_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = (
        {"capital_flow_summary": RunnableLambda(get_summary_from_interface)}
        | prompt
        | llm
        | parser
    )
    return chain
# tradingagents/agents/analysts/market_analyst.py (V4.2 双核分析版)
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain.output_parsers import PydanticOutputParser
import logging
from tradingagents.llms import llm_client_factory
from tradingagents.dataflows.interface import AShareDataInterface

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MarketAnalysis(BaseModel):
    analysis: str = Field(description="一份包含常规技术分析和缠论分析的、专业的A股技术分析报告。")

# --- [核心升级] 全新的、要求进行“双核分析”的Prompt ---
MARKET_ANALYST_PROMPT = """
你是一名顶级的A股技术分析大师，你既精通MACD、RSI、布林带等常规技术指标，也对“缠中说禅理论”有深刻的理解。
你的任务是基于我为你提供的综合技术情报，进行一次**双维度的、交叉验证的**技术分析。

{format_instructions}

**以下是由程序获取的综合技术情报：**
---
{technical_report}
---

**你的分析报告必须严格包含以下三个部分：**

**第一部分：常规技术指标分析**
1.  **趋势与关键价位**: 结合日线图，判断当前的主要趋势，并找出关键的支撑位和阻力位。
2.  **指标解读**: 深入解读日线数据中的MACD、RSI、布林带指标，它们分别给出了什么样的看多或看空信号？

**第二部分：缠论结构分析**
1.  **当前结构定位**: 基于30分钟K线数据，判断当前走势处于缠论中的什么结构？（例如：中枢震荡、离开中枢的上涨/下跌线段等）。
2.  **买卖点判断**: 当前是否存在潜在的、由背驰等情况引发的缠论买卖点（一、二、三类）？请明确指出。

**第三部分：综合结论 (交叉验证)**
1.  **观点印证**: 常规技术指标的分析结果，与缠论分析的结果，是否存在相互**印证**的地方？（例如：MACD金叉，同时缠论出现第二类买点，这是一个强烈的看多共振信号）。
2.  **观点矛盾**: 两套理论的分析结果，是否存在相互**矛盾**的地方？（例如：RSI处于超买区提示风险，但缠论结构显示上涨并未结束）。
3.  **最终策略建议**: 综合以上所有分析，给出一个最终的技术面看法和具体的操作策略建议。
"""

def get_market_analyst(llm_provider: str = None):
    def get_report_from_interface(ticker: str) -> str:
        logging.info(f"[MarketAnalyst] 正在委托数据接口生成综合技术分析报告 for {ticker}...")
        data_interface = AShareDataInterface(ticker=ticker)
        # 调用我们全新的、功能强大的接口函数
        return data_interface.fetch_comprehensive_technical_report()

    parser = PydanticOutputParser(pydantic_object=MarketAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        MARKET_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = (
        {"technical_report": RunnableLambda(get_report_from_interface)}
        | prompt
        | llm
        | parser
    )
    return chain
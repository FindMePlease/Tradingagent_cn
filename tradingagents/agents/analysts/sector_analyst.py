# tradingagents/agents/analysts/sector_analyst.py (V4.1 新增)
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging

from tradingagents.llms import llm_client_factory
from tradingagents.dataflows.interface import AShareDataInterface
from langchain_core.runnables import RunnableLambda

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 1. 定义分析师的输出格式 ---
class SectorAnalysis(BaseModel):
    analysis: str = Field(description="一份关于该股票行业地位和对标情况的专业分析报告。")

# --- 2. 定义分析师的Prompt ---
SECTOR_ANALYST_PROMPT = """
你是一名顶尖的A股行业分析师，擅长通过横向对比，发现公司的相对强弱和行业地位。
你的任务是基于“AI研究助理”为你提供的行业对标摘要，进行一次**深度解读和二次分析**。

{format_instructions}

**AI研究助理提供的最新行业对标摘要如下：**
---
{sector_comparison_summary}
---

**你的深度解读报告，必须包含以下几个方面：**
1.  **相对强弱判断**: 基于股价走势对比，明确判断该股票近期的表现是“领涨行业”、“同步行业”还是“弱于行业”？
2.  **原因探析**: 结合你对市场的理解，分析导致这种相对强弱表现的可能原因是什么？（例如：公司自身有利好/利空，或者它在行业中的龙头/跟风地位，再或是市场资金偏好等）
3.  **投资启示**: 这种行业地位和相对强弱的表现，对该股票未来的股价走势有何启示？是强者恒强的信号，还是补涨机会的暗示，抑或是需要警惕的风险？
4.  **综合结论**: 给出一个关于该公司行业地位的、清晰的、总结性的判断。
"""

# --- 3. 定义Agent的实现 ---
def get_sector_analyst(llm_provider: str = None):
    """
    构建并返回行业对标分析师的执行链。
    """
    def get_summary_from_interface(ticker: str) -> str:
        """工具函数，负责从数据接口获取AI助理生成的行业对标摘要"""
        logging.info(f"[SectorAnalyst] 正在委托 AI研究助理 for {ticker}...")
        data_interface = AShareDataInterface(ticker=ticker)
        return data_interface.ai_data.sector_comparison_summary if data_interface.ai_data else "AI获取行业对标数据失败"

    parser = PydanticOutputParser(pydantic_object=SectorAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        SECTOR_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    
    chain = (
        {"sector_comparison_summary": RunnableLambda(get_summary_from_interface)}
        | prompt
        | llm
        | parser
    )
    return chain
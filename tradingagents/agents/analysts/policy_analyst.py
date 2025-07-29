# tradingagents/agents/analysts/policy_analyst.py (V4.1 升级版)
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging

from tradingagents.llms import llm_client_factory
from tradingagents.dataflows.interface import AShareDataInterface
from langchain_core.runnables import RunnableLambda

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PolicyAnalysis(BaseModel):
    analysis: str = Field(description="一份关于政策及其跨行业影响的深度分析报告。")

# --- [核心升级] 全新的、具备全局视野的Prompt ---
POLICY_ANALYST_PROMPT = """
你是一位顶级的中国产业政策分析专家，拥有全局视野，擅长分析政策在不同行业间的传导效应。
你的任务是基于“AI研究助理”为你提供的最新政策信息，进行一次**深度解读和二次分析**。

{format_instructions}

**AI研究助理提供的最新政策与宏观新闻摘要如下：**
---
{policy_news}
---

**你的深度解读报告，必须包含以下几个方面：**
1.  **直接影响分析**: 这项政策对「{stock_name}」所在的**直接行业**有何影响？是利好还是利空？
2.  **跨行业传导分析 (核心)**: 这项政策，还可能对哪些**上下游或利益相关的行业板块**（例如：原材料、设备制造、消费端、替代品等）产生**间接的正面或负面影响**？请列举1-2个。
3.  **产业链逻辑总结**: 综合来看，这项政策在整个产业链上的传导逻辑是怎样的？
4.  **对本公司的最终影响**: 结合直接和间接影响，这项政策对「{stock_name}」的长期发展是重大的机遇，还是潜在的挑战？
"""

def get_policy_analyst(llm_provider: str = None):
    """
    构建并返回具备跨行业视野的政策分析师的执行链。
    """
    def get_summary_from_interface(ticker: str) -> dict:
        """工具函数，获取政策新闻和公司名称"""
        logging.info(f"[PolicyAnalyst] 正在委托 AI研究助理 for {ticker}...")
        data_interface = AShareDataInterface(ticker=ticker)
        return {
            "policy_news": data_interface.fetch_policy_news(),
            "stock_name": data_interface.stock_name
        }

    parser = PydanticOutputParser(pydantic_object=PolicyAnalysis)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(POLICY_ANALYST_PROMPT, partial_variables={"format_instructions": parser.get_format_instructions()})
    
    chain = (
        RunnableLambda(get_summary_from_interface)
        | prompt
        | llm
        | parser
    )
    return chain
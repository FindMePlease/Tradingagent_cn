# tradingagents/agents/analysts/policy_analyst.py (Pydantic V2 升级版)

from pydantic import BaseModel, Field  # [升级] 直接从 pydantic 导入
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.output_parsers import PydanticOutputParser
import logging

from tradingagents.llms import llm_client_factory
from tradingagents.dataflows.interface import AShareDataInterface
# [重要] policy_analyst 不再直接调用 policy_news_utils
# 它现在通过统一的 interface 获取数据

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Agent 的输出数据结构 ---
class PolicyAnalysis(BaseModel):
    analysis: str = Field(description="一份关于政策对公司影响的结构化分析报告。")

# --- System Prompt: 定义政策分析师的角色、任务和输出格式 ---
POLICY_ANALYST_PROMPT = """
你是一位顶级的中国宏观经济与产业政策分析师，对政策的解读既深刻又敏锐。你的任务是分析给定的宏观和产业政策新闻，并评估它们对特定A股上市公司 {ticker} ({stock_name}) 的潜在传导影响。

{format_instructions}

**你的分析框架应遵循以下逻辑：**
1.  **政策定性**: 识别最重要的政策新闻，判断其属于宏观层面还是产业层面。
2.  **影响路径分析**: 分析政策如何通过影响市场流动性、企业成本或行业需求，来传导至 {stock_name}。
3.  **影响评估与分类**: 对关键政策的影响进行总结，并给出明确的情绪分类标签：**[政策利好]**, **[政策利空]**, 或 **[影响中性]**。
4.  **综合结论**: 综合所有政策分析，给出一个关于当前政策环境对该公司总体影响的简短结论。

**输入信息如下：**
---
**股票代码:** {ticker} ({stock_name})
**相关政策新闻:**
{policy_news}
---
"""

# --- Agent的核心实现 ---
def get_policy_analyst(llm_provider: str = None):
    """构建并返回政策分析师的执行链。"""
    
    def get_policy_data(ticker: str) -> str:
        logging.info(f"[PolicyAnalyst] 正在为 {ticker} 获取政策数据...")
        try:
            # 现在通过统一的、干净的接口获取数据
            data_interface = AShareDataInterface(ticker=ticker)
            news_content = data_interface.fetch_policy_news()
            return news_content
        except Exception as e:
            logging.error(f"[PolicyAnalyst] 获取 {ticker} 政策数据时出错: {e}")
            return f"获取政策新闻失败: {e}"

    parser = PydanticOutputParser(pydantic_object=PolicyAnalysis)
    llm = llm_client_factory()
    prompt_template = ChatPromptTemplate.from_template(
        POLICY_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = (
        {
            "ticker": RunnablePassthrough(),
            "stock_name": lambda ticker: AShareDataInterface(ticker).stock_name,
            "policy_news": lambda ticker: get_policy_data(ticker),
        }
        | prompt_template
        | llm
        | parser  # [修正] 使用更健壮的解析器
    )
    
    return chain
# tradingagents/agents/analysts/market_analyst.py (V2.0 升级版)

from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain.output_parsers import PydanticOutputParser
import logging

from tradingagents.llms import llm_client_factory
from tradingagents.dataflows.interface import AShareDataInterface

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Agent 的输出定义 ---
class MarketAnalysis(BaseModel):
    analysis: str = Field(description="一份结构化的、关于股票技术面的详细分析报告。")

# --- [核心升级] 全新的、更专业的Prompt ---
MARKET_ANALYST_PROMPT = """
你是一位经验丰富的A股图表分析专家（Chartist），精通各种技术分析理论。你的任务是基于给出的、已包含关键技术指标的股票历史行情数据，提供一份专业、深刻的技术分析报告。

{format_instructions}

**你的分析必须深入探讨以下几个核心问题：**

1.  **市场趋势与K线形态 (Trend & Candlestick Patterns):**
    * 结合K线图的整体走势，判断当前股票处于何种主要趋势？（上升/下降/震荡）
    * 近期有无出现关键的K线组合形态？（例如：看涨吞没、十字星、黄昏之星等）

2.  **技术指标综合研判 (Indicator Analysis):**
    * **MACD**: 分析MACD线、信号线的位置关系以及柱状图的变化。近期是否出现或即将出现“金叉”或“死叉”信号？是否存在顶背离或底背离迹象？
    * **RSI**: 分析RSI_14的数值。当前市场是处于“超买区”（通常>70）、“超卖区”（通常<30），还是中性区域？
    * **布林带 (Bollinger Bands)**: 分析当前股价与布林带上轨（BBU）、中轨和下轨（BBL）的关系。股价是在上轨受到压制，还是在下轨获得支撑？布林带的开口是在收窄（预示变盘）还是在放大（预示趋势延续）？

3.  **成交量分析 (Volume Analysis):**
    * 分析价格变动与成交量的关系。是“价涨量增”的健康上涨，还是“价涨量缩”的量价背离？下跌时是“放量下跌”还是“缩量回调”？

4.  **关键支撑与阻力位 (Support & Resistance):**
    * 综合以上所有信息，明确指出当前最重要的**短期支撑位**和**阻力位**在哪个价格区间。

5.  **综合技术展望 (Overall Technical Outlook):**
    * 结合所有分析，给出一个综合的技术面看法和对后市的预判。

**输入材料如下：**
---
**股票代码:** {ticker} ({stock_name})
**最近30天行情与技术指标:**
{price_history}
---
"""

def get_market_analyst(llm_provider: str = None):
    """
    [V2.0 升级版] 构建并返回市场/技术分析师的执行链。
    """
    
    def get_price_data(ticker: str) -> str:
        """
        工具函数，负责调用数据接口获取所有需要的价格和技术指标数据。
        """
        logging.info(f"[MarketAnalyst] 正在为 {ticker} 获取历史行情与技术指标...")
        try:
            data_interface = AShareDataInterface(ticker=ticker)
            # data_interface中已经为我们计算好了所有指标
            price_data_str = data_interface.fetch_price_history(days=365)
            logging.info(f"[MarketAnalyst] 已成功获取 {ticker} 的行情与技术指标。")
            return price_data_str
        except Exception as e:
            logging.error(f"[MarketAnalyst] 获取 {ticker} 行情数据时出错: {e}")
            return f"获取行情数据失败: {e}"

    parser = PydanticOutputParser(pydantic_object=MarketAnalysis)
    llm = llm_client_factory()
    prompt_template = ChatPromptTemplate.from_template(
        MARKET_ANALYST_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )

    chain = (
        {
            "ticker": RunnablePassthrough(),
            "stock_name": lambda ticker: AShareDataInterface(ticker).stock_name,
            "price_history": lambda ticker: get_price_data(ticker)
        }
        | prompt_template
        | llm
        | parser
    )
    
    return chain

if __name__ == '__main__':
    # ... (独立的测试脚本) ...
    pass
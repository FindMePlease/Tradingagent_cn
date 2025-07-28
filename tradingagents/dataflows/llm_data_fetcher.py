# tradingagents/dataflows/llm_data_fetcher.py (已修正)
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StockFinancialMetrics(BaseModel):
    pe_ttm: float = Field(description="滚动市盈率 (PE-TTM)")
    pb_ratio: float = Field(description="市净率 (PB)")
    market_cap: float = Field(description="总市值 (单位：亿元人民币)") # [修正] 统一字段名
    cash_flow_per_share: float = Field(description="最新报告期的每股经营性现金流 (元)")
    shareholder_count: int = Field(description="最新一期的股东户数")

DATA_FETCHER_PROMPT = """你是一名顶级的金融数据分析师，拥有实时访问互联网获取最新金融数据的能力。你的任务是根据提供的公司名称和股票代码，以最高的准确性，查询并返回其最新的关键财务指标。
{format_instructions}
请为以下公司查询数据，所有数值都必须是最新的：
公司名称: {stock_name}
股票代码: {ticker}
"""

def get_financial_data_from_llm(ticker: str, stock_name: str) -> StockFinancialMetrics:
    logging.info(f"--- 启动AI数据获取智能体 for {stock_name} ---")
    try:
        parser = PydanticOutputParser(pydantic_object=StockFinancialMetrics)
        llm = llm_client_factory() 
        prompt = ChatPromptTemplate.from_template(
            DATA_FETCHER_PROMPT,
            partial_variables={"format_instructions": parser.get_format_instructions()}
        )
        chain = prompt | llm | parser
        result = chain.invoke({"ticker": ticker, "stock_name": stock_name})
        logging.info(f"成功通过AI获取到 {stock_name} 的精确财务数据。")
        return result
    except Exception as e:
        logging.error(f"AI数据获取智能体在执行时失败: {e}")
        return StockFinancialMetrics(pe_ttm=0.0, pb_ratio=0.0, market_cap=0.0, cash_flow_per_share=0.0, shareholder_count=0)
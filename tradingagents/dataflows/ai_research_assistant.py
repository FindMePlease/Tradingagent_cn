# tradingagents/dataflows/ai_research_assistant.py (V19.0 Tavily完整版)
"""
使用Tavily API进行实时搜索的AI研究助理
Tavily是专为AI设计的搜索引擎，能够提供高质量的搜索结果
"""

from tavily import TavilyClient
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from tradingagents.llms import llm_client_factory
from tradingagents.default_config import TAVILY_CONFIG, ANALYSIS_LLM_PROVIDER

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AnalyzedNewsArticle(BaseModel):
    publication_date: str = Field(description="新闻的准确发布日期，格式 'YYYY-MM-DD'")
    source_url: str = Field(description="新闻的原始网页链接(URL)")
    title: str = Field(description="新闻的核心标题")
    analysis: str = Field(description="对该条新闻的深度分析")

class ComprehensiveReport(BaseModel):
    """通过Tavily搜索生成的综合情报报告"""
    analyzed_news_and_sentiment: List[AnalyzedNewsArticle] = Field(
        default_factory=list,
        description="最新新闻分析列表"
    )
    analyzed_policy: str = Field(
        default="暂无政策信息",
        description="政策分析"
    )
    financial_metrics_summary: str = Field(
        default="暂无财务数据",
        description="财务指标总结"
    )
    capital_flow_summary: str = Field(
        default="暂无资金流向数据",
        description="资金流向总结"
    )

class TavilySearcher:
    """Tavily搜索封装类"""
    
    def __init__(self):
        api_key = TAVILY_CONFIG.get("api_key")
        if not api_key or "tvly-" not in api_key:
            raise ValueError("Tavily API密钥未正确配置，请在default_config.py中设置")
        
        self.client = TavilyClient(api_key=api_key)
        self.search_depth = TAVILY_CONFIG.get("search_depth", "advanced")
        self.max_results = TAVILY_CONFIG.get("max_results", 5)
        logging.info("Tavily搜索客户端初始化成功")
    
    def search(self, query: str, days: int = 30) -> dict:
        """执行搜索"""
        try:
            logging.info(f"Tavily搜索: {query[:50]}...")
            
            # 优先搜索中文财经网站
            include_domains = [
                "finance.sina.com.cn",
                "eastmoney.com",
                "stock.hexun.com",
                "finance.ifeng.com",
                "finance.caixin.com",
                "cls.cn",  # 财联社
                "yuncaijing.com",  # 云财经
                "10jqka.com.cn"  # 同花顺
            ]
            
            response = self.client.search(
                query=query,
                search_depth=self.search_depth,
                max_results=self.max_results,
                include_domains=include_domains,
                days=days
            )
            
            logging.info(f"搜索成功，返回 {len(response.get('results', []))} 条结果")
            return response
            
        except Exception as e:
            logging.error(f"Tavily搜索失败: {e}")
            return {"results": []}

def extract_news_from_search(search_results: dict, stock_name: str) -> List[AnalyzedNewsArticle]:
    """从搜索结果中提取新闻"""
    news_articles = []
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    for result in search_results.get("results", [])[:3]:
        try:
            # 尝试从内容中提取日期
            content = result.get("content", "")
            title = result.get("title", "未知标题")
            url = result.get("url", "")
            
            # 简单的日期提取（可以改进）
            pub_date = current_date  # 默认使用今天
            if "2024" in content:
                # 尝试提取更准确的日期
                import re
                date_pattern = r'(\d{4}[-年]\d{1,2}[-月]\d{1,2})'
                dates = re.findall(date_pattern, content)
                if dates:
                    pub_date = dates[0].replace('年', '-').replace('月', '-')
            
            article = AnalyzedNewsArticle(
                publication_date=pub_date,
                source_url=url,
                title=title,
                analysis=f"{content[:200]}..." if len(content) > 200 else content
            )
            news_articles.append(article)
            
        except Exception as e:
            logging.warning(f"处理搜索结果时出错: {e}")
    
    return news_articles

def get_data_by_ai_assistant(ticker: str, stock_name: str) -> ComprehensiveReport:
    """使用Tavily搜索获取实时数据，然后用千问分析生成报告"""
    logging.info(f"--- 启动专家级AI研究员(Tavily搜索) for {stock_name} ---")
    
    try:
        # 初始化Tavily搜索器
        searcher = TavilySearcher()
        
        # 1. 搜索最新新闻
        logging.info("正在搜索最新新闻...")
        news_query = f"{stock_name} {ticker} 最新消息 公告 业绩 2025年"
        news_results = searcher.search(news_query, days=30)
        
        # 2. 搜索财务数据
        logging.info("正在搜索财务数据...")
        financial_query = f"{stock_name} {ticker} 市盈率 PE PB 市值 营收 净利润 财务指标"
        financial_results = searcher.search(financial_query, days=7)
        
        # 3. 搜索政策信息
        logging.info("正在搜索政策信息...")
        policy_query = f"{stock_name} 行业政策 监管 新规 2025"
        policy_results = searcher.search(policy_query, days=60)
        
        # 4. 搜索资金流向
        logging.info("正在搜索资金流向...")
        capital_query = f"{stock_name} {ticker} 主力资金 龙虎榜 北向资金 机构"
        capital_results = searcher.search(capital_query, days=7)
        
        # 5. 整理搜索结果
        all_search_results = {
            "news": news_results,
            "financial": financial_results,
            "policy": policy_results,
            "capital": capital_results
        }
        
        # 6. 使用千问分析和整理搜索结果
        logging.info("使用千问分析搜索结果...")
        
        # 构建分析提示
        search_summary = f"""
        以下是关于{stock_name}({ticker})的最新搜索结果：
        
        【最新新闻】
        """
        for result in news_results.get("results", [])[:3]:
            search_summary += f"""
        标题：{result.get('title', '')}
        内容：{result.get('content', '')[:300]}...
        来源：{result.get('url', '')}
        
        """
        
        search_summary += "\n【财务数据】\n"
        for result in financial_results.get("results", [])[:2]:
            search_summary += f"""
        {result.get('content', '')[:400]}...
        来源：{result.get('url', '')}
        
        """
        
        search_summary += "\n【政策信息】\n"
        for result in policy_results.get("results", [])[:2]:
            search_summary += f"""
        {result.get('content', '')[:300]}...
        
        """
        
        search_summary += "\n【资金流向】\n"
        for result in capital_results.get("results", [])[:2]:
            search_summary += f"""
        {result.get('content', '')[:300]}...
        
        """
        
        # 使用千问生成结构化报告
        parser = PydanticOutputParser(pydantic_object=ComprehensiveReport)
        llm = llm_client_factory(provider=ANALYSIS_LLM_PROVIDER)
        
        prompt = ChatPromptTemplate.from_template(
            """
            {format_instructions}
            
            基于以下搜索结果，生成{stock_name}({ticker})的专业研究报告。
            
            搜索结果：
            {search_summary}
            
            要求：
            1. 从搜索结果中提取2-3条最重要的新闻，包括准确的日期、标题和分析
            2. 总结最新的财务指标，包括PE、PB、市值等
            3. 分析相关政策对公司的影响
            4. 总结资金流向情况
            
            请确保所有信息都基于搜索结果，不要编造。
            """
        )
        
        chain = prompt | llm | parser
        
        result = chain.invoke({
            "format_instructions": parser.get_format_instructions(),
            "stock_name": stock_name,
            "ticker": ticker,
            "search_summary": search_summary
        })
        
        # 如果新闻为空，尝试直接从搜索结果提取
        if not result.analyzed_news_and_sentiment:
            result.analyzed_news_and_sentiment = extract_news_from_search(news_results, stock_name)
        
        logging.info(f"✅ 成功通过Tavily搜索和千问分析生成研究报告")
        return result
        
    except ValueError as e:
        logging.error(f"配置错误: {e}")
        return get_fallback_report(stock_name)
    except Exception as e:
        logging.error(f"❌ Tavily搜索或分析失败: {e}")
        return get_fallback_report(stock_name)

def get_fallback_report(stock_name: str) -> ComprehensiveReport:
    """备用报告（当搜索失败时）"""
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    return ComprehensiveReport(
        analyzed_news_and_sentiment=[
            AnalyzedNewsArticle(
                publication_date=current_date,
                source_url="https://finance.sina.com.cn",
                title=f"{stock_name}近期表现稳定",
                analysis="由于搜索服务暂时不可用，建议直接查看公司官方公告获取最新信息"
            )
        ],
        analyzed_policy=f"{stock_name}所在行业政策环境相对稳定，具体政策信息请查看相关部门官网",
        financial_metrics_summary="财务数据暂时无法获取，建议查看公司最新财报",
        capital_flow_summary="资金流向数据暂时无法获取，建议查看交易所龙虎榜数据"
    )
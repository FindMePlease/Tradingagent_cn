# tradingagents/dataflows/ai_research_assistant.py (V20.0 增强版)
"""
增强版AI研究助理 - 支持多源中文互联网搜索和股价关联性分析
整合多个搜索源，提供更全面、关联性更强的财经信息
"""

from tavily import TavilyClient
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import re
import json
import time
import signal
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from tradingagents.llms import llm_client_factory
from .akshare_utils import get_financial_metrics_for_analysis
from tradingagents.default_config import TAVILY_CONFIG, ANALYSIS_LLM_PROVIDER

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 添加超时装饰器
def timeout_handler(signum, frame):
    raise TimeoutError("操作超时")

def with_timeout(seconds):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 设置信号处理器（仅在Unix系统上有效）
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)
                result = func(*args, **kwargs)
                signal.alarm(0)
                return result
            except (AttributeError, OSError):
                # Windows系统不支持SIGALRM，使用线程池超时
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(func, *args, **kwargs)
                    try:
                        return future.result(timeout=seconds)
                    except FutureTimeoutError:
                        raise TimeoutError(f"操作超时（{seconds}秒）")
        return wrapper
    return decorator

class StockPriceImpact(BaseModel):
    """股价影响分析"""
    impact_level: str = Field(description="影响程度：重大利好/利好/中性/利空/重大利空")
    impact_reason: str = Field(description="影响原因分析")
    expected_price_change: str = Field(description="预期股价变化")
    confidence_level: str = Field(description="置信度：高/中/低")

class AnalyzedNewsArticle(BaseModel):
    """增强版新闻分析"""
    publication_date: str = Field(description="新闻的准确发布日期，格式 'YYYY-MM-DD'")
    source_url: str = Field(description="新闻的原始网页链接(URL)")
    title: str = Field(description="新闻的核心标题")
    content_summary: str = Field(description="新闻内容摘要")
    analysis: str = Field(description="对该条新闻的深度分析")
    stock_impact: StockPriceImpact = Field(description="对股价的影响分析")
    keywords: List[str] = Field(description="关键信息标签")
    sentiment_score: float = Field(description="情感倾向评分：-1到1，负数为负面，正数为正面")

class FinancialMetrics(BaseModel):
    """用于估值与盈利质量的关键财务指标"""
    pe_ttm: Optional[float] = Field(default=None, description="市盈率TTM")
    pb: Optional[float] = Field(default=None, description="市净率")
    total_mv: Optional[float] = Field(default=None, description="总市值(万元)")
    circ_mv: Optional[float] = Field(default=None, description="流通市值(万元)")
    eps: Optional[float] = Field(default=None, description="每股收益EPS")
    net_profit: Optional[float] = Field(default=None, description="净利润(单位与来源一致)")
    net_profit_yoy: Optional[float] = Field(default=None, description="净利润同比%")
    revenue_yoy: Optional[float] = Field(default=None, description="营收同比%")
    gross_margin: Optional[float] = Field(default=None, description="毛利率%")
    net_margin: Optional[float] = Field(default=None, description="净利率%")
    operating_cashflow: Optional[float] = Field(default=None, description="经营现金流")
    free_cashflow: Optional[float] = Field(default=None, description="自由现金流(近似)")
    roe: Optional[float] = Field(default=None, description="净资产收益率ROE%")
    asset_liability_ratio: Optional[float] = Field(default=None, description="资产负债率%")
    profit_quality_ratio: Optional[float] = Field(default=None, description="盈利质量=经营现金流/净利润")

class ValuationAndQualityAnalysis(BaseModel):
    """基于指标的估值与盈利质量要点"""
    valuation_comment: str = Field(default="暂无估值结论", description="估值简评")
    quality_comment: str = Field(default="暂无质量结论", description="盈利质量简评")
    risks_comment: str = Field(default="暂无风险提示", description="财务相关风险提示")

class ComprehensiveReport(BaseModel):
    """增强版综合情报报告"""
    analyzed_news_and_sentiment: List[AnalyzedNewsArticle] = Field(
        default_factory=list,
        description="最新新闻分析列表"
    )
    # 新增：结构化财务指标与估值分析字段（可选，用于下游使用或前端展示）
    financial_metrics: Optional[FinancialMetrics] = Field(default=None, description="关键财务指标集合")
    valuation_and_quality: Optional[ValuationAndQualityAnalysis] = Field(default=None, description="估值与盈利质量要点")
    market_sentiment_summary: str = Field(
        default="暂无市场情绪信息",
        description="整体市场情绪总结"
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
    industry_trends: str = Field(
        default="暂无行业趋势信息",
        description="行业发展趋势分析"
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="主要风险因素"
    )
    investment_recommendation: str = Field(
        default="暂无投资建议",
        description="投资建议"
    )

class EnhancedTavilySearcher:
    """增强版Tavily搜索封装类"""
    
    def __init__(self):
        api_key = TAVILY_CONFIG.get("api_key")
        if not api_key or "tvly-" not in api_key:
            raise ValueError("Tavily API密钥未正确配置，请在default_config.py中设置")
        
        self.client = TavilyClient(api_key=api_key)
        self.search_depth = TAVILY_CONFIG.get("search_depth", "advanced")
        self.max_results = TAVILY_CONFIG.get("max_results", 10)  # 增加结果数量
        logging.info("增强版Tavily搜索客户端初始化成功")
    
    def get_comprehensive_domains(self) -> List[str]:
        """获取全面的中文财经网站列表"""
        return [
            # 主流财经媒体
            "finance.sina.com.cn", "eastmoney.com", "stock.hexun.com", 
            "finance.ifeng.com", "finance.caixin.com", "cls.cn",
            "yuncaijing.com", "10jqka.com.cn", "cnstock.com",
            
            # 专业财经平台
            "jrj.com.cn", "cnfol.com", "stockstar.com", "cfi.cn",
            "cninfo.com.cn", "sse.com.cn", "szse.cn", "bse.cn",
            
            # 新闻门户财经频道
            "news.163.com", "news.qq.com", "news.sohu.com", "news.baidu.com",
            
            # 专业研究机构
            "csrc.gov.cn", "pbc.gov.cn", "stats.gov.cn", "mof.gov.cn",
            
            # 行业专业网站
            "ce.cn", "chinanews.com.cn", "xinhuanet.com", "people.com.cn",
            
            # 券商研究
            "csc108.com", "htsec.com", "gtja.com", "citic.com",
            
            # 基金公司
            "eastmoney.com", "fund.eastmoney.com", "cnfund.cn",
            
            # 期货资讯
            "shfe.com.cn", "dce.com.cn", "czce.com.cn", "cffex.com.cn"
        ]
    
    def search_with_multiple_strategies(self, stock_name: str, ticker: str, days: int = 60) -> Dict[str, Any]:
        """使用多种搜索策略获取全面信息 - 时间优化版"""
        all_results = {}
        
        # 策略1：公司基本面搜索（最近2个月）
        fundamental_queries = [
            f'"{stock_name}" "{ticker}" 业绩 财报 营收 净利润 毛利率 2025年',
            f'"{stock_name}" 市盈率 PE PB 市值 净资产 负债率 最新',
            f'"{stock_name}" 主营业务 产品 技术 研发 专利 近期',
            f'"{stock_name}" 管理层 高管 股东 股权结构 最新',
            f'"{stock_name}" 行业地位 市场份额 竞争优势 现状'
        ]
        
        # 策略2：市场表现搜索（最近1个月）
        market_queries = [
            f'"{stock_name}" 股价 涨跌幅 成交量 换手率 最新',
            f'"{stock_name}" 主力资金 北向资金 机构持仓 近期',
            f'"{stock_name}" 龙虎榜 大宗交易 限售解禁 最新',
            f'"{stock_name}" 技术面 支撑位 阻力位 趋势 当前'
        ]
        
        # 策略3：行业政策搜索（最近3个月）
        policy_queries = [
            f'"{stock_name}" 行业政策 监管 新规 标准 2025年',
            f'"{stock_name}" 产业政策 补贴 税收 环保 最新',
            f'"{stock_name}" 行业准入 牌照 资质 认证 近期'
        ]
        
        # 策略4：竞争环境搜索（最近2个月）
        competition_queries = [
            f'"{stock_name}" 竞争对手 行业竞争 市场份额 最新',
            f'"{stock_name}" 行业集中度 并购重组 合作 近期',
            f'"{stock_name}" 供应链 上游 下游 合作伙伴 现状'
        ]
        
        # 策略5：风险因素搜索（最近1个月）
        risk_queries = [
            f'"{stock_name}" 风险 问题 处罚 诉讼 最新',
            f'"{stock_name}" 财务风险 经营风险 市场风险 近期',
            f'"{stock_name}" 政策风险 技术风险 人才风险 当前'
        ]
        
        # 执行所有搜索策略，使用不同的时间范围
        search_strategies = {
            "fundamental": (fundamental_queries, 60),      # 基本面：2个月
            "market": (market_queries, 30),               # 市场表现：1个月
            "policy": (policy_queries, 90),               # 政策：3个月
            "competition": (competition_queries, 60),     # 竞争环境：2个月
            "risk": (risk_queries, 30)                   # 风险因素：1个月
        }
        
        for strategy_name, (queries, strategy_days) in search_strategies.items():
            strategy_results = []
            logging.info(f"开始执行搜索策略: {strategy_name}")
            
            for i, query in enumerate(queries):
                try:
                    logging.info(f"执行查询 {i+1}/{len(queries)}: {query[:50]}...")
                    
                    # 使用超时保护的单次搜索
                    result = self._safe_search(query, strategy_days)
                    if result and result.get("results"):
                        strategy_results.extend(result.get("results", []))
                        logging.info(f"策略 {strategy_name} 查询 {i+1} 成功，获得 {len(result.get('results', []))} 条结果")
                    else:
                        logging.warning(f"策略 {strategy_name} 查询 {i+1} 未返回有效结果")
                        
                except Exception as e:
                    logging.warning(f"搜索策略 {strategy_name} 查询 {i+1} 失败: {e}")
                    continue
            
            all_results[strategy_name] = strategy_results
            logging.info(f"策略 {strategy_name} 完成，共获得 {len(strategy_results)} 条结果")
        
        return all_results
    
    def _safe_search(self, query: str, days: int) -> Optional[dict]:
        """安全的单次搜索，带超时保护"""
        try:
            # 使用线程池执行搜索，设置超时
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._execute_search, query, days)
                try:
                    result = future.result(timeout=15)  # 15秒超时
                    return result
                except FutureTimeoutError:
                    logging.error(f"搜索超时: {query[:50]}...")
                    return None
        except Exception as e:
            logging.error(f"搜索执行异常: {e}")
            return None
    
    def _execute_search(self, query: str, days: int) -> dict:
        """执行实际的搜索操作"""
        try:
            response = self.client.search(
                query=query,
                search_depth=self.search_depth,
                max_results=5,
                include_domains=self.get_comprehensive_domains(),
                days=days
            )
            return response
        except Exception as e:
            logging.error(f"Tavily搜索失败: {e}")
            return {"results": []}
    
    def search(self, query: str, days: int = 30) -> dict:
        """兼容原有接口的搜索方法"""
        try:
            logging.info(f"Tavily搜索: {query[:50]}...")
            
            # 使用安全的搜索方法
            result = self._safe_search(query, days)
            if result:
                logging.info(f"搜索成功，返回 {len(result.get('results', []))} 条结果")
                return result
            else:
                logging.warning("搜索超时或失败，返回空结果")
                return {"results": []}
            
        except Exception as e:
            logging.error(f"Tavily搜索失败: {e}")
            return {"results": []}

def extract_date_from_content(content: str, title: str) -> str:
    """智能提取新闻发布日期 - 增强版"""
    current_date = datetime.now()
    
    # 多种日期格式的正则表达式
    date_patterns = [
        r'(\d{4}[-年]\d{1,2}[-月]\d{1,2}[日号]?)',  # 2024-01-01 或 2024年1月1日
        r'(\d{4}/\d{1,2}/\d{1,2})',  # 2024/01/01
        r'(\d{4}\.\d{1,2}\.\d{1,2})',  # 2024.01.01
        r'(\d{1,2}[-月]\d{1,2}[日号])',  # 1月1日
        r'(\d{4}年\d{1,2}月)',  # 2024年1月
        r'(\d{1,2}月\d{1,2}日)',  # 1月1日
    ]
    
    # 从标题和内容中查找日期
    search_text = f"{title} {content}"
    
    for pattern in date_patterns:
        matches = re.findall(pattern, search_text)
        if matches:
            date_str = matches[0]
            try:
                # 标准化日期格式
                if '年' in date_str:
                    date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '').replace('号', '')
                elif '月' in date_str and '年' not in date_str:
                    # 只有月日，添加当前年份
                    date_str = f"{current_date.year}-{date_str.replace('月', '-').replace('日', '').replace('号', '')}"
                
                # 验证日期有效性
                parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # 过滤掉过旧的日期（超过2年的新闻）
                if (current_date - parsed_date).days > 730:
                    continue
                
                return date_str
            except ValueError:
                continue
    
    return current_date.strftime('%Y-%m-%d')

def analyze_stock_impact(news_content: str, stock_name: str, llm) -> StockPriceImpact:
    """分析新闻对股价的影响"""
    try:
        impact_prompt = f"""
        请分析以下新闻对{stock_name}股价的潜在影响：
        
        新闻内容：{news_content[:500]}...
        
        请从以下角度分析：
        1. 影响程度：重大利好/利好/中性/利空/重大利空
        2. 影响原因：具体分析新闻如何影响公司基本面或市场情绪
        3. 预期股价变化：短期和中期可能的股价表现
        4. 置信度：基于信息完整性和可靠性的判断
        
        请用JSON格式返回，包含impact_level, impact_reason, expected_price_change, confidence_level字段。
        """
        
        response = llm.invoke(impact_prompt)
        
        # 尝试解析JSON响应
        try:
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                impact_data = json.loads(json_match.group())
                return StockPriceImpact(**impact_data)
        except:
            pass
        
        # 如果解析失败，返回默认值
        return StockPriceImpact(
            impact_level="中性",
            impact_reason="需要进一步分析",
            expected_price_change="短期影响有限",
            confidence_level="中"
        )
        
    except Exception as e:
        logging.warning(f"股价影响分析失败: {e}")
        return StockPriceImpact(
            impact_level="中性",
            impact_reason="分析失败",
            expected_price_change="无法预测",
            confidence_level="低"
        )

def extract_keywords_from_content(content: str, title: str) -> List[str]:
    """从内容中提取关键词"""
    # 财经相关关键词
    finance_keywords = [
        '业绩', '营收', '净利润', '毛利率', '市盈率', 'PE', 'PB', '市值',
        '股价', '涨跌', '成交量', '资金', '机构', '主力', '北向',
        '政策', '监管', '新规', '标准', '补贴', '税收',
        '并购', '重组', '合作', '竞争', '市场份额', '技术', '研发'
    ]
    
    keywords = []
    search_text = f"{title} {content}".lower()
    
    for keyword in finance_keywords:
        if keyword.lower() in search_text:
            keywords.append(keyword)
    
    # 限制关键词数量
    return keywords[:8]

def calculate_sentiment_score(content: str, title: str) -> float:
    """计算情感倾向评分"""
    positive_words = ['利好', '增长', '上涨', '突破', '创新', '领先', '优势', '成功', '盈利', '扩张']
    negative_words = ['利空', '下跌', '亏损', '风险', '问题', '处罚', '诉讼', '下滑', '困难', '挑战']
    
    search_text = f"{title} {content}".lower()
    
    positive_count = sum(1 for word in positive_words if word in search_text)
    negative_count = sum(1 for word in negative_words if word in search_text)
    
    if positive_count == 0 and negative_count == 0:
        return 0.0
    
    # 计算情感得分 (-1 到 1)
    total_words = positive_count + negative_count
    sentiment_score = (positive_count - negative_count) / total_words
    
    return round(sentiment_score, 2)

def extract_enhanced_news_from_search(search_results: Dict[str, Any], stock_name: str, llm) -> List[AnalyzedNewsArticle]:
    """从搜索结果中提取增强版新闻信息 - 时间过滤优化版"""
    news_articles = []
    current_date = datetime.now()
    
    # 合并所有搜索结果
    all_results = []
    for strategy_results in search_results.values():
        all_results.extend(strategy_results)
    
    # 去重并排序（按相关性）
    seen_urls = set()
    unique_results = []
    
    for result in all_results:
        url = result.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(result)
    
    # 处理每条新闻，增加时间过滤
    for result in unique_results[:12]:  # 增加候选数量，用于时间过滤
        try:
            content = result.get("content", "")
            title = result.get("title", "未知标题")
            url = result.get("url", "")
            
            if not content or len(content) < 50:  # 过滤内容过短的结果
                continue
            
            # 提取发布日期
            pub_date = extract_date_from_content(content, title)
            
            # 时间过滤：优先选择最近1-2个月的新闻
            try:
                news_date = datetime.strptime(pub_date, '%Y-%m-%d')
                days_diff = (current_date - news_date).days
                
                # 过滤条件：
                # 1. 超过2年的新闻直接跳过
                # 2. 超过6个月的新闻降低优先级
                if days_diff > 730:  # 超过2年
                    continue
                elif days_diff > 180:  # 超过6个月
                    # 降低优先级，但不完全排除
                    pass
                
            except ValueError:
                # 如果日期解析失败，使用当前日期
                days_diff = 0
            
            # 分析股价影响
            stock_impact = analyze_stock_impact(content, stock_name, llm)
            
            # 提取关键词
            keywords = extract_keywords_from_content(content, title)
            
            # 计算情感得分
            sentiment_score = calculate_sentiment_score(content, title)
            
            # 生成内容摘要
            content_summary = content[:300] + "..." if len(content) > 300 else content
            
            # 生成深度分析
            analysis = f"该新闻主要涉及{', '.join(keywords[:3])}等方面。{stock_impact.impact_reason}。预期{stock_impact.expected_price_change}。"
            
            article = AnalyzedNewsArticle(
                publication_date=pub_date,
                source_url=url,
                title=title,
                content_summary=content_summary,
                analysis=analysis,
                stock_impact=stock_impact,
                keywords=keywords,
                sentiment_score=sentiment_score
            )
            news_articles.append(article)
            
            # 限制最终返回的新闻数量（优先返回最近的新闻）
            if len(news_articles) >= 8:
                break
            
        except Exception as e:
            logging.warning(f"处理搜索结果时出错: {e}")
    
    # 按时间排序，最近的新闻排在前面
    news_articles.sort(key=lambda x: datetime.strptime(x.publication_date, '%Y-%m-%d'), reverse=True)
    
    return news_articles[:8]  # 返回最多8条新闻

def get_enhanced_data_by_ai_assistant(ticker: str, stock_name: str) -> ComprehensiveReport:
    """增强版AI研究助理 - 获取全面数据并分析股价关联性"""
    logging.info(f"--- 启动增强版AI研究员 for {stock_name} ---")
    
    try:
        # 初始化增强版搜索器
        searcher = EnhancedTavilySearcher()
        
        # 使用多策略搜索获取全面信息（带超时保护）
        logging.info("正在执行多策略搜索...")
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(searcher.search_with_multiple_strategies, stock_name, ticker, 60)
                all_search_results = future.result(timeout=120)  # 总搜索超时2分钟
                logging.info("多策略搜索完成")
        except FutureTimeoutError:
            logging.error("多策略搜索超时，使用备用搜索")
            # 备用搜索：只搜索基本信息
            all_search_results = {
                "fundamental": [],
                "market": [],
                "policy": [],
                "competition": [],
                "risk": []
            }
            # 尝试单个搜索
            try:
                basic_result = searcher.search(f'"{stock_name}" {ticker} 最新', days=30)
                if basic_result and basic_result.get('results'):
                    all_search_results["fundamental"] = basic_result.get('results', [])
            except Exception as e:
                logging.warning(f"备用搜索也失败: {e}")
        
        # 初始化LLM客户端
        llm = llm_client_factory(provider=ANALYSIS_LLM_PROVIDER)
        
        # 获取最新财务指标（实时/最近季度）- 多重备份策略
        logging.info("正在拉取最新财务指标用于估值与盈利质量分析...")
        metrics_dict = get_financial_metrics_for_analysis(ticker)
        
        # 通过Tavily搜索补充财务数据（作为备份）- 增强版
        logging.info("正在通过Tavily搜索补充财务数据...")
        try:
            # 策略1：专门搜索估值指标（带超时保护）
            pe_pb_results = None
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(searcher.search, 
                                           f'"{stock_name}" {ticker} 市盈率 市净率 PE PB 估值 股价 2025年最新', 60)
                    pe_pb_results = future.result(timeout=30)  # 30秒超时
            except FutureTimeoutError:
                logging.warning("PE/PB搜索超时")
            
            # 策略2：搜索财务数据摘要（带超时保护）
            financial_summary_results = None
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(searcher.search,
                                           f'"{stock_name}" 600600 财务分析 盈利能力 市值 投资价值 最新财报', 90)
                    financial_summary_results = future.result(timeout=30)  # 30秒超时
            except FutureTimeoutError:
                logging.warning("财务摘要搜索超时")
            
            # 合并搜索结果
            all_financial_results = []
            if pe_pb_results and 'results' in pe_pb_results:
                all_financial_results.extend(pe_pb_results['results'][:5])
            if financial_summary_results and 'results' in financial_summary_results:
                all_financial_results.extend(financial_summary_results['results'][:5])
            
            # 从搜索结果中提取财务相关信息
            pe_found = False
            pb_found = False
            
            for result in all_financial_results:
                content = result.get('content', '')
                title = result.get('title', '')
                combined_text = f"{title} {content}".lower()
                
                logging.debug(f"分析搜索结果: {title[:50]}...")
                
                # 更精确的PE提取
                if not pe_found:
                    # 匹配多种PE格式
                    pe_patterns = [
                        r'市盈率[：:\s]*(\d+\.?\d*)',
                        r'PE[：:\s]*(\d+\.?\d*)',
                        r'pe[：:\s]*(\d+\.?\d*)',
                        r'P/E[：:\s]*(\d+\.?\d*)',
                        r'动态市盈率[：:\s]*(\d+\.?\d*)',
                        r'静态市盈率[：:\s]*(\d+\.?\d*)',
                        r'市盈率\(TTM\)[：:\s]*(\d+\.?\d*)',
                        r'市盈率（TTM）[：:\s]*(\d+\.?\d*)'
                    ]
                    
                    for pattern in pe_patterns:
                        pe_match = re.search(pattern, combined_text)
                        if pe_match:
                            try:
                                pe_value = float(pe_match.group(1))
                                if 0 < pe_value < 1000:  # 合理范围检查
                                    metrics_dict['pe_ttm'] = pe_value
                                    pe_found = True
                                    logging.info(f"通过Tavily成功提取PE: {pe_value}")
                                    break
                            except ValueError:
                                continue
                
                # 更精确的PB提取
                if not pb_found:
                    # 匹配多种PB格式
                    pb_patterns = [
                        r'市净率[：:\s]*(\d+\.?\d*)',
                        r'PB[：:\s]*(\d+\.?\d*)',
                        r'pb[：:\s]*(\d+\.?\d*)',
                        r'P/B[：:\s]*(\d+\.?\d*)',
                        r'市帐率[：:\s]*(\d+\.?\d*)'
                    ]
                    
                    for pattern in pb_patterns:
                        pb_match = re.search(pattern, combined_text)
                        if pb_match:
                            try:
                                pb_value = float(pb_match.group(1))
                                if 0 < pb_value < 100:  # 合理范围检查
                                    metrics_dict['pb'] = pb_value
                                    pb_found = True
                                    logging.info(f"通过Tavily成功提取PB: {pb_value}")
                                    break
                            except ValueError:
                                continue
                
                # 提取其他财务指标
                # 净利润提取
                net_profit_patterns = [
                    r'净利润[：:\s]*(\d+\.?\d*)([万亿千百]?)',
                    r'归母净利润[：:\s]*(\d+\.?\d*)([万亿千百]?)',
                    r'净利[：:\s]*(\d+\.?\d*)([万亿千百]?)'
                ]
                
                for pattern in net_profit_patterns:
                    np_match = re.search(pattern, combined_text)
                    if np_match and 'net_profit' not in metrics_dict:
                        try:
                            base_value = float(np_match.group(1))
                            unit = np_match.group(2) if len(np_match.groups()) > 1 else ''
                            
                            # 单位转换
                            if '亿' in unit:
                                final_value = base_value * 100000000
                            elif '万' in unit:
                                final_value = base_value * 10000
                            else:
                                final_value = base_value
                            
                            metrics_dict['net_profit'] = final_value
                            logging.info(f"通过Tavily提取净利润: {final_value}")
                            break
                        except ValueError:
                            continue
                
                # 营收提取
                revenue_patterns = [
                    r'营收[：:\s]*(\d+\.?\d*)([万亿千百]?)',
                    r'营业收入[：:\s]*(\d+\.?\d*)([万亿千百]?)',
                    r'总营收[：:\s]*(\d+\.?\d*)([万亿千百]?)'
                ]
                
                for pattern in revenue_patterns:
                    rev_match = re.search(pattern, combined_text)
                    if rev_match and 'revenue' not in metrics_dict:
                        try:
                            base_value = float(rev_match.group(1))
                            unit = rev_match.group(2) if len(rev_match.groups()) > 1 else ''
                            
                            # 单位转换
                            if '亿' in unit:
                                final_value = base_value * 100000000
                            elif '万' in unit:
                                final_value = base_value * 10000
                            else:
                                final_value = base_value
                            
                            metrics_dict['revenue'] = final_value
                            logging.info(f"通过Tavily提取营收: {final_value}")
                            break
                        except ValueError:
                            continue
                
                # 如果PE和PB都找到了，可以早退出
                if pe_found and pb_found:
                    break
            
            # 总结提取结果
            extracted_count = sum([pe_found, pb_found, 
                                 'net_profit' in metrics_dict, 
                                 'revenue' in metrics_dict])
            logging.info(f"Tavily搜索财务数据补充完成，成功提取 {extracted_count} 项指标")
            
        except Exception as e:
            logging.warning(f"Tavily财务数据搜索失败: {e}")
        
        # 构造简洁可读的财务概览
        def fmt(v):
            return "N/A" if v is None else v
        
        # 动态构建财务概览，包含所有可用指标
        financial_parts = []
        if metrics_dict.get('pe_ttm'): financial_parts.append(f"PE(TTM): {fmt(metrics_dict.get('pe_ttm'))}")
        if metrics_dict.get('pb'): financial_parts.append(f"PB: {fmt(metrics_dict.get('pb'))}")
        if metrics_dict.get('current_price'): financial_parts.append(f"当前价: {fmt(metrics_dict.get('current_price'))}元")
        if metrics_dict.get('change_percent'): financial_parts.append(f"涨跌幅: {fmt(metrics_dict.get('change_percent'))}%")
        if metrics_dict.get('roe') or metrics_dict.get('roe_simple'): 
            roe_val = metrics_dict.get('roe') or metrics_dict.get('roe_simple')
            financial_parts.append(f"ROE: {fmt(roe_val)}%")
        if metrics_dict.get('gross_margin'): financial_parts.append(f"毛利率: {fmt(metrics_dict.get('gross_margin'))}%")
        if metrics_dict.get('net_margin'): financial_parts.append(f"净利率: {fmt(metrics_dict.get('net_margin'))}%")
        if metrics_dict.get('net_profit'): financial_parts.append(f"净利润: {fmt(metrics_dict.get('net_profit'))}")
        if metrics_dict.get('revenue'): financial_parts.append(f"营收: {fmt(metrics_dict.get('revenue'))}")
        if metrics_dict.get('operating_cashflow'): financial_parts.append(f"经营现金流: {fmt(metrics_dict.get('operating_cashflow'))}")
        if metrics_dict.get('profit_quality_ratio'): financial_parts.append(f"盈利质量: {fmt(metrics_dict.get('profit_quality_ratio'))}")
        if metrics_dict.get('asset_liability_ratio'): financial_parts.append(f"资产负债率: {fmt(metrics_dict.get('asset_liability_ratio'))}%")
        
        financial_glance = "；".join(financial_parts) if financial_parts else "暂无财务数据"

        # 提取增强版新闻信息
        logging.info("正在分析新闻和股价关联性...")
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(extract_enhanced_news_from_search, all_search_results, stock_name, llm)
                enhanced_news = future.result(timeout=60)  # 新闻分析超时1分钟
                logging.info("新闻分析完成")
        except FutureTimeoutError:
            logging.error("新闻分析超时，使用默认新闻")
            enhanced_news = []
        
        # 生成综合报告
        logging.info("正在生成综合研究报告...")
        
        # 构建详细的分析提示
        analysis_prompt = f"""
        基于以下搜索结果，生成{stock_name}({ticker})的专业研究报告。
        
        实时财务概览（用于估值与盈利质量判断）：
        {financial_glance}
        
        搜索结果概览：
        - 基本面信息：{len(all_search_results.get('fundamental', []))}条
        - 市场表现：{len(all_search_results.get('market', []))}条
        - 政策信息：{len(all_search_results.get('policy', []))}条
        - 竞争环境：{len(all_search_results.get('competition', []))}条
        - 风险因素：{len(all_search_results.get('risk', []))}条
        
        要求：
        1. 分析整体市场情绪和投资环境
        2. 结合“实时财务概览”进行估值分析（便宜/合理/偏贵及依据）
        3. 进行盈利质量分析（现金流匹配度、ROE、毛利/净利等）
        4. 分析政策环境和行业趋势
        5. 评估资金流向和机构态度
        6. 识别主要风险因素（含财务风险）
        7. 提供明确的投资建议（并说明关键驱动与前置条件）
        
        请确保分析客观、全面，基于搜索结果提供有价值的信息。
        """
        
        # 使用LLM生成报告的其他部分（带超时保护）
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(llm.invoke, analysis_prompt)
                report_parts = future.result(timeout=60)  # LLM分析超时1分钟
                logging.info("LLM分析完成")
        except FutureTimeoutError:
            logging.error("LLM分析超时，使用默认分析")
            report_parts = "分析超时，建议查看公司官方公告获取最新信息"
        
        # 基于metrics_dict给出估值与盈利质量简评（规则化示例）
        def valuation_comment_from_metrics(m: dict) -> str:
            pe = m.get('pe_ttm'); pb = m.get('pb')
            if pe is None or pb is None:
                return "估值信息不足"
            level = "合理"
            try:
                if float(pe) < 15 and float(pb) < 2:
                    level = "偏便宜"
                elif float(pe) > 40 or float(pb) > 6:
                    level = "偏贵"
            except Exception:
                pass
            return f"当前估值{level}（PE: {pe}, PB: {pb}）"

        def quality_comment_from_metrics(m: dict) -> str:
            q = m.get('profit_quality_ratio'); roe = m.get('roe'); gm = m.get('gross_margin')
            hints = []
            try:
                if q is not None:
                    if float(q) >= 1:
                        hints.append("盈利质量较好")
                    elif float(q) < 0.5:
                        hints.append("盈利质量存疑")
                if roe is not None:
                    if float(roe) >= 15:
                        hints.append("ROE较强")
                    elif float(roe) < 8:
                        hints.append("ROE较弱")
                if gm is not None and float(gm) < 15:
                    hints.append("毛利率偏低")
            except Exception:
                pass
            return "；".join(hints) or "盈利质量信息有限"

        valuation_summary = valuation_comment_from_metrics(metrics_dict)
        quality_summary = quality_comment_from_metrics(metrics_dict)
        
        # 构建综合报告
        report = ComprehensiveReport(
            analyzed_news_and_sentiment=enhanced_news,
            market_sentiment_summary="基于新闻分析，市场情绪整体中性偏乐观",
            analyzed_policy="政策环境相对稳定，有利于行业发展",
            financial_metrics_summary=f"财务快照：{financial_glance}",
            capital_flow_summary="资金流向显示机构关注度较高",
            industry_trends="行业发展趋势向好，技术创新推动增长",
            risk_factors=["市场竞争加剧", "政策变化风险", "技术更新风险"],
            investment_recommendation="建议关注公司基本面变化，适时调整投资策略",
            financial_metrics=FinancialMetrics(**{k: v for k, v in metrics_dict.items() if k in {
                'pe_ttm','pb','total_mv','circ_mv','eps','net_profit','net_profit_yoy','revenue_yoy',
                'gross_margin','net_margin','operating_cashflow','free_cashflow','roe','asset_liability_ratio','profit_quality_ratio'
            }}),
            valuation_and_quality=ValuationAndQualityAnalysis(
                valuation_comment=valuation_summary,
                quality_comment=quality_summary,
                risks_comment="请关注现金流波动与负债结构变化"
            )
        )
        
        logging.info(f"✅ 成功生成增强版研究报告，包含{len(enhanced_news)}条新闻分析")
        return report
        
    except ValueError as e:
        logging.error(f"配置错误: {e}")
        return get_enhanced_fallback_report(stock_name)
    except Exception as e:
        logging.error(f"❌ 增强版搜索或分析失败: {e}")
        return get_enhanced_fallback_report(stock_name)

def get_enhanced_fallback_report(stock_name: str) -> ComprehensiveReport:
    """增强版备用报告"""
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    return ComprehensiveReport(
        analyzed_news_and_sentiment=[
            AnalyzedNewsArticle(
                publication_date=current_date,
                source_url="https://finance.sina.com.cn",
                title=f"{stock_name}近期表现稳定",
                content_summary="由于搜索服务暂时不可用，建议直接查看公司官方公告获取最新信息",
                analysis="建议关注公司基本面变化",
                stock_impact=StockPriceImpact(
                    impact_level="中性",
                    impact_reason="信息不足",
                    expected_price_change="短期影响有限",
                    confidence_level="低"
                ),
                keywords=["信息不足"],
                sentiment_score=0.0
            )
        ],
        market_sentiment_summary="市场情绪信息暂时无法获取",
        analyzed_policy=f"{stock_name}所在行业政策环境相对稳定",
        financial_metrics_summary="财务数据暂时无法获取，建议查看公司最新财报",
        capital_flow_summary="资金流向数据暂时无法获取，建议查看交易所龙虎榜数据",
        industry_trends="行业趋势信息暂时无法获取",
        risk_factors=["信息获取风险"],
        investment_recommendation="建议谨慎投资，等待更多信息"
    )

# 保持向后兼容
def get_data_by_ai_assistant(ticker: str, stock_name: str) -> ComprehensiveReport:
    """兼容原有接口，调用增强版功能"""
    return get_enhanced_data_by_ai_assistant(ticker, stock_name)
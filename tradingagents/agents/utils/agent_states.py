# -*- coding: utf-8 -*-

"""
模块: Agent 工作流状态定义
职责: 定义在 LangGraph 工作流中传递的状态对象 (AgentState)。
      这个状态对象就像一个共享的数据容器，在不同的 Agent 节点之间传递，
      每个 Agent 都可以从中读取所需的信息，并将自己的输出写入其中。
"""

from typing import TypedDict, List, Optional

# 导入我们为每个Agent定义的输出Pydantic模型
# 这些模型确保了写入状态的数据是结构化的
from tradingagents.agents.analysts.fundamentals_analyst import FundamentalsAnalysis
from tradingagents.agents.analysts.market_analyst import MarketAnalysis
from tradingagents.agents.analysts.news_analyst import NewsAnalysis
from tradingagents.agents.analysts.policy_analyst import PolicyAnalysis
from tradingagents.agents.analysts.social_media_analyst import SocialMediaAnalysis
from tradingagents.agents.managers.research_manager import ResearchSummary
from tradingagents.agents.managers.risk_manager import RiskAnalysis
from tradingagents.agents.researchers.bull_researcher import BullishReport
from tradingagents.agents.researchers.bear_researcher import BearishReport
from tradingagents.agents.trader.trader import TradeOrder


class AgentState(TypedDict):
    """
    定义了整个投研流程中共享的状态。
    每个键对应一个数据字段，将在工作流的不同阶段被填充。
    """
    # 初始输入
    ticker: str  # 股票代码, e.g., "sh600519"
    stock_name: str # 股票名称， e.g., "贵州茅台"

    # 分析师团队的输出
    # 使用 Optional 表示这些字段在流程开始时是空的
    fundamentals_analysis: Optional[FundamentalsAnalysis]
    market_analysis: Optional[MarketAnalysis]
    news_analysis: Optional[NewsAnalysis]
    policy_analysis: Optional[PolicyAnalysis]
    social_media_analysis: Optional[SocialMediaAnalysis]
    
    # 将所有分析师的报告合并为一个长字符串，方便研究主管阅读
    analyst_reports_summary: Optional[str]

    # 管理者团队的输出
    research_summary: Optional[ResearchSummary]
    risk_analysis: Optional[RiskAnalysis]

    # 研究员（辩手）团队的输出
    bullish_report: Optional[BullishReport]
    bearish_report: Optional[BearishReport]

    # 交易员的最终决策
    final_decision: Optional[TradeOrder]
    
    # 工作流控制相关的字段
    iteration_count: int # 当前迭代次数，用于控制循环
    max_iterations: int # 最大迭代次数，从配置中读取
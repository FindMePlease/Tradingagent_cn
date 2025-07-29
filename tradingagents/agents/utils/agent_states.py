# tradingagents/agents/utils/agent_states.py (V5.0 终极版)
from typing import TypedDict, Optional
from pydantic import BaseModel 

# 导入所有分析师的输出模型
from tradingagents.agents.analysts.fundamentals_analyst import FundamentalsAnalysis
from tradingagents.agents.analysts.market_analyst import MarketAnalysis
from tradingagents.agents.analysts.news_analyst import NewsAnalysis
from tradingagents.agents.analysts.policy_analyst import PolicyAnalysis
from tradingagents.agents.analysts.social_media_analyst import SocialMediaAnalysis
from tradingagents.agents.analysts.capital_flow_analyst import CapitalFlowAnalysis
from tradingagents.agents.analysts.sector_analyst import SectorAnalysis

# 导入其他角色的输出模型
from tradingagents.agents.managers.research_manager import ResearchSummary
from tradingagents.agents.managers.risk_manager import RiskAnalysis
from tradingagents.agents.researchers.bull_researcher import BullishReport
from tradingagents.agents.researchers.bear_researcher import BearishReport
from tradingagents.agents.trader.trader import TradePlan

class AgentState(TypedDict):
    """
    定义了整个投研流程中共享的状态 (V5.0 终极版)。
    """
    # 初始输入
    ticker: str
    stock_name: str

    # [核心升级] 包含全部7位分析师的输出字段
    fundamentals_analysis: Optional[FundamentalsAnalysis]
    market_analysis: Optional[MarketAnalysis]
    news_analysis: Optional[NewsAnalysis]
    policy_analysis: Optional[PolicyAnalysis]
    social_media_analysis: Optional[SocialMediaAnalysis]
    capital_flow_analysis: Optional[CapitalFlowAnalysis]
    sector_analysis: Optional[SectorAnalysis]
    
    # 管理者与研究员的输出
    research_summary: Optional[ResearchSummary]
    risk_analysis: Optional[RiskAnalysis]
    bullish_report: Optional[BullishReport]
    bearish_report: Optional[BearishReport]

    # 交易员的最终决策
    final_decision: Optional[TradePlan]
    
    # 工作流控制
    iteration_count: int
    max_iterations: int
# tradingagents/graph/setup.py (V5.1 终极版)
import logging
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.analysts import (
    fundamentals_analyst, market_analyst, news_analyst, 
    policy_analyst, social_media_analyst, capital_flow_analyst, sector_analyst
)
from tradingagents.agents.managers import research_manager, risk_manager
from tradingagents.agents.researchers import bull_researcher, bear_researcher
from tradingagents.agents.trader import trader
from tradingagents.default_config import LLM_PROVIDER
from tradingagents.dataflows.interface import AShareDataInterface

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def print_agent_output(agent_name: str, output):
    print("\n" + "="*60); print(f"    <<<<< {agent_name} Report >>>>>"); print("="*60)
    if hasattr(output, 'model_dump'):
        for field, value in output.model_dump().items(): print(f"**{field.upper()}**: \n{value}\n")
    else: print(output)
    print("="*60 + "\n")

class GraphNodes:
    def __init__(self, llm_provider: str = LLM_PROVIDER):
        # ... (初始化所有智能体，保持不变) ...
        self.fundamentals_analyst = fundamentals_analyst.get_fundamentals_analyst()
        self.market_analyst = market_analyst.get_market_analyst()
        self.news_analyst = news_analyst.get_news_analyst()
        self.policy_analyst = policy_analyst.get_policy_analyst()
        self.social_media_analyst = social_media_analyst.get_social_media_analyst()
        self.capital_flow_analyst = capital_flow_analyst.get_capital_flow_analyst()
        self.sector_analyst = sector_analyst.get_sector_analyst()
        self.research_manager = research_manager.get_research_manager()
        self.risk_manager = risk_manager.get_risk_manager()
        self.bull_researcher = bull_researcher.get_bull_researcher()
        self.bear_researcher = bear_researcher.get_bear_researcher()
        self.trader = trader.get_trader_agent()
    
    def gather_intelligence(self, state: AgentState):
        """[核心升级] 全新的“中央情报处”节点，一次性获取所有数据"""
        logging.info("节点执行: [中央情报处] - 启动情报收集...")
        
        # 只在这里初始化一次数据接口！
        data_interface = AShareDataInterface(state['ticker'])
        
        # 将所有需要的数据，一次性地获取并存入状态“篮子”
        intelligence_package = {
            "briefing_book": {
                "company_profile": data_interface.fetch_company_profile(),
                "financial_reports": data_interface.fetch_financial_reports(),
                "chanlun_kline_report": data_interface.fetch_chanlun_kline_report(),
                "latest_news": data_interface.fetch_latest_news(),
                "capital_flow": data_interface.fetch_capital_flow(),
                "sector_comparison": data_interface.fetch_sector_comparison(),
                "policy_news": data_interface.fetch_policy_news(),
                "social_media_posts": data_interface.fetch_social_media_posts(),
            },
            "latest_close_price": data_interface.get_latest_close_price()
        }
        logging.info("--- [中央情报处]：所有情报收集完毕 ---")
        return intelligence_package

    def run_analyst_team(self, state: AgentState):
        """[核心升级] 分析师现在直接使用“情报手册”，不再自己收集数据"""
        logging.info("节点执行: [分析师团队] - 7位专家基于情报手册并行启动...")
        
        briefing_book = state['briefing_book']
        analysis_results = {
            "fundamentals_analysis": self.fundamentals_analyst.invoke(briefing_book['financial_reports']),
            "market_analysis": self.market_analyst.invoke(briefing_book['chanlun_kline_report']),
            "news_analysis": self.news_analyst.invoke(briefing_book['latest_news']),
            "policy_analysis": self.policy_analyst.invoke({"policy_news": briefing_book['policy_news'], "stock_name": state['stock_name']}),
            "social_media_analysis": self.social_media_analyst.invoke(briefing_book['social_media_posts']),
            "capital_flow_analysis": self.capital_flow_analyst.invoke(briefing_book['capital_flow']),
            "sector_analysis": self.sector_analyst.invoke(briefing_book['sector_comparison']),
        }
        for name, result in analysis_results.items():
            print_agent_output(name.replace('_', ' ').title(), result)
        return analysis_results

    # ... (后续的 run_research_manager, run_debate_and_risk_team, run_trader 函数的输入也需要微调，以适应新的state结构) ...
    # 为了保持简洁，这里只展示核心修改，完整的最终代码将在下一步提供
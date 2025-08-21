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
        logging.info("节点执行: [中央情报处] - 启动情报收集...")
        data_interface = AShareDataInterface(state['ticker'])
        briefing_book = {
            "financial_reports": data_interface.fetch_financial_reports(),
            "comprehensive_technical_report": data_interface.fetch_comprehensive_technical_report(),
            "latest_news": data_interface.fetch_latest_news(),
            "capital_flow": data_interface.fetch_capital_flow(),
            "sector_comparison": data_interface.fetch_sector_comparison(),
            "policy_news": data_interface.fetch_policy_news(),
            "social_media_posts": data_interface.fetch_social_media_posts(),
        }
        latest_close_price = data_interface.get_latest_close_price()
        logging.info("--- [中央情报处]：所有情报收集完毕 ---")
        return {"briefing_book": briefing_book, "latest_close_price": latest_close_price}

    def run_analyst_team(self, state: AgentState):
        logging.info("节点执行: [分析师团队] - 7位专家基于情报手册并行启动...")
        briefing = state['briefing_book']
        analysis_results = {
            "fundamentals_analysis": self.fundamentals_analyst.invoke({"financial_summary": briefing['financial_reports']}),
            "market_analysis": self.market_analyst.invoke({"technical_report": briefing['comprehensive_technical_report']}),
            "news_analysis": self.news_analyst.invoke(briefing['latest_news']),
            "policy_analysis": self.policy_analyst.invoke({"policy_news": briefing['policy_news'], "stock_name": state['stock_name']}),
            "social_media_analysis": self.social_media_analyst.invoke({"market_sentiment_summary": briefing['social_media_posts']}),
            "capital_flow_analysis": self.capital_flow_analyst.invoke({"capital_flow_summary": briefing['capital_flow']}),
            "sector_analysis": self.sector_analyst.invoke({"sector_comparison_summary": briefing['sector_comparison']}),
        }
        for name, result in analysis_results.items():
            print_agent_output(name.replace('_', ' ').title(), result)
        return analysis_results

    def run_research_manager(self, state: AgentState):
        logging.info("节点执行: [研究主管] - 正在整合7份报告...")
        manager_input = { "ticker": state['ticker'], "stock_name": state['stock_name'] }
        for key, value in state.items():
            if "analysis" in key and hasattr(value, 'analysis'):
                manager_input[key] = value.analysis
        summary = self.research_manager.invoke(manager_input)
        print_agent_output("研究主管 (会议纪要)", summary)
        return {"research_summary": summary}
    
    def run_debate_and_risk_team(self, state: AgentState):
        logging.info("节点执行: [辩论与风控团队] - 并行启动...")
        summary = state['research_summary']
        bull_input = { "ticker": state['ticker'], "stock_name": state['stock_name'], "bull_case_points": summary.bull_case, "key_confirmations": summary.key_confirmations, "key_contradictions": summary.key_contradictions }
        bear_input = { "ticker": state['ticker'], "stock_name": state['stock_name'], "bear_case_points": summary.bear_case, "key_confirmations": summary.key_confirmations, "key_contradictions": summary.key_contradictions }
        risk_input = {"key_confirmations": summary.key_confirmations, "key_contradictions": summary.key_contradictions, "bull_case": summary.bull_case, "bear_case": summary.bear_case}
        bull_report = self.bull_researcher.invoke(bull_input)
        bear_report = self.bear_researcher.invoke(bear_input)
        risk_analysis = self.risk_manager.invoke(risk_input)
        print_agent_output("多头研究员", bull_report)
        print_agent_output("空头研究员", bear_report)
        print_agent_output("风险管理经理", risk_analysis)
        return {"bullish_report": bull_report, "bearish_report": bear_report, "risk_analysis": risk_analysis}

    def run_trader(self, state: AgentState):
        logging.info("节点执行: [首席投资官 - 最终决策]")
        full_briefing_book = "\n".join([f"--- {k} ---\n{v.analysis}\n" for k, v in state.items() if "analysis" in k])
        trader_input = {
            "ticker": state['ticker'], "stock_name": state['stock_name'], 
            "latest_close_price": state['latest_close_price'], 
            "full_briefing_book": full_briefing_book,
            "bull_report": state['bullish_report'].analysis, 
            "bear_report": state['bearish_report'].analysis,
            "risk_report": state['risk_analysis'].analysis
        }
        decision = self.trader.invoke(trader_input)
        return {"final_decision": decision}
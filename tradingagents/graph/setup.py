# tradingagents/graph/setup.py (V3.1 盘面感知版)
import logging
from tradingagents.agents.utils.agent_states import AgentState
from tradingagents.agents.analysts import fundamentals_analyst, market_analyst, news_analyst, policy_analyst, social_media_analyst
from tradingagents.agents.managers import research_manager, risk_manager
from tradingagents.agents.researchers import bull_researcher, bear_researcher
from tradingagents.agents.trader import trader
from tradingagents.default_config import LLM_PROVIDER
from tradingagents.dataflows.interface import AShareDataInterface # [新增] 导入接口

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def print_agent_output(agent_name: str, output):
    # ... (此函数不变) ...
    print("\n" + "="*50); print(f"    <<<<< {agent_name} Report >>>>>"); print("="*50)
    if hasattr(output, 'model_dump'):
        for field, value in output.model_dump().items(): print(f"**{field.upper()}**: \n{value}\n")
    else: print(output)
    print("="*50 + "\n")

class GraphNodes:
    def __init__(self, llm_provider: str = LLM_PROVIDER):
        # ... (初始化代码不变) ...
        self.fundamentals_analyst = fundamentals_analyst.get_fundamentals_analyst()
        self.market_analyst = market_analyst.get_market_analyst()
        self.news_analyst = news_analyst.get_news_analyst()
        self.policy_analyst = policy_analyst.get_policy_analyst()
        self.social_media_analyst = social_media_analyst.get_social_media_analyst()
        self.research_manager = research_manager.get_research_manager()
        self.risk_manager = risk_manager.get_risk_manager()
        self.bull_researcher = bull_researcher.get_bull_researcher()
        self.bear_researcher = bear_researcher.get_bear_researcher()
        self.trader = trader.get_trader_agent()
    
    # ... (所有分析师和研究员的run函数不变) ...
    
    def run_trader(self, state: AgentState):
        """[核心升级] 在决策前，获取并注入最新的收盘价"""
        logging.info("节点执行: [交易员 - 最终决策]")
        
        # [新增] 调用数据接口，获取最新收盘价
        data_interface = AShareDataInterface(state['ticker'])
        latest_price = data_interface.get_latest_close_price()
        logging.info(f"已获取最新收盘价为: {latest_price}")
        
        trader_input = {
            "ticker": state['ticker'],
            "stock_name": state['stock_name'],
            "latest_close_price": latest_price, # 注入最新价格
            "bull_report": state['bullish_report'].report,
            "bear_report": state['bearish_report'].report,
            "risk_report": state['risk_analysis'].report
        }
        decision = self.trader.invoke(trader_input)
        logging.info("--- 最终交易计划已生成 ---")
        return {"final_decision": decision}
    # ... (其他run函数保持不变) ...
    def run_fundamentals_analyst(self, state: AgentState):
        analysis = self.fundamentals_analyst.invoke(state['ticker']); print_agent_output("基本面分析师", analysis); return {"fundamentals_analysis": analysis}
    def run_market_analyst(self, state: AgentState):
        analysis = self.market_analyst.invoke(state['ticker']); print_agent_output("市场/技术分析师", analysis); return {"market_analysis": analysis}
    def run_news_analyst(self, state: AgentState):
        analysis = self.news_analyst.invoke(state['ticker']); print_agent_output("AI新闻智能体", analysis); return {"news_analysis": analysis}
    def run_policy_analyst(self, state: AgentState):
        analysis = self.policy_analyst.invoke(state['ticker']); print_agent_output("政策分析师", analysis); return {"policy_analysis": analysis}
    def run_social_media_analyst(self, state: AgentState):
        analysis = self.social_media_analyst.invoke(state['ticker']); print_agent_output("情绪分析师", analysis); return {"social_media_analysis": analysis}
    def run_research_manager(self, state: AgentState):
        manager_input = {"ticker": state['ticker'], "stock_name": state['stock_name'], "fundamentals_analysis": state['fundamentals_analysis'].analysis, "market_analysis": state['market_analysis'].analysis, "news_analysis": state['news_analysis'].analysis, "policy_analysis": state['policy_analysis'].analysis, "social_media_analysis": state['social_media_analysis'].analysis}
        summary = self.research_manager.invoke(manager_input); print_agent_output("研究主管 (会议纪要)", summary); return {"research_summary": summary}
    def run_bull_bear_researchers(self, state: AgentState):
        summary = state['research_summary']
        bull_input = {"ticker": state['ticker'], "stock_name": state['stock_name'], "bull_case_points": summary.bull_case, "key_confirmations": summary.key_confirmations, "key_contradictions": summary.key_contradictions}
        bear_input = {"ticker": state['ticker'], "stock_name": state['stock_name'], "bear_case_points": summary.bear_case, "key_confirmations": summary.key_confirmations, "key_contradictions": summary.key_contradictions}
        bull_report = self.bull_researcher.invoke(bull_input); bear_report = self.bear_researcher.invoke(bear_input)
        print_agent_output("多头研究员 (最终陈词)", bull_report); print_agent_output("空头研究员 (最终陈词)", bear_report)
        return {"bullish_report": bull_report, "bearish_report": bear_report}
    def run_risk_manager(self, state: AgentState):
        summary = state['research_summary']
        risk_input = {"key_confirmations": summary.key_confirmations, "key_contradictions": summary.key_contradictions, "bull_case": summary.bull_case, "bear_case": summary.bear_case}
        analysis = self.risk_manager.invoke(risk_input); print_agent_output("风险管理经理", analysis); return {"risk_analysis": analysis}
# tradingagents/graph/setup.py (V12.1 最终修复版)
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from tradingagents.utils.agent_states import AgentState
from tradingagents.utils.error_handler import LLMSafetyWrapper, TradingSystemError
from tradingagents.agents.analysts import (
    fundamentals_analyst, market_analyst, news_analyst,
    policy_analyst, social_media_analyst, capital_flow_analyst, sector_analyst
)
from tradingagents.agents.managers import research_manager, risk_manager
from tradingagents.agents.researchers import bull_researcher, bear_researcher
from tradingagents.agents.trader import trader
from tradingagents.default_config import ANALYSIS_LLM_PROVIDER
from tradingagents.dataflows.interface_optimized import OptimizedAShareDataInterface

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def print_agent_output(agent_name: str, output, content_to_print: str = None):
    """格式化打印智能体输出"""
    print("\n" + "="*80)
    print(f"    <<<<< {agent_name} Report >>>>>")
    print("="*80)
    if content_to_print:
        print(content_to_print)
    elif hasattr(output, 'model_dump'):
        for field, value in output.model_dump().items():
            print(f"**{field.upper()}**: \n{value}\n")
    else:
        print(output)
    print("="*80 + "\n")

def format_news_for_analyst(news_list: list) -> str:
    """将结构化的新闻列表格式化为可读的字符串，供下游分析师使用"""
    if not news_list:
        return "情报处未发现任何高度相关的最新新闻。"
    formatted_string = "--- 经核实来源的最新新闻情报 ---\n\n"
    for i, news in enumerate(news_list, 1):
        formatted_string += f"【新闻 {i}】\n"
        formatted_string += f"  - 标题: {news.title}\n"
        formatted_string += f"  - 发布时间: {news.publication_date}\n"
        formatted_string += f"  - 来源链接: {news.source_url}\n"
        formatted_string += f"  - AI初步分析: {news.analysis}\n\n"
    return formatted_string

class GraphNodes:
    def __init__(self, llm_provider: str = ANALYSIS_LLM_PROVIDER):
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
        logging.info("--- [节点 1/5] 中央情报处: 启动情报收集... ---")
        try:
            data_interface = OptimizedAShareDataInterface(state['ticker'])
            briefing_book = data_interface.fetch_all_data_parallel()
            formatted_news = format_news_for_analyst(briefing_book.get('latest_news', []))
            print_agent_output("Gemini 实时新闻情报", None, content_to_print=formatted_news)
            latest_close_price = data_interface.get_latest_close_price()
            return {"briefing_book": briefing_book, "latest_close_price": latest_close_price}
        except Exception as e:
            raise TradingSystemError(f"在 gather_intelligence 阶段发生致命错误: {e}")

    def run_analyst_team(self, state: AgentState):
        logging.info("--- [节点 2/5] 分析师团队: 7位专家并行启动... ---")
        briefing = state['briefing_book']
        formatted_news_summary = format_news_for_analyst(briefing.get('latest_news', []))
        tasks = {
            "fundamentals_analysis": (self.fundamentals_analyst, {"financial_summary": briefing.get('financial_reports', '')}),
            "market_analysis": (self.market_analyst, {"technical_report": briefing.get('comprehensive_technical_report', '')}),
            "news_analysis": (self.news_analyst, {"news_summary": formatted_news_summary}),
            "policy_analysis": (self.policy_analyst, {"policy_news": briefing.get('policy_news', ''), "stock_name": state['stock_name']}),
            "social_media_analysis": (self.social_media_analyst, {"market_sentiment_summary": briefing.get('social_media_posts', '')}),
            "capital_flow_analysis": (self.capital_flow_analyst, {"capital_flow_summary": briefing.get('capital_flow', '')}),
            "sector_analysis": (self.sector_analyst, {"sector_comparison_summary": briefing.get('sector_comparison', '')}),
        }
        analysis_results = {}
        with ThreadPoolExecutor(max_workers=7) as executor:
            future_to_name = { executor.submit(LLMSafetyWrapper.safe_invoke, agent, data, name): name for name, (agent, data) in tasks.items() }
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    result = future.result()
                    analysis_results[name] = result
                    print_agent_output(name.replace('_', ' ').title(), result)
                except Exception as e:
                    analysis_results[name] = None
        return analysis_results

    # --- [核心修复] 补全以下缺失的函数 ---
    def run_research_manager(self, state: AgentState):
        logging.info("--- [节点 3/5] 研究主管: 正在整合7份报告... ---")
        manager_input = { "ticker": state['ticker'], "stock_name": state['stock_name'] }
        for key, value in state.items():
            if "analysis" in key and value and hasattr(value, 'analysis'):
                manager_input[key] = value.analysis
            else:
                manager_input[key] = ""
        summary = LLMSafetyWrapper.safe_invoke(self.research_manager, manager_input, "研究主管")
        print_agent_output("研究主管 (会议纪要)", summary)
        return {"research_summary": summary}

    def run_debate_and_risk_team(self, state: AgentState):
        logging.info("--- [节点 4/5] 辩论与风控团队: 并行启动... ---")
        summary = state['research_summary']
        if not summary:
            raise TradingSystemError("研究主管未能生成摘要，无法进行辩论和风控。")
        tasks = {
            "bullish_report": (self.bull_researcher, {"ticker": state['ticker'], "stock_name": state['stock_name'], "bull_case_points": summary.bull_case, "key_confirmations": summary.key_confirmations, "key_contradictions": summary.key_contradictions}),
            "bearish_report": (self.bear_researcher, {"ticker": state['ticker'], "stock_name": state['stock_name'], "bear_case_points": summary.bear_case, "key_confirmations": summary.key_confirmations, "key_contradictions": summary.key_contradictions}),
            "risk_analysis": (self.risk_manager, {"key_confirmations": summary.key_confirmations, "key_contradictions": summary.key_contradictions, "bull_case": summary.bull_case, "bear_case": summary.bear_case})
        }
        results = {}
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_name = { executor.submit(LLMSafetyWrapper.safe_invoke, agent, data, name): name for name, (agent, data) in tasks.items() }
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    result = future.result()
                    results[name] = result
                    print_agent_output(name.replace('_', ' ').title(), result)
                except Exception as e:
                    results[name] = None
        return results

    def run_trader(self, state: AgentState):
        logging.info("--- [节点 5/5] 首席投资官: 正在进行最终决策... ---")
        full_briefing_book_parts = []
        analyst_keys = ['fundamentals_analysis', 'market_analysis', 'news_analysis', 'policy_analysis', 'social_media_analysis', 'capital_flow_analysis', 'sector_analysis']
        for key in analyst_keys:
            report = state.get(key)
            if report and hasattr(report, 'analysis'):
                title = key.replace('_', ' ').title()
                full_briefing_book_parts.append(f"--- {title} ---\n{report.analysis}\n")
        full_briefing_book = "\n".join(full_briefing_book_parts)
        trader_input = {
            "ticker": state['ticker'], "stock_name": state['stock_name'], "latest_close_price": state['latest_close_price'],
            "full_briefing_book": full_briefing_book,
            "bull_report": state['bullish_report'].analysis if state.get('bullish_report') else "多头报告生成失败",
            "bear_report": state['bearish_report'].analysis if state.get('bearish_report') else "空头报告生成失败",
            "risk_report": state['risk_analysis'].analysis if state.get('risk_analysis') else "风险报告生成失败"
        }
        decision = LLMSafetyWrapper.safe_invoke(self.trader, trader_input, "首席投资官")
        return {"final_decision": decision}
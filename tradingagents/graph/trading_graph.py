# tradingagents/graph/trading_graph.py (V5.1 终极版)
from langgraph.graph import StateGraph, END
import logging
from tradingagents.agents.utils.agent_states import AgentState
from .setup import GraphNodes # 确认从我们最新的setup导入
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def build_graph() -> callable:
    nodes = GraphNodes()
    workflow = StateGraph(AgentState)
    
    # [核心升级] 注册全新的“中央情报处”节点
    workflow.add_node("gather_intelligence", nodes.gather_intelligence)
    workflow.add_node("analyst_team", nodes.run_analyst_team)
    workflow.add_node("research_manager", nodes.run_research_manager)
    workflow.add_node("debate_and_risk_team", nodes.run_debate_and_risk_team)
    workflow.add_node("trader", nodes.run_trader)
    
    # [核心升级] 构建全新的、高效的工作流
    # 1. 首先由“中央情报处”收集所有情报
    workflow.set_entry_point("gather_intelligence")
    # 2. 情报收集完毕后，分发给分析师团队
    workflow.add_edge("gather_intelligence", "analyst_team")
    # 3. 后续流程保持不变
    workflow.add_edge("analyst_team", "research_manager")
    workflow.add_edge("research_manager", "debate_and_risk_team")
    workflow.add_edge("debate_and_risk_team", "trader")
    workflow.add_edge("trader", END)
    
    graph = workflow.compile()
    logging.info("V5.1 '中央情报处' 工作流图编译完成！")
    return graph
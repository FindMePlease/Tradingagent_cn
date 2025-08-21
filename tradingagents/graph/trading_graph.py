# tradingagents/graph/trading_graph.py (V6.3 最终版)
from langgraph.graph import StateGraph, END
import logging
# [路径修正] 从正确的 utils 路径导入
from tradingagents.utils.agent_states import AgentState
from .setup import GraphNodes

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def build_graph() -> callable:
    """构建并编译 LangGraph 工作流图"""
    nodes = GraphNodes()
    workflow = StateGraph(AgentState)
    
    # 定义所有节点
    workflow.add_node("gather_intelligence", nodes.gather_intelligence)
    workflow.add_node("analyst_team", nodes.run_analyst_team)
    workflow.add_node("research_manager", nodes.run_research_manager)
    workflow.add_node("debate_and_risk_team", nodes.run_debate_and_risk_team)
    workflow.add_node("trader", nodes.run_trader)
    
    # 定义工作流的边（执行顺序）
    workflow.set_entry_point("gather_intelligence")
    workflow.add_edge("gather_intelligence", "analyst_team")
    workflow.add_edge("analyst_team", "research_manager")
    workflow.add_edge("research_manager", "debate_and_risk_team")
    workflow.add_edge("debate_and_risk_team", "trader")
    workflow.add_edge("trader", END)
    
    # 编译图
    graph = workflow.compile()
    logging.info("投研工作流图编译完成！")
    return graph
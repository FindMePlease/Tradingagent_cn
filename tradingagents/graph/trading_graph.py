from langgraph.graph import StateGraph, END
import logging
from tradingagents.agents.utils.agent_states import AgentState
from .setup import GraphNodes
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def build_graph() -> callable:
    nodes = GraphNodes()
    workflow = StateGraph(AgentState)
    
    workflow.add_node("gather_intelligence", nodes.gather_intelligence)
    workflow.add_node("analyst_team", nodes.run_analyst_team)
    workflow.add_node("research_manager", nodes.run_research_manager)
    workflow.add_node("debate_and_risk_team", nodes.run_debate_and_risk_team)
    workflow.add_node("trader", nodes.run_trader)
    
    workflow.set_entry_point("gather_intelligence")
    workflow.add_edge("gather_intelligence", "analyst_team")
    workflow.add_edge("analyst_team", "research_manager")
    workflow.add_edge("research_manager", "debate_and_risk_team")
    workflow.add_edge("debate_and_risk_team", "trader")
    workflow.add_edge("trader", END)
    
    graph = workflow.compile()
    logging.info("V5.2 '中央情报处' 工作流图编译完成！")
    return graph
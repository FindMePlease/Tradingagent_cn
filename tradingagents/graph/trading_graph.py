# -*- coding: utf-8 -*-

"""
模块: 投研工作流图 (最终修正版)
职责: 定义和构建整个多智能体协作的工作流程。
"""

from langgraph.graph import StateGraph, END
import logging

# 确认这里的导入路径是正确的
from tradingagents.agents.utils.agent_states import AgentState
from .setup import GraphNodes

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def build_graph() -> callable:
    """
    构建并编译整个投研工作流图。
    """
    
    # 0. 实例化所有节点
    nodes = GraphNodes()

    # 1. 初始化图，并指定状态对象
    workflow = StateGraph(AgentState)

    # 2. 向图中添加所有节点
    logging.info("向图中添加所有Agent节点...")
    workflow.add_node("fundamentals_analyst", nodes.run_fundamentals_analyst)
    workflow.add_node("market_analyst", nodes.run_market_analyst)
    workflow.add_node("news_analyst", nodes.run_news_analyst)
    workflow.add_node("policy_analyst", nodes.run_policy_analyst)
    workflow.add_node("social_media_analyst", nodes.run_social_media_analyst)
    
    workflow.add_node("research_manager", nodes.run_research_manager)
    workflow.add_node("bull_bear_researchers", nodes.run_bull_bear_researchers)
    workflow.add_node("risk_manager", nodes.run_risk_manager)
    workflow.add_node("trader", nodes.run_trader)

    # 3. 定义节点之间的连接关系（边）

    # 设置图的入口点为基本面分析师
    workflow.set_entry_point("fundamentals_analyst")
    
    # 3.1 分析师层
    # 这里的串行连接是为了保证在LangGraph中流程的明确性
    # 在实际的高并发应用中，可以改造为真正的并行执行
    logging.info("定义分析师层的执行路径...")
    workflow.add_edge("fundamentals_analyst", "market_analyst")
    workflow.add_edge("market_analyst", "news_analyst")
    workflow.add_edge("news_analyst", "policy_analyst")
    workflow.add_edge("policy_analyst", "social_media_analyst")

    # 3.2 汇总与高层分析
    # 当最后一个分析师完成后，进入研究主管节点
    logging.info("定义汇总、研究主管的串行路径...")
    workflow.add_edge("social_media_analyst", "research_manager")
    
    # 3.3 多空辩论与风控
    # 研究主管完成后，启动多空辩手
    logging.info("定义研究主管到多空辩手和风控的路径...")
    workflow.add_edge("research_manager", "bull_bear_researchers")
    # 多空辩手完成后，进行最终的风险审查
    workflow.add_edge("bull_bear_researchers", "risk_manager")

    # 3.4 最终决策
    # 风险审查完成后，信息汇总给交易员
    logging.info("定义从风控到最终交易员的路径...")
    workflow.add_edge("risk_manager", "trader")

    # 4. 设置图的出口点
    workflow.add_edge("trader", END)

    # 5. 编译图
    logging.info("编译工作流图...")
    graph = workflow.compile()
    logging.info("工作流图编译完成！")
    
    return graph

if __name__ == '__main__':
    print("--- 测试构建并可视化A股投研工作流图 ---")
    
    trading_graph = build_graph()
    
    print("\n--- Graph Nodes ---")
    print(trading_graph.get_graph().nodes)
    
    try:
        image_data = trading_graph.get_graph().draw_mermaid_png()
        with open("trading_graph_cn.png", "wb") as f:
            f.write(image_data)
        print("\n成功生成图的可视化文件: trading_graph_cn.png")
    except Exception as e:
        print(f"\n生成图可视化失败 (可能是缺少graphviz依赖): {e}")
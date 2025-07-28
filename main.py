# main.py (V2.0 升级版)
import logging
import argparse

from tradingagents.graph.trading_graph import build_graph
from tradingagents.dataflows.akshare_utils import get_stock_name
from tradingagents.default_config import TRADING_TICKER, AGENT_CONFIG, LLM_PROVIDER

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main(ticker: str):
    logging.info(f"========= 开始为股票 {ticker} 执行投研工作流 (LLM: {LLM_PROVIDER}) =========")
    app = build_graph()
    initial_state = {
        "ticker": ticker,
        "stock_name": get_stock_name(ticker),
        "iteration_count": 0,
        "max_iterations": AGENT_CONFIG.get("max_iterations", 5)
    }
    logging.info(f"初始状态准备完成: {initial_state}")

    final_state = None
    for s in app.stream(initial_state):
        node_name = list(s.keys())[0]
        logging.info(f"--- 节点 '{node_name}' 执行完毕 ---")
        final_state = s

    logging.info("========= 投研工作流执行完毕 =========")
    if final_state:
        last_node_name = list(final_state.keys())[0]
        final_decision = final_state[last_node_name].get('final_decision')
        
        if final_decision:
            # [核心升级] 打印出完整的、详细的交易计划
            print("\n" + "="*60)
            print("                *** 最终交易计划 ***")
            print("="*60)
            print(f"**股票:** {initial_state['stock_name']} ({initial_state['ticker']})")
            print(f"**核心行动:** {final_decision.action}")
            print(f"**信心指数:** {'★' * final_decision.confidence}{'☆' * (5 - final_decision.confidence)}")
            print("-" * 60)
            print(f"**决策理由:** \n{final_decision.rationale}")
            print("-" * 60)
            print(f"**具体策略:**")
            print(f"  - **入场条件:** {final_decision.entry_condition}")
            print(f"  - **止损条件:** {final_decision.stop_loss}")
            print(f"  - **仓位管理:** {final_decision.position_sizing}")
            print("="*60)
            print("\n免责声明：以上内容由AI生成，仅供研究参考，不构成任何投资建议。")
        else:
            print("未能得出最终交易决策。")
    else:
        print("工作流未能成功执行。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行A股多智能体投研框架 V2.0")
    parser.add_argument(
        "--ticker",
        type=str,
        default=TRADING_TICKER,
        help=f"要分析的A股股票代码 (例如 'sh601068')。默认为: {TRADING_TICKER}"
    )
    args = parser.parse_args()
    main(args.ticker)
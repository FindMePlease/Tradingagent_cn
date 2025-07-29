# main.py (V4.2 终极网络修正版)
import logging
import argparse
import os # [新增] 导入os库来设置环境变量

# --- [核心修正] 在所有其他操作之前，强制设置网络代理 ---
# 我们假设您的代理服务器在本地运行 (127.0.0.1) 且端口为 7897
proxy_address = "http://127.0.0.1:7897"
os.environ['HTTP_PROXY'] = proxy_address
os.environ['HTTPS_PROXY'] = proxy_address
print(f"\n--- [系统信息]：已为当前程序强制设置网络代理: {proxy_address} ---\n")

# --- 后续代码保持不变 ---
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
    # 使用 try...except 来捕获可能的 KeyboardInterrupt，并给出友好提示
    try:
        for s in app.stream(initial_state):
            node_name = list(s.keys())[0]
            # 为了让日志更清晰，我们只在setup.py中打印详细报告
            # logging.info(f"--- 节点 '{node_name}' 执行完毕 ---")
            final_state = s
    except KeyboardInterrupt:
        print("\n\n[系统信息] 用户手动中断了程序执行。")
        return
    except Exception as e:
        print(f"\n\n[严重错误] 程序在执行过程中遇到未知错误: {e}")
        # 这里可以加入更详细的错误追踪代码
        import traceback
        traceback.print_exc()
        return

    logging.info("========= 投研工作流执行完毕 =========")
    if final_state:
        last_node_name = list(final_state.keys())[0]
        final_decision = final_state[last_node_name].get('final_decision')
        
        if final_decision:
            # 打印最终的详细交易计划
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
            print(f"  - **入场价格:** {final_decision.entry_price}")
            print(f"  - **止损价格:** {final_decision.stop_loss_price}")
            print(f"  - **目标价格:** {final_decision.target_price}")
            print(f"  - **仓位管理:** {final_decision.position_sizing}")
            print("="*60)
            print("\n免责声明：以上内容由AI生成，仅供研究参考，不构成任何投资建议。")
        else:
            print("工作流执行完毕，但未能得出最终交易决策。")
    else:
        print("工作流未能成功执行。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行A股多智能体投研框架 V4.2")
    parser.add_argument(
        "--ticker",
        type=str,
        default=TRADING_TICKER,
        help=f"要分析的A股股票代码 (例如 'sh601068')"
    )
    args = parser.parse_args()
    main(args.ticker)
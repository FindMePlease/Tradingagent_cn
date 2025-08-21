# main.py (V15.1 最终修复版)
import logging
import argparse
import os
import sys
import signal
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tradingagents.graph.trading_graph import build_graph
from tradingagents.dataflows.akshare_utils import get_stock_name, is_valid_a_stock_code
from tradingagents.default_config import TRADING_TICKER, AGENT_CONFIG
from tradingagents.utils.performance_monitor import global_monitor
from tradingagents.utils.error_handler import TradingSystemError

def setup_logging():
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"trading_system_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler(sys.stdout)])
    logging.info("日志系统初始化完成。")

def signal_handler(signum, frame):
    print(f"\n捕获到信号 {signum}，系统正在优雅关闭...")
    sys.exit(0)

def main(ticker: str):
    logger = logging.getLogger(__name__)

    if not is_valid_a_stock_code(ticker):
        error_msg = f"错误：您输入的股票代码 '{ticker}' 格式不正确。请输入有效的A股代码，例如 'sh600519' 或 'sz000858'。"
        logger.error(error_msg)
        print(f"\n❌ {error_msg}\n")
        return False

    try:
        stock_name = get_stock_name(ticker)
        if not stock_name:
             error_msg = f"错误：无法从数据源获取股票代码 '{ticker}' 的有效名称，请检查代码是否存在或稍后再试。"
             logger.error(error_msg)
             print(f"\n❌ {error_msg}\n")
             return False

        logger.info(f"--- 开始为股票 {stock_name} ({ticker}) 执行投研工作流 ---")
        app = build_graph()
        initial_state = {"ticker": ticker, "stock_name": stock_name}
        start_time = datetime.now()
        print(f"\n🚀 工作流启动，开始分析 {stock_name}...")
        final_state = None
        for step_count, s in enumerate(app.stream(initial_state), 1):
            node_name = list(s.keys())[0]
            print(f"✅ 步骤 {step_count}: 节点 '{node_name}' 执行完毕")
            final_state = s
        execution_time = (datetime.now() - start_time).total_seconds()
        if final_state:
            last_node_name = list(final_state.keys())[0]
            final_decision = final_state[last_node_name].get('final_decision')
            if final_decision:
                print_final_decision(final_decision, stock_name, ticker, execution_time)
                return True
        print("⚠️ 工作流执行完毕，但未能生成最终交易决策。")
        return False
    except Exception as e:
        logger.error(f"发生未知错误: {e}", exc_info=True)
        print(f"❌ 程序执行出现未知错误: {e}")
        return False

def print_final_decision(decision, stock_name, ticker, execution_time):
    print("\n" + "="*80)
    print("                   🎯 最终投资决策")
    print("="*80)
    print(f"📊 股票信息: {stock_name} ({ticker})")
    print(f"⏱️  分析耗时: {execution_time:.2f} 秒")
    print(f"🎯 核心决策: {decision.action}")
    print(f"💪 信心指数: {'★' * decision.confidence}{'☆' * (5 - decision.confidence)} ({decision.confidence}/5)")
    print("\n📝 决策理由:")
    print("-" * 60)
    print(decision.rationale)
    print("\n💰 交易计划:")
    print("-" * 60)
    print(f"  - 入场价格: {decision.entry_price}")
    print(f"  - 止损价格: {decision.stop_loss_price}")
    print(f"  - 目标价格: {decision.target_price}")
    print(f"  - 仓位管理: {decision.position_sizing}")
    print("="*80)
    print("⚠️  风险提示: 以上分析由AI生成，仅供参考，不构成投资建议。")
    print("    投资有风险，入市需谨慎。请根据自身情况做出独立判断。")
    print("="*80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A股多智能体投研系统 V15.1 (最终修复版)")
    parser.add_argument("--ticker", type=str, default=TRADING_TICKER, help="要分析的股票代码")
    args = parser.parse_args()
    setup_logging()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    success = main(ticker=args.ticker)
    sys.exit(0 if success else 1)
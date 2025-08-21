# main_optimized.py - 优化后的主程序

import logging
import argparse
import os
import sys
import signal
from datetime import datetime
from pathlib import Path

# 设置项目根路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 在其他导入之前设置网络代理
def setup_proxy():
    """设置网络代理"""
    try:
        from tradingagents.default_config import NETWORK_CONFIG
        if 'proxy' in NETWORK_CONFIG:
            for key, value in NETWORK_CONFIG['proxy'].items():
                os.environ[f'{key.upper()}_PROXY'] = value
            print(f"已设置网络代理: {NETWORK_CONFIG['proxy']}")
    except ImportError:
        # 默认代理配置
        proxy_address = "http://127.0.0.1:7897"
        os.environ['HTTP_PROXY'] = proxy_address
        os.environ['HTTPS_PROXY'] = proxy_address
        print(f"已设置默认网络代理: {proxy_address}")

setup_proxy()

# 导入项目模块
from tradingagents.graph.trading_graph import build_graph
from tradingagents.dataflows.akshare_utils import get_stock_name
from tradingagents.default_config import TRADING_TICKER, AGENT_CONFIG, LLM_PROVIDER
from tradingagents.utils.performance_monitor import global_monitor, health_checker
from tradingagents.utils.error_handler import TradingSystemError

# 配置日志
def setup_logging():
    """设置日志配置"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"trading_system_{datetime.now().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def signal_handler(signum, frame):
    """信号处理器，优雅关闭"""
    print(f"\n收到信号 {signum}，正在优雅关闭系统...")
    global_monitor.stop_monitoring()
    
    # 导出性能报告
    report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    global_monitor.export_performance_report(report_file)
    print(f"性能报告已保存至: {report_file}")
    
    sys.exit(0)

def validate_environment():
    """验证运行环境"""
    print("正在检查系统环境...")
    
    # 运行健康检查
    health_report = health_checker.run_comprehensive_check()
    
    if health_report["overall_status"] == "unhealthy":
        print("❌ 系统环境检查失败！")
        print(f"发现 {health_report['error_count']} 个错误")
        
        # 显示错误详情
        for category, checks in health_report.items():
            if category in ["check_time", "overall_status", "error_count", "warning_count"]:
                continue
            for check_name, result in checks.items():
                if isinstance(result, dict) and result.get("status") == "error":
                    print(f"  ❌ {category}.{check_name}: {result.get('error', '未知错误')}")
        
        return False
    
    elif health_report["overall_status"] == "warning":
        print(f"⚠️  系统环境检查通过，但有 {health_report['warning_count']} 个警告")
        for category, checks in health_report.items():
            if category in ["check_time", "overall_status", "error_count", "warning_count"]:
                continue
            for check_name, result in checks.items():
                if isinstance(result, dict) and result.get("status") == "warning":
                    print(f"  ⚠️  {category}.{check_name}: 可能存在问题")
    
    else:
        print("✅ 系统环境检查通过")
    
    return True

def print_system_info():
    """打印系统信息"""
    print("\n" + "="*80)
    print("          🤖 A股多智能体投研系统 V6.0 (优化版)")
    print("="*80)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"LLM 提供商: {LLM_PROVIDER}")
    print(f"Python 版本: {sys.version}")
    print(f"工作目录: {Path.cwd()}")
    print("="*80)

def main(ticker: str, enable_monitoring: bool = True, health_check: bool = True):
    """主程序"""
    setup_logging()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print_system_info()
    
    # 环境检查
    if health_check and not validate_environment():
        print("\n❌ 环境检查失败，程序退出")
        return False
    
    # 启动性能监控
    if enable_monitoring:
        global_monitor.start_monitoring(interval=30)
        print("📊 性能监控已启动")
    
    logger = logging.getLogger(__name__)
    
    try:
        # 获取股票名称
        stock_name = get_stock_name(ticker)
        
        logger.info(f"开始为股票 {stock_name} ({ticker}) 执行投研工作流")
        
        # 构建工作流
        app = build_graph()
        
        # 初始状态
        initial_state = {
            "ticker": ticker,
            "stock_name": stock_name,
            "iteration_count": 0,
            "max_iterations": AGENT_CONFIG.get("max_iterations", 3)
        }
        
        logger.info(f"初始状态: {initial_state}")
        
        # 执行工作流
        final_state = None
        start_time = datetime.now()
        
        print(f"\n🚀 开始执行投研工作流...")
        
        for step_count, s in enumerate(app.stream(initial_state), 1):
            node_name = list(s.keys())[0]
            print(f"✅ 步骤 {step_count}: {node_name} 执行完毕")
            final_state = s
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # 输出最终结果
        if final_state:
            last_node_name = list(final_state.keys())[0]
            final_decision = final_state[last_node_name].get('final_decision')
            
            if final_decision:
                print_final_decision(final_decision, stock_name, ticker, execution_time)
                logger.info("投研工作流执行成功完成")
                return True
            else:
                print("⚠️ 工作流执行完毕，但未能生成最终交易决策")
                return False
        else:
            print("❌ 工作流执行失败")
            return False
            
    except KeyboardInterrupt:
        print("\n\n🛑 用户手动中断程序执行")
        return False
        
    except TradingSystemError as e:
        logger.error(f"交易系统错误: {e}")
        print(f"❌ 交易系统错误: {e}")
        return False
        
    except Exception as e:
        logger.error(f"未知错误: {e}", exc_info=True)
        print(f"❌ 程序执行出现未知错误: {e}")
        return False
        
    finally:
        # 停止监控并导出报告
        if enable_monitoring:
            global_monitor.stop_monitoring()
            
            try:
                report_file = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                global_monitor.export_performance_report(report_file)
                print(f"📋 性能报告已保存: {report_file}")
            except Exception as e:
                logger.warning(f"导出性能报告失败: {e}")

def print_final_decision(decision, stock_name, ticker, execution_time):
    """打印最终交易决策"""
    print("\n" + "="*80)
    print("                   🎯 最终投资决策")
    print("="*80)
    print(f"📊 股票信息: {stock_name} ({ticker})")
    print(f"⏱️  分析耗时: {execution_time:.1f} 秒")
    print(f"🎯 核心决策: {decision.action}")
    print(f"💪 信心指数: {'★' * decision.confidence}{'☆' * (5 - decision.confidence)} ({decision.confidence}/5)")
    
    print("\n📝 决策理由:")
    print("-" * 60)
    print(decision.rationale)
    
    print("\n💰 交易计划:")
    print("-" * 60)
    print(f"🎯 入场价格: {decision.entry_price}")
    print(f"🛡️ 止损价格: {decision.stop_loss_price}")
    print(f"🎉 目标价格: {decision.target_price}")
    print(f"📊 仓位管理: {decision.position_sizing}")
    
    print("="*80)
    print("⚠️  风险提示: 以上分析由AI生成，仅供参考，不构成投资建议。")
    print("    投资有风险，入市需谨慎。请根据自身情况做出独立判断。")
    print("="*80)

def run_batch_analysis(tickers: list):
    """批量分析多只股票"""
    print(f"📊 开始批量分析 {len(tickers)} 只股票...")
    
    results = {}
    for i, ticker in enumerate(tickers, 1):
        print(f"\n🔄 [{i}/{len(tickers)}] 正在分析 {ticker}...")
        success = main(ticker, enable_monitoring=False, health_check=False)
        results[ticker] = success
        
        if i < len(tickers):  # 避免最后一次不必要的等待
            print("⏳ 等待5秒后继续下一只股票...")
            import time
            time.sleep(5)
    
    # 输出批量分析结果
    print("\n" + "="*60)
    print("            📈 批量分析结果汇总")
    print("="*60)
    success_count = sum(results.values())
    for ticker, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{ticker}: {status}")
    
    print(f"\n总结: {success_count}/{len(tickers)} 只股票分析成功")
    print("="*60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A股多智能体投研系统 V6.0 (优化版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main_optimized.py --ticker sh600036                    # 分析单只股票
  python main_optimized.py --batch sh600036 sz000858 sh600519   # 批量分析
  python main_optimized.py --health-only                        # 仅运行健康检查
        """
    )
    
    parser.add_argument(
        "--ticker", 
        type=str, 
        default=TRADING_TICKER,
        help="要分析的股票代码 (例如: sh600036)"
    )
    
    parser.add_argument(
        "--batch",
        nargs='+',
        help="批量分析多只股票 (例如: --batch sh600036 sz000858)"
    )
    
    parser.add_argument(
        "--no-monitoring",
        action="store_true",
        help="禁用性能监控"
    )
    
    parser.add_argument(
        "--no-health-check",
        action="store_true", 
        help="跳过环境健康检查"
    )
    
    parser.add_argument(
        "--health-only",
        action="store_true",
        help="仅运行系统健康检查"
    )
    
    args = parser.parse_args()
    
    if args.health_only:
        # 仅运行健康检查
        setup_logging()
        health_report = health_checker.run_comprehensive_check()
        print(f"\n系统状态: {health_report['overall_status']}")
        if health_report["overall_status"] != "healthy":
            sys.exit(1)
    elif args.batch:
        # 批量分析
        run_batch_analysis(args.batch)
    else:
        # 单只股票分析
        success = main(
            ticker=args.ticker,
            enable_monitoring=not args.no_monitoring,
            health_check=not args.no_health_check
        )
        
        sys.exit(0 if success else 1)
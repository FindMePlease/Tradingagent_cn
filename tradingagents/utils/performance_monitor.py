# tradingagents/utils/performance_monitor.py - 性能监控模块

import time
import psutil
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass
import threading
from collections import defaultdict, deque

@dataclass
class SystemMetrics:
    """系统性能指标"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    timestamp: datetime

@dataclass
class AgentPerformance:
    """智能体性能指标"""
    agent_name: str
    execution_time: float
    memory_usage: float
    success: bool
    error_message: Optional[str]
    timestamp: datetime

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.system_metrics_history = deque(maxlen=max_history)
        self.agent_performance_history = deque(maxlen=max_history)
        self.error_counts = defaultdict(int)
        self.success_counts = defaultdict(int)
        self._monitoring = False
        self._monitor_thread = None
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def start_monitoring(self, interval: int = 30):
        """开始系统监控"""
        if self._monitoring:
            return
            
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_system,
            args=(interval,),
            daemon=True
        )
        self._monitor_thread.start()
        self.logger.info("性能监控已启动")

    def stop_monitoring(self):
        """停止系统监控"""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
        self.logger.info("性能监控已停止")

    def _monitor_system(self, interval: int):
        """系统监控循环"""
        while self._monitoring:
            try:
                metrics = self._collect_system_metrics()
                self.system_metrics_history.append(metrics)
                
                # 检查系统警告
                self._check_system_warnings(metrics)
                
                time.sleep(interval)
            except Exception as e:
                self.logger.error(f"系统监控出错: {e}")

    def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            disk_usage_percent=disk.percent,
            timestamp=datetime.now()
        )

    def _check_system_warnings(self, metrics: SystemMetrics):
        """检查系统警告"""
        if metrics.cpu_percent > 80:
            self.logger.warning(f"CPU使用率过高: {metrics.cpu_percent}%")
        
        if metrics.memory_percent > 80:
            self.logger.warning(f"内存使用率过高: {metrics.memory_percent}%")
        
        if metrics.disk_usage_percent > 90:
            self.logger.warning(f"磁盘使用率过高: {metrics.disk_usage_percent}%")

    def record_agent_performance(
        self,
        agent_name: str,
        execution_time: float,
        success: bool,
        error_message: Optional[str] = None
    ):
        """记录智能体性能"""
        memory_usage = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
        
        performance = AgentPerformance(
            agent_name=agent_name,
            execution_time=execution_time,
            memory_usage=memory_usage,
            success=success,
            error_message=error_message,
            timestamp=datetime.now()
        )
        
        self.agent_performance_history.append(performance)
        
        if success:
            self.success_counts[agent_name] += 1
        else:
            self.error_counts[agent_name] += 1
            
        self.logger.info(
            f"智能体 {agent_name}: "
            f"执行时间={execution_time:.2f}s, "
            f"内存={memory_usage:.1f}MB, "
            f"状态={'成功' if success else '失败'}"
        )

    def get_agent_statistics(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """获取智能体统计信息"""
        if agent_name:
            # 单个智能体统计
            performances = [p for p in self.agent_performance_history if p.agent_name == agent_name]
            if not performances:
                return {"error": f"未找到智能体 {agent_name} 的性能数据"}
                
            execution_times = [p.execution_time for p in performances]
            success_rate = self.success_counts[agent_name] / (
                self.success_counts[agent_name] + self.error_counts[agent_name]
            ) if (self.success_counts[agent_name] + self.error_counts[agent_name]) > 0 else 0
            
            return {
                "agent_name": agent_name,
                "total_executions": len(performances),
                "success_rate": success_rate,
                "avg_execution_time": sum(execution_times) / len(execution_times),
                "min_execution_time": min(execution_times),
                "max_execution_time": max(execution_times),
                "success_count": self.success_counts[agent_name],
                "error_count": self.error_counts[agent_name]
            }
        else:
            # 所有智能体统计
            all_agents = set(p.agent_name for p in self.agent_performance_history)
            return {agent: self.get_agent_statistics(agent) for agent in all_agents}

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        if not self.system_metrics_history:
            return {"error": "无系统监控数据"}
        
        recent_metrics = list(self.system_metrics_history)[-10:]  # 最近10次记录
        
        return {
            "current_time": datetime.now().isoformat(),
            "monitoring_active": self._monitoring,
            "records_count": len(self.system_metrics_history),
            "current_metrics": {
                "cpu_percent": recent_metrics[-1].cpu_percent,
                "memory_percent": recent_metrics[-1].memory_percent,
                "memory_used_mb": recent_metrics[-1].memory_used_mb,
                "disk_usage_percent": recent_metrics[-1].disk_usage_percent
            },
            "avg_metrics_last_10": {
                "avg_cpu": sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics),
                "avg_memory": sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            }
        }

    def export_performance_report(self, filepath: str):
        """导出性能报告"""
        report = {
            "export_time": datetime.now().isoformat(),
            "system_status": self.get_system_status(),
            "agent_statistics": self.get_agent_statistics(),
            "recent_system_metrics": [
                {
                    "cpu_percent": m.cpu_percent,
                    "memory_percent": m.memory_percent,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in list(self.system_metrics_history)[-100:]  # 最近100条
            ],
            "recent_agent_performances": [
                {
                    "agent_name": p.agent_name,
                    "execution_time": p.execution_time,
                    "success": p.success,
                    "timestamp": p.timestamp.isoformat()
                }
                for p in list(self.agent_performance_history)[-100:]  # 最近100条
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"性能报告已导出到: {filepath}")

def performance_tracker(agent_name: str):
    """装饰器：自动跟踪智能体性能"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error_message = None
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error_message = str(e)
                raise
            finally:
                execution_time = time.time() - start_time
                
                # 获取全局监控器实例
                if hasattr(wrapper, '_monitor'):
                    wrapper._monitor.record_agent_performance(
                        agent_name, execution_time, success, error_message
                    )
        
        return wrapper
    return decorator

# 全局性能监控器实例
global_monitor = PerformanceMonitor()

class HealthChecker:
    """系统健康检查器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_dependencies(self) -> Dict[str, Any]:
        """检查依赖项"""
        results = {}
        
        # 检查核心库
        dependencies = [
            'akshare', 'pandas', 'numpy', 'requests', 'langchain',
            'pydantic', 'baostock', 'pandas_ta'
        ]
        
        for dep in dependencies:
            try:
                __import__(dep)
                results[dep] = {"status": "ok", "installed": True}
            except ImportError as e:
                results[dep] = {"status": "error", "installed": False, "error": str(e)}
        
        return results
    
    def check_configurations(self) -> Dict[str, Any]:
        """检查配置"""
        results = {}
        
        try:
            from tradingagents.default_config import (
                LLM_PROVIDER, QWEN_CONFIG, DEEPSEEK_CONFIG, Google_Search_CONFIG
            )
            
            # 检查LLM配置
            if LLM_PROVIDER == "qwen":
                api_key = QWEN_CONFIG.get("api_key", "")
                results["qwen_api"] = {
                    "status": "ok" if api_key and "在这里粘贴" not in api_key else "error",
                    "configured": bool(api_key and "在这里粘贴" not in api_key)
                }
            
            elif LLM_PROVIDER == "deepseek":
                api_key = DEEPSEEK_CONFIG.get("api_key", "")
                results["deepseek_api"] = {
                    "status": "ok" if api_key and "在这里粘贴" not in api_key else "error",
                    "configured": bool(api_key and "在这里粘贴" not in api_key)
                }
            
            # 检查Google搜索配置
            google_key = Google_Search_CONFIG.get("api_key", "")
            google_cx = Google_Search_CONFIG.get("cx_id", "")
            results["google_search"] = {
                "status": "ok" if google_key and google_cx and "在这里粘贴" not in google_key else "error",
                "configured": bool(google_key and google_cx and "在这里粘贴" not in google_key)
            }
            
        except ImportError as e:
            results["config_import"] = {"status": "error", "error": str(e)}
        
        return results
    
    def check_network_connectivity(self) -> Dict[str, Any]:
        """检查网络连接"""
        results = {}
        test_urls = [
            ("百度", "https://www.baidu.com"),
            ("Google", "https://www.google.com"),
            ("GitHub", "https://api.github.com")
        ]
        
        for name, url in test_urls:
            try:
                import requests
                response = requests.get(url, timeout=10)
                results[name] = {
                    "status": "ok" if response.status_code == 200 else "warning",
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
        
        return results
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """运行综合健康检查"""
        self.logger.info("开始系统健康检查...")
        
        health_report = {
            "check_time": datetime.now().isoformat(),
            "dependencies": self.check_dependencies(),
            "configurations": self.check_configurations(),
            "network": self.check_network_connectivity(),
            "system": global_monitor.get_system_status()
        }
        
        # 计算整体健康状态
        error_count = 0
        warning_count = 0
        
        for category, checks in health_report.items():
            if category == "check_time":
                continue
            for check_name, result in checks.items():
                if isinstance(result, dict) and "status" in result:
                    if result["status"] == "error":
                        error_count += 1
                    elif result["status"] == "warning":
                        warning_count += 1
        
        if error_count > 0:
            overall_status = "unhealthy"
        elif warning_count > 0:
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        health_report["overall_status"] = overall_status
        health_report["error_count"] = error_count
        health_report["warning_count"] = warning_count
        
        self.logger.info(f"健康检查完成，状态: {overall_status}")
        return health_report

# 全局健康检查器实例
health_checker = HealthChecker()
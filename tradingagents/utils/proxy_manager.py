# tradingagents/utils/proxy_manager.py
"""
网络代理管理器
用于控制不同数据源的代理使用策略
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any
import requests
import akshare as ak
import baostock as bs

logger = logging.getLogger(__name__)

class ProxyManager:
    """网络代理管理器"""
    
    def __init__(self):
        self.original_env = {}
        self.proxy_config = None
        self._load_proxy_config()
    
    def _load_proxy_config(self):
        """加载代理配置"""
        try:
            from tradingagents.default_config import NETWORK_CONFIG
            self.proxy_config = NETWORK_CONFIG.get('proxy')
            if self.proxy_config:
                logger.info(f"已加载代理配置: {self.proxy_config}")
        except ImportError:
            logger.warning("无法加载代理配置")
    
    def _get_current_proxy(self) -> Optional[str]:
        """获取当前环境变量中的代理设置"""
        return os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')
    
    def _set_proxy(self, proxy: Optional[str]):
        """设置代理环境变量"""
        if proxy:
            os.environ['HTTP_PROXY'] = proxy
            os.environ['HTTPS_PROXY'] = proxy
            logger.debug(f"设置代理: {proxy}")
        else:
            # 清除代理设置
            os.environ.pop('HTTP_PROXY', None)
            os.environ.pop('HTTPS_PROXY', None)
            logger.debug("清除代理设置")
    
    def _backup_env(self):
        """备份当前环境变量"""
        self.original_env = {
            'HTTP_PROXY': os.environ.get('HTTP_PROXY'),
            'HTTPS_PROXY': os.environ.get('HTTPS_PROXY')
        }
    
    def _restore_env(self):
        """恢复环境变量"""
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)
        logger.debug("已恢复环境变量")
    
    @contextmanager
    def no_proxy(self):
        """临时禁用代理的上下文管理器"""
        self._backup_env()
        try:
            self._set_proxy(None)
            yield
        finally:
            self._restore_env()
    
    @contextmanager
    def with_proxy(self, proxy: Optional[str] = None):
        """临时启用代理的上下文管理器"""
        if proxy is None:
            proxy = self.proxy_config.get('http') if self.proxy_config else None
        
        self._backup_env()
        try:
            self._set_proxy(proxy)
            yield
        finally:
            self._restore_env()
    
    def configure_akshare_no_proxy(self):
        """配置akshare不使用代理"""
        try:
            # 尝试设置akshare的代理配置
            if hasattr(ak, 'set_proxy'):
                ak.set_proxy(None)
                logger.info("已配置akshare不使用代理")
        except Exception as e:
            logger.warning(f"配置akshare代理失败: {e}")
    
    def configure_baostock_no_proxy(self):
        """配置baostock不使用代理"""
        try:
            # baostock通常不需要特殊配置，但我们可以确保环境变量正确
            if self._get_current_proxy():
                logger.info("检测到代理设置，baostock将使用直连")
        except Exception as e:
            logger.warning(f"配置baostock代理失败: {e}")
    
    def test_connection(self, url: str, use_proxy: bool = False) -> bool:
        """测试网络连接"""
        try:
            if use_proxy:
                with self.with_proxy():
                    response = requests.get(url, timeout=10)
            else:
                with self.no_proxy():
                    response = requests.get(url, timeout=10)
            
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"连接测试失败 {url}: {e}")
            return False

# 全局代理管理器实例
proxy_manager = ProxyManager()

def get_proxy_manager() -> ProxyManager:
    """获取代理管理器实例"""
    return proxy_manager

# 装饰器：强制不使用代理
def force_no_proxy(func):
    """强制不使用代理的装饰器"""
    def wrapper(*args, **kwargs):
        with proxy_manager.no_proxy():
            return func(*args, **kwargs)
    return wrapper

# 装饰器：强制使用代理
def force_with_proxy(func):
    """强制使用代理的装饰器"""
    def wrapper(*args, **kwargs):
        with proxy_manager.with_proxy():
            return func(*args, **kwargs)
    return wrapper

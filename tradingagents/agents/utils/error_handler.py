# tradingagents/utils/error_handler.py - 统一错误处理模块

import logging
import time
import functools
from typing import Any, Callable, Optional
from datetime import datetime, timedelta
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TradingSystemError(Exception):
    """交易系统基础异常类"""
    pass

class DataFetchError(TradingSystemError):
    """数据获取异常"""
    pass

class LLMError(TradingSystemError):
    """LLM调用异常"""
    pass

class NetworkError(TradingSystemError):
    """网络异常"""
    pass

def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """
    装饰器：为函数添加指数退避重试机制
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logging.error(f"函数 {func.__name__} 在 {max_retries} 次重试后仍然失败: {e}")
                        raise
                    
                    wait_time = backoff_factor * (2 ** attempt)
                    logging.warning(f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}，{wait_time}秒后重试...")
                    time.sleep(wait_time)
            
            raise last_exception
        return wrapper
    return decorator

def handle_network_request(
    url: str,
    method: str = 'GET',
    timeout: int = 30,
    max_retries: int = 3,
    **kwargs
) -> requests.Response:
    """
    统一的网络请求处理函数，包含重试和错误处理
    """
    session = requests.Session()
    
    # 设置代理（如果需要）
    try:
        from tradingagents.default_config import NETWORK_CONFIG
        if 'proxy' in NETWORK_CONFIG:
            session.proxies.update(NETWORK_CONFIG['proxy'])
        if 'headers' in NETWORK_CONFIG:
            session.headers.update(NETWORK_CONFIG['headers'])
    except ImportError:
        pass
    
    @retry_with_backoff(
        max_retries=max_retries,
        exceptions=(ConnectionError, Timeout, RequestException)
    )
    def make_request():
        response = session.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response
    
    try:
        return make_request()
    except RequestException as e:
        raise NetworkError(f"网络请求失败: {url}, 错误: {e}")

class SafeDataFetcher:
    """安全的数据获取类，包含缓存和容错机制"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = timedelta(minutes=15)  # 15分钟缓存
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.cache_duration:
                logging.info(f"使用缓存数据: {key}")
                return data
            else:
                del self.cache[key]
        return None
    
    def set_cache_data(self, key: str, data: Any):
        """设置缓存数据"""
        self.cache[key] = (data, datetime.now())
        logging.info(f"缓存数据已更新: {key}")
    
    @retry_with_backoff(max_retries=3, exceptions=(DataFetchError,))
    def fetch_stock_data(self, ticker: str, data_type: str, fetcher_func: Callable) -> Any:
        """
        安全的股票数据获取，带缓存和重试机制
        """
        cache_key = f"{ticker}_{data_type}"
        
        # 尝试从缓存获取
        cached_data = self.get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            logging.info(f"正在获取 {ticker} 的 {data_type} 数据...")
            data = fetcher_func(ticker)
            
            if data is None or (hasattr(data, '__len__') and len(data) == 0):
                raise DataFetchError(f"获取到的 {data_type} 数据为空")
            
            # 缓存数据
            self.set_cache_data(cache_key, data)
            logging.info(f"成功获取并缓存 {ticker} 的 {data_type} 数据")
            return data
            
        except Exception as e:
            error_msg = f"获取 {ticker} 的 {data_type} 数据失败: {e}"
            logging.error(error_msg)
            raise DataFetchError(error_msg)

class LLMSafetyWrapper:
    """LLM调用的安全包装器"""
    
    @staticmethod
    @retry_with_backoff(max_retries=3, exceptions=(LLMError,))
    def safe_invoke(llm_chain: Any, input_data: dict, agent_name: str = "未知") -> Any:
        """
        安全的LLM调用，包含重试和错误处理
        """
        try:
            logging.info(f"正在调用 {agent_name} LLM...")
            result = llm_chain.invoke(input_data)
            
            if result is None:
                raise LLMError(f"{agent_name} 返回空结果")
            
            # 验证结果格式
            if hasattr(result, 'analysis') and not result.analysis.strip():
                raise LLMError(f"{agent_name} 返回的分析内容为空")
            
            logging.info(f"{agent_name} LLM调用成功")
            return result
            
        except Exception as e:
            error_msg = f"{agent_name} LLM调用失败: {e}"
            logging.error(error_msg)
            raise LLMError(error_msg)

def log_execution_time(func: Callable) -> Callable:
    """装饰器：记录函数执行时间"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logging.info(f"函数 {func.__name__} 执行成功，耗时: {execution_time:.2f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"函数 {func.__name__} 执行失败，耗时: {execution_time:.2f}秒，错误: {e}")
            raise
    return wrapper

# 全局数据获取器实例
safe_fetcher = SafeDataFetcher()
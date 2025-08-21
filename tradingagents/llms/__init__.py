# tradingagents/llms/__init__.py (V16.0 修复版)
import os
import logging
import httpx
from langchain_core.language_models.chat_models import BaseChatModel

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_community.chat_models import ChatTongyi
except ImportError as e:
    raise ImportError(f"无法导入核心库: {e}。请确保所有依赖已安装。")

try:
    from tradingagents.default_config import (
        ANALYSIS_LLM_PROVIDER, QWEN_CONFIG, GEMINI_CONFIG, 
        NETWORK_CONFIG, SEARCH_LLM_PROVIDER
    )
except ImportError:
    logging.critical("无法加载 default_config.py，程序无法启动。")
    exit()

def llm_client_factory(provider: str = None) -> BaseChatModel:
    """创建LLM客户端，支持代理配置"""
    provider_to_use = provider if provider else ANALYSIS_LLM_PROVIDER
    logging.info(f"LLM客户端工厂: 正在为 '{provider_to_use}' 任务创建模型客户端...")

    if provider_to_use == "gemini":
        api_key = GEMINI_CONFIG.get("api_key")
        if not api_key or "在这里粘贴" in api_key:
            raise ValueError("Gemini API Key 未在 default_config.py 中正确配置。")
        
        # 修复：使用httpx处理代理
        proxies = NETWORK_CONFIG.get('proxy') if NETWORK_CONFIG else None
        
        if proxies:
            # 设置环境变量方式（推荐）
            if 'http' in proxies:
                os.environ['HTTP_PROXY'] = proxies['http']
                os.environ['HTTPS_PROXY'] = proxies.get('https', proxies['http'])
                logging.info(f"已通过环境变量配置Gemini代理: {proxies['http']}")
            
            # 创建自定义httpx客户端
            transport = httpx.HTTPTransport(proxy=proxies.get('http'))
            client = httpx.Client(transport=transport)
            
            llm = ChatGoogleGenerativeAI(
                model=GEMINI_CONFIG.get("model_name", "gemini-1.5-flash"),
                google_api_key=api_key,
                temperature=0.7,
                convert_system_message_to_human=True,
                max_retries=3,
                timeout=60,
                # 使用自定义client
                client=client if proxies else None
            )
        else:
            # 无代理配置
            llm = ChatGoogleGenerativeAI(
                model=GEMINI_CONFIG.get("model_name", "gemini-1.5-flash"),
                google_api_key=api_key,
                temperature=0.7,
                convert_system_message_to_human=True,
                max_retries=3,
                timeout=60
            )
        
        return llm

    elif provider_to_use == "qwen":
        api_key = QWEN_CONFIG.get("api_key")
        if not api_key or "在这里粘贴" in api_key:
            raise ValueError("QWEN API Key 未在 default_config.py 中正确配置。")
        
        os.environ["DASHSCOPE_API_KEY"] = api_key
        return ChatTongyi(
            model_name=QWEN_CONFIG.get("model_name", "qwen-max"),
            temperature=QWEN_CONFIG.get("temperature", 0.7),
            max_retries=3
        )

    else:
        raise ValueError(f"不支持的LLM提供商: '{provider_to_use}'")
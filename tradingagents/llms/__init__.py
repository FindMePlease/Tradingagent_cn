# tradingagents/llms/__init__.py (V15.0 最终版 - 精确代理)
import os
import logging
from langchain_core.language_models.chat_models import BaseChatModel

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_community.chat_models import ChatTongyi
except ImportError as e:
    raise ImportError(f"无法导入核心库: {e}。请确保所有依赖已安装。")

try:
    from tradingagents.default_config import (
        ANALYSIS_LLM_PROVIDER, QWEN_CONFIG, GEMINI_CONFIG, NETWORK_CONFIG
    )
except ImportError:
    logging.critical("无法加载 default_config.py，程序无法启动。")
    exit()

def llm_client_factory(provider: str = None) -> BaseChatModel:
    provider_to_use = provider if provider else ANALYSIS_LLM_PROVIDER
    logging.info(f"LLM客户端工厂: 正在为 '{provider_to_use}' 任务创建模型客户端...")

    if provider_to_use == "gemini":
        api_key = GEMINI_CONFIG.get("api_key")
        if not api_key or "在这里粘贴" in api_key:
            raise ValueError("Gemini API Key 未在 default_config.py 中正确配置。")
        
        # --- [核心改造] 只为Gemini客户端配置代理 ---
        proxies = NETWORK_CONFIG.get('proxy') if NETWORK_CONFIG else None
        
        if proxies:
             logging.info(f"已为Gemini客户端配置代理: {proxies}")

        llm = ChatGoogleGenerativeAI(
            model=GEMINI_CONFIG["model_name"], 
            google_api_key=api_key,
            temperature=0.0, 
            convert_system_message_to_human=True,
            # LangChain v0.2+ 推荐通过 client_options 传递代理
            client_options={"proxies": proxies} if proxies else None
        )
        return llm

    elif provider_to_use == "qwen":
        api_key = QWEN_CONFIG.get("api_key")
        if not api_key or "在这里粘贴" in api_key:
            raise ValueError("QWEN API Key 未在 default_config.py 中正确配置。")
        # 千问SDK通过环境变量读取代理，我们在这里不设置，让它直连
        os.environ["DASHSCOPE_API_KEY"] = api_key
        return ChatTongyi(model_name=QWEN_CONFIG["model_name"], temperature=QWEN_CONFIG.get("temperature", 0.1))

    else:
        raise ValueError(f"不支持的LLM提供商: '{provider_to_use}'")
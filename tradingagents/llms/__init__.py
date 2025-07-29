import os
import logging
from langchain_core.language_models.chat_models import BaseChatModel

# 导入所有需要的配置
try:
    from tradingagents.default_config import (
        LLM_PROVIDER,
        QWEN_CONFIG,
        DEEPSEEK_CONFIG
    )
except ImportError:
    logging.critical("无法加载 default_config.py，程序无法启动。")
    exit()


def llm_client_factory(provider: str = None) -> BaseChatModel:
    """
    根据提供商名称创建并返回一个LangChain的ChatModel实例。
    """
    provider_to_use = provider if provider else LLM_PROVIDER
    logging.info(f"LLM客户端工厂: 正在创建 '{provider_to_use}' 模型的客户端...")

    if provider_to_use == "qwen":
        try:
            from langchain_community.chat_models import ChatTongyi
        except ImportError:
            raise ImportError("要使用 'qwen' 模型, 请运行: pip install langchain-community dashscope")
        
        api_key = QWEN_CONFIG.get("api_key")
        if not api_key or "your_qwen_api_key" in api_key or "在这里粘贴" in api_key:
            raise ValueError("QWEN API Key 未在 default_config.py 中正确配置。")
        
        os.environ["DASHSCOPE_API_KEY"] = api_key
        return ChatTongyi(model_name=QWEN_CONFIG["model_name"])

    # --- [核心修正] 彻底修正 DeepSeek 的导入路径 ---
    elif provider_to_use == "deepseek":
        try:
            # 不再从 langchain_community 导入，而是从我们刚刚安装的 langchain_deepseek 导入
            from langchain_deepseek import ChatDeepSeek
        except ImportError:
            # 错误提示也变得更精准
            raise ImportError("要使用 'deepseek' 模型, 请确保您已运行: pip install langchain-deepseek")

        api_key = DEEPSEEK_CONFIG.get("api_key")
        if not api_key or "your_deepseek_api_key" in api_key or "在这里粘贴" in api_key:
            raise ValueError("DeepSeek API Key 未在 default_config.py 中正确配置。")

        return ChatDeepSeek(
            model=DEEPSEEK_CONFIG["model_name"],
            api_key=api_key,
            # [新增] DeepSeek的API基础URL，确保连接正确
            base_url="https://api.deepseek.com/v1"
        )
    # ---------------------------------------------

    else:
        supported_providers = ["qwen", "deepseek"]
        raise ValueError(f"不支持的LLM提供商: '{provider_to_use}'. 当前支持: {supported_providers}")
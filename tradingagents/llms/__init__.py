# -*- coding: utf-8 -*-

"""
模块: LLM 客户端工厂
职责: 根据项目配置文件 (default_config.py)，动态创建并返回一个
      与指定大语言模型提供商 (如 Qwen, Ollama) 对接的LangChain客户端实例。
      这是整个项目实现模型无关性(model-agnostic)的核心。
"""

import os
import logging
from langchain_core.language_models.chat_models import BaseChatModel

# 尝试从我们重构后的配置文件中导入配置
try:
    from tradingagents.default_config import (
        LLM_PROVIDER,
        QWEN_CONFIG,
        OLLAMA_CONFIG,
        OPENAI_CONFIG
    )
except ImportError:
    # 如果配置文件不存在，提供一个备用方案，防止程序在导入时就崩溃
    logging.warning("无法加载 default_config.py，将使用默认的 'qwen' 配置。")
    LLM_PROVIDER = "qwen"
    QWEN_CONFIG = {"api_key": "your_qwen_api_key", "model_name": "qwen-plus"}
    OLLAMA_CONFIG = {"host": "http://localhost:11434", "model_name": "llama3"}
    OPENAI_CONFIG = {"api_key": "your_openai_api_key", "model_name": "gpt-4-turbo"}


def llm_client_factory(provider: str = None) -> BaseChatModel:
    """
    根据提供商名称创建并返回一个LangChain的ChatModel实例。

    Args:
        provider (str, optional): 指定的LLM提供商。如果为None，则从配置文件中读取。
                                  可选项: 'qwen', 'ollama', 'openai'。

    Returns:
        BaseChatModel: 一个实例化的LangChain聊天模型客户端。

    Raises:
        ValueError: 如果指定的提供商不受支持。
    """
    # 如果未指定provider，则使用配置文件中的全局设置
    provider_to_use = provider if provider else LLM_PROVIDER
    
    logging.info(f"LLM客户端工厂: 正在创建 '{provider_to_use}' 模型的客户端...")

    if provider_to_use == "qwen":
        try:
            from langchain_community.chat_models import ChatTongyi
        except ImportError:
            raise ImportError("要使用 'qwen' 模型, 请运行: pip install langchain-community dashscope")
        
        # 确保API Key已设置
        if "your_qwen_api_key" in QWEN_CONFIG.get("api_key", ""):
            logging.error("检测到通义千问API Key未配置，请在 default_config.py 中设置 QWEN_CONFIG。")
            raise ValueError("QWEN API Key not configured.")
        
        # 将api_key设置为环境变量，这是langchain推荐的做法
        os.environ["DASHSCOPE_API_KEY"] = QWEN_CONFIG["api_key"]
        
        return ChatTongyi(model_name=QWEN_CONFIG["model_name"])

    elif provider_to_use == "ollama":
        try:
            from langchain_community.chat_models import Ollama
        except ImportError:
            raise ImportError("要使用 'ollama' 模型, 请运行: pip install langchain-community langchain-ollama")
            
        logging.info(f"连接到 Ollama host: {OLLAMA_CONFIG['host']}，使用模型: {OLLAMA_CONFIG['model_name']}")
        return Ollama(
            base_url=OLLAMA_CONFIG["host"],
            model=OLLAMA_CONFIG["model_name"]
        )
    
    elif provider_to_use == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("要使用 'openai' 模型, 请运行: pip install langchain-openai")
        
        if "your_openai_api_key" in OPENAI_CONFIG.get("api_key", ""):
            logging.error("检测到OpenAI API Key未配置，请在 default_config.py 中设置 OPENAI_CONFIG。")
            raise ValueError("OpenAI API Key not configured.")

        return ChatOpenAI(
            api_key=OPENAI_CONFIG["api_key"],
            model=OPENAI_CONFIG["model_name"]
        )

    else:
        supported_providers = ["qwen", "ollama", "openai"]
        raise ValueError(f"不支持的LLM提供商: '{provider_to_use}'. "
                         f"当前支持的提供商: {supported_providers}")

# ==============================================================================
# 示例用法
# ==============================================================================
if __name__ == '__main__':
    print(f"--- 测试LLM客户端工厂 ---")
    print(f"配置文件中的默认提供商是: '{LLM_PROVIDER}'")

    try:
        # 1. 创建默认的LLM客户端
        print("\n1. 尝试创建默认配置的客户端...")
        default_client = llm_client_factory()
        print(f"成功创建客户端: {type(default_client)}")
        print(f"模型名称: {default_client.model_name}")

        # 2. 模拟调用 (这部分可能因API Key无效而失败，但能测试创建逻辑)
        print("\n2. 尝试调用模型 (如果API Key无效，此处会报错)...")
        # response = default_client.invoke("你好")
        # print(f"模型调用成功，返回: {response.content}")

    except (ValueError, ImportError) as e:
        print(f"创建或调用默认客户端时出错: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}, 请检查API Key和网络连接。")

    # 3. 强制创建Ollama客户端进行测试
    print("\n3. 尝试强制创建 'ollama' 客户端...")
    try:
        ollama_client = llm_client_factory(provider="ollama")
        print(f"成功创建客户端: {type(ollama_client)}")
        print(f"模型名称: {ollama_client.model}")
        print("请确保你的Ollama服务正在本地运行以进行调用测试。")
        # response = ollama_client.invoke("你好")
        # print(f"Ollama模型调用成功，返回: {response.content}")
    except (ValueError, ImportError) as e:
        print(f"创建Ollama客户端时出错: {e}")
    except Exception as e:
        # 通常是网络连接错误
        print(f"连接Ollama时出错: {e}")
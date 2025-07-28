# verify_news_agent.py (V4.2 最终验证版)
import argparse
import logging
import os
import requests
from bs4 import BeautifulSoup
from typing import List
from datetime import datetime, timedelta

# --- 1. 配置日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 2. 复制 Pydantic 和 LangChain 定义 ---
try:
    from pydantic import BaseModel, Field
    from langchain.prompts import ChatPromptTemplate
    from langchain_community.chat_models import ChatTongyi
    from langchain.output_parsers import PydanticOutputParser
except ImportError:
    print("[错误] 核心库未安装。请在终端运行: pip install pydantic langchain langchain-community dashscope")
    exit()

# --- 3. 复制 AI分析师的输出格式 ---
class AnalyzedArticle(BaseModel):
    title: str = Field(description="新闻的主标题")
    source: str = Field(description="新闻来源网站名称")
    publication_date: str = Field(description="新闻的发布日期和时间, 格式为 'YYYY-MM-DD HH:MM:SS'")
    summary: str = Field(description="对新闻核心内容的2-3句话总结")
    relevance: str = Field(description="与公司核心业务的相关度, 必须是 '高', '中', '低' 中的一个")
    sentiment: str = Field(description="新闻的情绪倾向, 必须是 '利好', '中性', '利空' 中的一个")

# --- 4. 复制 Prompt 和 Chain 的定义 ---
HTML_ANALYZER_PROMPT = """你是一名顶尖的财经新闻分析师和网页信息提取专家。你的任务是“阅读”下面提供的、由我的程序从网上抓取到的实时网页内容，并为我提取和分析出关于「{stock_name}」的核心信息。
{format_instructions}
**以下是由我的程序刚刚从URL抓取到的实时网页内容：**
```{page_content}```
请将你的分析结果，以结构化的方式返回。你必须只返回一个JSON对象。"""

def get_html_analyzer_chain(api_key: str, model_name: str):
    parser = PydanticOutputParser(pydantic_object=AnalyzedArticle)
    llm = ChatTongyi(model_name=model_name, dashscope_api_key=api_key)
    prompt = ChatPromptTemplate.from_template(
        HTML_ANALYZER_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt | llm | parser

# --- 5. 复制主执行函数 ---
def run_verification(stock_name: str, num_articles: int, api_key: str, model_name: str, news_api_key: str):
    logging.info(f"--- 启动AI新闻智能体 for {stock_name} ---")
    urls_to_check = []
    try:
        from newsapi import NewsApiClient
        newsapi = NewsApiClient(api_key=news_api_key)
        
        # [核心升级] 使用 get_top_headlines 接口
        print(f"\n[诊断信息] 正在通过 NewsAPI.org 【中国头条】接口搜索关于 '{stock_name}' 的新闻...")
        top_headlines = newsapi.get_top_headlines(q=stock_name, country='cn')
        print("[诊断信息] NewsAPI.org 搜索执行完毕。")
        
        if top_headlines['status'] == 'ok' and top_headlines['articles']:
            urls_to_check = [article['url'] for article in top_headlines['articles']]
            logging.info(f"已通过 NewsAPI【中国头条】发现 {len(urls_to_check)} 条潜在新闻链接。")
        else:
            logging.warning("NewsAPI【中国头条】未能返回任何新闻资讯。")
    except Exception as e:
        return f"AI新闻智能体在[检索]阶段发生错误: {e}\n"
    
    if not urls_to_check:
        return f"--- AI新闻智能体报告 for {stock_name} ---\n\n通过 NewsAPI【中国头条】，未能找到任何近期相关新闻。\n"
    
    analyzer_chain = get_html_analyzer_chain(api_key, model_name)
    analyzed_articles = []

    for url in urls_to_check:
        if len(analyzed_articles) >= num_articles:
            break
        try:
            # ... (抓取和分析逻辑保持不变) ...
            logging.info(f"正在抓取并分析URL: {url}")
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, timeout=20, headers=headers)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'lxml')
            page_content = soup.get_text(separator='\n', strip=True)
            if len(page_content) < 150:
                logging.warning("页面有效内容过短，跳过。")
                continue
            analysis_result = analyzer_chain.invoke({
                "stock_name": stock_name,
                "page_content": page_content[:8000]
            })
            if analysis_result and analysis_result.relevance == "高":
                analysis_result.source = url
                analyzed_articles.append(analysis_result)
                logging.info(f"成功分析一篇 [高] 相关度新闻: {analysis_result.title}")
            elif analysis_result:
                logging.warning(f"分析完成，但相关度为[{analysis_result.relevance}]，已过滤: {analysis_result.title}")
        except Exception as e:
            logging.error(f"处理URL {url} 时失败: {e}")
    
    final_report = f"--- AI新闻智能体报告 for {stock_name} ---\n\n"
    if not analyzed_articles:
        final_report += f"通过 NewsAPI【中国头条】共找到 {len(urls_to_check)} 条近期相关新闻，但经AI分析后，未发现与公司核心业务【高度相关】的新闻。\n"
    else:
        for article in analyzed_articles:
            final_report += f"标题: {article.title}\n"
            final_report += f"来源: {article.source}\n"
            final_report += f"发布时间: {article.publication_date}\n"
            final_report += f"情绪倾向: [{article.sentiment}]\n"
            final_report += f"摘要: {article.summary}\n\n"
    return final_report

# --- 6. 主执行块 ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="独立的【NewsAPI 中国头条版】AI新闻智能体验证脚本。")
    parser.add_argument("--ticker", type=str, required=True, help="股票代码")
    parser.add_argument("--name", type=str, required=True, help="股票中文名称")
    parser.add_argument("--num", type=int, default=3, help="希望分析的新闻数量")
    
    QWEN_API_KEY, MODEL_NAME, NEWS_API_KEY = None, None, None
    try:
        from tradingagents.default_config import QWEN_CONFIG, NEWS_API_CONFIG
        QWEN_API_KEY = QWEN_CONFIG['api_key']
        MODEL_NAME = QWEN_CONFIG.get('model_name', 'qwen-plus')
        NEWS_API_KEY = NEWS_API_CONFIG['api_key']
        print("--- [诊断脚本]：成功从 default_config.py 加载所有API Key ---")
    except (ImportError, KeyError):
        print("\n[严重错误] 无法加载您的API Key配置。请检查 default_config.py 文件。")

    args = parser.parse_args()
    
    if QWEN_API_KEY and NEWS_API_KEY and "your_" not in QWEN_API_KEY and "在这里" not in NEWS_API_KEY:
        final_report_text = run_verification(
            stock_name=args.name, 
            num_articles=args.num,
            api_key=QWEN_API_KEY,
            model_name=MODEL_NAME,
            news_api_key=NEWS_API_KEY
        )
        print("\n" + "="*80)
        print("                 诊断完成 - 最终生成的报告")
        print("="*80)
        print(final_report_text)
    else:
        print("\n[执行中止] API Key 未正确配置，无法继续。")
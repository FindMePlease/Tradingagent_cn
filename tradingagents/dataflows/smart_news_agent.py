import requests
from bs4 import BeautifulSoup
import logging
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from typing import List
from datetime import datetime, timedelta

# 导入我们项目的核心工具
from tradingagents.llms import llm_client_factory
from tradingagents.default_config import Google_Search_CONFIG

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 1. 定义AI分析师的输出格式 ---
class AnalyzedArticle(BaseModel):
    title: str = Field(description="新闻的主标题")
    source: str = Field(description="新闻来源网站名称, 例如 '新浪财经' 或 '雪球'")
    publication_date: str = Field(description="新闻的发布日期和时间, 格式为 'YYYY-MM-DD HH:MM:SS'")
    summary: str = Field(description="对新闻核心内容的2-3句话总结")
    relevance: str = Field(description="与公司核心业务的相关度, 必须是 '高', '中', '低' 中的一个")
    sentiment: str = Field(description="新闻的情绪倾向, 必须是 '利好', '中性', '利空' 中的一个")

# --- 2. 定义AI分析师的Prompt和Chain ---
HTML_ANALYZER_PROMPT = """
你是一名顶尖的财经新闻分析师和网页信息提取专家。你的任务是“阅读”下面提供的、由我的程序从网上抓取到的实时网页内容，并为我提取和分析出关于「{stock_name}」的核心信息。

{format_instructions}

**以下是由我的程序刚刚从URL抓取到的实时网页内容：**
```{page_content}```

请将你的分析结果，以结构化的方式返回。你必须只返回一个JSON对象。
"""

def get_html_analyzer_chain():
    parser = PydanticOutputParser(pydantic_object=AnalyzedArticle)
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(
        HTML_ANALYZER_PROMPT,
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    return prompt | llm | parser

# --- 3. 主执行函数 (RAG流程 - Google API 时间限定版) ---
def get_smart_news(ticker: str, stock_name: str, num_articles: int = 10) -> str:
    logging.info(f"--- 启动AI新闻智能体 for {stock_name} ---")
    
    # **第一步：检索 (Retrieve) - [核心升级] 引入时间限定**
    urls_to_check = []
    try:
        from googleapiclient.discovery import build
        
        API_KEY = Google_Search_CONFIG.get("api_key")
        CX_ID = Google_Search_CONFIG.get("cx_id")
        
        if not API_KEY or "在这里粘贴" in API_KEY or not CX_ID:
            raise ValueError("Google Search API Key 或 CX ID 未在 default_config.py 中正确配置。")

        # [核心升级] 计算6个月前的日期
        six_months_ago = datetime.now() - timedelta(days=180)
        # Google API 需要的日期范围格式
        # dateRestrict: 'd[N]' for days, 'w[N]' for weeks, 'm[N]' for months
        # 我们将使用 m6 来代表过去6个月
        date_restriction = "m6"

        logging.info(f"\n[诊断信息] 正在通过【Google API】搜索关于 '{stock_name}' 的新闻 (时间范围：过去6个月)...")
        
        service = build("customsearch", "v1", developerKey=API_KEY)
        
        # [核心升级] 在请求中加入 dateRestrict 参数
        res = service.cse().list(
            q=stock_name, 
            cx=CX_ID, 
            sort='date', 
            num=10, 
            dateRestrict=date_restriction
        ).execute()
        
        logging.info("[诊断信息] Google API 搜索执行完毕。")

        if "items" in res and res["items"]:
            urls_to_check = [item['link'] for item in res['items']]
            logging.info(f"已通过 Google API 发现 {len(urls_to_check)} 条【过去6个月内】的潜在新闻链接。")
        else:
            logging.warning("Google API 未能返回任何指定时间范围的新闻资讯。")

    except Exception as e:
        logging.error(f"Google API在搜索时发生错误: {e}")
        return f"AI新闻智能体在[检索]阶段发生错误: {e}\n"

    if not urls_to_check:
        return f"--- AI新闻智能体报告 for {stock_name} ---\n\n通过【Google API】，未能在过去6个月内找到任何相关新闻。\n"

    analyzer_chain = get_html_analyzer_chain()
    analyzed_articles: List[AnalyzedArticle] = []

    # **第二步：生成 (Generate)**
    for url in urls_to_check:
        if len(analyzed_articles) >= num_articles:
            break
        try:
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

    # **第三步：汇总报告**
    final_report = f"--- AI新闻智能体报告 for {stock_name} ---\n\n"
    if not analyzed_articles:
        final_report += f"通过【Google API】共找到 {len(urls_to_check)} 条【过去6个月内】的相关新闻，但经AI分析后，未发现与公司核心业务【高度相关】的新闻。\n"
    else:
        for article in analyzed_articles:
            final_report += f"标题: {article.title}\n"
            final_report += f"来源: {article.source}\n"
            final_report += f"发布时间: {article.publication_date}\n"
            final_report += f"情绪倾向: [{article.sentiment}]\n"
            final_report += f"摘要: {article.summary}\n\n"
    return final_report
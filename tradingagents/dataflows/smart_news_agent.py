# tradingagents/dataflows/smart_news_agent.py (V3.0 RAG架构版)
import requests
from bs4 import BeautifulSoup
import logging
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from typing import List

# 从我们项目的llms模块导入LLM客户端工厂
from tradingagents.llms import llm_client_factory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- 1. 定义AI分析师的输出格式 ---
class AnalyzedArticle(BaseModel):
    """单篇新闻经过AI分析后输出的结构化数据"""
    title: str = Field(description="新闻的主标题")
    source: str = Field(description="新闻来源网站名称, 例如 '新浪财经' 或 '雪球'")
    publication_date: str = Field(description="新闻的发布日期和时间, 格式为 'YYYY-MM-DD HH:MM:SS'")
    summary: str = Field(description="对新闻核心内容的2-3句话总结")
    relevance: str = Field(description="与公司核心业务的相关度, 必须是 '高', '中', '低' 中的一个")
    sentiment: str = Field(description="新闻的情绪倾向, 必须是 '利好', '中性', '利空' 中的一个")

# --- 2. 定义AI分析师的Prompt和Chain ---
HTML_ANALYZER_PROMPT = """
你是一名顶尖的财经新闻分析师和网页信息提取专家。你的任务是“阅读”下面提供的、由我的程序从网上抓取到的实时网页内容，并为我提取和分析出关于「{stock_name}」的核心信息。

**请严格遵循以下指令：**
1.  **忽略所有无关内容**：彻底忽略网页中的广告、导航栏、页脚、相关文章推荐、用户评论区等所有噪音。
2.  **提取核心要素**：从正文区域中，精确地提取出新闻的主标题、来源、和发布日期。如果找不到确切来源，可以根据URL推断。
3.  **进行智能分析**：
    * **总结摘要**: 用2-3句话，凝练地总结这篇新闻的核心观点。
    * **评估相关度**: 判断这篇新闻与「{stock_name}」的**核心业务或重大事件**的相关度，给出"高"、"中"或"低"的评级。
    * **判断情绪**: 判断这篇新闻对「{stock_name}」的潜在影响，给出"利好"、"中性"或"利空"的评级。

**以下是由我的程序刚刚从URL抓取到的实时网页内容：**
{page_content}
请将你的分析结果，以结构化的方式返回。你必须只返回一个JSON对象，不要有任何其他多余的文字或解释。
"""

def get_html_analyzer_chain():
    """创建一个可以分析HTML并返回结构化数据的AI链"""
    llm = llm_client_factory()
    prompt = ChatPromptTemplate.from_template(HTML_ANALYZER_PROMPT)
    return prompt | llm.with_structured_output(AnalyzedArticle)

# --- 3. 主执行函数 (RAG流程) ---
def get_smart_news(ticker: str, stock_name: str, num_articles: int = 3) -> str:
    """
    AI驱动的新闻获取与分析流程 (RAG架构)
    """
    logging.info(f"--- 启动AI新闻智能体 for {stock_name} ---")
    
    # **第一步：检索 (Retrieve)**
    try:
        from duckduckgo_search import DDGS
        search_query = f"{stock_name} 公司 最新 财经 新闻 公告"
        results = DDGS().text(search_query, region='cn-zh', max_results=num_articles * 2)
        if not results:
            logging.warning("搜索引擎未能返回任何结果。")
            urls_to_check = []
        else:
            urls_to_check = [r['href'] for r in results]
        logging.info(f"已发现以下潜在新闻链接: {urls_to_check[:num_articles]}")
    except Exception as e:
        logging.error(f"搜索引擎在搜索时发生错误: {e}")
        return f"AI新闻智能体在[检索]阶段发生错误: {e}\n"

    analyzer_chain = get_html_analyzer_chain()
    analyzed_articles: List[AnalyzedArticle] = []

    # **第二步：生成 (Generate)，对每个检索到的内容进行处理**
    for url in urls_to_check:
        if len(analyzed_articles) >= num_articles:
            break
        try:
            logging.info(f"正在抓取并分析URL: {url}")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(url, timeout=20, headers=headers)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.text, 'lxml')
            article_body = soup.find('article') or soup.find('main') or soup.find('body')
            page_content = article_body.get_text(separator='\n', strip=True) if article_body else ''
            
            if len(page_content) < 150:
                logging.warning("页面有效内容过短，跳过。")
                continue

            # **将检索到的内容，增强(Augment)到Prompt中，并交给AI生成**
            analysis_result = analyzer_chain.invoke({
                "stock_name": stock_name,
                "page_content": page_content[:8000]  # 限制token数量
            })
            
            if analysis_result.relevance == "高":
                analysis_result.source = url
                analyzed_articles.append(analysis_result)
                logging.info(f"成功分析一篇 [高] 相关度新闻: {analysis_result.title}")
            else:
                logging.warning(f"分析完成，但相关度为[{analysis_result.relevance}]，已过滤: {analysis_result.title}")

        except Exception as e:
            logging.error(f"处理URL {url} 时失败: {e}")

    # --- 4. 汇总报告 ---
    if not analyzed_articles:
        return f"--- AI新闻智能体报告 for {stock_name} ---\n\n通过全网搜索，未能找到与该公司核心业务高度相关的新闻。\n"
        
    final_report = f"--- AI新闻智能体报告 for {stock_name} ---\n\n"
    for article in analyzed_articles:
        final_report += f"标题: {article.title}\n"
        final_report += f"来源: {article.source}\n"
        final_report += f"发布时间: {article.publication_date}\n"
        final_report += f"情绪倾向: [{article.sentiment}]\n"
        final_report += f"摘要: {article.summary}\n\n"
        
    return final_report

# ... 独立的测试脚本 ...
if __name__ == '__main__':
    pass  # 在main.py中统一测试
# -*- coding: utf-8 -*-
"""
这是一个诊断脚本，它的唯一目的，就是列出您当前安装的 akshare 库中，
所有可能与获取“新闻”、“快讯”、“电报”相关的函数名称。
"""

import akshare as ak

print("="*80)
print(f"正在检查您安装的 akshare 库 (版本: {ak.__version__})")
print("="*80)

# 定义我们关心的关键词
keywords = ['news', 'flash', 'telegraph', 'jinshi', 'cls', 'subscribe']
found_functions = []

# dir(ak) 会列出 akshare 库中所有的可用函数和属性
for func_name in dir(ak):
    # 检查函数名是否包含任何一个关键词
    if any(keyword in func_name for keyword in keywords):
        found_functions.append(func_name)

if found_functions:
    print("\n[成功] 在您的 akshare 中找到了以下可能相关的函数：\n")
    for func_name in sorted(found_functions):
        print(f"  - {func_name}")
    print("\n请将上面的函数列表完整地复制给我，我将为您挑选出最合适的一个来重写代码。")
else:
    print("\n[错误] 在您的 akshare 中没有找到任何与新闻快讯相关的已知函数。")
    print("这可能意味着您的 akshare 版本过低。")
    print("请尝试在终端中运行 'pip install akshare --upgrade' 来升级它，然后再次运行此脚本。")

print("="*80)
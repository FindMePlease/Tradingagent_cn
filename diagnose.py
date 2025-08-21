import os
import sys
from pathlib import Path

print("="*80)
print("🐍 Python 导入系统诊断工具 🐍")
print("="*80)

# 1. 打印当前的工作目录
print(f"[*] 当前工作目录 (Current Working Directory):\n    {os.getcwd()}\n")

# 2. 打印 Python 的搜索路径 (sys.path)
print("[*] Python 当前的模块搜索路径 (sys.path):")
for i, path in enumerate(sys.path):
    print(f"    {i}: {path}")
print("\n")

# 3. 检查关键文件和文件夹是否存在
try:
    project_root = Path(__file__).resolve().parent
    print(f"[*] 脚本计算出的项目根目录:\n    {project_root}\n")

    paths_to_check = {
        "项目根目录": project_root,
        "'tradingagents' 文件夹": project_root / "tradingagents",
        "'tradingagents/__init__.py' 文件": project_root / "tradingagents" / "__init__.py",
        "'utils' 文件夹": project_root / "tradingagents" / "utils",
        "'tradingagents/utils/__init__.py' 文件": project_root / "tradingagents" / "utils" / "__init__.py",
    }

    print("[*] 检查必要的文件和文件夹:")
    all_found = True
    for name, path in paths_to_check.items():
        if path.exists():
            status = "✅ 找到"
            if name.endswith("文件夹"):
                is_dir = " (正确识别为文件夹)" if path.is_dir() else " (❌ 错误识别为文件!)"
                if not path.is_dir(): all_found = False
            else:
                is_dir = " (正确识别为文件)" if path.is_file() else " (❌ 错误识别为文件夹!)"
                if not path.is_file(): all_found = False
            print(f"    - {name}: {status}{is_dir}")
        else:
            status = "❌ 未找到"
            all_found = False
            print(f"    - {name}: {status}")
    print("\n")

    # 4. 尝试执行有问题的导入语句
    print("[*] 正在尝试执行有问题的导入语句...")
    # 像 main.py 一样，将项目根目录添加到 sys.path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"    -> 已将 '{project_root}' 添加到搜索路径的顶端。")

    from tradingagents.utils import error_handler
    print("    ✅ 成功: 'from tradingagents.utils import error_handler' 这条导入语句执行成功了！\n")

except ModuleNotFoundError as e:
    print(f"    ❌ 失败: 导入时出现了完全相同的错误:\n       {e}\n")
except ImportError as e:
    print(f"    ❌ 失败: 导入时出现了不同的错误:\n       {e}\n")
except Exception as e:
    print(f"    ❌ 失败: 出现了预料之外的错误:\n       {e}\n")

# 5. 最终结论
print("="*80)
print("诊断结论:")
if 'all_found' in locals() and all_found:
    print("    ✅ 所有必要的 `__init__.py` 文件和文件夹似乎都存在。")
    print("    如果导入仍然失败，问题很可能出在您的 Python 环境或 VS Code 的配置上。")
else:
    print("    ❌ 一个或多个必要的文件/文件夹 未找到。")
    print("    这是导致 `ModuleNotFoundError` 的最可能原因。")
    print("    请仔细检查上面标记为 '未找到' 的路径，并确保文件/文件夹被正确创建。")
print("="*80)
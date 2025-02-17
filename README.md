# DeepseekCodeReview
利用deepseek来进行固定模板要求下的代码审查，生成代码审查报告，十分好用

# 自动代码审查工具

基于DeepSeek大模型实现的智能代码审查系统，提供多维度代码质量分析并生成结构化报告。

## 主要功能
- 三级问题分类（错误/警告/建议）
- 代码质量四维分析（质量/性能/安全/规范）
- 结构化报告输出（Markdown格式）
- 智能修复建议与示例代码

## 快速开始

### 环境要求
- Python 3.8+
- 有效DeepSeek API密钥

安装依赖
pip install openai argparse
bash
python code_review.py [-h] [-f FILE]
选项：
-h, --help 显示帮助信息
-f FILE, --file FILE 指定要审查的代码文件路径（默认：coze.txt）
python
... existing code ...
client = OpenAI(api_key="您的API密钥", base_url="https://api.deepseek.com")
... existing code ...
markdown
代码质量报告 - example.py
问题摘要
严重问题: 2 个
警告事项: 3 个
改进建议: 5 个
问题详情
ERROR 级别问题
位置: 第15-18行
描述: 未处理数据库连接异常
建议: 添加try-except块处理连接超时情况

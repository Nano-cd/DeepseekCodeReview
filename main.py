import argparse
import json
import os
import re

from openai import OpenAI


def perform_code_review(agent, file_content):
    code_review_prompt = """
    请遵循以下代码审查规范：
    1. 错误等级分类（按严重性降序）：
       - error: 阻碍编译/运行的致命问题
       - warning: 潜在逻辑错误或安全隐患
       - info: 代码风格/可维护性改进建议

    2. 审查维度：
       a. 代码质量（可读性、复杂度、错误处理）
       b. 性能优化（算法效率、资源管理）
       c. 安全漏洞（注入风险、敏感数据处理）
       d. 代码规范（命名、注释、格式）

    3. 输出要求：
       - 按问题严重性排序
       - 每个问题需包含：
         1) 问题位置（行号范围）
         2) 问题描述
         3) 改进建议
         4) 示例代码（可选）
       - 中文输出，使用清晰的分级标题
    """

    try:
        # 修正后的API调用方式
        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": f"{code_review_prompt}\n"},
                {"role": "user", "content": f"审查代码：\n{file_content}"}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return parse_review_result(response.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}


def parse_review_result(raw_text):
    """解析AI返回的原始文本为结构化数据"""
    report = {
        "summary": {"error": 0, "warning": 0, "info": 0},
        "details": [],
        "recommendations": []
    }

    current_category = None
    for line in raw_text.split('\n'):
        # 解析问题等级标题
        if "error" in line.lower():
            current_category = "error"
        elif "warning" in line.lower():
            current_category = "warning"
        elif "info" in line.lower():
            current_category = "info"

        # 解析具体问题条目
        if line.strip().startswith(('-', '•')):
            problem = {
                "level": current_category,
                "location": extract_line_numbers(line),
                "description": extract_description(line),
                "suggestion": extract_suggestion(line)
            }
            report["details"].append(problem)
            report["summary"][current_category] += 1

    return report


def generate_quality_report(review_data, file_path):
    """生成可视化质量报告"""
    report = f"# 代码质量报告 - {os.path.basename(file_path)}\n\n"

    # 生成摘要面板
    report += "## 问题摘要\n"
    report += f"- 严重问题: {review_data['summary']['error']} 个\n"
    report += f"- 警告事项: {review_data['summary']['warning']} 个\n"
    report += f"- 改进建议: {review_data['summary']['info']} 个\n\n"

    # 生成详细问题列表
    report += "## 问题详情\n"
    for issue in review_data['details']:
        report += f"### {issue['level'].upper()} 级别问题\n"
        report += f"- **位置**: 第{issue['location']}行\n"
        report += f"- **描述**: {issue['description']}\n"
        report += f"- **建议**: {issue['suggestion']}\n\n"

    # 生成优化建议
    if review_data['recommendations']:
        report += "## 全局优化建议\n"
        for rec in review_data['recommendations']:
            report += f"- {rec}\n"

    return report


def save_documentation(root_dir, file_path, content):
    file_name = os.path.basename(file_path)
    camel_case_name = ''.join(word.capitalize() for word in os.path.splitext(file_name)[0].split('_'))
    camel_case_name = camel_case_name[0].lower() + camel_case_name[1:]

    file_ext = f"{camel_case_name}.md"
    full_path = os.path.join(root_dir, file_ext)

    with open(full_path, "w") as file:
        file.write(content)


def extract_line_numbers(line):
    """使用正则表达式提取行号范围"""
    match = re.search(r'第(\d+)-(\d+)行', line)
    return f"{match.group(1)}-{match.group(2)}" if match else "N/A"


def extract_description(line):
    """提取问题描述"""
    return re.split(r'描述：', line)[-1].split('建议：')[0].strip()


def extract_suggestion(line):
    """提取改进建议"""
    return re.split(r'建议：', line)[-1].strip()


def main(client,args):
    """命令行入口函数"""
    try:
        # 获取代码内容
        code_content = read_code_file(args.file)

        # 执行代码审查
        review_data = perform_code_review(client, code_content)  # 修改agent参数为client

        # 生成并保存报告
        if not os.path.exists('reports'):
            os.makedirs('reports')

        report_content = generate_quality_report(
            review_data,
            args.file if args.file else 'input_code.txt'
        )

        save_documentation('reports',
                           args.file.replace('.', '_') + '_report.md' if args.file else
                           'code_review_report.md',
                           report_content)

        print(f"报告已生成：reports/{1}")

    except Exception as e:
        print(f"处理过程中发生错误：{str(e)}")


def read_code_file(file_path):
    """读取代码文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def verify_client_connection():
    """验证客户端连接是否正常"""
    try:
        test_prompt = [{"role": "user", "content": "ping"}]
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=test_prompt,
            max_tokens=5,
            timeout=10
        )
        return response.choices[0].message.content.strip() != ""
    except Exception as e:
        print(f"连接验证失败: {str(e)}")
        return False


if __name__ == "__main__":
    client = OpenAI(api_key="", base_url="https://api.deepseek.com")
    print("正在验证API连接...")
    if verify_client_connection():
        print("✅ 客户端连接成功")
    else:
        print("❌ 客户端连接失败")
    parser = argparse.ArgumentParser(description='自动代码审查工具')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('-f', '--file',
                      help='要审查的代码文件路径',
                      default='coze.txt')  # 设置默认文件路径
    args = parser.parse_args()
    main(client,args)
    print("finished")

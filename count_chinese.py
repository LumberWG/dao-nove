import re
import sys

def count_chinese_chars(text):
    """统计文本中的汉字数（按正则 [\u4e00-\u9fff] 计数）"""
    return len(re.findall(r'[\u4e00-\u9fff]', text))

def count_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    chars = count_chinese_chars(text)
    print(f"{path}: {chars} 汉字")
    return chars

if __name__ == '__main__':
    files = [
        '第1章_旧货摊前的雨.md',
        '第2章_两种未来.md',
        '第3章_许老头的粥.md'
    ]
    for f in files:
        count_file(f)

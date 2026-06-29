"""
恢复所有 md 文件的段落空行格式：
每段之间保留一个空行，场景切换处保留两个空行。
"""

import os, re

ROOT = r"d:\Study\Dao"
DIRS = ["chapters", "docs"]

def restore_blank_lines(text):
    """给段落之间加上空行"""
    # 先把所有连续的空白行归一化为一个 \n\n
    text = re.sub(r'\n{3,}', '\n\n', text)
    # 按行分割
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        result.append(line)
        # 如果当前行不是空行，且下一行存在且不是空行
        # 且当前行不是标题行（#开头），且下一行不是标题行
        # 且当前行不是水平分割线（---），且下一行不是水平分割线
        if line.strip() and i + 1 < len(lines) and lines[i + 1].strip():
            # 不是表格行（| 开头），且下一行也不是表格行
            if not line.startswith('|') and not lines[i + 1].startswith('|'):
                result.append('')  # 插入空行
        i += 1
    return '\n'.join(result)


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    restored = restore_blank_lines(content)
    if restored != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(restored)
        return True
    return False


if __name__ == '__main__':
    count = 0
    for d in DIRS:
        dirpath = os.path.join(ROOT, d)
        if not os.path.isdir(dirpath):
            continue
        for fname in sorted(os.listdir(dirpath)):
            if not fname.endswith('.md'):
                continue
            filepath = os.path.join(dirpath, fname)
            changed = process_file(filepath)
            if changed:
                print(f"  ✓ {d}/{fname}")
                count += 1
    print(f"\n共修改 {count} 个文件")

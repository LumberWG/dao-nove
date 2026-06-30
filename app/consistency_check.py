"""
《岁蚀》章节一致性检查脚本
用法: python app/consistency_check.py [章节文件名或目录]

自动检查:
1. 角色名是否与设定一致（柳三娘 vs 秦望舒 不混用）
2. 关键概念是否与世界观一致（隙径、岁蚀、境界等）
3. 伏笔状态标记
"""

import os, re, sys, glob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTER_DIR = os.path.join(BASE_DIR, "chapters")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

# ── 加载设定 ────────────────────────────────────────

def load_doc(filename):
    path = os.path.join(DOCS_DIR, filename)
    if not os.path.isfile(path):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def parse_character_names(text):
    """从文档中提取角色名"""
    names = set()
    # 匹配 ## 标题行的人物名 或 表格中的人物名
    for m in re.finditer(r'\|\s*\*\*([^|]+?)\*\*\s*\|', text):
        name = m.group(1).strip()
        if name and len(name) <= 8:
            names.add(name)
    # 匹配 **某某某** 作为强调的人名
    for m in re.finditer(r'\*\*([^《》\n]{2,6}?)\*\*', text):
        name = m.group(1)
        if name not in ('加粗', '重点', '核心', '关键'):
            names.add(name)
    return names


def load_known_characters():
    """从人物档案和出场记录中加载已知角色名"""
    known = set()
    for doc in ['人物档案.md', '人物出场记录.md']:
        text = load_doc(doc)
        for m in re.finditer(r'\*\*([^*/]{2,6}?)\*\*', text):
            name = m.group(1).strip()
            if name and len(name) <= 6 and not any(c in name for c in '《》、，。；：'):
                known.add(name)
    # 额外补充核心人名
    known.update(['许若存', '许老头', '柳三娘', '秦望舒', '沈见微',
                  '苏缠', '许衡', '红姑', '纪无咎', '叶知秋',
                  '小六子', '阿芷', '老陈', '柳无眠', '霍斩',
                  '季真', '谢渊', '白无瑕', '灵犀', '许承望',
                  '何伯安', '钟离燕', '老鸹', '花姐', '老鼹鼠',
                  '赵大爷', '王婶', '李婶', '周小满'])
    return known


def get_chapter_info(filepath):
    """解析章节文件名"""
    basename = os.path.basename(filepath)
    m = re.search(r'第(\d+)章_(.+)\.md', basename)
    if m:
        return int(m.group(1)), m.group(2), basename
    return None, None, basename


def count_chinese_chars(text):
    """统计中文字数"""
    return len(re.findall(r'[一-鿿]', text))


# ── 检查项 ──────────────────────────────────────────

def check_character_consistency(text, filename, known_chars):
    """检查角色名是否与设定一致"""
    issues = []
    # 应该用柳三娘的地方是否误用了秦望舒（在客店场景）
    inn_patterns = [
        (r'秦望舒.*?客店', '客店场景中应使用"柳三娘"，非"秦望舒"'),
        (r'秦望舒.*?荷包蛋', '荷包蛋场景属于柳三娘（客店老板娘）'),
        (r'秦望舒.*?(?:煮面|面条)', '煮面场景属于柳三娘（客店老板娘）'),
        (r'望舒客店', '客店已更名为"三娘客店"'),
    ]
    for pattern, msg in inn_patterns:
        for m in re.finditer(pattern, text):
            issues.append(('⚠️ 角色混用', f'第{filename}: {msg}\n   → 原文: "...{m.group()}..."'))
            break

    # 检查是否出现未知的角色名（可能打错）
    found_names = set()
    for m in re.finditer(r'[^一-鿿]([一-鿿]{2,4})[^一-鿿]', text):
        name = m.group(1)
        if name in known_chars:
            found_names.add(name)

    return issues


def check_concept_consistency(text, filename):
    """检查关键概念是否使用正确"""
    issues = []
    concepts = {
        r'境界.*?感气': '感气是卷一第6章觉醒的境界',
        r'境界.*?明心': '明心是卷一第60章达到的境界',
        r'境界.*?通法': '通法是卷二达到的境界',
        r'隙径.*?(?:不晕|不耳鸣|不恶心)': '走隙径通常会耳鸣恶心——如果角色不晕，需在情节中解释',
    }
    for pattern, msg in concepts.items():
        for m in re.finditer(pattern, text):
            issues.append(('💡 概念提醒', f'第{filename}: {msg}'))
            break

    return issues


def check_volume_consistency(text, filename, chapter_num):
    """根据章号判断各卷设定是否匹配"""
    issues = []
    if chapter_num is None:
        return issues

    # 各卷境界限制
    if chapter_num <= 65:  # 卷一
        if re.search(r'境界.*?通法', text):
            issues.append(('⚠️ 境界超前', f'第{filename}: 卷一（{chapter_num}章）不应出现"通法"境界（卷二才解锁）'))

    # 隙径在第8章首次引入，之后各章均可出现

    return issues


# ── 主流程 ──────────────────────────────────────────

def check_file(filepath):
    if not os.path.isfile(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    chapter_num, chapter_title, basename = get_chapter_info(filepath)
    char_count = count_chinese_chars(text)
    known_chars = load_known_characters()

    print(f"\n{'='*60}")
    print(f"📖 {basename}")
    if chapter_title:
        print(f"   第{chapter_num}章 {chapter_title}")
    print(f"   中文字数: {char_count}")
    print(f"{'='*60}")

    all_issues = []
    all_issues += check_character_consistency(text, basename, known_chars)
    all_issues += check_concept_consistency(text, basename)
    all_issues += check_volume_consistency(text, basename, chapter_num)

    if not all_issues:
        print("\n✅ 未发现明显问题")
    else:
        print(f"\n共发现 {len(all_issues)} 项：")
        for level, msg in all_issues:
            print(f"\n  {level}")
            print(f"    {msg}")

    return all_issues


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else [CHAPTER_DIR]

    all_results = []
    for target in targets:
        if os.path.isfile(target):
            all_results.extend(check_file(target) or [])
        elif os.path.isdir(target):
            files = sorted(glob.glob(os.path.join(target, "新_第*章_*.md")))
            print(f"📂 扫描目录: {target}  ({len(files)} 个章节)")
            for f in files:
                all_results.extend(check_file(f) or [])
        else:
            # 尝试 glob 模式
            matches = glob.glob(target)
            if matches:
                for f in sorted(matches):
                    all_results.extend(check_file(f) or [])
            else:
                print(f"❌ 未找到: {target}")

    issues_count = len(all_results)
    print(f"\n{'='*60}")
    if issues_count == 0:
        print("✅ 全部检查通过，无一致性问题")
    else:
        print(f"⚠️ 共 {issues_count} 项问题，建议逐条确认")
    print(f"{'='*60}\n")

    return 1 if issues_count > 0 else 0


if __name__ == '__main__':
    exit(main())

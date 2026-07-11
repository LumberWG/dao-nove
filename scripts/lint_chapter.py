#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《岁蚀》章节规则自检脚本

用法：
    python scripts/lint_chapter.py chapters/新_第21章_入城.md
    python scripts/lint_chapter.py chapters/              # 扫描目录下所有 .md

检查项来自 docs/笔法核心规则.md 中可量化的部分：
1. 每段不超过 3 句话
2. 每章「不是……是……」结构不超过 3 处
3. 每章禁用过渡词（然后/一会儿/忽然/接着/之后）不超过 2 处
4. 每章破折号（—）不超过 3 处
5. 每章「像是在/仿佛在」不超过 2 处
"""

import re
import sys
from pathlib import Path

# 规则阈值
LIMITS = {
    "not_x_but_y": 3,          # 不是……是……
    "transitions": 2,          # 过渡词
    "dashes": 3,               # 破折号
    "seems_like": 2,           # 像是在/仿佛在
}

TRANSITION_WORDS = ["然后", "一会儿", "忽然", "接着", "之后"]


def split_paragraphs(text):
    """按空行分段。"""
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def count_sentences(paragraph):
    """粗略统计句子数：句号、问号、感叹号。"""
    # 去掉章节标题
    if paragraph.startswith("#"):
        return 0
    return len(re.findall(r"[。！？]", paragraph))


def find_not_x_but_y(text):
    """查找「不是……是……」结构。"""
    # 匹配同一行或跨到下一行的"不是X是Y"
    pattern = re.compile(r"不是([^。！？\n]{0,40})是([^。！？\n]{0,40})")
    matches = []
    for m in pattern.finditer(text):
        matches.append((m.start(), m.group(0)))
    return matches


def find_transitions(text):
    """查找禁用过渡词。"""
    matches = []
    for word in TRANSITION_WORDS:
        for m in re.finditer(re.escape(word), text):
            matches.append((m.start(), word, m.group(0)))
    return matches


def find_dashes(text):
    """查找破折号（— 或 ——）。"""
    return [(m.start(), m.group(0)) for m in re.finditer(r"—{1,2}", text)]


def find_seems_like(text):
    """查找「像是在」「仿佛在」。"""
    pattern = re.compile(r"像是在|仿佛在")
    return [(m.start(), m.group(0)) for m in pattern.finditer(text)]


def lint_file(path):
    text = path.read_text(encoding="utf-8")
    paragraphs = split_paragraphs(text)

    issues = []

    # 1. 段落句子数
    for i, p in enumerate(paragraphs, 1):
        s_count = count_sentences(p)
        if s_count > 3:
            issues.append({
                "type": "paragraph",
                "msg": f"第 {i} 段有 {s_count} 句话，超过 3 句",
                "preview": p[:80].replace("\n", " ") + "...",
            })

    # 2. 不是……是……
    not_xy = find_not_x_but_y(text)
    if len(not_xy) > LIMITS["not_x_but_y"]:
        issues.append({
            "type": "not_x_but_y",
            "msg": f"「不是……是……」结构出现 {len(not_xy)} 处，超过 {LIMITS['not_x_but_y']} 处",
            "preview": "；".join([m[1][:60] for m in not_xy[:5]]),
        })

    # 3. 过渡词
    trans = find_transitions(text)
    if len(trans) > LIMITS["transitions"]:
        issues.append({
            "type": "transitions",
            "msg": f"禁用过渡词出现 {len(trans)} 处，超过 {LIMITS['transitions']} 处",
            "preview": "；".join([f"{m[1]}" for m in trans[:10]]),
        })

    # 4. 破折号
    dashes = find_dashes(text)
    if len(dashes) > LIMITS["dashes"]:
        issues.append({
            "type": "dashes",
            "msg": f"破折号出现 {len(dashes)} 处，超过 {LIMITS['dashes']} 处",
            "preview": "",
        })

    # 5. 像是在/仿佛在
    seems = find_seems_like(text)
    if len(seems) > LIMITS["seems_like"]:
        issues.append({
            "type": "seems_like",
            "msg": f"「像是在/仿佛在」出现 {len(seems)} 处，超过 {LIMITS['seems_like']} 处",
            "preview": "；".join([m[1] for m in seems[:5]]),
        })

    return issues


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    target = Path(sys.argv[1])
    files = []
    if target.is_dir():
        files = sorted(target.glob("*.md"))
    elif target.is_file():
        files = [target]
    else:
        print(f"路径不存在：{target}")
        sys.exit(1)

    has_error = False
    for f in files:
        issues = lint_file(f)
        print(f"\n{f.name}")
        if not issues:
            print("  ✅ 通过")
        else:
            has_error = True
            for issue in issues:
                print(f"  ⚠️  {issue['msg']}")
                if issue.get("preview"):
                    print(f"      示例：{issue['preview']}")

    if has_error:
        sys.exit(2)


if __name__ == "__main__":
    main()

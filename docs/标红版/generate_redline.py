#!/usr/bin/env python3
"""
生成前8章标红版：在当前文本基础上，把相对于 c8121bf 新增的行用红色标注。
"""
import subprocess
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = Path(__file__).resolve().parent
BASE_COMMIT = "c8121bf"

FILES = [
    "chapters/新_第1章_旧货摊前的雨.md",
    "chapters/新_第2章_两种未来.md",
    "chapters/新_第3章_许老头的粥.md",
    "chapters/新_第5章_红姑的故事.md",
    "chapters/新_第6章_心湖.md",
    "chapters/新_第8章_隙径.md",
]


def get_added_lines(filepath):
    """返回该文件相对于 BASE_COMMIT 新增的非空行列表（按出现顺序）。"""
    result = subprocess.run(
        ["git", "diff", BASE_COMMIT, "--", filepath],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    diff = result.stdout
    added = []
    for line in diff.splitlines():
        # 只取新增行，排除文件头 +++
        if line.startswith("+") and not line.startswith("+++"):
            content = line[1:]
            # 保留空行但不做标红（避免大量空行染色）
            if content.strip():
                added.append(content)
    return added


def mark_red(text):
    """把 markdown 段落包进红色 span。注意避开已含 HTML 的复杂情况。"""
    return f'<span style="color:red">{text}</span>'


def generate_redline(filepath):
    src = ROOT / filepath
    filename = src.name
    out_path = OUT_DIR / f"{src.stem}_标红版{src.suffix}"

    added_lines = get_added_lines(filepath)
    with open(src, "r", encoding="utf-8") as f:
        current_lines = f.readlines()

    # 为每个新增行记录其是否已被使用
    used = [False] * len(added_lines)

    out_lines = []
    for line in current_lines:
        line_stripped = line.rstrip("\n\r")
        matched = False
        for i, added in enumerate(added_lines):
            if used[i]:
                continue
            if line_stripped == added:
                # 标红这一行，保留换行
                out_lines.append(mark_red(line_stripped) + "\n")
                used[i] = True
                matched = True
                break
        if not matched:
            out_lines.append(line)

    # 文件头说明
    header = f"""# {filename} 标红版

> 红色部分为相对于 `{BASE_COMMIT}` 新增或修改的内容。
> 本文件仅供校对，不要直接用于正文编辑。

---

"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.writelines(out_lines)

    print(f"已生成：{out_path}")
    unused = sum(1 for u in used if not u)
    if unused:
        print(f"  警告：有 {unused} 处新增行未在正文中找到匹配（可能是重复或已删除）。")


def main():
    for fp in FILES:
        generate_redline(fp)


if __name__ == "__main__":
    main()

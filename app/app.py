"""
简易小说阅读平台
管理 d:\Study\Dao\ 下的章节文件
"""

import os, re, glob, json
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

CHAPTER_DIR = r"d:\Study\Dao\chapters"
BACKUP_DIR  = os.path.join(CHAPTER_DIR, "_backup")
os.makedirs(BACKUP_DIR, exist_ok=True)

# ── 辅助函数 ──────────────────────────────────────────

def parse_chapter_number(filename):
    """从文件名解析章号，如 新_第3章_许老头的粥.md → 3"""
    m = re.search(r'第(\d+)章', filename)
    return int(m.group(1)) if m else 9999


def get_chapters():
    """扫描目录，按章号排序返回章节列表"""
    files = glob.glob(os.path.join(CHAPTER_DIR, "新_第*章_*.md"))
    chapters = []
    for f in files:
        basename = os.path.basename(f)
        num = parse_chapter_number(basename)
        # 从文件名提取标题
        title_match = re.search(r'第\d+章_(.+)\.md', basename)
        title = title_match.group(1) if title_match else basename
        chapters.append({
            'number': num,
            'title': title,
            'filename': basename,
            'path': f,
        })
    chapters.sort(key=lambda x: x['number'])
    return chapters


def render_content(raw):
    """将伪戒格式的 markdown 渲染为 HTML，保留段落和换行结构。

    - 同场景内连续行（单换行）→ 同一段落内的 <br> 换行
    - 场景切换处（双换行）   → 独立 <p> 段落
    - 仅保留 **加粗** 和行内代码，不解析其他 markdown 语法
    """
    if not raw:
        return ''
    # 去掉开头的章节标题行（单独处理）
    body = re.sub(r'^# .+\n\n', '', raw, count=1).strip()
    # 按双换行分割出段落块（场景切换）
    blocks = re.split(r'\n\n+', body)
    html_parts = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # 行内 **加粗**
        block = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', block)
        # 行内 `代码`
        block = re.sub(r'`(.+?)`', r'<code>\1</code>', block)
        # 单换行 → <br>
        block = block.replace('\n', '<br>')
        html_parts.append(f'<p>{block}</p>')
    return '\n'.join(html_parts)


# ── 路由 ──────────────────────────────────────────────

@app.route('/')
def index():
    chapters = get_chapters()
    return render_template('index.html', chapters=chapters)


@app.route('/chapter/<int:num>')
def view_chapter(num):
    chapters = get_chapters()
    target = [c for c in chapters if c['number'] == num]
    if not target:
        return "章节不存在", 404
    info = target[0]
    with open(info['path'], 'r', encoding='utf-8') as f:
        raw = f.read()
    # 自定义渲染：保留段落和换行结构
    html = render_content(raw)
    # 找上一章/下一章
    idx = chapters.index(info)
    prev_ch = chapters[idx - 1] if idx > 0 else None
    next_ch = chapters[idx + 1] if idx < len(chapters)-1 else None
    return render_template('chapter.html',
                          chapter=info,
                          content=html,
                          prev=prev_ch,
                          next=next_ch,
                          chapters=chapters)


@app.route('/publish', methods=['GET', 'POST'])
def publish():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not content:
            return "标题和内容不能为空", 400
        # 自动分配章号
        chapters = get_chapters()
        max_num = max((c['number'] for c in chapters), default=0)
        new_num = max_num + 1
        filename = f"新_第{new_num}章_{title}.md"
        filepath = os.path.join(CHAPTER_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# 第{new_num}章 {title}\n\n{content}\n")
        return redirect(url_for('view_chapter', num=new_num))
    return render_template('publish.html', chapters=get_chapters())


@app.route('/edit/<int:num>', methods=['GET', 'POST'])
def edit(num):
    chapters = get_chapters()
    target = [c for c in chapters if c['number'] == num]
    if not target:
        return "章节不存在", 404
    info = target[0]

    if request.method == 'POST':
        new_content = request.form.get('content', '').strip()
        if not new_content:
            return "内容不能为空", 400
        # 备份原文件
        backup_path = os.path.join(BACKUP_DIR, info['filename'] + '.bak')
        with open(info['path'], 'r', encoding='utf-8') as f:
            with open(backup_path, 'w', encoding='utf-8') as bf:
                bf.write(f.read())
        # 写回
        with open(info['path'], 'w', encoding='utf-8') as f:
            f.write(f"# 第{num}章 {info['title']}\n\n{new_content}\n")
        return redirect(url_for('view_chapter', num=num))

    with open(info['path'], 'r', encoding='utf-8') as f:
        raw = f.read()
    # 去掉开头的标题行
    body = re.sub(r'^# .+\n\n', '', raw, count=1)
    return render_template('edit.html', chapter=info, content=body, chapters=get_chapters())


@app.route('/delete/<int:num>', methods=['POST'])
def delete(num):
    chapters = get_chapters()
    target = [c for c in chapters if c['number'] == num]
    if not target:
        return "章节不存在", 404
    info = target[0]
    # 移到备份目录
    dst = os.path.join(BACKUP_DIR, info['filename'])
    os.replace(info['path'], dst)
    return redirect(url_for('index'))


# ── 发布接口（供 Claude 写作流程调用） ──────────────

@app.route('/api/publish', methods=['POST'])
def api_publish():
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    if not title or not content:
        return jsonify({'error': 'title and content required'}), 400
    chapters = get_chapters()
    max_num = max((c['number'] for c in chapters), default=0)
    new_num = max_num + 1
    filename = f"新_第{new_num}章_{title}.md"
    filepath = os.path.join(CHAPTER_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# 第{new_num}章 {title}\n\n{content}\n")
    return jsonify({'number': new_num, 'title': title, 'filename': filename})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

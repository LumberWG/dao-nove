"""
简易小说阅读平台
自动适配 chapters/ 目录
"""

import os, re, glob, json
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory

app = Flask(__name__)

# 自动定位项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTER_DIR = os.path.join(BASE_DIR, "chapters")
DOCS_DIR    = os.path.join(BASE_DIR, "docs")
BACKUP_DIR  = os.path.join(CHAPTER_DIR, "_backup")
os.makedirs(BACKUP_DIR, exist_ok=True)

PER_PAGE = 30  # 每页章数

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


def get_docs():
    """扫描 docs/ 目录，返回所有 .md 文件列表"""
    if not os.path.isdir(DOCS_DIR):
        return []
    files = glob.glob(os.path.join(DOCS_DIR, "*.md"))
    docs = []
    for f in files:
        basename = os.path.basename(f)
        # 从文件名提取可读标题（去掉 .md 和前缀序号）
        title_match = re.search(r'(?:[\d]+[-_])?(.+)\.md', basename)
        title = title_match.group(1) if title_match else basename.replace('.md', '')
        docs.append({
            'title': title,
            'filename': basename,
            'path': f,
        })
    docs.sort(key=lambda x: x['filename'])
    return docs


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


def render_markdown_doc(raw):
    """将完整 markdown 渲染为 HTML（用于设定文档），保留 # 标题层级"""
    if not raw:
        return ''
    lines = raw.split('\n')
    html_parts = []
    for line in lines:
        line = line.rstrip()
        if not line:
            html_parts.append('<br>')
            continue
        # 标题
        h_match = re.match(r'^(#{1,4})\s+(.+)$', line)
        if h_match:
            level = len(h_match.group(1))
            text = h_match.group(2)
            html_parts.append(f'<h{level}>{text}</h{level}>')
            continue
        # 表格行
        if re.match(r'^\|.+\|$', line):
            # 表头分隔行（---|---）直接跳过
            if re.match(r'^\|[\s\-:|]+\|$', line):
                continue
            cells = [c.strip() for c in line.split('|')[1:-1]]
            html_parts.append('<tr>' + ''.join(f'<td>{c}</td>' for c in cells) + '</tr>')
            continue
        # 加粗 + 内联代码
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
        line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)
        # 列表项
        if re.match(r'^[\s]*[-*+]\s+', line):
            line = re.sub(r'^[\s]*[-*+]\s+', '', line)
            html_parts.append(f'<li>{line}</li>')
            continue
        # 普通段落
        html_parts.append(f'<p>{line}</p>')
    return '\n'.join(html_parts)


# ── 路由 ──────────────────────────────────────────────

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    chapters = get_chapters()
    total = len(chapters)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    page_chapters = chapters[start:end]
    return render_template('index.html',
                           chapters=page_chapters,
                           page=page,
                           total_pages=total_pages,
                           total=total)


@app.route('/chapter/<int:num>')
def view_chapter(num):
    chapters = get_chapters()
    target = [c for c in chapters if c['number'] == num]
    if not target:
        return "章节不存在", 404
    info = target[0]
    with open(info['path'], 'r', encoding='utf-8') as f:
        raw = f.read()
    html = render_content(raw)
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
        backup_path = os.path.join(BACKUP_DIR, info['filename'] + '.bak')
        with open(info['path'], 'r', encoding='utf-8') as f:
            with open(backup_path, 'w', encoding='utf-8') as bf:
                bf.write(f.read())
        with open(info['path'], 'w', encoding='utf-8') as f:
            f.write(f"# 第{num}章 {info['title']}\n\n{new_content}\n")
        return redirect(url_for('view_chapter', num=num))

    with open(info['path'], 'r', encoding='utf-8') as f:
        raw = f.read()
    body = re.sub(r'^# .+\n\n', '', raw, count=1)
    return render_template('edit.html', chapter=info, content=body, chapters=get_chapters())


@app.route('/delete/<int:num>', methods=['POST'])
def delete(num):
    chapters = get_chapters()
    target = [c for c in chapters if c['number'] == num]
    if not target:
        return "章节不存在", 404
    info = target[0]
    dst = os.path.join(BACKUP_DIR, info['filename'])
    os.replace(info['path'], dst)
    return redirect(url_for('index'))


# ── 设定文档 ──────────────────────────────────────────

@app.route('/docs')
def docs_index():
    docs = get_docs()
    return render_template('docs.html', docs=docs)


@app.route('/docs/view/<path:filename>')
def view_doc(filename):
    # 安全检查：防止目录穿越
    if '..' in filename or '/' in filename.replace('\\', '/'):
        return "非法路径", 400
    filepath = os.path.join(DOCS_DIR, filename)
    if not os.path.isfile(filepath):
        return "文档不存在", 404
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read()
    html = render_markdown_doc(raw)
    title = filename.replace('.md', '')
    return render_template('doc_view.html',
                           title=title,
                           filename=filename,
                           content=html)


@app.route('/docs/edit/<path:filename>', methods=['GET', 'POST'])
def edit_doc(filename):
    if '..' in filename or '/' in filename.replace('\\', '/'):
        return "非法路径", 400
    filepath = os.path.join(DOCS_DIR, filename)
    if not os.path.isfile(filepath):
        return "文档不存在", 404

    if request.method == 'POST':
        new_content = request.form.get('content', '').strip()
        if not new_content:
            return "内容不能为空", 400
        # 备份
        bak_dir = os.path.join(DOCS_DIR, "_backup")
        os.makedirs(bak_dir, exist_ok=True)
        with open(filepath, 'r', encoding='utf-8') as f:
            with open(os.path.join(bak_dir, filename + '.bak'), 'w', encoding='utf-8') as bf:
                bf.write(f.read())
        # 写回
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return redirect(url_for('view_doc', filename=filename))

    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read()
    title = filename.replace('.md', '')
    return render_template('doc_edit.html', title=title, filename=filename, content=raw)


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


@app.route('/cover')
def view_cover():
    return render_template('cover.html', cover_image=True)

@app.route('/cover-image')
def cover_image():
    return send_from_directory('static', 'cover.webp')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=3001, debug=True)

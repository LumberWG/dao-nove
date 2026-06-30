const express = require('express');
const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');
const marked = require('marked');

const app = express();
const PORT = process.env.PORT || 3000;
const DB_DIR = process.env.DB_DIR || __dirname;
app.use(express.urlencoded({ extended: true }));
app.use(express.json({ limit: '10mb' }));

// ── Database ──
const DB_PATH = path.join(DB_DIR, 'writer.db');
const db = new Database(DB_PATH);
db.pragma('journal_mode = WAL');
db.pragma('foreign_keys = ON');

db.exec(`
  CREATE TABLE IF NOT EXISTS novels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT DEFAULT '',
    description TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime'))
  );
  CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id INTEGER NOT NULL,
    chapter_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    word_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'draft',
    created_at TEXT DEFAULT (datetime('now','localtime')),
    updated_at TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (novel_id) REFERENCES novels(id) ON DELETE CASCADE
  );
  CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
  );
`);

const insertNovel = db.prepare('INSERT INTO novels (title, author, description) VALUES (?, ?, ?)');
const updateNovel = db.prepare('UPDATE novels SET title=?, author=?, description=?, updated_at=datetime(\'now\',\'localtime\') WHERE id=?');
const getNovels = db.prepare('SELECT * FROM novels ORDER BY updated_at DESC');
const getNovel = db.prepare('SELECT * FROM novels WHERE id=?');
const deleteNovel = db.prepare('DELETE FROM novels WHERE id=?');

const insertChapter = db.prepare('INSERT INTO chapters (novel_id, chapter_number, title, content, word_count) VALUES (?, ?, ?, ?, ?)');
const updateChapter = db.prepare('UPDATE chapters SET title=?, content=?, word_count=?, updated_at=datetime(\'now\',\'localtime\') WHERE id=?');
const updateChapterNumber = db.prepare('UPDATE chapters SET chapter_number=? WHERE id=?');
const getChapters = db.prepare('SELECT id, novel_id, chapter_number, title, word_count, status, created_at, updated_at FROM chapters WHERE novel_id=? ORDER BY chapter_number ASC');
const getChapter = db.prepare('SELECT * FROM chapters WHERE id=?');
const deleteChapter = db.prepare('DELETE FROM chapters WHERE id=?');
const getMaxChapterNum = db.prepare('SELECT COALESCE(MAX(chapter_number),0) as max_num FROM chapters WHERE novel_id=?');

// ── Initialize with current novel if empty ──
const existingNovels = getNovels.all();
if (existingNovels.length === 0) {
    // Try to import existing chapters from markdown files
    const novelId = insertNovel.run('岁蚀', '', '伪戒风格·300万字长篇').lastInsertRowid;
    const files = fs.readdirSync(path.resolve(__dirname, '..'))
        .filter(f => f.startsWith('新_第') && f.endsWith('.md'))
        .sort();
    files.forEach((f, idx) => {
        const filePath = path.resolve(__dirname, '..', f);
        const content = fs.readFileSync(filePath, 'utf8');
        let firstLine = content.split('\n')[0].trim().replace(/^﻿/, '').replace(/^#\s*/, '');
        // 统一章号：第八章→第8章
        firstLine = firstLine.replace(/第([一二三四五六七八九十百]+)章/g, function(m, cn) {
            var d = {一:1,二:2,三:3,四:4,五:5,六:6,七:7,八:8,九:9,十:10};
            var n = 0;
            for (var i = 0; i < cn.length; i++) {
                var c = cn[i];
                if (c === '十' && n === 0) n = 10;
                else if (c === '十') n += 10;
                else if (n >= 10) n += d[c];
                else n = d[c];
            }
            return '第' + n + '章';
        });
        var title = /^第\d+\S/.test(firstLine) ? firstLine : f.replace(/\.md$/, '').replace(/新_第\d+章_/, '').replace(/_/g, ' ');
        var fileNum = parseInt(f.match(/第(\d+)章/)[1]);
        var clean = content.replace(/\s/g, '').replace(/（本章约\d+字）/g, '');
        var wc = clean.length;
        insertChapter.run(novelId, fileNum, title, content, wc);
    });
    console.log(`  Imported ${files.length} chapters into 《岁蚀》`);
}

// ── HTML Template Helper ──
function layout(title, body, extraHead = '') {
    return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${title}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,"Microsoft YaHei",sans-serif;background:#f5f3ef;color:#2c2c2c;line-height:1.7;font-size:15px;}
.container{max-width:860px;margin:0 auto;padding:30px 20px;}
h1{font-size:26px;font-weight:500;margin-bottom:6px;}
.subtitle{color:#888;font-size:14px;margin-bottom:25px;}
.card{background:#fff;border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,0.06);padding:15px 20px;margin-bottom:10px;}
.card:hover{box-shadow:0 2px 8px rgba(0,0,0,0.1);}
.flex{display:flex;align-items:center;gap:15px;}
.flex1{flex:1;}
.btn{display:inline-block;padding:5px 14px;border-radius:4px;font-size:13px;text-decoration:none;border:none;cursor:pointer;transition:background 0.15s;}
.btn-primary{background:#d4a853;color:#fff;}.btn-primary:hover{background:#c49a48;}
.btn-outline{background:#e8e6e1;color:#555;}.btn-outline:hover{background:#ddd;}
.btn-danger{background:#e65;color:#fff;}.btn-danger:hover{background:#d44;}
.btn-sm{padding:3px 10px;font-size:12px;}
.mt10{margin-top:10px;}.mb10{margin-bottom:10px;}.mr10{margin-right:10px;}
.tag{display:inline-block;font-size:11px;padding:1px 8px;border-radius:3px;background:#f0ede8;color:#888;}
.gap20{display:flex;gap:20px;flex-wrap:wrap;}
.stat-card{background:#fff;border-radius:6px;box-shadow:0 1px 3px rgba(0,0,0,0.06);padding:15px 25px;text-align:center;flex:1;min-width:100px;}
.stat-card .num{font-size:24px;font-weight:600;color:#333;}
.stat-card .label{font-size:12px;color:#999;margin-top:2px;}
.nav-bar{background:#fff;border-bottom:1px solid #eee;padding:10px 0;margin-bottom:20px;}
.nav-bar .container{display:flex;align-items:center;gap:20px;padding:0 20px;}
.nav-bar a{color:#666;text-decoration:none;font-size:14px;}.nav-bar a:hover{color:#333;}
input[type=text],textarea{border:1px solid #ddd;border-radius:4px;padding:8px 12px;font-size:14px;width:100%;font-family:inherit;}
input:focus,textarea:focus{outline:none;border-color:#d4a853;}
textarea{line-height:1.8;}
.footer{margin-top:50px;text-align:center;font-size:12px;color:#bbb;}
${extraHead}
</style></head><body>${body}</body></html>`;
}

function navBar(currentNovel) {
    const novelLinks = getNovels.all().map(n =>
        `<a href="/novel/${n.id}">${n.title}</a>`
    ).join('\n');
    return `<div class="nav-bar"><div class="container" style="max-width:860px;">
        <a href="/" style="font-weight:500;color:#333;">写作系统</a>
        ${novelLinks}
        <a href="/docs">设定文档</a>
        <span style="flex:1"></span>
        <a href="/novel/${currentNovel}/settings">设置</a>
    </div></div>`;
}

// ── Routes ──

// Landing page - list novels
app.get('/', (req, res) => {
    const novels = getNovels.all();
    const body = `
    <div class="container">
        <h1>写作管理系统</h1>
        <div class="subtitle">多小说支持 · 自动保存 · 数据库存储</div>
        <div class="gap20 mb10">
            ${novels.map(n => `
                <a href="/novel/${n.id}" class="card" style="display:block;text-decoration:none;color:inherit;flex:1;min-width:200px;">
                    <div style="font-size:16px;font-weight:500;">${n.title}</div>
                    <div style="font-size:13px;color:#999;margin-top:4px;">${n.author || '未设置作者'}</div>
                    <div style="font-size:12px;color:#bbb;margin-top:2px;">${n.description || ''}</div>
                </a>
            `).join('')}
        </div>
        <a href="/novel/new" class="btn btn-primary">＋ 新建小说</a>
        <div class="footer">数据存储于 server/writer.db · 可随时导出为 .md 文件</div>
    </div>`;
    res.send(layout('写作管理系统', body));
});

// Novel detail page
app.get('/novel/:id', (req, res) => {
    const novelId = req.params.id;
    if (novelId === 'new') {
        return res.send(layout('新建小说', `
        <div class="container">
            <h1>新建小说</h1>
            <form method="POST" action="/novel/create" style="margin-top:20px;">
                <div class="mb10"><input type="text" name="title" placeholder="小说名称" required></div>
                <div class="mb10"><input type="text" name="author" placeholder="作者名（可选）"></div>
                <div class="mb10"><textarea name="description" rows="2" placeholder="简介（可选）" style="height:60px;"></textarea></div>
                <button type="submit" class="btn btn-primary">创建</button>
                <a href="/" class="btn btn-outline">取消</a>
            </form>
        </div>`));
    }
    const novel = getNovel.get(novelId);
    if (!novel) return res.status(404).send('小说不存在');
    const allChapters = getChapters.all(novelId);
    const totalWords = allChapters.reduce((s, c) => s + (c.word_count || 0), 0);

    // ── 分页 ──
    const PAGE_SIZE = 20;
    const page = Math.max(1, parseInt(req.query.page) || 1);
    const totalPages = Math.max(1, Math.ceil(allChapters.length / PAGE_SIZE));
    const start = (page - 1) * PAGE_SIZE;
    const chapters = allChapters.slice(start, start + PAGE_SIZE);

    const chapterRows = chapters.map((ch, i) => `
        <div class="card">
            <div class="flex">
                <span style="width:36px;font-size:13px;color:#aaa;">${ch.chapter_number}</span>
                <div class="flex1">
                    <a href="/chapter/${ch.id}/read" style="text-decoration:none;color:#333;font-size:15px;">${ch.title || '无标题'}</a>
                    <div style="font-size:12px;color:#999;margin-top:2px;">
                        <span class="tag">${ch.word_count}字</span>
                        <span class="tag">${ch.status === 'published' ? '定稿' : '初稿'}</span>
                        <span style="margin-left:8px;">${ch.updated_at}</span>
                    </div>
                </div>
                <a href="/chapter/${ch.id}/edit" class="btn btn-primary btn-sm">编辑</a>
                <a href="/chapter/${ch.id}/delete" class="btn btn-danger btn-sm" onclick="return confirm('确认删除？')">删除</a>
            </div>
        </div>
    `).join('');

    // ── 分页导航 ──
    const pageLinks = [];
    const maxShow = 5;
    let pStart = Math.max(1, page - Math.floor(maxShow / 2));
    let pEnd = Math.min(totalPages, pStart + maxShow - 1);
    if (pEnd - pStart < maxShow - 1) pStart = Math.max(1, pEnd - maxShow + 1);
    for (let p = pStart; p <= pEnd; p++) {
        if (p === page) {
            pageLinks.push(`<span style="display:inline-block;padding:4px 12px;background:#d4a853;color:#fff;border-radius:4px;font-size:13px;font-weight:500;">${p}</span>`);
        } else {
            pageLinks.push(`<a href="/novel/${novelId}?page=${p}" style="display:inline-block;padding:4px 12px;color:#666;text-decoration:none;font-size:13px;border-radius:4px;">${p}</a>`);
        }
    }
    const paginationHtml = totalPages > 1 ? `
        <div style="display:flex;justify-content:center;align-items:center;gap:6px;margin-top:20px;padding:10px 0;">
            ${page > 1 ? `<a href="/novel/${novelId}?page=${page-1}" class="btn btn-outline btn-sm">← 上一页</a>` : ''}
            ${pageLinks.join('')}
            ${page < totalPages ? `<a href="/novel/${novelId}?page=${page+1}" class="btn btn-outline btn-sm">下一页 →</a>` : ''}
        </div>
        <div style="text-align:center;font-size:12px;color:#bbb;margin-top:4px;">
            第 ${start+1}-${Math.min(start+PAGE_SIZE, allChapters.length)} 章 / 共 ${allChapters.length} 章
        </div>
    ` : '';

    const body = `
    ${navBar(novelId)}
    <div class="container">
        <div class="flex" style="margin-bottom:20px;">
            <div class="flex1">
                <h1>${novel.title}</h1>
                <div class="subtitle">${novel.author ? novel.author + ' · ' : ''}共 ${allChapters.length} 章 · 约 ${(totalWords/1000).toFixed(1)}k 字</div>
            </div>
            <a href="/novel/${novelId}/import" class="btn btn-outline">导入.md文件</a>
            <a href="/novel/${novelId}/export" class="btn btn-outline">导出全部</a>
        </div>
        <div class="gap20 mb10">
            <div class="stat-card"><div class="num">${allChapters.length}</div><div class="label">章节</div></div>
            <div class="stat-card"><div class="num">${Math.round(totalWords/1000)}k</div><div class="label">总字数</div></div>
            <div class="stat-card"><div class="num">${allChapters.length ? Math.round(totalWords/allChapters.length) : 0}</div><div class="label">平均每章</div></div>
        </div>
        ${allChapters.length > 0 ? chapterRows : '<div style="color:#999;text-align:center;padding:40px;">还没有章节，点击下方按钮新建</div>'}
        ${paginationHtml}
        <a href="/novel/${novelId}/chapter/new" class="btn btn-primary mt10">＋ 新建章节</a>
    </div>`;
    res.send(layout(novel.title, body));
});

// Create novel
app.post('/novel/create', (req, res) => {
    const { title, author, description } = req.body;
    const result = insertNovel.run(title, author || '', description || '');
    res.redirect(`/novel/${result.lastInsertRowid}`);
});

// Delete novel
app.get('/novel/:id/delete', (req, res) => {
    deleteNovel.run(req.params.id);
    res.redirect('/');
});

// Settings page
app.get('/novel/:id/settings', (req, res) => {
    const novel = getNovel.get(req.params.id);
    if (!novel) return res.status(404).send('不存在');
    const body = `
    ${navBar(req.params.id)}
    <div class="container">
        <h1>设置 - ${novel.title}</h1>
        <form method="POST" action="/novel/${req.params.id}/update" style="margin-top:20px;max-width:500px;">
            <div class="mb10"><label style="font-size:13px;color:#888;">小说名称</label><input type="text" name="title" value="${novel.title}"></div>
            <div class="mb10"><label style="font-size:13px;color:#888;">作者</label><input type="text" name="author" value="${novel.author}"></div>
            <div class="mb10"><label style="font-size:13px;color:#888;">简介</label><textarea name="description" rows="2" style="height:60px;">${novel.description}</textarea></div>
            <button type="submit" class="btn btn-primary">保存</button>
            <a href="/novel/${req.params.id}/delete" class="btn btn-danger" onclick="return confirm('确认删除整部小说及其所有章节？')">删除这部小说</a>
        </form>
    </div>`;
    res.send(layout('设置', body));
});

// Update novel
app.post('/novel/:id/update', (req, res) => {
    updateNovel.run(req.body.title, req.body.author, req.body.description, req.params.id);
    res.redirect(`/novel/${req.params.id}`);
});

// Import .md files
app.get('/novel/:id/import', (req, res) => {
    const novelId = req.params.id;
    const novel = getNovel.get(novelId);
    const files = fs.readdirSync(path.resolve(__dirname, '..'))
        .filter(f => f.endsWith('.md') && !f.includes('archive'));
    const existingMax = getMaxChapterNum.get(novelId).max_num;
    let imported = 0;
    files.forEach(f => {
        const filePath = path.resolve(__dirname, '..', f);
        const content = fs.readFileSync(filePath, 'utf8');
        const firstLine = content.split('\n')[0].replace('# ', '').trim();
        const clean = content.replace(/\s/g, '').replace(/（本章约\d+字）/g, '');
        const wc = clean.length;
        // Avoid duplicates by checking title
        const dup = db.prepare('SELECT id FROM chapters WHERE novel_id=? AND title=?').get(novelId, firstLine);
        if (!dup) {
            insertChapter.run(novelId, existingMax + imported + 1, firstLine || f, content, wc);
            imported++;
        }
    });
    res.redirect(`/novel/${novelId}`);
});

// ── 设定文档 ──
const DOCS_DIR = path.resolve(__dirname, '..', 'docs');

app.get('/docs', (req, res) => {
    const files = fs.readdirSync(DOCS_DIR)
        .filter(f => f.endsWith('.md'))
        .map(f => {
            const content = fs.readFileSync(path.join(DOCS_DIR, f), 'utf8');
            const firstLine = content.split('\n')[0].replace(/^#\s*/, '').trim();
            return { file: f, title: firstLine || f.replace('.md', '') };
        });
    const body = `
    <div class="container">
        <a href="/" class="btn btn-outline btn-sm mb10">← 返回</a>
        <h1>设定文档</h1>
        <div class="subtitle">世界观、人物、伏笔等设定资料</div>
        <div class="gap20">
            ${files.map(f => `
                <a href="/docs/${encodeURIComponent(f.file)}" class="card" style="display:block;text-decoration:none;color:inherit;flex:1;min-width:260px;">
                    <div style="font-size:15px;font-weight:500;">${f.title}</div>
                    <div style="font-size:12px;color:#bbb;margin-top:4px;">${f.file}</div>
                </a>
            `).join('')}
        </div>
    </div>`;
    res.send(layout('设定文档', body, `<style>.content p{text-indent:2em;margin:0.8em 0;}.content h1{text-align:center;text-indent:0;margin:30px 0;}.content h2{font-size:20px;margin:24px 0 12px;border-left:3px solid #d4a853;padding-left:12px;}.content h3{font-size:17px;margin:20px 0 8px;}.content ul,.content ol{margin:0.5em 0 0.5em 1.5em;}.content table{border-collapse:collapse;width:100%;margin:12px 0;}.content td,.content th{border:1px solid #ddd;padding:6px 10px;font-size:14px;}.content th{background:#f5f3ef;}</style>`));
});

app.get('/docs/:file', (req, res) => {
    const filePath = path.join(DOCS_DIR, decodeURIComponent(req.params.file));
    if (!fs.existsSync(filePath) || !filePath.startsWith(DOCS_DIR)) {
        return res.status(404).send('文档不存在');
    }
    const content = fs.readFileSync(filePath, 'utf8');
    const html = marked.parse(content, {breaks: true});
    const body = `
    <div class="container" style="max-width:860px;">
        <a href="/docs" class="btn btn-outline btn-sm mb10">← 设定文档</a>
        <div class="content" style="font-family:'Noto Serif SC','Source Han Serif SC',serif;font-size:17px;line-height:2;color:#333;">
            ${html}
        </div>
    </div>`;
    res.send(layout(req.params.file.replace('.md', ''), body, `<style>.content p{text-indent:2em;margin:0.8em 0;}.content h1{text-align:center;text-indent:0;margin:30px 0;}.content h2{font-size:20px;margin:24px 0 12px;border-left:3px solid #d4a853;padding-left:12px;}.content h3{font-size:17px;margin:20px 0 8px;}.content ul,.content ol{margin:0.5em 0 0.5em 1.5em;}.content table{border-collapse:collapse;width:100%;margin:12px 0;}.content td,.content th{border:1px solid #ddd;padding:6px 10px;font-size:14px;}.content th{background:#f5f3ef;}</style>`));
});

// Export all chapters as individual .md files
app.get('/novel/:id/export', (req, res) => {
    const novelId = req.params.id;
    const novel = getNovel.get(novelId);
    const chapters = getChapters.all(novelId);
    const exportDir = path.resolve(__dirname, '..', `export_${novel.title}`);
    if (!fs.existsSync(exportDir)) fs.mkdirSync(exportDir);
    chapters.forEach(ch => {
        const fileName = `第${ch.chapter_number}章_${ch.title.replace(/[\/\\?*|:<>]/g, '')}.md`;
        fs.writeFileSync(path.join(exportDir, fileName), ch.content, 'utf8');
    });
    res.redirect(`/novel/${novelId}`);
});

// New chapter
app.get('/novel/:id/chapter/new', (req, res) => {
    const novelId = req.params.id;
    const max = getMaxChapterNum.get(novelId).max_num;
    const newNum = max + 1;
    const result = insertChapter.run(novelId, newNum, `第${newNum}章`, `# 第${newNum}章\n\n`, 0);
    res.redirect(`/chapter/${result.lastInsertRowid}/edit`);
});

// Read chapter
app.get('/chapter/:id/read', (req, res) => {
    const ch = getChapter.get(req.params.id);
    if (!ch) return res.status(404).send('章节不存在');
    const novel = getNovel.get(ch.novel_id);
    const html = marked.parse(ch.content, {breaks: true});
    const chapters = getChapters.all(ch.novel_id);
    const idx = chapters.findIndex(c => c.id == req.params.id);
    const prev = idx > 0 ? chapters[idx-1] : null;
    const next = idx < chapters.length-1 ? chapters[idx+1] : null;
    const body = `
    ${navBar(ch.novel_id)}
    <div class="container" style="max-width:740px;">
        <div style="display:flex;gap:15px;margin-bottom:20px;font-size:14px;">
            <a href="/novel/${ch.novel_id}" class="btn btn-outline btn-sm">← 目录</a>
            <a href="/chapter/${ch.id}/edit" class="btn btn-primary btn-sm">编辑</a>
            <span style="flex:1"></span>
            ${prev ? `<a href="/chapter/${prev.id}/read" class="btn btn-outline btn-sm">← 上一章</a>` : ''}
            ${next ? `<a href="/chapter/${next.id}/read" class="btn btn-outline btn-sm">下一章 →</a>` : ''}
        </div>
        <div class="content" style="font-family:'Noto Serif SC','Source Han Serif SC',serif;font-size:17px;line-height:2;color:#333;">
            ${html}
        </div>
        <div style="margin-top:30px;display:flex;gap:15px;font-size:14px;">
            ${prev ? `<a href="/chapter/${prev.id}/read" class="btn btn-outline btn-sm">← 上一章</a>` : ''}
            ${next ? `<a href="/chapter/${next.id}/read" class="btn btn-outline btn-sm">下一章 →</a>` : ''}
        </div>
    </div>`;
    res.send(layout(ch.title, body, `<style>.content p{text-indent:2em;margin:0.8em 0;}.content h1{text-align:center;text-indent:0;margin:30px 0;}</style>`));
});

// Edit chapter
app.get('/chapter/:id/edit', (req, res) => {
    const ch = getChapter.get(req.params.id);
    if (!ch) return res.status(404).send('章节不存在');
    const novel = getNovel.get(ch.novel_id);
    const body = `
    ${navBar(ch.novel_id)}
    <div class="container" style="max-width:960px;">
        <div class="flex" style="margin-bottom:10px;">
            <input type="text" id="title" value="${ch.title}" style="font-size:18px;font-weight:500;width:auto;flex:1;border:none;background:#f5f3ef;padding:5px 0;" placeholder="章节标题">
            <span style="font-size:13px;color:#999;white-space:nowrap;">第${ch.chapter_number}章 · <span id="status">已就绪</span></span>
        </div>
        <div style="display:flex;gap:8px;margin-bottom:8px;">
            <button class="btn btn-primary" onclick="save()">保存 (Ctrl+S)</button>
            <button class="btn btn-outline" onclick="togglePreview()">预览</button>
            <a href="/chapter/${ch.id}/read" class="btn btn-outline">阅读模式</a>
            <span style="flex:1"></span>
            <span id="wordDisplay" style="font-size:13px;color:#999;line-height:28px;">${ch.word_count}字</span>
        </div>
        <textarea id="editor" style="width:100%;height:70vh;padding:20px;font-size:16px;line-height:1.8;border:1px solid #ddd;border-radius:4px;background:#fff;font-family:'Microsoft YaHei',sans-serif;">${ch.content.replace(/</g,'&lt;')}</textarea>
        <div id="preview" class="content" style="display:none;background:#fff;border:1px solid #ddd;border-radius:4px;padding:30px;line-height:2;font-size:16px;min-height:50vh;"></div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"><\/script>
    <script>
        const editor = document.getElementById('editor');
        const status = document.getElementById('status');
        const preview = document.getElementById('preview');
        const titleInput = document.getElementById('title');
        const wordDisplay = document.getElementById('wordDisplay');
        let previewVisible = false;

        document.addEventListener('keydown', e => { if((e.ctrlKey||e.metaKey)&&e.key==='s'){ e.preventDefault(); save(); } });

        async function save() {
            status.textContent = '保存中...';
            const content = editor.value;
            const title = titleInput.value.trim() || '无标题';
            try {
                const r = await fetch('/chapter/${ch.id}/save', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({content, title})
                });
                const data = await r.json();
                if(data.ok) {
                    status.textContent = '已保存 ' + new Date().toLocaleTimeString();
                    wordDisplay.textContent = data.wordCount + '字';
                } else {
                    status.textContent = '保存失败';
                }
            } catch(e) {
                status.textContent = '保存出错';
            }
        }

        function togglePreview() {
            previewVisible = !previewVisible;
            if(previewVisible) {
                editor.style.display = 'none';
                preview.style.display = 'block';
                preview.innerHTML = marked.parse(editor.value, {breaks: true});
            } else {
                editor.style.display = 'block';
                preview.style.display = 'none';
            }
        }

        setInterval(save, 60000);
    <\/script>`;
    res.send(layout(`编辑 - ${ch.title}`, body, `<style>.content p{text-indent:2em;margin:0.8em 0;}.content h1{text-align:center;text-indent:0;margin:30px 0;}</style>`));
});

// Save chapter
app.post('/chapter/:id/save', (req, res) => {
    const ch = getChapter.get(req.params.id);
    if (!ch) return res.json({ ok: false });
    const { content, title } = req.body;
    const clean = content.replace(/\s/g, '').replace(/（本章约\d+字）/g, '');
    const wc = clean.length;
    let finalContent = content.replace(/（本章约\d+字）/g, '').trim();
    finalContent += `\n\n（本章约${wc}字）`;
    updateChapter.run(title || ch.title, finalContent, wc, req.params.id);
    res.json({ ok: true, wordCount: wc });
});

// Delete chapter
app.get('/chapter/:id/delete', (req, res) => {
    const ch = getChapter.get(req.params.id);
    if (!ch) return res.redirect('/');
    const novelId = ch.novel_id;
    deleteChapter.run(req.params.id);
    // Re-number remaining chapters
    const remaining = getChapters.all(novelId);
    remaining.forEach((c, i) => updateChapterNumber.run(i + 1, c.id));
    res.redirect(`/novel/${novelId}`);
});

// ── Start ──
app.listen(PORT, () => {
    console.log(`\n  📚 《岁蚀》写作系统 v2`);
    console.log(`  ─────────────────────────`);
    console.log(`  地址: http://localhost:${PORT}`);
    console.log(`  数据: server/writer.db`);
    console.log(`  md文件自动导入数据库\n`);
});

const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

function countChinese(text) {
    const clean = text.replace(/\s/g, '').replace(/（本章约\d+字）/g, '');
    const hanzi = clean.match(/[一-鿿㐀-䶿豈-﫿]/g);
    return hanzi ? hanzi.length : 0;
}

// 中文数字转阿拉伯数字
function cnToNum(cn) {
    const d = {一:1,二:2,三:3,四:4,五:5,六:6,七:7,八:8,九:9,十:10};
    let n = 0;
    for (let i = 0; i < cn.length; i++) {
        const c = cn[i];
        if (c === '十' && n === 0) n = 10;
        else if (c === '十') n += 10;
        else if (n >= 10) n += d[c];
        else n = d[c];
    }
    return n;
}

function extractTitleAndNum(content, filename) {
    let firstLine = content.split('\n')[0].trim()
        .replace(/^﻿/, '')     // BOM
        .replace(/^#\s*/, '')       // markdown heading
        .trim();

    // 统一章号：第八章 → 第8章
    firstLine = firstLine.replace(/第([一二三四五六七八九十百]+)章/g, (_, cn) => '第' + cnToNum(cn) + '章');

    // Try to get chapter number from filename first (more reliable)
    const fileMatch = filename.match(/新_第(\d+)章/);
    const fileNum = fileMatch ? parseInt(fileMatch[1]) : null;

    // If first line is a valid title starting with "第N章", use it
    const titleMatch = firstLine.match(/^第(\d+)章/);
    if (titleMatch && firstLine.length > 5) {
        return { chapterNum: parseInt(titleMatch[1]), title: firstLine };
    }

    // Fallback: use file number and first line or filename
    if (fileNum) {
        const fallbackTitle = firstLine || filename.replace(/\.md$/, '').replace(/新_第\d+章_/, '').replace(/_/g, ' ');
        return { chapterNum: fileNum, title: fallbackTitle };
    }

    return { chapterNum: 0, title: firstLine || filename };
}

// ── Main ──
const dbPath = path.resolve(__dirname, 'writer.db');
const db = new Database(dbPath);
db.pragma('journal_mode = WAL');

const chaptersDir = path.resolve(__dirname, '..', 'chapters');

function walkDir(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach(f => {
    const full = path.join(dir, f);
    const stat = fs.statSync(full);
    if (stat && stat.isDirectory()) {
      results = results.concat(walkDir(full));
    } else if (stat && stat.isFile() && f.startsWith('新_第') && f.endsWith('.md')) {
      results.push(full);
    }
  });
  return results;
}

const files = walkDir(chaptersDir)
    .sort((a, b) => {
        const baseA = path.basename(a);
        const baseB = path.basename(b);
        const na = parseInt((baseA.match(/新_第(\d+)章/) || [0, 0])[1]);
        const nb = parseInt((baseB.match(/新_第(\d+)章/) || [0, 0])[1]);
        return na - nb;
    });

console.log(`找到 ${files.length} 个章节文件\n`);

// Ensure novel exists
let novel = db.prepare('SELECT id FROM novels WHERE title = ?').get('岁蚀');
if (!novel) {
    const result = db.prepare('INSERT INTO novels (title, author, description) VALUES (?, ?, ?)').run('岁蚀', '', '伪戒风格·300万字长篇');
    novel = { id: result.lastInsertRowid };
    console.log('创建小说《岁蚀》');
}
const novelId = novel.id;

let updated = 0;
let inserted = 0;
let totalWords = 0;

const updateStmt = db.prepare('UPDATE chapters SET title=?, content=?, word_count=?, updated_at=datetime(\'now\',\'localtime\') WHERE novel_id=? AND chapter_number=?');
const insertStmt = db.prepare('INSERT INTO chapters (novel_id, chapter_number, title, content, word_count) VALUES (?, ?, ?, ?, ?)');

for (const f of files) {
    const filePath = f;
    const content = fs.readFileSync(filePath, 'utf8');
    const { chapterNum, title } = extractTitleAndNum(content, path.basename(f));
    const wc = countChinese(content);

    if (!chapterNum) {
        console.log(`  [跳过] 无法解析章号: ${f}`);
        continue;
    }

    const existing = db.prepare('SELECT id, word_count FROM chapters WHERE novel_id=? AND chapter_number=?').get(novelId, chapterNum);

    if (existing) {
        updateStmt.run(title, content, wc, novelId, chapterNum);
        const diff = wc - (existing.word_count || 0);
        const diffStr = diff !== 0 ? ` (${diff >= 0 ? '+' : ''}${diff})` : '';
        console.log(`  [更新] 第${chapterNum}章 ${title} → ${wc}字${diffStr}`);
        updated++;
    } else {
        insertStmt.run(novelId, chapterNum, title, content, wc);
        console.log(`  [新增] 第${chapterNum}章 ${title} → ${wc}字`);
        inserted++;
    }
    totalWords += wc;
}

// Report chapters in DB that don't have corresponding md files
const dbChapters = db.prepare('SELECT chapter_number, title FROM chapters WHERE novel_id=? ORDER BY chapter_number').all(novelId);
const dbChapterNums = new Set(dbChapters.map(c => c.chapter_number));
const fileChapterNums = new Set();
for (const f of files) {
    const m = f.match(/新_第(\d+)章/);
    if (m) fileChapterNums.add(parseInt(m[1]));
}

const orphanChapters = dbChapters.filter(c => !fileChapterNums.has(c.chapter_number));
if (orphanChapters.length > 0) {
    console.log(`\n⚠ 数据库中有 ${orphanChapters.length} 章在文件系统中不存在:`);
    orphanChapters.forEach(c => console.log(`   第${c.chapter_number}章 ${c.title}`));
}

console.log(`\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
console.log(`同步完成: ${updated} 章更新, ${inserted} 章新增`);
console.log(`总计 ${updated + inserted} 章, ${totalWords.toLocaleString()} 汉字 ≈ ${(totalWords/10000).toFixed(2)}万字`);

// Verify count
const dbCount = db.prepare('SELECT COUNT(*) as cnt FROM chapters WHERE novel_id=?').get(novelId);
console.log(`数据库中共 ${dbCount.cnt} 章`);
console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);

db.close();

const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

const chapterNum = process.argv[2];
if (!chapterNum) { console.log('Usage: node sync_chapter.js <number>'); process.exit(1); }

const db = new Database('writer.db');

function countChinese(text) {
    const clean = text.replace(/\s/g, '').replace(/（本章约\d+字）/g, '');
    const hanzi = clean.match(/[一-鿿㐀-䶿豈-﫿]/g);
    return hanzi ? hanzi.length : 0;
}

const chaptersDir = path.resolve(__dirname, '..', 'chapters');
const files = fs.readdirSync(chaptersDir).filter(f => f.startsWith('新_第') && f.endsWith('.md'));
const matchFile = files.find(f => {
    const m = f.match(/新_第(\d+)章/);
    return m && parseInt(m[1]) === parseInt(chapterNum);
});

if (!matchFile) { console.log('Chapter file not found'); process.exit(1); }

const content = fs.readFileSync(path.join(chaptersDir, matchFile), 'utf8');
const wc = countChinese(content);

const ch = db.prepare('SELECT id, title FROM chapters WHERE chapter_number=? AND novel_id=1').get(parseInt(chapterNum));
if (ch) {
    db.prepare('UPDATE chapters SET content=?, word_count=?, updated_at=datetime(\'now\',\'localtime\') WHERE id=?').run(content, wc, ch.id);
    console.log(ch.title + ' updated: ' + wc + ' 汉字');
}

const total = db.prepare('SELECT SUM(word_count) as total FROM chapters').get();
console.log('Total: ' + total.total + ' 汉字 ≈ ' + (total.total/10000).toFixed(1) + '万字');
db.close();

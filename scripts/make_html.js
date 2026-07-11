const fs = require('fs');
const endChapter = 42;
let html = '<!DOCTYPE html><html lang=zh-CN><head><meta charset=utf-8>';
html += `<title>岁蚀·第1-${endChapter}章</title>`;
html += '<style>';
html += 'body{font-family:"Noto Serif SC","SimSun",serif;max-width:720px;margin:0 auto;padding:40px 20px;line-height:2;font-size:17px;color:#1a1a1a}';
html += 'h1{text-align:center;font-size:28px;margin:1em 0 0.5em}';
html += 'h2{text-align:center;font-size:20px;margin:2em 0 0.5em;font-weight:600}';
html += 'h3{margin:1.5em 0 0.5em;font-size:18px}';
html += 'hr{margin:2em 0;border:none;border-top:2px solid #ddd}';
html += 'p{margin:0.3em 0;text-indent:2em}';
html += 'strong{font-weight:600}';
html += '.chapter-title{text-align:center;font-size:24px;font-weight:600;margin:3em 0 1.5em}';
html += '</style></head><body>';
html += `<h1>岁蚀</h1><h2>卷一·旧雨不来 / 弧2·序隙之裂</h2><p style="text-align:center;color:#888;text-indent:0">第1-${endChapter}章</p><hr>`;
for (let i = 1; i <= endChapter; i++) {
  const files = fs.readdirSync('chapters').filter(f => f.startsWith('新_第' + i + '章'));
  if (files.length === 0) continue;
  let md = fs.readFileSync('chapters/' + files[0], 'utf8');
  md = md.replace(/（本章约\d+字）[^)]*.*$/gm, '');
  md = md.replace(/---\s+/g, '');
  // Parse basic markdown
  let chapter = md.replace(/^# (.+)$/gm, '<div class=chapter-title>$1</div>');
  chapter = chapter.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  chapter = chapter.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  chapter = chapter.replace(/^---$/gm, '<hr>');
  // Split into paragraphs and wrap
  const paragraphs = chapter.split(/\n\n+/);
  chapter = paragraphs.map(p => {
    p = p.trim();
    if (!p) return '';
    if (p.startsWith('<')) return p;
    p = p.replace(/\n/g, '<br>');
    return '<p>' + p + '</p>';
  }).join('\n');
  html += chapter + '<hr>';
}
html += '</body></html>';
const outPath = `www/岁蚀_1-${endChapter}章.html`;
// remove old 1-25 file if exists
try { fs.unlinkSync('www/岁蚀_1-25章.html'); } catch(e) {}
fs.writeFileSync(outPath, html, 'utf8');
console.log(`Done: ${outPath} (` + (fs.statSync(outPath).size / 1024).toFixed(0) + 'KB)');

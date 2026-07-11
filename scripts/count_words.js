/**
 * 统计并更新所有章节的准确字数（汉字+标点，不含空格）
 * 用法: node scripts/count_words.js
 * 会更新每章末尾的（本章XXXX字）标记
 */

const fs = require('fs');
const path = require('path');

const CHAPTERS_DIR = path.join(__dirname, '..', 'chapters');

function count(text) {
  const clean = text.replace(/\s/g, '');
  const hanzi = clean.match(/[一-鿿㐀-䶿豈-﫿]/g) || [];
  const punct = clean.match(/[，。、！？；：""''（）《》——…—]/g) || [];
  return hanzi.length + punct.length;
}

function updateWordMark(filename) {
  const filepath = path.join(CHAPTERS_DIR, filename);
  let content = fs.readFileSync(filepath, 'utf8');
  const total = count(content);

  // 去掉旧的字数标记
  content = content.replace(/（本章约?\d+字）\n?/g, '');
  content = content.replace(/\n（本章\d+字）/g, '');

  // 追加新的准确标记
  content = content.trimEnd() + `\n\n（本章${total}字）\n`;

  fs.writeFileSync(filepath, content, 'utf8');
  return total;
}

// 处理所有章节
const files = fs.readdirSync(CHAPTERS_DIR)
  .filter(f => f.startsWith('新_第') && f.endsWith('.md'))
  .sort((a, b) => {
    return parseInt(a.match(/第(\d+)/)[1]) - parseInt(b.match(/第(\d+)/)[1]);
  });

let grandTotal = 0;
files.forEach(f => {
  const num = f.match(/第(\d+)章/)[1];
  const title = f.match(/第\d+章_(.+)\.md/)[1];
  const total = updateWordMark(f);
  grandTotal += total;
  console.log(`${num.padStart(2)}  ${title.padEnd(12)} ${total}字`);
});
console.log(`---\n共 ${files.length} 章，合计 ${grandTotal} 字`);

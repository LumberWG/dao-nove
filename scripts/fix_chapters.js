const fs = require('fs');
[21,22,23,24,25].forEach(i => {
  const file = fs.readdirSync('chapters').find(f => f.startsWith('新_第' + i + '章'));
  if (!file) return;
  let t = fs.readFileSync('chapters/' + file, 'utf8');
  const before = (t.match(/——/g) || []).length;
  t = t.replace(/——/g, '，');
  fs.writeFileSync('chapters/' + file, t, 'utf8');
  const after = (t.match(/——/g) || []).length;
  const chars = t.replace(/\s/g, '').replace(/（本章约\d+字）/g, '');
  const h = (chars.match(/[一-鿿]/g) || []).length;
  const p = (chars.match(/[，。、！？；：""''（）《》—…]/g) || []).length;
  console.log('第' + i + '章: 破折号 ' + before + '→' + after + ', 汉字+标点: ' + (h + p));
});

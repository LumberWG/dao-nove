const fs = require('fs');
const files = fs.readdirSync('chapters')
  .filter(f => f.startsWith('新_第') && f.endsWith('.md'))
  .sort((a,b) => parseInt(a.match(/第(\d+)/)[1]) - parseInt(b.match(/第(\d+)/)[1]));

files.forEach(f => {
  const content = fs.readFileSync('chapters/' + f, 'utf8');
  const num = f.match(/第(\d+)章/)[1];
  const title = f.match(/第\d+章_(.+)\.md/)[1];

  // 破折号
  const emDash = (content.match(/——/g) || []).length;

  // 省略号（正常是……，不能是。。。。或。。。）
  const ellipsis = (content.match(/\.\.\.\.\.\./g) || []).length;
  const wrongEllipsis = (content.match(/。{3,}|\.{4,}/g) || []).length;

  // 中英文引号混用
  const hasMixed = (content.match(/[""]/g) || []).length > 0 && (content.match(/[""]/g) || []).length > 0;

  // 连续两个以上逗号/句号
  const repeatComma = (content.match(/，{2,}/g) || []).length;
  const repeatPeriod = (content.match(/。{2,}/g) || []).length;

  // 行首行尾空格
  const leadingSpace = (content.match(/\n +[^\s]/g) || []).length;

  const issues = [];
  if (emDash > 3) issues.push('破折号' + emDash + '处(限3)');
  if (wrongEllipsis > 0) issues.push('错误省略号');
  if (repeatComma > 0) issues.push('连续逗号');
  if (repeatPeriod > 0) issues.push('连续句号');
  if (leadingSpace > 0) issues.push('行首空格');

  if (issues.length > 0) {
    console.log(num.padStart(2) + '  ' + title.padEnd(12) + '  ⚠ ' + issues.join(', '));
  }
});
console.log('检查完成');

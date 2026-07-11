const fs = require('fs');
let t = fs.readFileSync('chapters/新_第21章_界碑.md', 'utf8');

// Replace all —— with appropriate punctuation based on context
t = t.replace(/——/g, (match, offset) => {
  // Check context - if preceded by dialog, keep as dialog interruption
  const before = t.substring(Math.max(0, offset - 10), offset);
  const after = t.substring(offset + 2, offset + 10);
  // Dialog interruption: preceded by " or ended by "
  if (before.includes('"') || after.includes('"')) return '——';
  // Default: replace with comma
  return '，';
});

fs.writeFileSync('chapters/新_第21章_界碑.md', t, 'utf8');
const d = (t.match(/——/g)||[]).length;
console.log('剩余破折号: ' + d);

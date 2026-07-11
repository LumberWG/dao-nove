const fs = require('fs');

const files = [
  '新_第31章_不要靠近我',
  '新_第49章_解绳',
  '新_第50章_苏缠之缠'
];

files.forEach(name => {
  let t = fs.readFileSync('chapters/' + name + '.md', 'utf8');
  const before = (t.match(/——/g) || []).length;

  // 不是X——是Y → 删前半
  t = t.replace(/——不是[^，。]*是/g, match => {
    const after = match.replace(/——不是[^，。]*是/, '');
    return '——' + after.trim();
  });

  // 解释性破折号 → 逗号
  t = t.replace(/——像/g, '，像');
  t = t.replace(/——似/g, '，似');
  t = t.replace(/——那/g, '。那');
  t = t.replace(/——他/g, '。他');
  t = t.replace(/——她/g, '。她');
  t = t.replace(/——这/g, '。这');
  t = t.replace(/——只/g, '。只');
  t = t.replace(/——可/g, '。可');
  t = t.replace(/——但/g, '。但');
  t = t.replace(/——比/g, '，比');
  t = t.replace(/——在/g, '，在');
  t = t.replace(/——越/g, '，越');
  t = t.replace(/——让/g, '，让');
  t = t.replace(/——已/g, '，已');
  t = t.replace(/——从/g, '，从');

  fs.writeFileSync('chapters/' + name + '.md', t, 'utf8');
  const after = (t.match(/——/g) || []).length;
  console.log(name.substring(4).padEnd(12) + ' ' + before + '→' + after);
});

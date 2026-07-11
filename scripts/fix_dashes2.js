const fs = require('fs');

const fixes = {
  '新_第31章_不要靠近我.md': [
    ['他也曾经有过同样的感觉——有什么东西等了他很久', '他也曾经有过同样的感觉，有什么东西等了他很久'],
  ],
  '新_第49章_解绳.md': [
    ['它帮我看到了很多我本来看不到的东西——也帮幻音楼看到了很多他们不应该看到的东西。', '它帮我看到了很多我本来看不到的东西，也帮幻音楼看到了很多他们不应该看到的东西。'],
    ['我不是在等他们同意——我是在等我自己准备好。', '我是在等我自己准备好。'],
    ['但皮肤上那道常年系绳留下的红印还在——红印的末端，有一根极细的丝线连出来', '但皮肤上那道常年系绳留下的红印还在。红印的末端，有一根极细的丝线连出来'],
    ['它是渗进命脉里的东西——不是绳子管的。', '它是渗进命脉里的东西，不是绳子管的。'],
  ],
  '新_第50章_苏缠之缠.md': [
    ['不是车夫要停——是车夫听见车厢里那姑娘说了一句话', '是车夫听见车厢里那姑娘说了一句话'],
    ['所以不管它指不指——我都得往北走', '所以不管它指不指，我都得往北走'],
  ],
};

Object.keys(fixes).forEach(file => {
  let t = fs.readFileSync('chapters/' + file, 'utf8');
  const before = (t.match(/——/g) || []).length;
  fixes[file].forEach(([from, to]) => {
    if (t.includes(from)) {
      t = t.replace(from, to);
    } else {
      console.log(file + ' 未匹配: ' + from.substring(0, 50));
    }
  });
  fs.writeFileSync('chapters/' + file, t, 'utf8');
  const after = (t.match(/——/g) || []).length;
  console.log(file + ' ' + before + '→' + after);
});

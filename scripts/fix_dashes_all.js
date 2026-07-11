const fs = require('fs');
let t = fs.readFileSync('chapters/新_第21章_界碑.md', 'utf8');

const pairs = [
  ['消失——是突然断掉的', '消失，是突然断掉的'],
  ['一种很暗的颜色在深处流动，像干涸的血在缓慢地翻动', '一种很暗的颜色在深处流动，像干了的血在翻动'],
  ['不是太阳晒的温——是内里透出来的温', '不是太阳晒的温，是内里透出来的温'],
  ['不是石板，不是泥土——是一根埋在土里的铁链', '不是石板，不是泥土，是一根埋在土里的铁链'],
  ['他的表情很平静——不是正常人的平静', '他的表情很平静，不是正常人的平静'],
  ['不是他知道路——是铜钱忽然在掌心里转了一个方向', '不是他知道路，是铜钱忽然在掌心里转了一个方向'],
  ['铜钱在怀里温着，正北偏东，指向那座塔', '铜钱在怀里温着，正北偏东，指向那座塔'],
].filter(([from]) => {
  if (t.includes(from)) return true;
  console.log('跳过: ' + from.substring(0, 30));
  return false;
});

pairs.forEach(([from, to]) => { t = t.replace(from, to); });

fs.writeFileSync('chapters/新_第21章_界碑.md', t, 'utf8');
const d = (t.match(/——/g)||[]).length;
console.log('剩余破折号: ' + d);

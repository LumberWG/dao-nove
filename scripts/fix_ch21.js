const fs = require('fs');
let t = fs.readFileSync('chapters/新_第21章_界碑.md', 'utf8');

const subs = [
  ['没有喊——他怕', '没有喊，他怕'],
  ['水是干净的——有人不久前刚打过', '水是干净的，有人不久前刚打过'],
  ['还能看出轮廓——一道弧线', '还能看出轮廓，一道弧线'],
  ['田里有庄稼——不是没人管的野地', '田里有庄稼，不是没人管的野地'],
  ['又低下去了——没有好奇', '又低下去了，没有好奇'],
  ['多了起来——挑担的菜农', '多了起来，挑担的菜农'],
  ['有一座哨卡——木棚搭了一半', '有一座哨卡，木棚搭了一半'],
  ['塞着一块木楔——门没锁', '塞着一块木楔，门没锁'],
  ['最高的那座建筑——序塔', '最高的那座建筑，序塔'],
  ['皱纹，瘦，嘴角叼着烟杆——不是幻觉', '皱纹，瘦，嘴角叼着烟杆，不是幻觉'],
];

subs.forEach(([from, to]) => {
  if (t.includes(from)) {
    t = t.replace(from, to);
  } else {
    console.log('未匹配: ' + from);
  }
});

fs.writeFileSync('chapters/新_第21章_界碑.md', t, 'utf8');
const dashes = (t.match(/——/g) || []).length;
const chars = t.replace(/\s/g, '').replace(/（本章约\d+字）/g, '').match(/[一-鿿㐀-䶿豈-﫿，。、！？；：""''（）《》——…—]/g);
console.log('破折号: ' + dashes);
console.log('汉字+标点: ' + (chars ? chars.length : 0));

@echo off
cd /d "f:\Study\dao-nove"
echo.
echo === [1/3] 提交 Git ===
git add -A
git commit -m "sync: %date% %time%"
if %errorlevel% equ 0 (
    echo [OK] 已提交
) else (
    echo [SKIP] 无变更
)
echo.
echo === [2/3] 推送到远程 ===
git push
echo.
echo === [3/3] 入库（同步到写作系统数据库）===
cd server
node -e "
const D=require('better-sqlite3'),fs=require('fs'),path=require('path');
const d=new D('writer.db');
d.exec('DROP TABLE IF EXISTS chapters;DROP TABLE IF EXISTS novels;');
d.exec('CREATE TABLE novels(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,author TEXT,description TEXT,created_at TEXT DEFAULT(datetime(\"now\",\"localtime\")),updated_at TEXT DEFAULT(datetime(\"now\",\"localtime\")));');
d.exec('CREATE TABLE chapters(id INTEGER PRIMARY KEY AUTOINCREMENT,novel_id INTEGER NOT NULL,chapter_number INTEGER NOT NULL,title TEXT NOT NULL,content TEXT DEFAULT \"\",word_count INTEGER DEFAULT 0,status TEXT DEFAULT \"draft\",created_at TEXT DEFAULT(datetime(\"now\",\"localtime\")),updated_at TEXT DEFAULT(datetime(\"now\",\"localtime\")));');
var nid=d.prepare('INSERT INTO novels(title) VALUES(?)').run('岁蚀').lastInsertRowid;
var dir=path.resolve(__dirname,'..','chapters');
var files=fs.readdirSync(dir).filter(function(f){return /^新_第\d+章_/.test(f);}).sort(function(a,b){return parseInt(a.match(/第(\d+)章/)[1])-parseInt(b.match(/第(\d+)章/)[1]);});
var ins=d.prepare('INSERT INTO chapters(novel_id,chapter_number,title,content,word_count) VALUES(?,?,?,?,?)');
var skip=0;
files.forEach(function(f){
  var num=parseInt(f.match(/第(\d+)章/)[1]);
  var c=fs.readFileSync(path.join(dir,f),'utf8');
  var t=c.split('\n')[0].trim().replace(/^﻿/,'').replace(/^#\s*/,'');
  t=t.replace(/第([一-也十百]+)章/g,function(m,cn){var dm={'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10};var n=0;for(var i=0;i<cn.length;i++){var ch=cn[i];if(ch==='十'&&n===0)n=10;else if(ch==='十')n+=10;else if(n>=10)n+=dm[ch];else n=dm[ch];}return '第'+n+'章';});
  if(!/^第\d+章/.test(t)){var title=f.replace(/\.md$/,'').replace(/^新_第\d+章_/,'').replace(/_/g,' ');t='第'+num+'章 '+title;}
  var t2=t.replace(/^第\d+章\s*/,'');
  if(t2==='阿芷的铜钱'&&skip===1)return;
  if(t2==='阿芷的铜钱')skip++;
  if(t2==='解绳'||t2==='沈见微的最后一次清醒')return;
  var clean=c.replace(/\s/g,'').replace(/（本章约\d+字）/g,'');
  ins.run(nid,num,t,c,clean.length);
});
console.log('[OK] 入库完成: '+d.prepare('SELECT COUNT(*) as c FROM chapters').get().c+'章');
"
echo.
pause

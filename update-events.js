// update-events.js — 全自动事件更新（扫描 + 去重 + 填充收益）
// 每天自动运行一次，输出 events.json + events-display.json
// 用法: node update-events.js [扫描天数, 默认30]

var fs=require('fs'),https=require('https'),cp=require('child_process'),path=require('path');
var DIR=__dirname;

// ═══ 1. 调用 Python 扫描公告 ═══
function runScanner(days){
  return new Promise(function(ok){
    console.log('[1/3] Python scan_announcements.py '+days+' days...');
    var pyExe=process.env.LOCALAPPDATA+'\\Python\\bin\\python.exe';
if(!fs.existsSync(pyExe))pyExe='python'; // fallback
var py=cp.spawn(pyExe,['scan_announcements.py',String(days)],{cwd:DIR,shell:false});
    var out='';py.stdout.on('data',function(d){out+=d});py.stderr.on('data',function(d){out+=d});
    py.on('close',function(code){
      console.log('  exit='+code);
      ok(code===0?out:'');
    });
  });
}

// ═══ 2. K线获取与收益计算（从 fill-returns.js 移植） ═══
function fetchURL(url){
  return new Promise(function(ok){
    https.get(url,{headers:{'User-Agent':'Mozilla/5.0','Referer':'https://web.ifzq.gtimg.cn/'}},function(r){
      var d='';r.on('data',function(c){d+=c});r.on('end',function(){ok(d)});
    }).on('error',function(){ok('')});
  });
}

function fetchKL(code,market){
  var pf=market===1?'sh':'sz';
  var url='https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param='+pf+code+',day,,,400,qfq';
  return fetchURL(url).then(function(body){
    try{
      var j=JSON.parse(body);
      var key=pf+code;
      if(j&&j.data&&j.data[key]&&j.data[key].qfqday){
        return j.data[key].qfqday.map(function(d){return {d:d[0],o:parseFloat(d[1]),c:parseFloat(d[2]),h:parseFloat(d[3]),l:parseFloat(d[4]),v:parseFloat(d[5])};});
      }
    }catch(e){}
    return [];
  });
}

function findIndex(kl,dateStr){
  for(var i=kl.length-1;i>=0;i--){if(kl[i].d<=dateStr)return i}
  return -1;
}

function calcReturn(kl,fromIdx,days){var to=fromIdx+days;if(to>=kl.length)return null;return ((kl[to].c-kl[fromIdx].c)/kl[fromIdx].c)*100;}

async function fillReturns(events){
  console.log('[2/3] Fetching K-line and computing returns...');
  // 收集唯一股票
  var stocks={};events.forEach(function(e){if(e&&e.stock_code)stocks[e.stock_code]=e.stock_code.charAt(0)==='6'||e.stock_code.charAt(0)==='5'?1:0;});
  stocks['510300']=1; // 沪深300ETF基准
  var klines={};
  var codes=Object.keys(stocks);
  for(var i=0;i<codes.length;i++){var s=codes[i];klines[s]=await fetchKL(s,stocks[s]);if((i+1)%10===0)process.stdout.write('\r  K-line '+(i+1)+'/'+codes.length+' ...');}
  console.log('\r  K-line done ('+codes.length+' stocks)');

  var hs300=klines['510300'];var filled=0;
  events.forEach(function(e){
    if(!e||!e.stock_code)return;
    var kl=klines[e.stock_code];if(!kl||kl.length<60)return;
    var idx=findIndex(kl,e.event_date);if(idx<0)return;
    var prev=idx-1;
    e.d0_return=(prev>=0)?Math.round(((kl[idx].c-kl[prev].c)/kl[prev].c)*10000)/100:null;
    var hsIdx=hs300?findIndex(hs300,e.event_date):-1;
    e.d5_excess=calcExcess(kl,idx,hs300,hsIdx,5);
    e.d20_excess=calcExcess(kl,idx,hs300,hsIdx,20);
    e.d60_excess=calcExcess(kl,idx,hs300,hsIdx,60);
    filled++;
  });
  console.log('  Filled '+filled+' events');
  return events;
}

function calcExcess(kl,ki,hsKL,hi,days){
  var sr=calcReturn(kl,ki,days);if(sr===null)return null;
  if(!hsKL||hi<0)return Math.round(sr*100)/100;
  var hr=calcReturn(hsKL,hi,days);if(hr===null)return Math.round(sr*100)/100;
  return Math.round((sr-hr)*100)/100;
}

// ═══ 3. 生成展示数据 ═══
function generateDisplay(events){
  // 汇总统计
  var total=events.length;
  var withReturns=events.filter(function(e){return e.d5_excess!==null}).length;
  var recent=events.filter(function(e){return e.event_date>=getDateStr(30)});

  // 按事件类型聚合
  var byType={};events.forEach(function(e){
    if(!byType[e.event_type])byType[e.event_type]={count:0,sum_d5:0,sum_d20:0,n_d5:0,n_d20:0};
    var t=byType[e.event_type];t.count++;
    if(e.d5_excess!==null){t.sum_d5+=e.d5_excess;t.n_d5++;}
    if(e.d20_excess!==null){t.sum_d20+=e.d20_excess;t.n_d20++;}
  });

  // 最近5条
  var sorted=events.slice().sort(function(a,b){return b.event_date.localeCompare(a.event_date)});
  var latest=sorted.slice(0,5).map(function(e){
    var typeLabels={supply_confirm:'供应确认',order_disclose:'订单披露',cert_progress:'认证进展',
      share_change:'份额变化',sub_signal:'替代信号',sanction:'管制制裁',expand:'扩产公告',refute:'证伪'};
    return {date:e.event_date,name:e.stock_name,code:e.stock_code,type:typeLabels[e.event_type]||e.event_type,
      desc:e.event_desc.substring(0,60),d5:e.d5_excess,d20:e.d20_excess,d60:e.d60_excess};
  });

  return {
    updated:new Date().toISOString(),
    total:total,filled:withReturns,recentCount:recent.length,
    byType:byType,latest:latest,
    needMore:total<30  // 是否需要更多事件才能做归因分析
  };
}

function getDateStr(daysAgo){var d=new Date(Date.now()-daysAgo*86400000);return d.toISOString().slice(0,10);}

// ═══ 主流程 ═══
async function main(){
  var days=parseInt(process.argv[2])||30;
  console.log('=== Auto Events Update ===');
  console.log('Scan range: '+days+' days\n');

  // Step 1: 扫描
  var scanOut=await runScanner(days);
  var pendingFile=path.join(DIR,'events-pending.json');
  var scanned=[];
  if(fs.existsSync(pendingFile)){
    try{scanned=JSON.parse(fs.readFileSync(pendingFile,'utf8'))}catch(e){}
  }
  console.log('  Scanned: '+scanned.length+' candidates');

  // Step 2: 合并到 events.json（去重）
  var eventsFile=path.join(DIR,'events.json');
  var existing=[];
  if(fs.existsSync(eventsFile)){
    try{existing=JSON.parse(fs.readFileSync(eventsFile,'utf8'))}catch(e){}
  }

  var existingKeys={};existing.forEach(function(e){existingKeys[e.stock_code+'|'+(e.event_desc||'').substring(0,60)]=true;});

  var added=0;
  scanned.forEach(function(e){
    var key=e.stock_code+'|'+(e.event_desc||'').substring(0,60);
    if(!existingKeys[key]){
      existing.push(e);
      existingKeys[key]=true;
      added++;
    }
  });

  if(added>0){
    fs.writeFileSync(eventsFile,JSON.stringify(existing,null,2),'utf8');
    console.log('  Added '+added+' new events → events.json ('+existing.length+' total)');
  } else {
    console.log('  No new events (total: '+existing.length+')');
  }

  // Step 3: 填充收益
  await fillReturns(existing);
  fs.writeFileSync(eventsFile,JSON.stringify(existing,null,2),'utf8');

  // Step 4: 生成展示数据
  var display=generateDisplay(existing);
  fs.writeFileSync(path.join(DIR,'events-display.json'),JSON.stringify(display,null,2),'utf8');

  // Step 5: 生成 JS 文件供浏览器直接加载
  var jsContent='// Auto-generated '+new Date().toISOString()+'\nvar EVENTS_DATA='+JSON.stringify(existing,null,2)+';\nvar EVENTS_DISPLAY='+JSON.stringify(display,null,2)+';\n';
  fs.writeFileSync(path.join(DIR,'events-data.js'),jsContent,'utf8');

  console.log('[3/3] Done: '+existing.length+' events, '+display.filled+' with returns');
  console.log('Display: events-display.json, events-data.js');
  if(display.needMore)console.log('Note: Need '+(30-existing.length)+' more events for first attribution analysis.');
}

main().catch(function(e){console.error(e);process.exit(1)});

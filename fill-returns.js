// fill-returns.js — 自动填充事件收益数据
// 读取 events.json → 拉取 K 线 → 计算 D0/D+5/D+20/D+60 收益 → 写回
// 用法: node fill-returns.js

var fs=require('fs'),https=require('https');

function fetchURL(url){
  return new Promise(function(ok,no){
    var opts={headers:{'User-Agent':'Mozilla/5.0','Referer':'https://web.ifzq.gtimg.cn/'}};
    https.get(url,opts,function(r){var d='';r.on('data',function(c){d+=c});r.on('end',function(){ok(d)})}).on('error',no);
  });
}

// ═══ K 线获取（HTTPS + Referer，与代理转发规则一致）═══
function fetchKL(code,market){
  var pf=market===1?'sh':'sz';
  var url='https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param='+pf+code+',day,,,400,qfq';
  console.log('  拉取 '+code+' ('+pf+')...');
  return fetchURL(url).then(function(body){
    try{
      var j=JSON.parse(body);
      if(j&&j.data&&j.data[pf+code]&&j.data[pf+code].qfqday){
        return j.data[pf+code].qfqday.map(function(d){
          return {d:d[0],o:parseFloat(d[1]),c:parseFloat(d[2]),h:parseFloat(d[3]),l:parseFloat(d[4]),v:parseFloat(d[5])};
        });
      }
    }catch(e){console.log('  解析失败: '+e.message)}
    return [];
  }).catch(function(e){console.log('  网络错误: '+e.message);return[]});
}

// ═══ K 线查找 ═══
function findIndex(kl,dateStr){
  // 找到日期 ≤ dateStr 的最近一个交易日
  for(var i=kl.length-1;i>=0;i--){if(kl[i].d<=dateStr)return i}
  return -1;
}

function calcReturn(kl,fromIdx,offsetDays){
  // offsetDays 个交易日后的收盘价收益率
  var toIdx=fromIdx+offsetDays;
  if(toIdx>=kl.length)return null; // 数据不足
  return ((kl[toIdx].c-kl[fromIdx].c)/kl[fromIdx].c)*100;
}

// ═══ 主流程 ═══
async function main(){
  var events=JSON.parse(fs.readFileSync('events.json','utf8'));
  console.log('读取 '+events.length+' 条事件\n');

  // 收集所有需要的股票代码
  var stocks={};
  events.forEach(function(e){
    var key=e.stock_code;
    if(!stocks[key])stocks[key]={code:e.stock_code,market:e.stock_code.charAt(0)==='6'||e.stock_code.charAt(0)==='5'?1:0};
  });
  // 沪深300ETF基准（sh510300 跟踪沪深300指数，腾讯接口可用）
  stocks['hs300']={code:'510300',market:1};

  // 拉取所有 K 线
  var klines={};
  var codes=Object.keys(stocks);
  for(var i=0;i<codes.length;i++){
    var s=stocks[codes[i]];
    klines[codes[i]]=await fetchKL(s.code,s.market);
    console.log('  '+s.code+' → '+(klines[codes[i]]?klines[codes[i]].length+' 条':'失败'));
  }
  console.log('');

  // 填充收益数据
  var hs300=klines['hs300'];
  var filled=0,skipped=0;

  events.forEach(function(e){
    var kl=klines[e.stock_code];
    if(!kl||kl.length<60){console.log('  ✗ '+e.stock_name+' 无K线数据');skipped++;return}

    var idx=findIndex(kl,e.event_date);
    if(idx<0){console.log('  ✗ '+e.stock_name+' '+e.event_date+' 日期无数据');skipped++;return}

    // D-Day: 事件日当天收益率
    var prevIdx=idx-1;
    e.d0_return=(prevIdx>=0)?((kl[idx].c-kl[prevIdx].c)/kl[prevIdx].c)*100:null;

    // D+5 / D+20 / D+60 超额收益（相对沪深300）
    var hsIdx=hs300?findIndex(hs300,e.event_date):-1;

    e.d5_excess=calcExcess(kl,idx,hs300,hsIdx,5);
    e.d20_excess=calcExcess(kl,idx,hs300,hsIdx,20);
    e.d60_excess=calcExcess(kl,idx,hs300,hsIdx,60);

    e._filled_at=new Date().toISOString().slice(0,10);

    var summary=[];
    if(e.d0_return!==null)summary.push('D0:'+fmt(e.d0_return));
    if(e.d5_excess!==null)summary.push('D+5超额:'+fmt(e.d5_excess));
    if(e.d20_excess!==null)summary.push('D+20超额:'+fmt(e.d20_excess));
    else summary.push('D+20:数据不足');
    if(e.d60_excess!==null)summary.push('D+60超额:'+fmt(e.d60_excess));
    else summary.push('D+60:数据不足');

    console.log('  ✓ '+e.stock_name+' '+e.event_date+' '+summary.join(' | '));
    filled++;
  });

  // 写回
  fs.writeFileSync('events.json',JSON.stringify(events,null,2),'utf8');
  console.log('\n完成: '+filled+' 条已填充, '+skipped+' 条跳过');
  console.log('已写入 events.json');

  // 生成供 event-tracker.html 导入的 JS 文件
  var exportJS='// 自动生成于 '+new Date().toISOString()+'\n// 复制此数组到浏览器控制台执行:\n// localStorage.setItem("mx_events",JSON.stringify(EVENTS_DATA));location.reload();\nvar EVENTS_DATA='+JSON.stringify(events,null,2)+';\n';
  fs.writeFileSync('events-data.js',exportJS,'utf8');
  console.log('已生成 events-data.js（可在浏览器控制台导入）');
}

function calcExcess(kl,klIdx,hsKL,hsIdx,days){
  var stockRet=calcReturn(kl,klIdx,days);
  if(stockRet===null)return null;
  if(!hsKL||hsIdx<0)return stockRet; // 无基准时返绝对收益
  var hsRet=calcReturn(hsKL,hsIdx,days);
  if(hsRet===null)return stockRet;
  return Math.round((stockRet-hsRet)*100)/100;
}

function fmt(v){return v===null?'--':(v>=0?'+':'')+v.toFixed(2)+'%'}

main().catch(function(e){console.error(e);process.exit(1)});

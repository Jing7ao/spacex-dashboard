// 回测引擎 — 模拟模型在过去一年的表现
var http=require('http'),https=require('https'),fs=require('fs');

var STOCKS=[
  {c:'002149',m:0,n:'西部材料',rk:'high',pew:344,rn:'试样送测/Q1利润-71%'},
  {c:'300136',m:0,n:'信维通信',rk:'high',pew:97,rn:'SpaceX独家供应商/实控人减持'},
  {c:'300433',m:0,n:'蓝思科技',rk:'mid',pew:30,rn:'航天UTG玻璃'},
  {c:'688102',m:1,n:'斯瑞新材',rk:'high',pew:156,rn:'火箭热端部件'},
  {c:'603809',m:1,n:'豪能股份',rk:'mid',pew:23,rn:'航天+机器人'},
  {c:'301005',m:0,n:'超捷股份',rk:'critical',pew:1281,rn:'纯概念炒作/无实质'},
  {c:'002865',m:0,n:'钧达股份',rk:'high',pew:0,rn:'无收入/亏损'},
  // 英伟达供应链
  {c:'300476',m:0,n:'胜宏科技',rk:'mid',pew:35,rn:'GPU PCB全球第一'},
  {c:'601138',m:1,n:'工业富联',rk:'mid',pew:20,rn:'AI服务器40%'},
  {c:'300308',m:0,n:'中际旭创',rk:'mid',pew:40,rn:'800G光模块龙头'},
  {c:'300502',m:0,n:'新易盛',rk:'mid',pew:40,rn:'GB300 CPO'},
  {c:'002463',m:0,n:'沪电股份',rk:'mid',pew:35,rn:'AI PCB北美80%'},
  // 特斯拉供应链
  {c:'601689',m:1,n:'拓普集团',rk:'mid',pew:35,rn:'Tesla底盘+Optimus'},
  {c:'002050',m:0,n:'三花智控',rk:'mid',pew:40,rn:'Tesla热管理'},
  {c:'603305',m:1,n:'旭升集团',rk:'mid',pew:30,rn:'Tesla一级供应商'},
];

var BUDGET=2000,STOP_LOSS=-0.08,TAKE_PROFIT=0.15,MIN_SCORE=65;

// === 技术分析函数（与面板一致）===
function calcRSI(cl,p){p=p||14;if(cl.length<p+1)return 50;var g=0,l=0;for(var i=cl.length-p;i<cl.length;i++){var d=cl[i]-cl[i-1];if(d>0)g+=d;else l-=d}if(l===0)return 100;return 100-(100/(1+g/l))}
function calcMA(d,p){if(d.length<p)return d[d.length-1];var s=0;for(var i=d.length-p;i<d.length;i++)s+=d[i];return s/p}

function scoreDay(kline,idx,stock){
  if(idx<60)return null; // 需要至少60天数据
  var cl=[],vl=[];
  for(var i=idx-60;i<=idx;i++){cl.push(kline[i].c);vl.push(kline[i].v)}
  var cp=cl[cl.length-1],pp=cl[cl.length-2];
  var m5=calcMA(cl,5),m20=calcMA(cl,20),m60=calcMA(cl,60);
  var trendStr=Math.abs(m20-m60)/m60;
  var vol20=0;for(var i=vl.length-20;i<vl.length;i++)vol20+=vl[i];vol20/=20;
  var vol5=0;for(var i=vl.length-5;i<vl.length;i++)vol5+=vl[i];vol5/=5;
  var volTrend=vol5/vol20;
  var volatility=0;for(var i=cl.length-20;i<cl.length;i++)volatility+=Math.pow((cl[i]-m20)/m20,2);volatility=Math.sqrt(volatility/20);
  var env='range';if(trendStr>0.05&&volTrend>1.0)env='trend';else if(volatility>0.08||volTrend>2.5||volTrend<0.3)env='volatile';
  var wRSI=0.25,wMA=0.25,wVol=0.20,wBB=0.15,wFund=0.15;
  if(env==='trend'){wMA=0.35;wRSI=0.15;wBB=0.10}else if(env==='range'){wRSI=0.30;wBB=0.20;wMA=0.20}else{wRSI=0.20;wMA=0.20;wVol=0.10;wFund=0.30}
  var rsi=calcRSI(cl);var rsS=rsi<=20?100:rsi<=30?80:rsi<=40?65:rsi<=50?55:rsi<=60?45:rsi<=70?30:rsi<=80?15:0;
  var maS=cp>m5&&m5>m20?100:cp>m5?75:cp>m20?60:40;
  var vr=vl[vl.length-1]/vol20;var pc=((cp-pp)/pp)*100;
  var vlS=vr>2&&pc>0?100:vr>1.5&&pc>0?70:vr>2&&pc<0?0:vr>1.5&&pc<0?30:50;
  var mb=calcMA(cl,20);var vv=0;for(var i=cl.length-20;i<cl.length;i++)vv+=Math.pow(cl[i]-mb,2);var sd=Math.sqrt(vv/20);var bu=mb+2*sd,bl=mb-2*sd;var bp=safediv(cp-bl,bu-bl);var bbS=bp<.15?80:bp<.3?65:bp>.85?20:bp>.7?35:50;
  var comp=Math.round(rsS*wRSI+maS*wMA+vlS*wVol+bbS*wBB+50*wFund);
  if(stock.pew>200||stock.pew===0)comp-=10;
  if(stock.rk==='critical'){comp-=15;if(comp>40)comp=40}else if(stock.rk==='high')comp-=5;
  if(stock.rn&&(stock.rn.indexOf('亏损')>=0||stock.rn.indexOf('Q1利润')>=0||stock.rn.indexOf('无收入')>=0||stock.rn.indexOf('无实质')>=0))comp-=10;
  if(env==='volatile')comp=Math.round(comp*0.85);
  comp=Math.max(0,Math.min(100,comp));
  return {comp:comp,env:env,rsi:rsi,price:cp};
}
function safediv(a,b){return b===0||isNaN(b)?0.5:a/b}

// === 数据获取 ===
function fetchKL(stock){
  return new Promise(function(resolve){
    var pf=stock.m===1?'sh':'sz';var code=pf+stock.c;
    var url='http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param='+code+',day,,,300,qfq';
    console.log('Fetching '+stock.n+'...');
    fetch(url).then(function(r){return r.text()}).then(function(body){
      try{
        var j=JSON.parse(body);
        if(j&&j.data&&j.data[code]&&j.data[code].qfqday){
          var raw=j.data[code].qfqday;
          var data=[];for(var i=0;i<raw.length;i++){var d=raw[i];data.push({d:d[0],o:parseFloat(d[1]),c:parseFloat(d[2]),h:parseFloat(d[3]),l:parseFloat(d[4]),v:parseFloat(d[5])})}
          resolve(data);
        }else{console.log('  no data');resolve([])}
      }catch(e){console.log('  parse err');resolve([])}
    }).catch(function(e){console.log('  fetch err: '+e.message);resolve([])});
  });
}

// === 回测主逻辑 ===
function backtest(klineData){
  var trades=[]; // {buyDate, buyPrice, sellDate, sellPrice, stock, plPct, score}

  for(var si=0;si<STOCKS.length;si++){
    var stock=STOCKS[si];var kl=klineData[stock.c];if(!kl||kl.length<100)continue;

    for(var i=60;i<kl.length-5;i++){
      var sc=scoreDay(kl,i,stock);if(!sc||sc.comp<MIN_SCORE)continue;

      // 模拟买入
      var buyDate=kl[i+1].d,buyPrice=kl[i+1].o; // 次日开盘买入

      // 模拟卖出：跟踪接下来30天，触及止盈止损或到期卖出
      var sellDate='',sellPrice=0,reason='';
      for(var j=i+2;j<Math.min(i+32,kl.length);j++){
        var high=kl[j].h,low=kl[j].l,close=kl[j].c;
        var plH=(high-buyPrice)/buyPrice,plL=(low-buyPrice)/buyPrice;
        if(plL<=STOP_LOSS){sellDate=kl[j].d;sellPrice=buyPrice*(1+STOP_LOSS);reason='止损';break}
        if(plH>=TAKE_PROFIT){sellDate=kl[j].d;sellPrice=buyPrice*(1+TAKE_PROFIT);reason='止盈';break}
        if(j===Math.min(i+31,kl.length-1)){sellDate=kl[j].d;sellPrice=close;reason='到期'}
      }
      if(!sellDate)continue;

      var plPct=(sellPrice-buyPrice)/buyPrice*100;
      trades.push({stock:stock.n,code:stock.c,buyDate:buyDate,buyPrice:buyPrice,sellDate:sellDate,sellPrice:sellPrice,plPct:plPct,score:sc.comp,reason:reason,env:sc.env});
      i=j; // 跳过已持仓期间
    }
  }

  return trades;
}

// === 统计 ===
function stats(trades){
  if(trades.length===0)return {total:0,winRate:0,avgPL:0,annual:0,maxDD:0};
  var wins=trades.filter(function(t){return t.plPct>0});
  var winRate=(wins.length/trades.length*100);
  var avgPL=trades.reduce(function(s,t){return s+t.plPct},0)/trades.length;
  var avgWin=wins.length>0?wins.reduce(function(s,t){return s+t.plPct},0)/wins.length:0;
  var losses=trades.filter(function(t){return t.plPct<=0});
  var avgLoss=losses.length>0?losses.reduce(function(s,t){return s+t.plPct},0)/losses.length:0;
  // 按时间排序计算最大回撤
  trades.sort(function(a,b){return a.buyDate.localeCompare(b.buyDate)});
  var equity=100,peak=100,maxDD=0;
  for(var i=0;i<trades.length;i++){
    equity*=(1+trades[i].plPct/100);
    if(equity>peak)peak=equity;
    var dd=(peak-equity)/peak*100;if(dd>maxDD)maxDD=dd;
  }
  var finalEquity=equity;
  var dates=trades.map(function(t){return t.buyDate});dates.sort();
  var firstDate=dates[0],lastDate=dates[dates.length-1];
  var years=(new Date(lastDate)-new Date(firstDate))/(365*86400000);
  var annual=years>0?(Math.pow(finalEquity/100,1/years)-1)*100:0;

  // 按行业
  var byEnv={trend:[],range:[],volatile:[]};
  trades.forEach(function(t){if(byEnv[t.env])byEnv[t.env].push(t)});

  return{
    total:trades.length,
    winRate:winRate.toFixed(1),
    avgPL:avgPL.toFixed(2),
    avgWin:avgWin.toFixed(2),
    avgLoss:avgLoss.toFixed(2),
    annual:annual.toFixed(1),
    maxDD:maxDD.toFixed(1),
    finalEquity:finalEquity.toFixed(1),
    years:years.toFixed(1),
    byEnv:{
      trend:{count:byEnv.trend.length,wr:byEnv.trend.length>0?(byEnv.trend.filter(function(t){return t.plPct>0}).length/byEnv.trend.length*100).toFixed(1):'-'},
      range:{count:byEnv.range.length,wr:byEnv.range.length>0?(byEnv.range.filter(function(t){return t.plPct>0}).length/byEnv.range.length*100).toFixed(1):'-'},
      volatile:{count:byEnv.volatile.length,wr:byEnv.volatile.length>0?(byEnv.volatile.filter(function(t){return t.plPct>0}).length/byEnv.volatile.length*100).toFixed(1):'-'},
    }
  };
}

// === 主程序 ===
async function main(){
  console.log('=== 回测引擎启动 ===');
  console.log('模型: 六维+环境感知+基本面过滤');
  console.log('止损: '+fmtP(STOP_LOSS)+' | 止盈: '+fmtP(TAKE_PROFIT)+' | 买入线: '+MIN_SCORE);
  console.log('标的: '+STOCKS.length+'只 | 时间: 近1年 | 模拟: 次日开盘买入\n');

  var klineData={};
  for(var i=0;i<STOCKS.length;i++){
    var data=await fetchKL(STOCKS[i]);
    if(data.length>0)klineData[STOCKS[i].c]=data;
    console.log('  '+STOCKS[i].n+': '+data.length+' days');
  }

  console.log('\n=== 运行回测 ===');
  var trades=backtest(klineData);
  console.log('总交易次数: '+trades.length);

  var s=stats(trades);
  console.log('\n========================================');
  console.log('         回 测 结 果');
  console.log('========================================');
  console.log('总交易次数:  '+s.total);
  console.log('胜率:        '+s.winRate+'%');
  console.log('平均盈亏:    '+s.avgPL+'%');
  console.log('平均盈利:    +'+s.avgWin+'%  |  平均亏损: '+s.avgLoss+'%');
  console.log('年化收益率:  '+s.annual+'%');
  console.log('最大回撤:    -'+s.maxDD+'%');
  console.log('最终净值:    '+s.finalEquity+' (初始100)');
  console.log('回测时长:    '+s.years+' 年');
  console.log('----------------------------------------');
  console.log('按市场环境:');
  console.log('  趋势市: '+s.byEnv.trend.count+'笔  胜率 '+s.byEnv.trend.wr+'%');
  console.log('  震荡市: '+s.byEnv.range.count+'笔  胜率 '+s.byEnv.range.wr+'%');
  console.log('  异常市: '+s.byEnv.volatile.count+'笔  胜率 '+s.byEnv.volatile.wr+'%');
  console.log('========================================\n');

  // 按月分组
  var byMonth={};
  trades.forEach(function(t){
    var m=t.buyDate.slice(0,7);
    if(!byMonth[m])byMonth[m]={count:0,wins:0};
    byMonth[m].count++;if(t.plPct>0)byMonth[m].wins++;
  });
  console.log('按月表现:');
  Object.keys(byMonth).sort().forEach(function(m){
    var d=byMonth[m];var wr=(d.wins/d.count*100).toFixed(0);
    var bar='';for(var i=0;i<Math.round(d.wins/d.count*20);i++)bar+='█';
    console.log('  '+m+'  '+d.count+'笔  胜率'+wr+'%  '+bar);
  });

  // 按股票
  console.log('\n按股票:');
  var byStock={};
  trades.forEach(function(t){if(!byStock[t.code])byStock[t.code]={n:t.stock,count:0,wins:0,pl:0};byStock[t.code].count++;if(t.plPct>0)byStock[t.code].wins++;byStock[t.code].pl+=t.plPct});
  Object.values(byStock).sort(function(a,b){return b.count-a.count}).forEach(function(s){
    var wr=s.count>0?(s.wins/s.count*100).toFixed(0):'-';
    var avg=s.count>0?(s.pl/s.count).toFixed(1):'-';
    console.log('  '+s.n+': '+s.count+'笔  胜率'+wr+'%  均'+avg+'%');
  });

  console.log('\n=== 回测完成 ===');
}

function fmtP(n){return (n>0?'+':'')+(n*100).toFixed(1)+'%'}

main().catch(console.error);

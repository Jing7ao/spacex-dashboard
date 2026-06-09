// 参数自动校准器 — 逐个参数测试最优值
var http=require('http');
var STOCKS=[
  {c:'002149',m:0,n:'西部材料'},{c:'300136',m:0,n:'信维通信'},{c:'300476',m:0,n:'胜宏科技'},{c:'601138',m:1,n:'工业富联'},{c:'300308',m:0,n:'中际旭创'},{c:'601689',m:1,n:'拓普集团'},{c:'002050',m:0,n:'三花智控'},{c:'603305',m:1,n:'旭升集团'},
];

var PARAMS_BASE={
  criticalCap:40,coolCap:45,coolDays:30,dynCap:55,dynDays:90,dynLosses:2,
  flowPersistCap:65,flowReverseCap:35,
  etfWeakDiscount:0.75,weeklyDivDiscount:0.88,volatileDiscount:0.85,
  peWarn:200,pePenalty:10,criticalPenalty:15,highPenalty:5,
  stopLoss:-0.08,takeProfit:0.15,
};

// 每个参数的测试范围
var RANGES={
  criticalCap:[35,40,45,50],
  coolCap:[40,45,50,55],
  coolDays:[20,30,40,60],
  dynCap:[50,55,60,65],
  dynLosses:[1,2,3,4],
  flowPersistCap:[55,60,65,70],
  flowReverseCap:[30,35,40,45],
  etfWeakDiscount:[0.6,0.7,0.75,0.8,0.85],
  weeklyDivDiscount:[0.8,0.85,0.88,0.9,0.95],
  volatileDiscount:[0.75,0.8,0.85,0.9,0.95],
  peWarn:[150,200,250,300],
  pePenalty:[5,8,10,12,15],
  criticalPenalty:[10,15,20],
  highPenalty:[3,5,8],
  stopLoss:[-0.05,-0.08,-0.10,-0.12],
  takeProfit:[0.10,0.15,0.20,0.25],
};

function fetchKL(code,m){
  return new Promise(function(resolve){
    var pf=m===1?'sh':'sz';var u='http://127.0.0.1:8080/api/txk?param='+encodeURIComponent(pf+code+',day,,,300,qfq');
    http.get(u,function(r){var b='';r.on('data',function(d){b+=d});r.on('end',function(){
      try{var j=JSON.parse(b);var raw=j.data[pf+code].qfqday;resolve(raw.map(function(d){return{o:parseFloat(d[1]),c:parseFloat(d[2]),h:parseFloat(d[3]),l:parseFloat(d[4])}}))}catch(e){resolve([])}
    })}).on('error',function(){resolve([])});
  });
}

function calcRSI(cl,p){p=p||14;if(cl.length<p+1)return 50;var g=0,l=0;for(var i=cl.length-p;i<cl.length;i++){var d=cl[i]-cl[i-1];if(d>0)g+=d;else l-=d}if(l===0)return 100;return 100-(100/(1+g/l))}
function calcMA(d,p){if(d.length<p)return d[d.length-1];var s=0;for(var i=d.length-p;i<d.length;i++)s+=d[i];return s/p}

function backtestOne(kline,params){
  var trades=[];var pp=Object.assign({},PARAMS_BASE,params);
  STOCKS.forEach(function(s){
    var kl=kline[s.c];if(!kl||kl.length<100)return;
    for(var i=60;i<kl.length-5;i++){
      var cl=kl.slice(i-60,i+1).map(function(k){return k.c}),vl=kl.slice(i-60,i+1).map(function(k){return 1});
      var cp=cl[cl.length-1];
      var m5=calcMA(cl,5),m20=calcMA(cl,20),m60=calcMA(cl,60);
      var trendStr=Math.abs(m20-m60)/m60;
      var env=trendStr>0.05?'trend':'range';
      var rsi=calcRSI(cl);var rsS=rsi<=20?100:rsi<=30?80:rsi<=40?65:rsi<=50?55:rsi<=60?45:rsi<=70?30:rsi<=80?15:0;
      var maS=cp>m5&&m5>m20?100:cp>m5?75:cp>m20?60:40;
      var comp=Math.round(rsS*0.25+maS*0.3+(50)*0.15+50*0.15+50*0.15);
      if(env==='volatile')comp=Math.round(comp*pp.volatileDiscount);
      if(s.pew>pp.peWarn||s.pew===0)comp-=pp.pePenalty;
      if(s.rk==='critical'){comp-=pp.criticalPenalty;if(comp>pp.criticalCap)comp=pp.criticalCap}
      else if(s.rk==='high')comp-=pp.highPenalty;
      if(comp<60)continue;
      var buy=kl[i+1].o;var sell=0,reason='';
      for(var j=i+2;j<Math.min(i+32,kl.length);j++){
        if(kl[j].l<=buy*(1+pp.stopLoss)){sell=buy*(1+pp.stopLoss);reason='SL';break}
        if(kl[j].h>=buy*(1+pp.takeProfit)){sell=buy*(1+pp.takeProfit);reason='TP';break}
        if(j===Math.min(i+31,kl.length-1)){sell=kl[j].c;reason='expire'}
      }
      if(sell>0)trades.push({pl:(sell-buy)/buy});i=j;
    }
  });
  if(trades.length<5)return null;
  var avg=trades.reduce(function(s,t){return s+t.pl},0)/trades.length;
  var vr=0;trades.forEach(function(t){vr+=Math.pow(t.pl-avg,2)});var std=Math.sqrt(vr/trades.length);
  var sharpe=std>0?(avg/std*Math.sqrt(trades.length)).toFixed(3):'0';
  var wins=trades.filter(function(t){return t.pl>0}).length;
  return{n:trades.length,wr:(wins/trades.length*100).toFixed(0),avg:(avg*100).toFixed(1),sharpe:sharpe,dd:'-'};
}

async function main(){
  console.log('加载K线...');
  var kline={};for(var i=0;i<STOCKS.length;i++){var data=await fetchKL(STOCKS[i].c,STOCKS[i].m);kline[STOCKS[i].c]=data;console.log('  '+STOCKS[i].n+': '+data.length+'d')}

  console.log('\n基线回测(默认参数):');
  var base=backtestOne(kline,{});
  console.log('  '+base.n+'笔 胜率'+base.wr+'% 均'+base.avg+'% 夏普'+base.sharpe);

  console.log('\n逐个参数扫描...');
  for(var pk in RANGES){
    var best=null,bestV=null;
    for(var vi=0;vi<RANGES[pk].length;vi++){
      var p={};p[pk]=RANGES[pk][vi];
      var r=backtestOne(kline,p);if(!r)continue;
      if(!best||parseFloat(r.sharpe)>parseFloat(best.sharpe)){best=r;bestV=RANGES[pk][vi]}
    }
    if(best)console.log('  '+pk+': 最优值='+bestV+' → '+best.n+'笔 胜率'+best.wr+'% 夏普'+best.sharpe);
  }
  console.log('\n完成。');
}
main();

// sharpe-ecosystem.js — 跨生态 vs 单生态 风险调整收益对比
// 验证 §19.5 "跨生态 Sharpe 3.78 vs 单生态 0.18" 的发现
// 用法: node sharpe-ecosystem.js

var https=require('https'),fs=require('fs'),path=require('path');

// ═══ 标的定义 ═══
// 跨生态：同一只股票出现在 ≥2 个生态分类中
var CROSS_ECO = [
  {c:'688629',n:'华丰科技', eco:'国产AI算力+商业航天'},
  {c:'600584',n:'长电科技', eco:'英伟达+国产AI算力+长鑫存储链'},
  {c:'001270',n:'铖昌科技', eco:'SpaceX+中国商业航天'},
  {c:'688017',n:'绿的谐波', eco:'特斯拉Optimus+国产机器人'},
  {c:'688631',n:'莱斯信息', eco:'SpaceX+低空经济'},
  {c:'002837',n:'英维克', eco:'英伟达+国产AI算力+液冷散热'},
  {c:'301018',n:'申菱环境', eco:'英伟达液冷+国产AI算力'},
  {c:'002281',n:'光迅科技', eco:'光通信CPO+国产AI算力'},
  {c:'002156',n:'通富微电', eco:'英伟达+国产AI算力+长鑫存储链'},
  {c:'601689',n:'拓普集团', eco:'特斯拉+国产机器人'},
  {c:'603606',n:'东方电缆', eco:'电力能源+海底光缆'},
  {c:'600487',n:'亨通光电', eco:'光通信CPO+海底光缆'},
  {c:'600522',n:'中天科技', eco:'海底光缆+电力能源'},
];

// 单生态：仅出现在 1 个生态分类中
var SINGLE_ECO = [
  {c:'002916',n:'深南电路', eco:'英伟达'},
  {c:'600118',n:'中国卫星', eco:'中国商业航天'},
  {c:'002179',n:'中航光电', eco:'中国商业航天'},
  {c:'603662',n:'柯力传感', eco:'国产机器人'},
  {c:'000099',n:'中信海直', eco:'低空经济'},
  {c:'688070',n:'纵横股份', eco:'低空经济'},
  {c:'601100',n:'恒立液压', eco:'国产机器人'},
  {c:'002920',n:'德赛西威', eco:'特斯拉'},
  {c:'603305',n:'旭升集团', eco:'特斯拉'},
  {c:'600745',n:'闻泰科技', eco:'特斯拉'},
  {c:'688668',n:'鼎通科技', eco:'液冷散热'},
  {c:'300249',n:'依米康', eco:'液冷散热'},
  {c:'300394',n:'天孚通信', eco:'英伟达'},
  {c:'688012',n:'中微公司', eco:'半导体'},
];

var BENCHMARK = '510300'; // 沪深300ETF
var RF_RATE = 0.015;      // 无风险利率（1.5%，一年期定存近似）

// ═══ K线获取 ═══
function fetchURL(url){
  return new Promise(function(ok){
    https.get(url,{headers:{'User-Agent':'Mozilla/5.0','Referer':'https://web.ifzq.gtimg.cn/'}},function(r){
      var d='';r.on('data',function(c){d+=c});r.on('end',function(){ok(d)});
    }).on('error',function(){ok('')});
  });
}

function fetchKL(code,type){
  var pf=(type===1||code.charAt(0)==='6'||code.charAt(0)==='5')?'sh':'sz';
  var url='https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param='+pf+code+',day,,,400,qfq';
  return fetchURL(url).then(function(body){
    try{
      var j=JSON.parse(body),key=pf+code;
      if(j&&j.data&&j.data[key]&&j.data[key].qfqday){
        return j.data[key].qfqday.map(function(d){
          return {d:d[0],o:+d[1],c:+d[2],h:+d[3],l:+d[4],v:+d[5]};
        });
      }
    }catch(e){}
    return [];
  });
}

// ═══ 收益率计算 ═══
function dailyReturns(kl){
  var rets=[];
  for(var i=1;i<kl.length;i++){rets.push((kl[i].c-kl[i-1].c)/kl[i-1].c);}
  return rets;
}

// 年化夏普比率
function sharpe(dailyRets,rf){
  if(!dailyRets||dailyRets.length<20)return null;
  var n=dailyRets.length,mean=0;
  for(var i=0;i<n;i++)mean+=dailyRets[i];mean/=n;
  var dailyRf=rf/252;
  var excess=mean-dailyRf,std=0;
  for(var i=0;i<n;i++)std+=Math.pow(dailyRets[i]-mean,2);
  std=Math.sqrt(std/(n-1));
  if(std===0)return null;
  return (excess/std)*Math.sqrt(252);
}

// Sortino比率（下行标准差）
function sortino(dailyRets,rf){
  if(!dailyRets||dailyRets.length<20)return null;
  var n=dailyRets.length,mean=0;
  for(var i=0;i<n;i++)mean+=dailyRets[i];mean/=n;
  var dailyRf=rf/252,excess=mean-dailyRf;
  var downs=0;
  for(var i=0;i<n;i++){
    var d=dailyRets[i]-dailyRf;
    if(d<0)downs+=d*d;
  }
  downs=Math.sqrt(downs/n);
  if(downs===0)return null;
  return (excess/downs)*Math.sqrt(252);
}

// Calmar比率 = 年化收益率 / 最大回撤
function calmar(dailyRets,kl){
  if(!dailyRets||dailyRets.length<20||!kl||kl.length<20)return null;
  var mean=0;for(var i=0;i<dailyRets.length;i++)mean+=dailyRets[i];
  mean/=dailyRets.length;
  var annualReturn=mean*252;
  var peak=kl[0].c,maxDD=0;
  for(var i=1;i<kl.length;i++){
    if(kl[i].c>peak)peak=kl[i].c;
    var dd=(peak-kl[i].c)/peak;
    if(dd>maxDD)maxDD=dd;
  }
  if(maxDD===0)return null;
  return annualReturn/maxDD;
}

// YTD 收益率
function ytdReturn(kl){
  if(!kl||kl.length<2)return null;
  // 找2026年第一个交易日
  var first=null;
  for(var i=0;i<kl.length;i++){
    if(kl[i].d>='2026-01-02'){first=kl[i];break;}
  }
  if(!first)return null;
  var last=kl[kl.length-1];
  return ((last.c-first.c)/first.c)*100;
}

// 波动率（年化）
function annualVol(dailyRets){
  if(!dailyRets||dailyRets.length<20)return null;
  var n=dailyRets.length,mean=0;
  for(var i=0;i<n;i++)mean+=dailyRets[i];mean/=n;
  var std=0;
  for(var i=0;i<n;i++)std+=Math.pow(dailyRets[i]-mean,2);
  std=Math.sqrt(std/(n-1));
  return std*Math.sqrt(252)*100;
}

// 胜率（日胜率）
function winRate(dailyRets){
  if(!dailyRets||dailyRets.length===0)return null;
  var wins=0;
  for(var i=0;i<dailyRets.length;i++){if(dailyRets[i]>0)wins++;}
  return (wins/dailyRets.length)*100;
}

// ═══ 主流程 ═══
async function main(){
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║    跨生态 vs 单生态 — 风险调整收益对比                       ║');
  console.log('║    验证 §19.5: "跨生态 Sharpe 3.78 vs 单生态 0.18"           ║');
  console.log('╚══════════════════════════════════════════════════════════════╝');
  console.log();

  // Fetch all K-lines
  var allStocks=CROSS_ECO.concat(SINGLE_ECO);
  var codes={};
  allStocks.forEach(function(s){codes[s.c]=s;});
  codes[BENCHMARK]={c:BENCHMARK,n:'沪深300ETF'};

  console.log('Fetching K-line for '+Object.keys(codes).length+' stocks...');
  var klines={};
  var codeList=Object.keys(codes);
  for(var i=0;i<codeList.length;i++){
    var c=codeList[i];
    klines[c]=await fetchKL(c,1);
    process.stdout.write('\r  '+(i+1)+'/'+codeList.length+' '+codes[c].n+' ('+(klines[c]?klines[c].length+' bars':'FAIL')+')');
  }
  console.log('\n');

  // 计算基准
  var benchKL=klines[BENCHMARK];
  var benchRets=dailyReturns(benchKL);
  var benchSharpe=sharpe(benchRets,RF_RATE);
  var benchVol=annualVol(benchRets);
  var benchYTD=ytdReturn(benchKL);
  console.log('基准: 沪深300 | Sharpe '+benchSharpe.toFixed(2)+' | 波动率 '+(benchVol||0).toFixed(1)+'% | YTD '+(benchYTD||0).toFixed(1)+'%');
  console.log();

  // 计算每组
  function calcGroup(group,label){
    console.log('── '+label+' ('+group.length+' stocks) ──');
    var results=[];
    group.forEach(function(s){
      var kl=klines[s.c];
      if(!kl||kl.length<20){console.log('  '+s.n+' SKIP (no data)');return;}
      var rets=dailyReturns(kl);
      var sh=sharpe(rets,RF_RATE),so=sortino(rets,RF_RATE);
      var ca=calmar(rets,kl),vol=annualVol(rets),ytd=ytdReturn(kl),wr=winRate(rets);
      results.push({name:s.n,code:s.c,eco:s.eco||'',sharpe:sh,sortino:so,calmar:ca,vol:vol,ytd:ytd,winRate:wr,bars:kl.length});
      console.log('  '+s.n.padEnd(8)+' | Sharpe '+(sh||0).toFixed(2).padStart(6)
        +' | Sortino '+(so||0).toFixed(2).padStart(6)
        +' | Calmar '+(ca||0).toFixed(2).padStart(6)
        +' | Vol '+(vol||0).toFixed(1).padStart(6)+'%'
        +' | YTD '+(ytd||0).toFixed(1).padStart(6)+'%'
        +' | 胜率 '+(wr||0).toFixed(0).padStart(4)+'%'
        +' | '+s.eco||'');
    });

    // 汇总统计
    var validR=results.filter(function(r){return r.sharpe!==null;});
    if(validR.length===0){console.log('  No valid results\n');return null;}
    var avgSharpe=validR.reduce(function(s,r){return s+(r.sharpe||0);},0)/validR.length;
    var avgSortino=validR.reduce(function(s,r){return s+(r.sortino||0);},0)/validR.length;
    var avgCalmar=validR.reduce(function(s,r){return s+(r.calmar||0);},0)/validR.length;
    var avgVol=validR.reduce(function(s,r){return s+(r.vol||0);},0)/validR.length;
    var avgYTD=validR.reduce(function(s,r){return s+(r.ytd||0);},0)/validR.length;
    var avgWin=validR.reduce(function(s,r){return s+(r.winRate||0);},0)/validR.length;
    // 组内Sharpe标准差
    var ss=0;for(var i=0;i<validR.length;i++)ss+=Math.pow(validR[i].sharpe-avgSharpe,2);
    var stdSharpe=validR.length>1?Math.sqrt(ss/(validR.length-1)):0;

    console.log('  '+('平均').padEnd(8)+' | Sharpe '+(avgSharpe).toFixed(2).padStart(6)
      +' | Sortino '+avgSortino.toFixed(2).padStart(6)
      +' | Calmar '+avgCalmar.toFixed(2).padStart(6)
      +' | Vol '+avgVol.toFixed(1).padStart(6)+'%'
      +' | YTD '+avgYTD.toFixed(1).padStart(6)+'%'
      +' | 胜率 '+avgWin.toFixed(0).padStart(4)+'%');
    console.log('  Sharpe σ: '+stdSharpe.toFixed(2)+' (组内离散度)');
    console.log();
    return {results:validR,avgSharpe:avgSharpe,avgSortino:avgSortino,avgCalmar:avgCalmar,avgVol:avgVol,avgYTD:avgYTD,stdSharpe:stdSharpe};
  }

  var crossResult=calcGroup(CROSS_ECO,'🔗 跨生态（≥2个生态）');
  var singleResult=calcGroup(SINGLE_ECO,'📍 单生态（仅1个生态）');

  // 统计检验
  if(crossResult&&singleResult){
    console.log('═══════════════════════════════════════════════════════════');
    console.log(' 对比汇总');
    console.log('═══════════════════════════════════════════════════════════');
    var diffSharpe=crossResult.avgSharpe-singleResult.avgSharpe;
    var diffSortino=crossResult.avgSortino-singleResult.avgSortino;
    var diffCalmar=crossResult.avgCalmar-singleResult.avgCalmar;
    var diffVol=crossResult.avgVol-singleResult.avgVol;
    var diffYTD=crossResult.avgYTD-singleResult.avgYTD;

    console.log('                   跨生态     单生态     差值');
    console.log('  Sharpe          '+(crossResult.avgSharpe).toFixed(2).padStart(6)+'      '+(singleResult.avgSharpe).toFixed(2).padStart(6)+'      '+(diffSharpe>0?'+':'')+diffSharpe.toFixed(2));
    console.log('  Sortino         '+(crossResult.avgSortino).toFixed(2).padStart(6)+'      '+(singleResult.avgSortino).toFixed(2).padStart(6)+'      '+(diffSortino>0?'+':'')+diffSortino.toFixed(2));
    console.log('  Calmar          '+(crossResult.avgCalmar).toFixed(2).padStart(6)+'      '+(singleResult.avgCalmar).toFixed(2).padStart(6)+'      '+(diffCalmar>0?'+':'')+diffCalmar.toFixed(2));
    console.log('  年化波动率      '+(crossResult.avgVol).toFixed(1).padStart(6)+'%     '+(singleResult.avgVol).toFixed(1).padStart(6)+'%     '+(diffVol>0?'+':'')+diffVol.toFixed(1)+'%');
    console.log('  YTD             '+(crossResult.avgYTD).toFixed(1).padStart(6)+'%     '+(singleResult.avgYTD).toFixed(1).padStart(6)+'%     '+(diffYTD>0?'+':'')+diffYTD.toFixed(1)+'%');

    // t-stat (粗糙版)
    var n1=crossResult.results.length,n2=singleResult.results.length;
    var pooledSE=Math.sqrt(Math.pow(crossResult.stdSharpe,2)/n1+Math.pow(singleResult.stdSharpe,2)/n2);
    var tStat=pooledSE>0?diffSharpe/pooledSE:0;
    console.log();
    console.log('  Sharpe差值 t-stat: '+tStat.toFixed(2)+' (n1='+n1+', n2='+n2+')');
    if(Math.abs(tStat)>2){
      console.log('  ⚠️ 差异显著（|t|>2）。跨生态 vs 单生态的Sharpe差异不太可能是噪声');
    }else{
      console.log('  差异不显著（|t|<2）。需要更多样本或更长回看期');
    }

    // 判断
    console.log();
    console.log('═══════════════════════════════════════════════════════════');
    if(diffSharpe>0&&diffVol>0){
      console.log('  结论：跨生态 ✓ Sharpe更高 + 波动也更高');
      console.log('  「跨生态=天然对冲=低波动」假设被推翻');
      console.log('  真实机制：双生态同时上行时收益放大，非降波动');
    }else if(diffSharpe>0&&diffVol<0){
      console.log('  结论：跨生态 ✓ Sharpe更高 + 波动更低');
      console.log('  跨生态确实提供了对冲收益（更高回报+更低风险）');
    }else{
      console.log('  结论：跨生态 ✗ 未跑赢单生态');
      console.log('  需要重新评估跨生态标的筛选标准');
    }
    console.log('═══════════════════════════════════════════════════════════');

    // 输出JSON
    var out={
      date:new Date().toISOString(),
      benchmark:{sharpe:benchSharpe,vol:benchVol,ytd:benchYTD},
      cross:{avgSharpe:crossResult.avgSharpe,avgSortino:crossResult.avgSortino,avgCalmar:crossResult.avgCalmar,avgVol:crossResult.avgVol,avgYTD:crossResult.avgYTD,n:n1,stocks:crossResult.results.map(function(r){return{name:r.name,code:r.code,sharpe:r.sharpe,sortino:r.sortino,calmar:r.calmar,vol:r.vol,ytd:r.ytd,eco:r.eco};})},
      single:{avgSharpe:singleResult.avgSharpe,avgSortino:singleResult.avgSortino,avgCalmar:singleResult.avgCalmar,avgVol:singleResult.avgVol,avgYTD:singleResult.avgYTD,n:n2,stocks:singleResult.results.map(function(r){return{name:r.name,code:r.code,sharpe:r.sharpe,sortino:r.sortino,calmar:r.calmar,vol:r.vol,ytd:r.ytd,eco:r.eco};})},
      diff:{sharpe:diffSharpe,sortino:diffSortino,calmar:diffCalmar,vol:diffVol,ytd:diffYTD,tStat:tStat},
    };
    fs.writeFileSync(path.join(__dirname,'sharpe-ecosystem.json'),JSON.stringify(out,null,2),'utf8');
    console.log();
    console.log('输出: sharpe-ecosystem.json');
  }
}

main().catch(function(e){console.error(e);process.exit(1);});

function computeScores(){
  const ind=INDUSTRIES[cur];
  for(const s of ind.watchlist){
    const kl=kline[s.c];if(!kl||kl.length<20){scores[s.c]=null;continue}
    // --- 供应链证据解析（v2.2）---
    if(!supplyMeta[s.c]&&s.rn)supplyMeta[s.c]=parseSupplyChain(s.rn);
    var scRel=getSupplyReliability(supplyMeta[s.c]);
    const cl=kl.map(k=>k.c),vl=kl.map(k=>k.v);
    const cp=cl[cl.length-1],pp=cl[cl.length-2]||cp;
    const m5=calcMA(cl,5),m20=calcMA(cl,20),m60=calcMA(cl,Math.min(60,cl.length));
    // === 市场环境感知层 ===
    var trendStr=Math.abs(m20-m60)/m60;                 // 趋势强度
    var vol20=vl.slice(-20).reduce(function(s,v){return s+v},0)/20;
    var vol5=vl.slice(-5).reduce(function(s,v){return s+v},0)/5;
    var volTrend=vol5/vol20;                             // 量能趋势 (>1放量 <1缩量)
    var volatility=0;for(var vi=cl.length-20;vi<cl.length;vi++){volatility+=Math.pow((cl[vi]-m20)/m20,2)}

    volatility=Math.sqrt(volatility/20);                 // 年化波动率
    // 环境分类: trend=趋势强势, range=震荡, volatile=高波动异常
    var env='range';
    if(trendStr>PARAMS.envTrendMA&&volTrend>1.0)env='trend';
    else if(volatility>PARAMS.envVolAnnual||volTrend>PARAMS.envVolExtreme||volTrend<PARAMS.envVolShrink)env='volatile';
    var wRSI=PARAMS.wRSI_base,wMA=PARAMS.wMA_base,wVol=PARAMS.wVol_base,wBB=PARAMS.wBB_base,wFund=PARAMS.wFund_base;
    // 动态IC权重调制: 加载 ic_data.json, IC>0→boost, IC<0→reduce
    if(icMult.rsi!==undefined){wRSI*=icMult.rsi;wMA*=icMult.ma;wVol*=icMult.vol;wBB*=icMult.bb;wFund*=icMult.vp||1.0}
    var sumW=wRSI+wMA+wVol+wBB+wFund;wRSI/=sumW;wMA/=sumW;wVol/=sumW;wBB/=sumW;wFund/=sumW; // re-normalize
    if(env==='trend'){wMA=PARAMS.wMA_trend;wRSI=PARAMS.wRSI_trend;wBB=PARAMS.wBB_trend}
    else if(env==='range'){wRSI=PARAMS.wRSI_range;wBB=PARAMS.wBB_range;wMA=PARAMS.wMA_range}
    else{wRSI=PARAMS.wRSI_vol;wMA=PARAMS.wMA_vol;wVol=PARAMS.wVol_vol;wFund=PARAMS.wFund_vol}
    // 计算各维度得分
    const rs=calcRSI(cl);const rsS=rs<=20?100:rs<=30?80:rs<=40?65:rs<=50?55:rs<=60?45:rs<=70?30:rs<=80?15:0;
    const maS=cp>m5&&m5>m20?100:cp>m5?75:cp>m20?60:40;
    const vr=vl[vl.length-1]/vol20;const pc=((cp-pp)/pp)*100;
    const vlS=vr>2&&pc>0?100:vr>1.5&&pc>0?70:vr>2&&pc<0?0:vr>1.5&&pc<0?30:50;
    const mb=calcMA(cl,20);let vv=0;for(let vi2=cl.length-20;vi2<cl.length;vi2++)vv+=Math.pow(cl[vi2]-mb,2);
    const sd=Math.sqrt(vv/20);const bu=mb+2*sd,bl=mb-2*sd;const bp=(cp-bl)/(bu-bl);
    const bbS=bp<.15?80:bp<.3?65:bp>.85?20:bp>.7?35:50;
    // 资金流向得分 (真实数据, VPN已通)
    var fundS=50;var ff=prices[s.c]&&prices[s.c]._ff;
    if(ff&&ff.main!==undefined){var mc=prices[s.c].mc||1e10;var flowPct=ff.main/mc;if(flowPct>0.001)fundS=100;else if(flowPct>0.0005)fundS=80;else if(flowPct>0)fundS=65;else if(flowPct>-0.0005)fundS=35;else if(flowPct>-0.001)fundS=20;else fundS=0}
    // 持续性硬规则(不依赖估计系数)
    if(ff&&ff.persist&&ff.persist.indexOf('持续')>=0&&fundS<PARAMS.flowPersistCap)fundS=PARAMS.flowPersistCap;
    if(ff){var fh=prices[s.c]._flowHist;if(fh&&fh.length>=2&&fh[fh.length-2]!==fh[fh.length-1]&&fundS>PARAMS.flowReverseCap)fundS=PARAMS.flowReverseCap;}
    var comp=Math.round(rsS*wRSI+maS*wMA+vlS*wVol+bbS*wBB+fundS*wFund);
    var finScore=50;var fd=window._finData?window._finData[s.c]:null;
    if(fd){finScore=50;if(fd.roe>20)finScore+=15;else if(fd.roe>10)finScore+=8;else if(fd.roe>5)finScore+=3;else if(fd.roe<0)finScore-=10;if(fd.prfG>50)finScore+=10;else if(fd.prfG>20)finScore+=5;else if(fd.prfG<-30)finScore-=8;if(fd.debtR>0&&fd.debtR<40)finScore+=5;else if(fd.debtR>70)finScore-=5;if(fd.grossM>40)finScore+=5;else if(fd.grossM<15)finScore-=3}
    else{if(s.pew>0&&s.pew<30)finScore+=10;else if(s.pew>=30&&s.pew<60)finScore+=5;else if(s.pew>=PARAMS.peWarn)finScore-=8;else if(s.pew===0)finScore-=10}
    comp=Math.round(comp*(1-PARAMS.wFin)+finScore*PARAMS.wFin);
    var weeklyOK=true;if(kl.length>=120){var wCl=[];for(var wi=kl.length-100;wi<kl.length;wi+=5){var ws=kl.slice(wi,Math.min(wi+5,kl.length));wCl.push(ws[ws.length-1].c)}if(wCl.length>=12){var wM5=calcMA(wCl,5),wM20=calcMA(wCl,Math.min(20,wCl.length));weeklyOK=wCl[wCl.length-1]>wM5||wM5>wM20}}
    if(!weeklyOK&&comp>=60)comp=Math.round(comp*PARAMS.weeklyDivDiscount);
    if(s.pew>PARAMS.peWarn||s.pew===0)comp-=PARAMS.pePenalty;
    if(s.rk==='critical'){comp-=PARAMS.criticalPenalty;if(comp>PARAMS.criticalCap)comp=PARAMS.criticalCap}
    else if(s.rk==='high')comp-=PARAMS.highPenalty;
    if(s.rn&&(s.rn.indexOf('亏损')>=0||s.rn.indexOf('Q1利润')>=0||s.rn.indexOf('无收入')>=0||s.rn.indexOf('无实质')>=0))comp-=10;
    // === 时间过滤器1: 均线缠绕 → 方向不明，信号降权 ===
    if(m5>0&&m20>0){var maGap=Math.abs(m5-m20)/m20;if(maGap<0.02)comp=Math.round(comp*0.85)} // MA5/MA20距离<2%=均线缠绕
    // === 时间过滤器2: 财报沉默期 → 季报3日内不出强买入 ===
    var now2=new Date();var m=now2.getMonth()+1,d=now2.getDate();var inEarnings=(m===4&&d<=15)||(m===8&&d<=15)||(m===10&&d<=15); // 财报季前半段(集中发布期)
    if(inEarnings&&comp>=60)comp=58; // 财报季不出强买入，等靴子落地
    // === 供应链证据分级 ===
    var evLevel='E3';if(s.rn){var rn2=s.rn;if(rn2.indexOf('独家')>=0||rn2.indexOf('量产')>=0||rn2.indexOf('一级')>=0||rn2.indexOf('批量')>=0)evLevel='E1';else if(rn2.indexOf('送样')>=0||rn2.indexOf('认证')>=0||rn2.indexOf('确认')>=0)evLevel='E2'}
    if(evLevel==='E1'&&comp>=55)comp+=3;if(evLevel==='E3'&&comp>=55)comp-=2;
    // 瓶颈标的(源自瓶颈初筛与验证结果v3.1): B1+B2+B3全满足 → +3分
    if(window._bnE1&&window._bnE1.indexOf(s.c)>=0&&comp>=40){comp+=3}else if(window._bnE3&&window._bnE3.indexOf(s.c)>=0&&comp>=40){comp+=2}
    var etfCode=INDUSTRIES[cur].etfs.filter(function(e){return !e.us})[0];
    if(etfCode&&kline[etfCode.c]&&kline[etfCode.c].length>=60){
      var etfCl=kline[etfCode.c].map(function(k){return k.c});
      var etfMA60=calcMA(etfCl,Math.min(60,etfCl.length));
      if(cp<etfMA60)comp=Math.round(comp*PARAMS.etfWeakDiscount);
    }
    var now=new Date();var cooldown=false;
    for(var hi=0;hi<tradeHist.length;hi++){if(tradeHist[hi].code===s.c&&tradeHist[hi].plPct<0&&(now-new Date(tradeHist[hi].date))/(86400000)<PARAMS.coolDays){cooldown=true;break}}
    if(cooldown){if(comp>PARAMS.coolCap)comp=PARAMS.coolCap}
    var recentLosses=0;
    for(var hi2=0;hi2<tradeHist.length;hi2++){if(tradeHist[hi2].code===s.c&&tradeHist[hi2].plPct<0&&(now-new Date(tradeHist[hi2].date))/(86400000)<PARAMS.dynDays)recentLosses++;}
    if(recentLosses>=PARAMS.dynLosses){if(comp>PARAMS.dynCap)comp=PARAMS.dynCap}
    // === 波动率目标(缺口#2): 高波动时Kelly仓位缩半 ===
    var annVol=volatility*100;var volScale=1.0;if(annVol>40)volScale=0.4;else if(annVol>30)volScale=0.6;else if(annVol>20)volScale=0.8;
    if(env==='volatile')comp=Math.round(comp*PARAMS.volatileDiscount);
    // 美股联动: NVDA/TSLA当日涨跌影响供应链
    comp=applyUSLinkage(s.c,comp,scRel.factor);
    comp=Math.max(0,Math.min(100,comp));
    // 因子扩展: 42号量价背离(±3分) + 成交额稳定性(±2分)
    var ext=prices[s.c]&&prices[s.c]._ext;if(ext){comp+=Math.round(ext.vpScore*-3); // A股短期反转: 缩量涨反跌,42号反向if(ext.amtStab>0.7)comp+=2;else if(ext.amtStab<0.3)comp-=1}
    // 北向资金因子: 外资持续增持+1~2分
    comp=Math.max(0,Math.min(100,comp));
    // 信号平滑: 3日均值压低换手率(视频16: 降turnover→Sharpe提升)
    if(!smoothScores[s.c])smoothScores[s.c]=[];
    smoothScores[s.c].push(comp);if(smoothScores[s.c].length>3)smoothScores[s.c].shift();
    var smoothComp=comp;if(smoothScores[s.c].length>=3){smoothComp=Math.round((smoothScores[s.c][0]+smoothScores[s.c][1]+smoothScores[s.c][2])/3)}
    var sg,sl;if(smoothComp>=PARAMS.buyThreshold){sg='s-strong';sl='🔥强买入'}else if(smoothComp>=PARAMS.holdThreshold){sg='s-buy';sl='📈偏买入'}else if(smoothComp>=PARAMS.sellThreshold){sg='s-hold';sl='➡️观望'}else if(smoothComp>=PARAMS.warnThreshold){sg='s-sell';sl='⚠️偏卖出'}else{sg='s-warn';sl='🚨强卖出'}
    // === 概率学: 信号置信度（六维共振强度）===
    var dims=[rsS>=60,maS>=60,vlS>=60,bbS>=60,fundS>=60,env!=='volatile'];var agree=dims.filter(function(x){return x}).length;
    var conf=agree>=5?'高置信':agree>=3?'中置信':'低置信';
    // v2.2: 供应链证据密度附加标签（不替代置信度，只补充）
    var scTag='';
    if(scRel.level==='speculative')scTag=' 📡?';
    else if(scRel.level==='unverified_multi')scTag=' 📡~';
    else if(scRel.level==='unverified')scTag=' 📡';
    conf+=scTag;
    // === 统计学: 个股历史表现 ===
    var stockTrades=tradeHist.filter(function(t){return t.code===s.c});var stockWins=stockTrades.filter(function(t){return t.plPct>0}).length;
    var stockWR=stockTrades.length>=3?(stockWins/stockTrades.length*100).toFixed(0)+'%':'-';
    var avgWin=0,avgLoss=0;stockTrades.forEach(function(t){if(t.plPct>0)avgWin+=t.plPct;else avgLoss+=Math.abs(t.plPct)});
    avgWin=stockWins>0?avgWin/stockWins:10;avgLoss=(stockTrades.length-stockWins)>0?avgLoss/(stockTrades.length-stockWins||1):8;
    // === 经济学: 凯利公式仓位建议 ===
    var winRate=stockTrades.length>=5?stockWins/stockTrades.length:0.58;var kelly=winRate-(1-winRate)/(avgWin/Math.max(avgLoss,1));
    var kellyPct=Math.max(0,Math.min(30,Math.round(kelly*100)));if(stockTrades.length<3)kellyPct=15;kellyPct=Math.round(kellyPct*volScale);
    // 标记异常市+低置信=行为经济学警告
    if(env==='volatile'){sl='⚡'+sl;sg=sg}
    if(conf==='低置信'&&comp>=60)sl='❓'+sl;
    var techRaw=Math.round(rsS*wRSI+maS*wMA+vlS*wVol+bbS*wBB+fundS*wFund);
    var q='';if(techRaw>=60&&finScore>=60)q='最佳';else if(techRaw<60&&finScore>=60)q='稳健';else if(techRaw>=60&&finScore<60)q='诱多';else q='回避';
    scores[s.c]={rs:Math.round(rs),m5:Math.round(m5*100)/100,m20:Math.round(m20*100)/100,vr:Math.round(vr*100)/100,comp,sg,sl,tech:techRaw,fin:finScore,flow:fundS,quad:q,env:env,conf:conf,stockWR:stockWR,kelly:kellyPct,
      scRelLevel:scRel.level,scRelLabel:scRel.label,scRelReason:scRel.reason,scTier:supplyMeta[s.c]?supplyMeta[s.c].tier:null,ev:evLevel,volScale:volScale,annVol:Math.round(annVol)};
  }
}
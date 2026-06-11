# rebuild_cs.py — 分步重建 computeScores
import os, re
DIR = os.path.dirname(os.path.abspath(__file__))
FILE = os.path.join(DIR, "monitor.html")

# 原始 computeScores (从 _check.js 提取)
with open(os.path.join(DIR, "_check.js"), encoding='utf-8') as f:
    js = f.read()

# 找到 computeScores 的完整定义
start = js.index('function computeScores(){')
depth = 1
i = start + 26
while depth > 0 and i < len(js):
    if js[i] == '{': depth += 1
    elif js[i] == '}': depth -= 1
    i += 1
cs = js[start:i]

print(f"Original computeScores: {len(cs)} chars")

# 分成步骤
lines = cs.split('\n')
print(f"Lines: {len(lines)}")
print("First 5:", lines[:5])
print("Last 5:", lines[-5:])

# 简化版 computeScores: 三元因子(Vol+MA+AmtStab) + 基本风控
new_cs = '''function computeScores(){
  const ind=INDUSTRIES[cur];
  for(const s of ind.watchlist){
    const kl=kline[s.c];if(!kl||kl.length<20){scores[s.c]=null;continue}
    const cl=kl.map(k=>k.c);
    const cp=cl[cl.length-1],pp=cl[cl.length-2]||cp;
    const m5=calcMA(cl,5),m20=calcMA(cl,20);
    // 成交量
    const vl=kl.map(k=>k.v);
    const vol20=vl.slice(-20).reduce(function(s,v){return s+v},0)/20;
    const vr=vl[vl.length-1]/vol20;
    const pc=((cp-pp)/pp)*100;
    const vlS=vr>2&&pc>0?100:vr>1.5&&pc>0?70:vr>2&&pc<0?0:vr>1.5&&pc<0?30:50;
    // 均线
    const maS=cp>m5&&m5>m20?100:cp>m5?75:cp>m20?60:40;
    // 成交额稳定性
    var amts=[];for(var ai=Math.max(0,kl.length-30);ai<kl.length;ai++){amts.push(kl[ai].v*kl[ai].c/10000)}
    var amtAvg=amts.reduce(function(s,v){return s+v},0)/amts.length;
    var amtStd=Math.sqrt(amts.reduce(function(s,v){return s+Math.pow(v-amtAvg,2)},0)/amts.length);
    var amtStab=amtAvg>0?Math.max(0,Math.min(1,1-amtStd/amtAvg)):0.5;
    // RSI
    const rs=calcRSI(cl);const rsS=rs<=20?100:rs<=30?80:rs<=40?65:rs<=50?55:rs<=60?45:rs<=70?30:rs<=80?15:0;
    // 布林带
    const mb=calcMA(cl,20);var vv=0;for(var vi2=cl.length-20;vi2<cl.length;vi2++)vv+=Math.pow(cl[vi2]-mb,2);
    const sd=Math.sqrt(vv/20);const bu=mb+2*sd,bl=mb-2*sd;const bp=(cp-bl)/(bu-bl);
    const bbS=bp<.15?80:bp<.3?65:bp>.85?20:bp>.7?35:50;
    // 资金流
    var fundS=50;var ff=prices[s.c]&&prices[s.c]._ff;
    if(ff&&ff.main!==undefined){var mc=prices[s.c].mc||1e10;var flowPct=ff.main/mc;if(flowPct>0.001)fundS=100;else if(flowPct>0.0005)fundS=80;else if(flowPct>0)fundS=65;else if(flowPct>-0.0005)fundS=35;else if(flowPct>-0.001)fundS=20;else fundS=0}
    if(ff&&ff.persist&&ff.persist.indexOf('持续')>=0&&fundS<65)fundS=65;
    if(ff){var fh=prices[s.c]._flowHist;if(fh&&fh.length>=2&&fh[fh.length-2]!==fh[fh.length-1]&&fundS>35)fundS=35;}
    // 分生态因子: 每生态只用Top-2/3因子
    var ecoCfg=_ecoFactors[cur];var comp=50;
    if(ecoCfg&&ecoCfg.top_factors&&ecoCfg.top_factors.length>=2){
      var tf=ecoCfg.top_factors;var totalW=0;comp=0;
      for(var tfi=0;tfi<Math.min(3,tf.length);tfi++){
        var fkey=tf[tfi][0],fic=Math.abs(tf[tfi][1]),reverse=tf[tfi][1]<0;
        if(fic<0.05)continue;
        var fs=50;
        if(fkey==='rsi'||fkey==='rsi_rev')fs=rsS;
        else if(fkey==='ma')fs=maS;
        else if(fkey==='vol'||fkey==='vol_rev')fs=vlS;
        else if(fkey==='mom5')fs=(pc>5?80:pc>2?65:pc<-5?20:pc<-2?35:50);
        else if(fkey==='rev5')fs=(pc<-5?80:pc<-2?65:pc>5?20:pc>2?35:50);
        else if(fkey==='amt_stab')fs=Math.round(amtStab*100);
        else if(fkey==='gap'){var gapSum=0;for(var gi=Math.max(0,kl.length-4);gi<kl.length;gi++){var prevC=gi>0?kl[gi-1].c:kl[gi].c;gapSum+=(kl[gi].o-prevC)/prevC*100}fs=gapSum>3?80:gapSum>1?60:gapSum<-3?20:40;}
        else if(fkey==='clv'||fkey==='vwap'||fkey==='shadow'||fkey==='vp_div')fs=50;
        if(reverse)fs=100-fs;
        var w=fic;comp+=fs*w;totalW+=w;
      }
      comp=totalW>0?Math.round(comp/totalW):50;
    }else{
      comp=Math.round(rsS*PARAMS.wRSI_base+maS*PARAMS.wMA_base+vlS*PARAMS.wVol_base+bbS*PARAMS.wBB_base+fundS*PARAMS.wFund_base);
    }
    // 财务
    var finScore=50;var fd=window._finData?window._finData[s.c]:null;
    if(fd){finScore=50;if(fd.roe>20)finScore+=15;else if(fd.roe>10)finScore+=8;else if(fd.roe>5)finScore+=3;else if(fd.roe<0)finScore-=10;if(fd.prfG>50)finScore+=10;else if(fd.prfG>20)finScore+=5;else if(fd.prfG<-30)finScore-=8;if(fd.debtR>0&&fd.debtR<40)finScore+=5;else if(fd.debtR>70)finScore-=5;if(fd.grossM>40)finScore+=5;else if(fd.grossM<15)finScore-=3}
    else{if(s.pew>0&&s.pew<30)finScore+=10;else if(s.pew>=30&&s.pew<60)finScore+=5;else if(s.pew>=PARAMS.peWarn)finScore-=8;else if(s.pew===0)finScore-=10}
    comp=Math.round(comp*(1-PARAMS.wFin)+finScore*PARAMS.wFin);
    // 风控
    if(s.pew>PARAMS.peWarn||s.pew===0)comp-=PARAMS.pePenalty;
    if(s.rk==='critical'){comp-=PARAMS.criticalPenalty;if(comp>PARAMS.criticalCap)comp=PARAMS.criticalCap}
    else if(s.rk==='high')comp-=PARAMS.highPenalty;
    if(s.rn&&(s.rn.indexOf('亏损')>=0||s.rn.indexOf('Q1利润')>=0||s.rn.indexOf('无收入')>=0||s.rn.indexOf('无实质')>=0))comp-=10;
    if(m5>0&&m20>0){var maGap=Math.abs(m5-m20)/m20;if(maGap<0.02)comp=Math.round(comp*0.85)}
    var now2=new Date();var m2=now2.getMonth()+1,d2=now2.getDate();var inEarnings=(m2===4&&d2<=15)||(m2===8&&d2<=15)||(m2===10&&d2<=15);
    if(inEarnings&&comp>=60)comp=58;
    var evLevel='E3';if(s.rn){var rn2=s.rn;if(rn2.indexOf('独家')>=0||rn2.indexOf('量产')>=0||rn2.indexOf('一级')>=0||rn2.indexOf('批量')>=0)evLevel='E1';else if(rn2.indexOf('送样')>=0||rn2.indexOf('认证')>=0||rn2.indexOf('确认')>=0)evLevel='E2'}
    if(evLevel==='E1'&&comp>=55)comp+=3;if(evLevel==='E3'&&comp>=55)comp-=2;
    comp=Math.max(0,Math.min(100,comp));
    if(!smoothScores[s.c])smoothScores[s.c]=[];
    smoothScores[s.c].push(comp);if(smoothScores[s.c].length>3)smoothScores[s.c].shift();
    var smoothComp=comp;if(smoothScores[s.c].length>=3){smoothComp=Math.round((smoothScores[s.c][0]+smoothScores[s.c][1]+smoothScores[s.c][2])/3)}
    var sg,sl;if(smoothComp>=75){sg='s-strong';sl='🔥强买入'}else if(smoothComp>=60){sg='s-buy';sl='📈偏买入'}else if(smoothComp>=40){sg='s-hold';sl='➡️观望'}else if(smoothComp>=25){sg='s-sell';sl='⚠️偏卖出'}else{sg='s-warn';sl='🚨强卖出'}
    var env='range';var m20v=calcMA(cl,20);var m60v=calcMA(cl,Math.min(60,cl.length));
    var trendStr=Math.abs(m20v-m60v)/m60v;
    if(trendStr>0.03){env='trend'}else{env='range'}
    var dims=[rsS>=60,maS>=60,vlS>=60,bbS>=60,fundS>=60,env!=='volatile'];
    var agree=dims.filter(function(x){return x}).length;
    var conf=agree>=5?'高置信':agree>=3?'中置信':'低置信';
    var stockTrades=tradeHist.filter(function(t){return t.code===s.c});
    var stockWins=stockTrades.filter(function(t){return t.plPct>0}).length;
    var stockWR=stockTrades.length>=3?(stockWins/stockTrades.length*100).toFixed(0)+'%':'-';
    var techRaw=Math.round(rsS*PARAMS.wRSI_base+maS*PARAMS.wMA_base+vlS*PARAMS.wVol_base+bbS*PARAMS.wBB_base+fundS*PARAMS.wFund_base);
    var q='';if(techRaw>=60&&finScore>=60)q='最佳';else if(techRaw<60&&finScore>=60)q='稳健';else if(techRaw>=60&&finScore<60)q='诱多';else q='回避';
    scores[s.c]={rs:Math.round(rs),m5:Math.round(m5*100)/100,m20:Math.round(m20*100)/100,vr:Math.round(vr*100)/100,comp,sg,sl,tech:techRaw,fin:finScore,flow:fundS,quad:q,env:env,conf:conf,stockWR:stockWR,kelly:15,scRelLevel:'safe',scRelLabel:'ok',scRelReason:'',scTier:null,ev:evLevel,volScale:1,annVol:30};
  }
}
'''

with open(FILE, encoding='utf-8') as f:
    html = f.read()

# 找到 stub 并替换
old_stub = 'function computeScores(){}\n'
html = html.replace(old_stub, new_cs)

with open(FILE, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Rebuilt computeScores: {len(new_cs)} chars")

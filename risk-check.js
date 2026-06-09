// risk-check.js — 自动检测持仓标的风险指标
// 检测项: 未来6月解禁 + 大股东质押比例 + 商誉占比 + 大股东减持
// 输出 risk-data.json → 面板加载
// 用法: node risk-check.js
// 建议每周跑一次，或重大解禁日前跑

var https = require('https'), fs = require('fs');

// ====== 核心持仓（与 allocate.html 同步）======
var CORE_STOCKS = [
  {c:'300136',m:0,n:'信维通信',  eco:'马斯克',tier:'T2星链'},
  {c:'002149',m:0,n:'西部材料',  eco:'马斯克',tier:'T3火箭'},
  {c:'601689',m:1,n:'拓普集团',  eco:'马斯克',tier:'T2特斯拉'},
  {c:'002050',m:0,n:'三花智控',  eco:'马斯克',tier:'T2特斯拉'},
  {c:'603305',m:1,n:'旭升集团',  eco:'马斯克',tier:'T3特斯拉'},
  {c:'688017',m:1,n:'绿的谐波',  eco:'马斯克',tier:'T3 Optimus'},
  {c:'300476',m:0,n:'胜宏科技',  eco:'英伟达',tier:'T2 PCB'},
  {c:'601138',m:1,n:'工业富联',  eco:'英伟达',tier:'T1.5服务器'},
  {c:'300308',m:0,n:'中际旭创',  eco:'英伟达',tier:'T1.5光模块'},
  {c:'300394',m:0,n:'天孚通信',  eco:'英伟达',tier:'T1.5 CPO'},
  {c:'002463',m:0,n:'沪电股份',  eco:'英伟达',tier:'T2 PCB'},
  {c:'600183',m:1,n:'生益科技',  eco:'英伟达',tier:'T3 CCL'},
  {c:'300502',m:0,n:'新易盛',    eco:'英伟达',tier:'T1.5 CPO'},
  {c:'002837',m:0,n:'英维克',    eco:'英伟达',tier:'T1.5液冷'},
  {c:'002851',m:0,n:'麦格米特',  eco:'英伟达',tier:'T1.5电源'},
  {c:'600584',m:1,n:'长电科技',  eco:'英伟达',tier:'T2封测'},
];

// 也可以手动扩展监控列表
var EXTRA = [
  {c:'300433',m:0,n:'蓝思科技'},{c:'688102',m:1,n:'斯瑞新材'},
  {c:'603809',m:1,n:'豪能股份'},{c:'301005',m:0,n:'超捷股份'},
  {c:'688256',m:1,n:'寒武纪'},{c:'002230',m:0,n:'科大讯飞'},
  {c:'300750',m:0,n:'宁德时代'},{c:'002371',m:0,n:'北方华创'},
  {c:'002475',m:0,n:'立讯精密'},{c:'002241',m:0,n:'歌尔股份'},
  {c:'300395',m:0,n:'菲利华'},{c:'300855',m:0,n:'图南股份'},
  {c:'002916',m:0,n:'深南电路'},{c:'002156',m:0,n:'通富微电'},
  {c:'688981',m:1,n:'中芯国际'},{c:'688599',m:1,n:'天合光能'},
  {c:'300274',m:0,n:'阳光电源'},{c:'603986',m:1,n:'兆易创新'},
];

var ALL = CORE_STOCKS.concat(EXTRA.filter(function(ex){
  return !CORE_STOCKS.find(function(c){return c.c===ex.c});
}));

// ====== HTTP 工具 ======
function fetchURL(url, opts){
  opts = opts || {};
  return new Promise(function(ok, no){
    var u = new URL(url);
    var mod = u.protocol==='https:'?https:require('http');
    var rq = {hostname:u.hostname, path:u.pathname+u.search, method:'GET',
      headers:Object.assign({'User-Agent':'Mozilla/5.0','Referer':'https://data.eastmoney.com/'},opts.headers||{})};
    var req = mod.request(rq, function(r){
      var d='';r.on('data',function(c){d+=c});r.on('end',function(){ok(d)});
    });
    req.on('error',function(e){no(e)});
    req.setTimeout(opts.timeout||15000, function(){req.destroy();no(new Error('timeout'))});
    req.end();
  });
}

function sleep(ms){return new Promise(function(r){setTimeout(r,ms)});}

// ====== 1. 解禁日历 ======
// 数据源: 东方财富数据中心 — 限售解禁
async function fetchLockup(code, market){
  var prefix = market===1?'SH':'SZ';
  try{
    var now = new Date();
    var endDate = new Date(now.getTime()+180*86400000); // 未来180天
    var sDate = now.toISOString().slice(0,10).replace(/-/g,'');
    var eDate = endDate.toISOString().slice(0,10).replace(/-/g,'');

    var url = 'https://datacenter.eastmoney.com/securities/api/data/v1/get?'+
      'reportName=RPTA_DISCLOSURE_HOLDER&columns=ALL&'+
      'filter=(SECURITY_CODE="'+code+'")&pageNumber=1&pageSize=20&sortColumns=NOTICE_DATE&sortTypes=-1';
    var body = await fetchURL(url);
    var j = JSON.parse(body);
    if(j && j.result && j.result.data && j.result.data.length>0){
      var items = [];
      j.result.data.forEach(function(d){
        var liftDate = d.LIFT_DATE;
        if(!liftDate) return;
        var dt = new Date(liftDate);
        if(dt < now) return; // 已过期的不显示
        items.push({
          date: liftDate,
          shares: d.LIFT_SHARES,     // 解禁股数
          ratio: d.LIFT_RATIO,        // 解禁占比(%)
          type: d.LIFT_MARKET_TYPE||'', // 解禁类型
          holder: d.HOLDER_NAME||'',    // 解禁股东
        });
      });
      return items;
    }
  }catch(e){}
  return [];
}

// ====== 2. 大股东质押比例 ======
// 数据源: 东方财富个股F10 — 股东研究
async function fetchPledge(code, market){
  var prefix = market===1?'SH':'SZ';
  try{
    // F10 股东研究页面有质押数据
    var url = 'https://emweb.securities.eastmoney.com/PC_HSF10/ShareholderResearch/PageAjax?code='+prefix+code;
    var body = await fetchURL(url);
    var j = JSON.parse(body);
    if(j && j.jjzcDJList && j.jjzcDJList.length>0){
      // 第一大股东质押比例
      var top = j.jjzcDJList[0];
      return {
        topPledgeRatio: parseFloat(top.PLEDGE_RATIO)||0,   // 第一大股东质押比例
        topHolder: top.HOLDER_NAME||'',
        totalPledge: j.totalPledgeRatio||0,   // 总质押比例
      };
    }
  }catch(e){}
  // 备用方案: 用 push2 API
  try{
    var secid = (market===1?'1':'0')+'.'+code;
    var url2 = 'https://push2.eastmoney.com/api/qt/stock/get?secid='+secid+'&fields=f57,f58,f292';
    var body2 = await fetchURL(url2);
    var j2 = JSON.parse(body2);
    if(j2 && j2.data){
      return {
        topPledgeRatio: 0,
        topHolder: '',
        totalPledge: parseFloat(j2.data.f292)||0,
      };
    }
  }catch(e2){}
  return {topPledgeRatio:0,topHolder:'',totalPledge:0};
}

// ====== 3. 商誉占比 ======
// 数据源: 东方财富 F10 财务分析 — 资产负债表
async function fetchGoodwill(code, market){
  var prefix = market===1?'SH':'SZ';
  try{
    var url = 'https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew?type=0&code='+prefix+code;
    var body = await fetchURL(url);
    var j = JSON.parse(body);
    if(j && j.data && j.data.length>0){
      var fd = j.data[0];  // 最新一期
      // 商誉 / 净资产 * 100
      var goodwill = parseFloat(fd.SHANGYU)||0;          // 商誉（万元）
      var netAssets = parseFloat(fd.TOTAL_SHAREHOLDEREQUITY)||1; // 净资产（万元）
      var ratio = netAssets>0 ? (goodwill/netAssets*100) : 0;
      return {
        goodwill: goodwill,
        netAssets: netAssets,
        ratio: parseFloat(ratio.toFixed(2)),
        reportDate: fd.REPORT_DATE||'',
      };
    }
  }catch(e){}
  return {goodwill:0,netAssets:0,ratio:0,reportDate:''};
}

// ====== 4. 大股东减持/增持动态 ======
async function fetchShareholderChange(code, market){
  try{
    var url = 'https://datacenter.eastmoney.com/securities/api/data/v1/get?'+
      'reportName=RPTA_DISCLOSURE_SHAREHOLDER_CHANGE&columns=ALL&'+
      'filter=(SECURITY_CODE="'+code+'")&pageNumber=1&pageSize=5&sortColumns=NOTICE_DATE&sortTypes=-1';
    var body = await fetchURL(url);
    var j = JSON.parse(body);
    if(j && j.result && j.result.data && j.result.data.length>0){
      return j.result.data.map(function(d){
        return {
          date: d.NOTICE_DATE||'',
          holder: d.HOLDER_NAME||'',
          changeType: d.CHANGE_REASON||d.CHANGE_TYPE||'',
          changeAmount: d.CHANGE_NUM||0,     // 变动数量
          changeRatio: d.CHANGE_RATIO||0,     // 变动比例(%)
          afterRatio: d.HOLD_RATIO_AFTER||0,  // 变动后持股比例
          avgPrice: d.AVG_PRICE||0,           // 交易均价
        };
      });
    }
  }catch(e){}
  return [];
}

// ====== 综合风险评估 ======
function calcRisk(lockups, pledge, goodwill, changes){
  var score = 0;
  var alerts = [];

  // 1. 解禁风险（最高40分）
  if(lockups.length>0){
    lockups.forEach(function(l){
      var ratio = parseFloat(l.ratio)||0;
      if(ratio > 20){
        score += 30;
        alerts.push('🔴 近期大额解禁: '+l.date+' ('+ratio+'%流通盘)');
      }else if(ratio > 10){
        score += 20;
        alerts.push('🟡 近期解禁: '+l.date+' ('+ratio+'%流通盘)');
      }else if(ratio > 5){
        score += 10;
        alerts.push('🟢 小额解禁: '+l.date+' ('+ratio+'%流通盘)');
      }
    });
  }

  // 2. 质押风险（最高30分）
  var pledges = pledge.totalPledge||pledge.topPledgeRatio||0;
  if(pledges > 50){
    score += 30;
    alerts.push('🔴 质押比例极高: '+pledges+'%');
  }else if(pledges > 30){
    score += 20;
    alerts.push('🟡 质押比例偏高: '+pledges+'%');
  }else if(pledges > 20){
    score += 10;
    alerts.push('🟢 质押比例中等: '+pledges+'%');
  }

  // 3. 商誉风险（最高20分）
  var gw = goodwill.ratio||0;
  if(gw > 50){
    score += 20;
    alerts.push('🔴 商誉占比极高: '+gw+'%净资产');
  }else if(gw > 30){
    score += 13;
    alerts.push('🟡 商誉占比较高: '+gw+'%净资产');
  }else if(gw > 15){
    score += 7;
    alerts.push('🟢 商誉占比: '+gw+'%净资产');
  }

  // 4. 减持风险（最高10分）
  var hasReduce = changes.filter(function(c){return parseFloat(c.changeRatio)<0});
  if(hasReduce.length>0){
    score += 10;
    hasReduce.forEach(function(c){
      alerts.push('⚠️ 减持: '+c.holder+' ('+c.date+', '+Math.abs(c.changeRatio)+'%)');
    });
  }

  // 风险等级
  var level, color;
  if(score >= 50){ level='极高'; color='#ef4444'; }
  else if(score >= 30){ level='高'; color='#f97316'; }
  else if(score >= 15){ level='中'; color='#eab308'; }
  else{ level='低'; color='#22c55e'; }

  return {score:Math.min(100,score), level:level, color:color, alerts:alerts};
}

// ====== 主程序 ======
async function run(){
  console.log('🔍 风险检测开始...');
  console.log('检测项目: 解禁日历 | 大股东质押 | 商誉占比 | 股东增减持\n');

  var results = {};
  var total = ALL.length, done = 0;

  for(var i=0;i<ALL.length;i++){
    var s = ALL[i];
    var name = s.n+' ('+s.c+')';
    process.stdout.write('  ['+(done+1)+'/'+total+'] '+name+'... ');

    try{
      var [lockups, pledge, goodwill, changes] = await Promise.all([
        fetchLockup(s.c, s.m),
        fetchPledge(s.c, s.m),
        fetchGoodwill(s.c, s.m),
        fetchShareholderChange(s.c, s.m),
      ]);

      var risk = calcRisk(lockups, pledge, goodwill, changes);

      results[s.c] = {
        n: s.n,
        c: s.c,
        m: s.m,
        eco: s.eco||'',
        tier: s.tier||'',
        risk: risk,
        lockups: lockups,
        pledge: pledge,
        goodwill: goodwill,
        changes: changes.slice(0,3), // 只保留最近3条
        checkedAt: new Date().toISOString(),
      };

      var icon = risk.level==='低'?'✅':risk.level==='中'?'🟡':risk.level==='高'?'🟠':'🔴';
      console.log(icon+' '+risk.level+'('+risk.score+'分) '+
        (lockups.length>0?'解禁'+lockups.length+'批 ':'')+
        (pledge.totalPledge>0?'质押'+pledge.totalPledge+'% ':'')+
        (goodwill.ratio>5?'商誉'+goodwill.ratio+'%':''));
      if(risk.alerts.length>0) risk.alerts.forEach(function(a){console.log('     '+a)});

      done++;
    }catch(e){
      console.log('❌ '+e.message);
      results[s.c] = {n:s.n,c:s.c,m:s.m,error:e.message};
      done++;
    }

    // 控制频率，避免被封
    if(i%5===4) await sleep(500);
  }

  // 按风险分降序排列
  var sorted = Object.values(results).sort(function(a,b){
    return (b.risk?b.risk.score:0) - (a.risk?a.risk.score:0);
  });

  // 写结果
  fs.writeFileSync(__dirname+'/risk-data.json', JSON.stringify({
    updated: new Date().toISOString(),
    summary: {
      critical: sorted.filter(function(s){return s.risk&&s.risk.level==='极高'}).length,
      high: sorted.filter(function(s){return s.risk&&s.risk.level==='高'}).length,
      medium: sorted.filter(function(s){return s.risk&&s.risk.level==='中'}).length,
      low: sorted.filter(function(s){return s.risk&&s.risk.level==='低'}).length,
    },
    stocks: sorted,
  }, null, 2));

  // 汇总
  var summary = {};
  summary.critical = sorted.filter(function(s){return s.risk&&s.risk.level==='极高'}).length;
  summary.high = sorted.filter(function(s){return s.risk&&s.risk.level==='高'}).length;
  summary.medium = sorted.filter(function(s){return s.risk&&s.risk.level==='中'}).length;
  summary.low = sorted.filter(function(s){return s.risk&&s.risk.level==='低'}).length;

  console.log('\n═══════════════════════════════════');
  console.log('📊 风险汇总');
  console.log('   🔴 极高风险: '+summary.critical+' 只');
  console.log('   🟠 高风险:   '+summary.high+' 只');
  console.log('   🟡 中风险:   '+summary.medium+' 只');
  console.log('   🟢 低风险:   '+summary.low+' 只');
  console.log('═══════════════════════════════════');
  console.log('\n⚠️  高风险标的:');
  sorted.filter(function(s){return s.risk&&(s.risk.level==='极高'||s.risk.level==='高')}).forEach(function(s){
    console.log('  '+s.n+' ('+s.c+') — '+s.risk.level+'风险 '+s.risk.score+'分');
    s.risk.alerts.forEach(function(a){console.log('    '+a)});
  });
  console.log('\n✅ 结果已保存到 risk-data.json');
}

run().catch(function(e){console.error('执行失败: '+e.message)});

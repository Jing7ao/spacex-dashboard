var fs = require('fs');
var l = fs.readFileSync(__dirname + '/_check.js', 'utf8').split('\n');
var deps = 'const P=1;\n';
deps += 'var prices={},kline={},scores={},supplyMeta={},cur="musk",tradeHist=[];\n';
deps += 'var smoothScores={},apiErrors={},icMult={},_nbData={},volHealth={},pos=[],budget=2000;\n';
deps += 'var PARAMS={wRSI_base:1,wMA_base:1,wVol_base:1,wBB_base:1,wFund_base:1,wFin:1,coolDays:30,flowPersistCap:65,flowReverseCap:35,peWarn:200,criticalPenalty:15,criticalCap:40,highPenalty:5,buyThreshold:75,holdThreshold:60,sellThreshold:40,warnThreshold:25,weeklyDivDiscount:0.88,volatileDiscount:0.85,envTrendMA:0.03,envVolAnnual:8,envVolExtreme:3,envVolShrink:0.3,etfWeakDiscount:0.88};\n';
deps += 'function parseSupplyChain(r){return{level:"safe"};}\n';
deps += 'function getSupplyReliability(x){return{level:"safe",factor:1,label:"ok",reason:""};}\n';
deps += 'function calcMA(a,n){return a[0];}\n';
deps += 'function calcRSI(a){return 50;}\n';
deps += 'function applyUSLinkage(a,b,c){return b;}\n';
deps += 'var window={_finData:{}};\n';

var cs = l.slice(410, 528).join('\n');
var test = deps + cs;
try {
    new Function(test);
    console.log('computeScores: OK');
} catch(e) {
    console.log('computeScores: FAIL -', e.message.slice(0, 120));
}

var fs = require('fs');
var l = fs.readFileSync(__dirname + '/_check.js', 'utf8').split('\n');
var deps = 'const P=1;var prices={},kline={},scores={},supplyMeta={},cur="musk",tradeHist=[],smoothScores={},apiErrors={},icMult={},_nbData={},volHealth={},pos=[],PARAMS={wRSI_base:1,wMA_base:1,wVol_base:1,wBB_base:1,wFund_base:1,wFin:1,coolDays:30,flowPersistCap:65,flowReverseCap:35,peWarn:200,criticalPenalty:15,criticalCap:40,highPenalty:5,buyThreshold:75,holdThreshold:60,sellThreshold:40,warnThreshold:25,weeklyDivDiscount:0.88,volatileDiscount:0.85,envTrendMA:0.03,envVolAnnual:8,envVolExtreme:3,envVolShrink:0.3,etfWeakDiscount:0.88};function parseSupplyChain(r){return{level:"safe"}};function getSupplyReliability(x){return{level:"safe",factor:1,label:"ok",reason:""}};function calcMA(a,n){return a[0]};function calcRSI(a){return 50};function applyUSLinkage(a,b,c){return b};var window={_finData:{}};\n';

var inner = l.slice(411, 528); // computeScores body only (without the opening {)
// Line 0 of inner = first line after 'function computeScores(){'

console.log('Testing computeScores body incrementally...');
for (var n = 5; n <= inner.length; n += 5) {
    var test = deps + 'function test(){' + inner.slice(0, n).join('\n') + '\n}';
    try {
        new Function(test);
        if (n + 5 > inner.length) console.log('  All OK up to line', 411+n);
    } catch(e) {
        console.log('  FAIL at inner line', n, '(orig line', 411+n, '):', e.message.slice(0,80));
        console.log('  Content:', (inner[n-1] || '').slice(0, 120));
        break;
    }
}

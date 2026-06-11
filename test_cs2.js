var fs = require('fs');
var html = fs.readFileSync(__dirname + '/monitor.html', 'utf8');

// Extract computeScores from HTML directly (not from _check.js)
var start = html.indexOf('function computeScores(){');
var end = start;
var depth = 1;
for (var i = start + 26; i < html.length && depth > 0; i++) {
    if (html[i] === '{') depth++;
    if (html[i] === '}') depth--;
    if (depth === 0) end = i;
}
var cs = html.slice(start, end + 1);
console.log('computeScores length:', cs.length, 'chars');

// Test it
var deps = 'const P=1;var prices={},kline={},scores={},supplyMeta={},cur="musk",tradeHist=[],smoothScores={},apiErrors={},icMult={},_nbData={},volHealth={},pos=[],PARAMS={wRSI_base:1,wMA_base:1,wVol_base:1,wBB_base:1,wFund_base:1,wFin:1,coolDays:30,flowPersistCap:65,flowReverseCap:35,peWarn:200,criticalPenalty:15,criticalCap:40,highPenalty:5};function parseSupplyChain(r){return{level:"safe"}};function getSupplyReliability(x){return{level:"safe",factor:1}};function calcMA(a,n){return a[0]};function calcRSI(a){return 50};function applyUSLinkage(a,b,c){return b};\n';

try {
    new Function(deps + cs);
    console.log('computeScores from HTML: OK');
} catch(e) {
    console.log('FAIL:', e.message.slice(0, 100));
    // Find exact position
    var lines = cs.split('\n');
    for (var n = 1; n <= lines.length; n++) {
        try {
            new Function(deps + 'function test_(){' + lines.slice(0, n).join('\n') + '\n}');
        } catch(e2) {
            if (n > 1) {
                console.log('Error introduced at line', n, ':', lines[n-1].slice(0, 120));
                console.log('Prev line:', (lines[n-2] || '').slice(0, 120));
            }
            break;
        }
    }
}

var fs = require('fs');
var lines = fs.readFileSync(__dirname + '/_check.js', 'utf8').split('\n');

// Find computeScores
var start = -1, end = -1, depth = 0;
for (var i = 0; i < lines.length; i++) {
    if (start < 0 && lines[i].indexOf('function computeScores(){') >= 0) {
        start = i; depth = 1; continue;
    }
    if (start >= 0) {
        var opens = (lines[i].match(/{/g) || []).length;
        var closes = (lines[i].match(/}/g) || []).length;
        depth += opens - closes;
        if (depth === 0) { end = i; break; }
    }
}
if (start < 0) { console.log('computeScores not found'); process.exit(1); }
console.log('computeScores: line', start+1, 'to', end+1, '(' + (end-start+1) + ' lines)');

var body = lines.slice(start, end+1).join('\n');
var deps = 'const P="http://localhost:8080";\nvar prices={},kline={},scores={},supplyMeta={},cur="musk",tradeHist=[],smoothScores={},apiErrors={},icMult={},_nbData={},volHealth={},pos=[],budget=2000;\n';

// Test incrementally
var inner = lines.slice(start, end+1);
for (var n = 5; n <= inner.length; n += 10) {
    var test = deps + inner.slice(0, n).join('\n') + '\n}'; // close function
    try { new Function(test); } catch(e) {
        console.log('Fails at inner line', n, '(line', start+n, '):', e.message.slice(0, 80));
        console.log('Content:', inner[n-1].slice(0, 120));
        break;
    }
    if (n + 10 > inner.length) console.log('All inner lines OK');
}

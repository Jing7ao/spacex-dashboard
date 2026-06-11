var fs = require('fs');
var js = fs.readFileSync(__dirname + '/_check.js', 'utf8');

// Find the line with the bad ')'
var n = js.length;
// Binary search on character position — remove from position X to end
var lo = 0, hi = n;
while (hi - lo > 5) {
    var mid = Math.floor((lo + hi) / 2);
    try { new Function(js.slice(0, mid)); lo = mid; }
    catch(e) { hi = mid; }
}
// Show context around the error
var ctx = js.slice(Math.max(0, hi-100), Math.min(n, hi+20));
var lineNum = js.slice(0, hi).split('\n').length;
console.log('Error around char', hi, '(line', lineNum, ')');
console.log('Context:', ctx.slice(-120));

// find_bug.js — 逐块加载JS，定位确切错误行
var fs = require('fs');
var js = fs.readFileSync(__dirname + '/_check.js', 'utf8');
var lines = js.split('\n');

// 从后往前删，找到打破语法的那一行
var lo = 0, hi = lines.length;
while (hi > lo + 1) {
    var mid = Math.floor((lo + hi) / 2);
    var test = lines.slice(0, mid).join('\n');
    try {
        new Function(test);
        lo = mid;  // OK, error is after mid
    } catch(e) {
        hi = mid;  // error is at or before mid
    }
}
console.log('Error introduced between line', lo, 'and', hi);
console.log('Line', lo, ':', (lines[lo-1] || '').slice(0, 150));
console.log('Line', hi, ':', (lines[hi-1] || '').slice(0, 150));
if (hi < lines.length) console.log('Line', hi+1, ':', (lines[hi] || '').slice(0, 150));

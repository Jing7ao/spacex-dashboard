// find_block.js — 从文件末尾删代码，定位错误块
var fs = require('fs');
var lines = fs.readFileSync(__dirname + '/_check.js', 'utf8').split('\n');

// Remove lines from the end until it parses
var n = lines.length;
while (n > 0) {
    var test = lines.slice(0, n).join('\n');
    try {
        new Function(test);
        // It parsed! Error is AFTER line n
        console.log('Parses OK with', n, 'lines');
        console.log('Next line (first failing):', (lines[n] || '(empty)').slice(0, 150));
        console.log('Line after:', (lines[n+1] || '(empty)').slice(0, 150));
        break;
    } catch(e) {
        n--;
    }
}
if (n === 0) console.log('Even empty file fails? Something fundamental is wrong.');

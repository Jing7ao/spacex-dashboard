// find_break.js — 找到第一个成功解析的行数
var fs = require('fs');
var lines = fs.readFileSync(__dirname + '/_check.js', 'utf8').split('\n');

// Jump by 100 lines at a time
var n = 400;
var found = false;
while (n <= lines.length && !found) {
    var test = lines.slice(0, n).join('\n');
    try {
        new Function(test);
        if (!found) {
            console.log('First success at', n, 'lines');
            found = true;
        }
    } catch(e) {}
    n += 100;
}
if (!found) {
    // Try the full file
    try {
        new Function(lines.join('\n'));
        console.log('Full file parses OK');
    } catch(e) {
        console.log('Full file still fails:', e.message.slice(0,100));
    }
}

// check_syntax.js — 深度JS语法检查
var fs = require('fs');
var vm = require('vm');
var js = fs.readFileSync(__dirname + '/_check.js', 'utf8');

try {
    new vm.Script(js, { filename: 'monitor.html' });
    console.log('OK - No syntax errors');
} catch (e) {
    console.log('Error:', e.message);
    if (e.stack) {
        var match = e.stack.match(/monitor\.html:(\d+)/);
        if (match) {
            var line = parseInt(match[1]);
            var lines = js.split('\n');
            console.log('At line', line, ':');
            if (line > 0) console.log('  ' + (lines[line-1] || '(empty)').slice(0, 120));
            if (line > 1) console.log('  prev: ' + (lines[line-2] || '(empty)').slice(0, 120));
            if (line < lines.length) console.log('  next: ' + (lines[line] || '(empty)').slice(0, 120));
        }
    }
}

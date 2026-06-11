// find_tpl.js — 检查模板字符串是否闭合
var fs = require('fs');
var js = fs.readFileSync(__dirname + '/_check.js', 'utf8');
var lines = js.split('\n');
var inTemplate = false;
var tplStart = -1;

for (var i = 0; i < lines.length; i++) {
    var line = lines[i];
    for (var j = 0; j < line.length; j++) {
        var ch = line[j];
        var prev = j > 0 ? line[j-1] : '';
        // Skip escaped backticks
        if (ch === '`' && prev !== '\\') {
            if (!inTemplate) {
                inTemplate = true;
                tplStart = i + 1;
            } else {
                inTemplate = false;
                tplStart = -1;
            }
        }
    }
}
if (inTemplate) {
    console.log('UNCLOSED template literal starting at line', tplStart);
} else {
    console.log('All template literals closed');
}

// Also check for odd backtick count
var backtickCount = (js.match(/`/g) || []).length;
console.log('Backtick count:', backtickCount, 'even:', backtickCount % 2 === 0);

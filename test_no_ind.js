var fs = require('fs');
var lines = fs.readFileSync(__dirname + '/_check.js', 'utf8').split('\n');

// Find INDUSTRIES object boundaries (line 5 to ~line 340)
var start = -1, end = -1, depth = 0;
for (var i = 0; i < lines.length; i++) {
    if (lines[i].indexOf('const INDUSTRIES={') >= 0) { start = i; depth = 1; continue; }
    if (start >= 0) {
        for (var j = 0; j < lines[i].length; j++) {
            if (lines[i][j] === '{') depth++;
            if (lines[i][j] === '}') depth--;
        }
        if (depth === 0) { end = i; break; }
    }
}
console.log('INDUSTRIES from line', start+1, 'to', end+1);

// Replace INDUSTRIES with empty object
var repl = lines.slice(0, start).concat(['const INDUSTRIES={};'], lines.slice(end+1));
var test = repl.join('\n');
try {
    new Function(test);
    console.log('WITHOUT INDUSTRIES: OK!');
    // The error IS in the INDUSTRIES definition!
    // Now narrow down within INDUSTRIES
    var indLines = lines.slice(start, end+1);
    console.log('INDUSTRIES has', indLines.length, 'lines');
    // Check braces within INDUSTRIES
    var b = 0;
    for (var i = 0; i < indLines.length; i++) {
        for (var j = 0; j < indLines[i].length; j++) {
            if (indLines[i][j] === '{') b++;
            if (indLines[i][j] === '}') b--;
        }
        if (b < 0) {
            console.log('Extra } at INDUSTRIES line', start+i+1, ':', indLines[i].slice(0, 120));
            break;
        }
    }
    console.log('INDUSTRIES final braces:', b);
} catch(e) {
    console.log('WITHOUT INDUSTRIES still fails:', e.message.slice(0, 100));
}

// acorn_check.js — 用acorn精确解析
var fs = require('fs');
var js = fs.readFileSync(__dirname + '/_check.js', 'utf8');

try {
    var acorn = require('acorn');
    var ast = acorn.parse(js, {ecmaVersion: 2020, locations: true});
    console.log('OK - parsed successfully,', Object.keys(ast).length, 'top-level keys');
} catch(e) {
    console.log('Error:', e.message);
    if (e.loc) {
        console.log('At line', e.loc.line, 'column', e.loc.column);
        var lines = js.split('\n');
        var ln = e.loc.line;
        if (ln > 0 && ln <= lines.length) {
            console.log('Line:', lines[ln-1].slice(0, 200));
            console.log('Pos:', lines[ln-1].slice(Math.max(0,e.loc.column-10), e.loc.column+10));
        }
    }
}

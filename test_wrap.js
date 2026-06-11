var fs = require('fs');
var js = fs.readFileSync(__dirname + '/_check.js', 'utf8');
var wrapped = '(function(){\n' + js + '\n})();';
try {
    new Function(wrapped);
    console.log('WRAPPED OK');
} catch(e) {
    console.log('WRAPPED Error:', e.message.slice(0, 100));
}
try {
    new Function(js);
    console.log('RAW Error: OK');
} catch(e) {
    console.log('RAW Error:', e.message.slice(0, 100));
}

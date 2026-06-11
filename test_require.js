// test_require.js
try {
    var m = require(__dirname + '/_check.js');
    console.log('OK - required successfully');
} catch(e) {
    console.log('Error:', e.message.slice(0, 200));
    if (e.stack) {
        var match = e.stack.match(/<anonymous>:(\d+):(\d+)/);
        if (match) console.log('Line', match[1], 'Col', match[2]);
    }
}

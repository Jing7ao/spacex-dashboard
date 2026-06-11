// split_test.js — 将JS按函数/数据块拆分，逐块定位错误
var fs = require('fs');
var js = fs.readFileSync(__dirname + '/_check.js', 'utf8');
var lines = js.split('\n');

// Find major block boundaries
var blocks = [];
var depth = 0, blockStart = 0;
for (var i = 0; i < lines.length; i++) {
    var line = lines[i];
    for (var j = 0; j < line.length; j++) {
        if (line[j] === '{') depth++;
        if (line[j] === '}') depth--;
    }
    // Block end: depth returns to 0
    if (depth === 0 && i > blockStart + 2 && line.trim().length > 0) {
        var title = lines[blockStart].trim().slice(0, 60);
        blocks.push({start: blockStart, end: i, title: title});
        blockStart = i+1;
    }
}

console.log('Found', blocks.length, 'blocks (depth=0 boundaries)');
console.log('Testing each block + INDUSTRIES header...');

// Test: INDUSTRIES header (lines 0-5) + each block individually
var header = lines.slice(0, 5).join('\n');  // First 5 lines (P + INDUSTRIES={)

for (var b = 0; b < Math.min(blocks.length, 30); b++) {
    var blk = blocks[b];
    var test = header + '\n' + lines.slice(blk.start, blk.end+1).join('\n');
    // Close the INDUSTRIES object if needed
    test += '\n};';  // Close the object that header opened
    try {
        new Function(test);
        // OK — this block is fine
    } catch(e) {
        console.log('BLOCK', b, '(line', blk.start+1, '-', blk.end+1, '):', e.message.slice(0, 80));
        console.log('  Title:', blk.title);
        // Print the block
        var blockText = lines.slice(blk.start, blk.end+1).join('\n');
        if (blockText.length > 300) blockText = blockText.slice(0, 150) + '...' + blockText.slice(-150);
        console.log('  Content:', blockText.slice(0, 200));
    }
}

// Also test: just header + }; alone
try {
    new Function(header + '\n};');
    console.log('Header alone: OK');
} catch(e) {
    console.log('Header alone fails:', e.message);
}

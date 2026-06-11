// count_braces.js
var fs = require('fs');
var lines = fs.readFileSync(__dirname + '/_check.js', 'utf8').split('\n');
var braces = 0, lineNum = 0;
for (var i = 0; i < lines.length; i++) {
  var line = lines[i];
  for (var j = 0; j < line.length; j++) {
    if (line[j] === '{') braces++;
    if (line[j] === '}') braces--;
  }
  if (braces < 0) {
    console.log('Extra } at line', i+1, ':', line.slice(0, 120));
    break;
  }
}
if (braces >= 0) console.log('No extra }. Final braces:', braces);
console.log('Lines:', lines.length);

// Also check for negative-depth regions
var depth = 0;
for (var i = 0; i < lines.length; i++) {
  for (var j = 0; j < lines[i].length; j++) {
    if (lines[i][j] === '{') depth++;
    if (lines[i][j] === '}') depth--;
    if (depth < 0) {
      console.log('Depth negative at line', i+1, 'col', j);
      console.log('Context:', lines[i].slice(Math.max(0,j-30), j+30));
      process.exit(0);
    }
  }
}
console.log('Depth never negative, final:', depth);

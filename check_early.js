// Quick check
var fs=require('fs');
var js=fs.readFileSync(__dirname+'/_check.js','utf8');
var lines=js.split('\n');
for(var n of [5,10,20,30,40,50,60,70,80,90,100]){
  var test=lines.slice(0,n).join('\n');
  var ok=true;
  try{new Function(test)}catch(e){ok=false;console.log('FAIL line',n,':',e.message.slice(0,100))}
  if(!ok)break;
}

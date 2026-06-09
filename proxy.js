var http=require('http'),https=require('https'),fs=require('fs'),path=require('path'),cp=require('child_process');
var PORT=8080,DIR=__dirname;
var CLASH='127.0.0.1',CLASH_PORT=7890;

var MIME={'.html':'text/html;charset=utf-8','.js':'application/javascript','.css':'text/css','.json':'application/json','.md':'text/plain;charset=utf-8','.txt':'text/plain;charset=utf-8'};

// 微信测试号配置
var WX_APPID='wx12638a290906c4f8',WX_SECRET='7d279ce476833e772ade01f78b1d5545';
var WX_OPENID='oRCv22_Olctg1XCsnbkcMf13g0J0',WX_TMPL='86N8AMxv4LofYGEMApnE2RjNuqQ3ZmO82rjiRovbkLE';
var wxToken='',wxTokenExp=0;

function getWxToken(cb){
  if(wxToken&&Date.now()<wxTokenExp){cb(wxToken);return}
  var opts={hostname:'api.weixin.qq.com',port:443,path:'/cgi-bin/token?grant_type=client_credential&appid='+WX_APPID+'&secret='+WX_SECRET,method:'GET',timeout:10000};
  var req=https.request(opts,function(res){var body='';res.on('data',function(d){body+=d});res.on('end',function(){
    try{var j=JSON.parse(body);wxToken=j.access_token;wxTokenExp=Date.now()+(j.expires_in-300)*1000;cb(wxToken)}catch(e){console.log('WX token err:'+body);cb(null)}
  })});
  req.on('error',function(){cb(null)});req.end();
}

function sendWxMsg(title,content,cb){
  getWxToken(function(tk){
    if(!tk){cb('no token');return}
    var timeStr=new Date().toLocaleTimeString('zh-CN',{hour12:false});
    var body=JSON.stringify({touser:WX_OPENID,template_id:WX_TMPL,data:{first:{value:'量化信号',color:'#1a1a1a'},keyword1:{value:title,color:'#173177'},keyword2:{value:content.replace(/<[^>]+>/g,''),color:'#333'},keyword3:{value:timeStr,color:'#999'},remark:{value:'点击查看详情',color:'#666'}}});
    var opts={hostname:'api.weixin.qq.com',port:443,path:'/cgi-bin/message/template/send?access_token='+tk,method:'POST',timeout:10000,headers:{'Content-Type':'application/json'}};
    var req=https.request(opts,function(res){var body='';res.on('data',function(d){body+=d});res.on('end',function(){console.log('WX send:'+body.slice(0,100));cb(null,body)})});
    req.on('error',function(e){cb(e.message)});req.end(body);
  });
}

function getBaiduToken(cb){
  if(baiduToken&&Date.now()<baiduTokenExp){cb(baiduToken);return}
  var opts={hostname:'aip.baidubce.com',port:443,path:'/oauth/2.0/token?grant_type=client_credentials&client_id='+BAIDU_KEY+'&client_secret='+BAIDU_SECRET,method:'POST',timeout:10000};
  var req=https.request(opts,function(res){var body='';res.on('data',function(d){body+=d});res.on('end',function(){
    try{var j=JSON.parse(body);baiduToken=j.access_token;baiduTokenExp=Date.now()+(j.expires_in-300)*1000;cb(baiduToken)}catch(e){cb(null)}
  })});
  req.on('error',function(){cb(null)});req.end();
}

var ROUTES=[
  {p:'/api/txk',h:'web.ifzq.gtimg.cn',port:443,ssl:true,rew:function(x){return'/appstock/app/fqkline/get'+x.replace('/api/txk','')}},
  {p:'/api/min',h:'ifzq.gtimg.cn',port:443,ssl:true,rew:function(x){return'/appstock/app/minute/query'+x.replace('/api/min','')}},
  {p:'/api/emf',h:'push2.eastmoney.com',port:80,ssl:false,rew:function(x){return'/api'+x.replace('/api/emf','')}},
  {p:'/api/emfin',h:'emweb.securities.eastmoney.com',port:80,ssl:false,rew:function(x){return'/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew'+x.replace('/api/emfin','')}},
  {p:'/api/em',h:'push2.eastmoney.com',port:80,ssl:false,rew:function(x){return'/api'+x.replace('/api/em','')}},
  {p:'/api/news',h:'searchapi.eastmoney.com',port:80,ssl:false,rew:function(x){return'/bussiness/Web'+x.replace('/api/news','')}},
  {p:'/api/yh',h:'query1.finance.yahoo.com',port:443,ssl:true,rew:function(x){return'/v8/finance'+x.replace('/api/yh','')}},
  {p:'/api/sina',h:'money.finance.sina.com.cn',port:443,ssl:true,rew:function(x){return'/quotes_service/api/json_v2.php'+x.replace('/api/sina','')}},
  {p:'/api/nlp',nlp:true},
  {p:'/api/snews',h:'feed.mix.sina.com.cn',port:443,ssl:true,rew:function(x){return'/api/roll/get'+x.replace('/api/snews','')}},
  {p:'/api/ai',ai:true},
  {p:'/api/notify',notify:true},
  {p:'/api/risk',risk:true},
];

var clashOn=false;

function proxy(route,target,req,res){
  if(clashOn&&route.ssl){
    // HTTPS via Clash CONNECT tunnel
    var opts={host:CLASH,port:CLASH_PORT,method:'CONNECT',path:route.h+':443',timeout:15000};
    var cr=http.request(opts);
    cr.on('connect',function(_,socket){
      var opts2={socket:socket,hostname:route.h,port:443,path:target,method:'GET',timeout:15000,agent:false,headers:{'User-Agent':'Mozilla/5.0'}};
      var pr=https.request(opts2,function(prRes){
        var hd={};for(var k in prRes.headers)hd[k]=prRes.headers[k];
        hd['access-control-allow-origin']='*';hd['cache-control']='no-cache';
        res.writeHead(prRes.statusCode,hd);prRes.pipe(res);
      });
      pr.on('error',function(e){if(!res.headersSent){res.writeHead(502);res.end('err: '+e.message)}});
      pr.end();
    });
    cr.on('error',function(e){if(!res.headersSent){res.writeHead(502);res.end('clash err:'+e.message)}});
    cr.on('timeout',function(){cr.destroy();if(!res.headersSent){res.writeHead(504);res.end('timeout')}});
    cr.end();
    return;
  }
  // Direct or HTTP proxy
  var mod=route.ssl?https:http;
  var opts={hostname:clashOn?CLASH:route.h,port:clashOn?CLASH_PORT:route.port,path:clashOn&&route.ssl?('https://'+route.h+target):target,method:'GET',timeout:15000,headers:{'User-Agent':'Mozilla/5.0','Referer':'https://'+route.h+'/','Host':route.h}};
  var pr=mod.request(opts,function(prRes){
    var hd={};for(var k in prRes.headers)hd[k]=prRes.headers[k];
    hd['access-control-allow-origin']='*';hd['cache-control']='no-cache';
    res.writeHead(prRes.statusCode,hd);prRes.pipe(res);
  });
  pr.on('error',function(e){if(!res.headersSent){res.writeHead(502);res.end('err: '+e.message)}});
  pr.on('timeout',function(){pr.destroy();if(!res.headersSent){res.writeHead(504);res.end('timeout')}});
  pr.end();
}

// Check if Clash is running
function checkClash(cb){
  var r=http.get({hostname:CLASH,port:CLASH_PORT,path:'/',timeout:3000},function(res){
    clashOn=res.statusCode<500;cb();
  });
  r.on('error',function(){clashOn=false;cb()});
  r.on('timeout',function(){r.destroy();clashOn=false;cb()});
}

checkClash(function(){
  http.createServer(function(req,res){
    if(req.method==='OPTIONS'){res.writeHead(200,{'Access-Control-Allow-Origin':'*','Access-Control-Allow-Methods':'GET,POST,OPTIONS','Access-Control-Allow-Headers':'Content-Type,Authorization'});res.end();return}
    var u=new URL(req.url,'http://localhost');var pn=u.pathname;
    for(var i=0;i<ROUTES.length;i++){
      if(ROUTES[i].nlp&&pn==='/api/nlp'){
        var body='';req.on('data',function(d){body+=d});req.on('end',function(){
          getBaiduToken(function(token){
            if(!token){res.writeHead(502);res.end('{"error":"token"}');return}
            var q='?charset=UTF-8&access_token='+token;var o2={hostname:'aip.baidubce.com',port:443,path:'/rpc/2.0/nlp/v1/sentiment_classify'+q,method:'POST',timeout:15000,headers:{'Content-Type':'application/json'}};
            var p2=https.request(o2,function(r2){var b2='';r2.on('data',function(d){b2+=d});r2.on('end',function(){res.writeHead(200,{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'});res.end(b2)})});
            p2.on('error',function(e){res.writeHead(502);res.end('{"error":"'+e.message+'"}')});p2.end(JSON.stringify({text:body}));
          });
        });return;
      }
      if(ROUTES[i].sent&&pn==='/api/sentiment'){
        var txt=u.searchParams.get('text')||'';if(!txt){res.writeHead(400);res.end('{"error":"no text"}');return}
        cp.exec('py -3.12 "'+DIR+'/sentiment.py" "'+txt.replace(/"/g,'\\"')+'"',{timeout:10000},function(err,stdout){
          if(err){res.writeHead(500);res.end('{"error":"'+err.message+'"}');return}
          res.writeHead(200,{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'});res.end(stdout.trim()||'{}');
        });return;
      }
      if(pn.startsWith(ROUTES[i].p)&&!ROUTES[i].ai&&!ROUTES[i].sent&&!ROUTES[i].notify&&!ROUTES[i].risk&&!ROUTES[i].nlp){
        var target=ROUTES[i].rew(pn)+u.search;
        proxy(ROUTES[i],target,req,res);return;
      }
      if(ROUTES[i].ai&&pn==='/api/ai'){
        var body='';req.on('data',function(d){body+=d});req.on('end',function(){
var gmKey='AQ.Ab8RN6JLMu7tWvnymIs0eh8inYGMbMGQR4eT6JMuH3sUM8XUow';
          var gmUrl='/v1beta/models/gemini-2.0-flash:generateContent?key='+encodeURIComponent(gmKey);
          var opts2={hostname:'generativelanguage.googleapis.com',port:443,path:gmUrl,method:'POST',timeout:30000,headers:{'Content-Type':'application/json'}};
          try{var msg=JSON.parse(body);body=JSON.stringify({contents:[{parts:[{text:msg.messages[0].content}]}]})}catch(e){};
          var p2=https.request(opts2,function(r2){var b2='';r2.on('data',function(d){b2+=d});r2.on('end',function(){console.log('AI status:'+r2.statusCode+' body:'+b2.slice(0,200));res.writeHead(r2.statusCode,{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'});res.end(b2)})});
          p2.on('error',function(e){console.log('AI err:'+e.message);res.writeHead(502);res.end('{"error":"'+e.message+'"}')});p2.end(body);
        });return;
      }
      if(ROUTES[i].notify&&pn==='/api/notify'){
        if(req.method==='GET'){
          sendWxMsg('✅ 量化系统已就绪','代理服务器重启成功，微信推送通道正常。生态轮动/买入信号/回撤预警将自动推送。',function(err,result){
            res.writeHead(200,{'Content-Type':'text/html;charset=utf-8','Access-Control-Allow-Origin':'*'});
            res.end(err?'<h1>❌ 推送失败</h1><pre>'+err+'</pre>':'<h1>✅ 测试消息已发送</h1><p>检查微信是否收到「量化系统已就绪」</p><pre>'+result+'</pre>');
          });return;
        }
        var body='';req.on('data',function(d){body+=d});req.on('end',function(){
          try{
            var n=JSON.parse(body);
            sendWxMsg(n.title||'量化信号',n.content||'',function(err,result){
              if(err){res.writeHead(502);res.end('{"error":"'+err+'"}');return}
              res.writeHead(200,{'Content-Type':'application/json','Access-Control-Allow-Origin':'*'});res.end(result||'{"ok":1}');
            });
          }catch(e){res.writeHead(400);res.end('{"error":"parse error"}')}
        });return;
      }
      if(ROUTES[i].risk&&pn==="/api/risk"){
        var rf=path.join(DIR,"risk-data.json");
        try{
          var rd=JSON.parse(fs.readFileSync(rf,"utf8"));
          var age=Date.now()-new Date(rd.updated).getTime();
          if(age>21600000) cp.spawn("node",["risk-check.js"],{cwd:DIR});
          res.writeHead(200,{"Content-Type":"application/json","Access-Control-Allow-Origin":"*"});
          res.end(JSON.stringify(rd));
        }catch(e){
          cp.spawn("node",["risk-check.js"],{cwd:DIR});
          res.writeHead(200,{"Content-Type":"application/json","Access-Control-Allow-Origin":"*"});
          res.end(JSON.stringify({status:"generating",updated:new Date().toISOString(),stocks:[]}));
        }
        return;
      }
    }
    var fp=pn==='/'?'/index.html':pn;fp=path.join(DIR,fp);
    if(fp.indexOf(DIR)!==0){res.writeHead(403);res.end();return}
    fs.readFile(fp,function(err,data){
      if(err){res.writeHead(404);res.end('404');return}
      res.writeHead(200,{'Content-Type':MIME[path.extname(fp)]||'text/plain','Access-Control-Allow-Origin':'*'});
      res.end(data);
    });
  }).listen(PORT,function(){
    console.log('Clash VPN: '+(clashOn?'ON':'OFF'));
    console.log('Proxy: http://localhost:'+PORT);
  });
});

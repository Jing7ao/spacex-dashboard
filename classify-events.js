// classify-events.js — 用 DeepSeek API 过滤公告扫描中的噪声
// 替代纯关键词匹配，减少修路/盖楼/停车等误报
// 用法: node classify-events.js [--dry-run]
//   --dry-run: 只打印分类结果，不写入 events.json

var fs=require('fs'),https=require('https'),path=require('path');
var DIR=__dirname;

// ═══ 配置 ═══
var DEEPSEEK_KEY='';
try{ DEEPSEEK_KEY=fs.readFileSync(path.join(DIR,'.deepseek-key'),'utf8').trim(); }catch(e){}
if(!DEEPSEEK_KEY) DEEPSEEK_KEY=process.env.DEEPSEEK_API_KEY||'';
var DEEPSEEK_URL='api.deepseek.com';
var MODEL='deepseek-chat';

if(!DEEPSEEK_KEY){
  console.error('请设置 DEEPSEEK_API_KEY 环境变量');
  console.error('  Windows: set DEEPSEEK_API_KEY=sk-xxx');
  console.error('  或在脚本第10行直接填写');
  process.exit(1);
}

// ═══ Prompt ═══
var SYSTEM_PROMPT=`你是A股供应链事件分类器。判断一条公告是否与"供应链关系"有关。

供应链关系包括：
- 成为某大客户的供应商、通过认证、批量供货
- 获得供应链相关订单（如GPU配套电源、液冷模组、光模块订单）
- 扩产以满足客户需求、新建产线服务某客户
- 供应链中断、客户终止合作、替代风险

NOT 供应链关系：
- 建筑施工中标（修路、盖楼、桥梁、市政工程）
- 普通工程总包（EPC、机电安装）
- 内部管理公告（股东大会、章程修改、分红）
- 财务报告本身（年报/季报发布公告）
- 减持/增持/股权变动
- 环保/水务/废弃物处理项目中标（除非明确涉及半导体/数据中心供应链）

返回JSON格式，不要markdown包裹：
{"is_supply_chain": true/false, "confidence": 0-1, "reason": "一句话理由(≤20字)"}`;

function classify(announcement){
  return new Promise(function(resolve,reject){
    var body=JSON.stringify({
      model:MODEL,
      messages:[
        {role:'system',content:SYSTEM_PROMPT},
        {role:'user',content:'公告标题：'+announcement.event_desc+'\n公司：'+announcement.stock_name+'('+announcement.stock_code+')\n类型：'+announcement.event_type}
      ],
      temperature:0.1,
      max_tokens:100,
      response_format:{type:'json_object'}
    });

    var req=https.request({
      hostname:DEEPSEEK_URL,path:'/chat/completions',method:'POST',
      headers:{'Content-Type':'application/json','Authorization':'Bearer '+DEEPSEEK_KEY,'Content-Length':Buffer.byteLength(body)}
    },function(res){
      var d='';res.on('data',function(c){d+=c});res.on('end',function(){
        try{
          var j=JSON.parse(d);
          if(j.choices&&j.choices[0]){
            var content=j.choices[0].message.content;
            var result=JSON.parse(content);
            resolve(result);
          }else{reject(new Error('API error: '+d));}
        }catch(e){reject(new Error('Parse error: '+d.substring(0,200)));}
      });
    });
    req.on('error',function(e){reject(e);});
    req.write(body);req.end();
  });
}

// 批量分类（带速率限制）
async function classifyBatch(candidates,concurrency){
  concurrency=concurrency||3; // DeepSeek 免费版速率限制较低
  var results=[],i=0;

  async function worker(){
    while(i<candidates.length){
      var idx=i++,c=candidates[idx];
      process.stdout.write('\r  '+idx+'/'+candidates.length+' '+c.stock_name+'...');
      try{
        var r=await classify(c);
        results[idx]={candidate:c,classification:r};
      }catch(e){
        results[idx]={candidate:c,classification:{is_supply_chain:null,confidence:0,reason:'API Error: '+e.message}};
      }
      // 速率限制：100ms between calls
      await new Promise(function(ok){setTimeout(ok,150);});
    }
  }

  var workers=[];for(var w=0;w<concurrency;w++)workers.push(worker());
  await Promise.all(workers);
  console.log('\n');
  return results;
}

// ═══ 主流程 ═══
async function main(){
  var dryRun=process.argv.includes('--dry-run');

  // 读取待分类的公告
  var pendingFile=path.join(DIR,'events-pending.json');
  if(!fs.existsSync(pendingFile)){
    console.log('events-pending.json 不存在。先运行 scan_announcements.py。');
    process.exit(0);
  }
  var candidates=JSON.parse(fs.readFileSync(pendingFile,'utf8'));
  console.log('待分类: '+candidates.length+' 条候选公告\n');

  // 分类
  var results=await classifyBatch(candidates,3);

  // 统计
  var supply=[],noise=[],errors=[];
  results.forEach(function(r){
    if(!r||!r.classification)return;
    var c=r.classification;
    if(c.is_supply_chain===true)supply.push(r);
    else if(c.is_supply_chain===false)noise.push(r);
    else errors.push(r);
  });

  console.log('═══════════════════════════════════════');
  console.log('分类结果');
  console.log('  供应链相关: '+supply.length+' 条');
  console.log('  噪声(过滤): '+noise.length+' 条');
  console.log('  错误:      '+errors.length+' 条');
  console.log('═══════════════════════════════════════');

  // 打印噪声详情
  if(noise.length>0){
    console.log('\n过滤掉的噪声:');
    noise.forEach(function(r){
      console.log('  ❌ '+r.candidate.stock_name+'('+r.candidate.stock_code+')');
      console.log('     '+r.candidate.event_desc.substring(0,80));
      console.log('     理由: '+r.classification.reason);
    });
  }

  // 打印供应链确认
  if(supply.length>0){
    console.log('\n供应链相关:');
    supply.forEach(function(r){
      console.log('  ✅ '+r.candidate.stock_name+'('+r.candidate.stock_code+') conf='+r.classification.confidence.toFixed(1));
      console.log('     '+r.candidate.event_desc.substring(0,80));
      console.log('     理由: '+r.classification.reason);
    });
  }

  if(dryRun){
    console.log('\n[dry-run] 未写入 events.json。去掉 --dry-run 参数可实际写入。');
    return;
  }

  // 写入过滤后的结果
  var filtered=supply.map(function(r){return r.candidate;});
  fs.writeFileSync(pendingFile,JSON.stringify(filtered,null,2),'utf8');
  console.log('\n已更新 events-pending.json ('+filtered.length+' 条供应链相关)');
  console.log('下一步: node update-events.js 合并到 events.json');
}

main().catch(function(e){console.error(e);process.exit(1);});

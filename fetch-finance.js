// 财报数据批量拉取工具 — Node.js直连, 绕过浏览器CORS
// 用法: node fetch-finance.js
var fs=require('fs');
var STOCKS=[
  {c:'002149',m:0,n:'西部材料'},{c:'300136',m:0,n:'信维通信'},{c:'300433',m:0,n:'蓝思科技'},{c:'688102',m:1,n:'斯瑞新材'},{c:'603809',m:1,n:'豪能股份'},{c:'301005',m:0,n:'超捷股份'},{c:'002865',m:0,n:'钧达股份'},{c:'300502',m:0,n:'新易盛'},{c:'688256',m:1,n:'寒武纪'},{c:'002230',m:0,n:'科大讯飞'},{c:'688111',m:1,n:'金山办公'},{c:'300418',m:0,n:'昆仑万维'},{c:'600602',m:1,n:'云赛智联'},{c:'300750',m:0,n:'宁德时代'},{c:'601012',m:1,n:'隆基绿能'},{c:'002129',m:0,n:'中环股份'},{c:'688599',m:1,n:'天合光能'},{c:'300274',m:0,n:'阳光电源'},{c:'688981',m:1,n:'中芯国际'},{c:'002371',m:0,n:'北方华创'},{c:'603986',m:1,n:'兆易创新'},{c:'688012',m:1,n:'中微公司'},{c:'300782',m:0,n:'卓胜微'},{c:'688008',m:1,n:'澜起科技'},{c:'002475',m:0,n:'立讯精密'},{c:'601138',m:1,n:'工业富联'},{c:'002241',m:0,n:'歌尔股份'},{c:'600745',m:1,n:'闻泰科技'},{c:'600456',m:1,n:'宝钛股份'},{c:'603601',m:1,n:'再升科技'},{c:'301522',m:0,n:'上大股份'},{c:'688333',m:1,n:'铂力特'},{c:'605123',m:1,n:'派克新材'},{c:'603308',m:1,n:'应流股份'},{c:'300855',m:0,n:'图南股份'},{c:'300395',m:0,n:'菲利华'},{c:'603305',m:1,n:'旭升集团'},{c:'603348',m:1,n:'文灿股份'},{c:'601689',m:1,n:'拓普集团'},{c:'002050',m:0,n:'三花智控'},{c:'600699',m:1,n:'均胜电子'},{c:'002036',m:0,n:'联创电子'},{c:'002920',m:0,n:'德赛西威'},{c:'688017',m:1,n:'绿的谐波'},{c:'002466',m:0,n:'天齐锂业'},{c:'603799',m:1,n:'华友钴业'},{c:'000970',m:0,n:'中科三环'},{c:'300748',m:0,n:'金力永磁'},{c:'601208',m:1,n:'东材科技'},{c:'688300',m:1,n:'联瑞新材'},{c:'301389',m:0,n:'隆扬电子'},{c:'605589',m:1,n:'圣泉集团'},{c:'600183',m:1,n:'生益科技'},{c:'603256',m:1,n:'宏和科技'},{c:'688535',m:1,n:'华海诚科'},{c:'300408',m:0,n:'三环集团'},{c:'300476',m:0,n:'胜宏科技'},{c:'002463',m:0,n:'沪电股份'},{c:'002916',m:0,n:'深南电路'},{c:'600584',m:1,n:'长电科技'},{c:'300308',m:0,n:'中际旭创'},{c:'300394',m:0,n:'天孚通信'},{c:'002837',m:0,n:'英维克'},{c:'002851',m:0,n:'麦格米特'},{c:'002156',m:0,n:'通富微电'},{c:'300567',m:0,n:'精测电子'},{c:'300604',m:0,n:'长川科技'},{c:'300990',m:0,n:'同飞股份'},{c:'002281',m:0,n:'光迅科技'},{c:'300738',m:0,n:'奥飞数据'},{c:'688248',m:1,n:'南网科技'},
];

function finURL(code,prefix){
  return 'https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew?type=0&code='+prefix+code;
}

var file='finance-data.json';
var existing={};try{existing=JSON.parse(fs.readFileSync(file,'utf8'))}catch(e){}

async function run(){
  var ok=0,total=STOCKS.length;
  console.log('拉取 '+total+' 只股票财报...\n');
  for(var i=0;i<STOCKS.length;i++){
    var s=STOCKS[i];var prefix=s.m===1?'SH':'SZ';var code=prefix+s.c;
    try{
      var r=await fetch(finURL(s.c,prefix));
      var j=await r.json();
      if(j&&j.data&&j.data.length>0){
        var fd=j.data[0];
        existing[s.c]={n:s.n,roe:fd.ROEJQ,prfG:fd.PARENTNETPROFITTZ,grossM:fd.XSMLL,debtR:fd.ZCFZL,reportDate:fd.REPORT_DATE,reportType:fd.REPORT_TYPE};
        ok++;console.log('✅ '+s.n+' ROE:'+fd.ROEJQ+'% 利润:'+(fd.PARENTNETPROFITTZ>0?'+':'')+fd.PARENTNETPROFITTZ+'%');
      }else{
        console.log('❌ '+s.n+' 无数据');
      }
    }catch(e){
      console.log('❌ '+s.n+' '+e.message);
    }
  }
  fs.writeFileSync(file,JSON.stringify(existing,null,2));
  console.log('\n完成: '+ok+'/'+total+' 已保存到 '+file);
}
run();

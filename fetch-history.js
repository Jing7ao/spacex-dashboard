// 批量拉取历史收盘价 — 东方财富API (本地运行,无跨域限制)
// 用法: node fetch-history.js
// 输出: history-prices.json + history-hs300.json

const https = require('https');
const fs = require('fs');

const STOCKS = [
  {code:'300476',name:'胜宏科技',market:'0'},  // 0=深圳 1=上海
  {code:'002851',name:'麦格米特',market:'0'},
  {code:'300136',name:'信维通信',market:'0'},
  {code:'688017',name:'绿的谐波',market:'1'},
  {code:'688629',name:'华丰科技',market:'1'},
  {code:'001270',name:'铖昌科技',market:'0'},
  {code:'688631',name:'莱斯信息',market:'1'},
  {code:'600584',name:'长电科技',market:'1'},
  {code:'300395',name:'菲利华',market:'0'},
  {code:'002463',name:'沪电股份',market:'0'},
];

// 沪深300 (000300) 也用同样API
const HS300 = {code:'000300',name:'沪深300',market:'1'};

function fetchKline(stock, begin, end) {
  return new Promise((resolve, reject) => {
    const secid = stock.market + '.' + stock.code;
    const url = `https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=${secid}&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=0&beg=${begin}&end=${end}`;

    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          if (!json.data || !json.data.klines) {
            console.log(`  ⚠️ ${stock.code} ${stock.name}: 无数据`);
            resolve([]);
            return;
          }
          const prices = json.data.klines.map(line => {
            const parts = line.split(',');
            return {
              date: parts[0],
              open: parseFloat(parts[1]),
              close: parseFloat(parts[2]),
              high: parseFloat(parts[3]),
              low: parseFloat(parts[4]),
              volume: parseInt(parts[5]),
            };
          });
          console.log(`  ✅ ${stock.code} ${stock.name}: ${prices.length} 条`);
          resolve(prices);
        } catch(e) {
          console.log(`  ❌ ${stock.code} ${stock.name}: 解析失败`);
          resolve([]);
        }
      });
    }).on('error', (e) => {
      console.log(`  ❌ ${stock.code} ${stock.name}: ${e.message}`);
      resolve([]);
    });
  });
}

async function main() {
  console.log('📊 批量拉取历史收盘价 (2026-01-01 ~ 2026-06-06)\n');

  const result = {};
  for (const s of STOCKS) {
    result[s.code] = await fetchKline(s, '20260101', '20260606');
  }

  // 沪深300
  console.log('');
  const hs300Data = await fetchKline(HS300, '20260101', '20260606');
  result['000300'] = hs300Data;

  fs.writeFileSync('history-prices.json', JSON.stringify(result, null, 2));
  console.log(`\n✅ 已保存 history-prices.json (${Object.keys(result).length} 只标的)`);
  console.log('   包含: ' + Object.entries(result).map(([k,v])=>`${k}(${v.length}条)`).join(', '));
}

main().catch(console.error);

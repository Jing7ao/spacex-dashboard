// StockPrice.fetch([codes], callback)
// Uses Sina API via script tag injection (reads global vars)
var StockPrice = (function() {
  var CACHE = {}, TTL = 15000;
  function pfx(c) {
    c = String(c);
    return (c[0]==='6'||c[0]==='5') ? 'sh'+c : 'sz'+c;
  }
  return { fetch: function(codes, cb) {
    var now = Date.now(), res = {}, need = [];
    codes.forEach(function(c) {
      if (CACHE[c] && (now - CACHE[c]._t) < TTL) res[c] = CACHE[c];
      else need.push(c);
    });
    if (need.length === 0) { cb(res); return; }

    var url = 'https://hq.sinajs.cn/list=' + need.map(pfx).join(',');
    var s = document.createElement('script');
    s.src = url;
    s.onload = function() {
      document.head.removeChild(s);
      need.forEach(function(c) {
        var raw = window['hq_str_'+pfx(c)];
        if (raw && typeof raw === 'string' && raw.length > 10) {
          var f = raw.split(',');
          if (f.length > 20) {
            var price = parseFloat(f[3]), prev = parseFloat(f[2]);
            var d = { name:f[0], price:price, prev_close:prev, open:parseFloat(f[1]),
              high:parseFloat(f[4]), low:parseFloat(f[5]), volume:parseInt(f[8]),
              change: price&&prev ? (price-prev).toFixed(2) : null,
              change_pct: price&&prev ? ((price-prev)/prev*100).toFixed(2) : null, _t:now };
            CACHE[c] = d; res[c] = d;
            try { delete window['hq_str_'+pfx(c)]; } catch(e){}
            return;
          }
        }
        res[c] = null;
      });
      cb(res);
    };
    s.onerror = function() { document.head.removeChild(s); need.forEach(function(c){res[c]=null;}); cb(res); };
    document.head.appendChild(s);
  }, clearCache: function(){ CACHE = {}; } };
})();

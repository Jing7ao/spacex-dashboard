

// ═══ 数据定义 ═══════════════════════════════════════

const P='http://localhost:8080';



const INDUSTRIES={

  space:{name:'🚀 商业航天',watchlist:[

    {c:'002149',m:0,n:'西部材料',rk:'high',rn:'核级控制棒国内唯一[E1] 钛合金中船金牌供应商[E1]',pew:344},

    {c:'300136',m:0,n:'信维通信',rk:'high',rn:'北美大客户送样[E1] 年报未提SpaceX/独家',pew:97},

    {c:'300433',m:0,n:'蓝思科技',rk:'mid',rn:'航天UTG玻璃/Q1亏损',pew:30},

    {c:'688102',m:1,n:'斯瑞新材',rk:'high',rn:'火箭热端部件/PE极高',pew:156},

    {c:'603809',m:1,n:'豪能股份',rk:'mid',rn:'航天+机器人/小盘',pew:23},

    {c:'301005',m:0,n:'超捷股份',rk:'critical',rn:'PE1281倍/纯概念炒作',pew:1281},

    {c:'002865',m:0,n:'钧达股份',rk:'high',rn:'太空光伏无收入/实控人减持',pew:0},

      {c:'001270',m:0,n:'铖昌科技',rk:'high',rn:'星载T/R>70% 物理开关16分',pew:120},

      {c:'600118',m:1,n:'中国卫星',rk:'mid',rn:'卫星制造 年报未披露份额',pew:80},

      {c:'002179',m:0,n:'中航光电',rk:'mid',rn:'防务首选供应商[E1] 高压连接器国内前列[E1] 年报未提蓝箭',pew:35},

      {c:'000099',m:0,n:'中信海直',rk:'mid',rn:'低空经济布局 年报未称唯一',pew:50},

      {c:'688631',m:1,n:'莱斯信息',rk:'high',rn:'空管60-80% 物理开关13分',pew:100},

  ],etfs:[

    {c:'563230',m:1,n:'富国卫星ETF'},{c:'512630',m:1,n:'广发卫星ETF'},

    {s:'XOVR',n:'ERShares XOVR',us:true,note:'SpaceX~19%'},{s:'NASA',n:'Tema NASA',us:true,note:'SpaceX~8-10%'},

  ]},

  ai:{name:'🤖 AI人工智能',watchlist:[

    {c:'300502',m:0,n:'新易盛',rk:'mid',rn:'高速光模块 800G/1.6T布局 年报未称龙头',pew:40},

    {c:'688256',m:1,n:'寒武纪',rk:'high',rn:'AI芯片/持续亏损/高波动',pew:0},

    {c:'002230',m:0,n:'科大讯飞',rk:'mid',rn:'大模型/星火/ToG收入',pew:120},

    {c:'688111',m:1,n:'金山办公',rk:'mid',rn:'WPS AI/办公智能化',pew:80},

    {c:'300418',m:0,n:'昆仑万维',rk:'high',rn:'AI布局/游戏承压',pew:0},

    {c:'600602',m:1,n:'云赛智联',rk:'mid',rn:'AI算力/上海国资',pew:60},

  ],etfs:[{c:'159819',m:0,n:'人工智能ETF'},{s:'QQQ',n:'Invesco QQQ',us:true,note:'纳斯达克100'}]},

  newenergy:{name:'☀️ 新能源',watchlist:[

    {c:'300750',m:0,n:'宁德时代',rk:'mid',rn:'动力电池全球第一(SNE Research) 市占39.2%(年报)',pew:25},

    {c:'601012',m:1,n:'隆基绿能',rk:'mid',rn:'硅片累计出货全球第一(年报) 组件出货86.58GW',pew:30},

    {c:'002129',m:0,n:'中环股份',rk:'mid',rn:'光伏硅片 G12规格(年报)',pew:35},

    {c:'688599',m:1,n:'天合光能',rk:'mid',rn:'组件/储能/分布式',pew:28},

    {c:'300274',m:0,n:'阳光电源',rk:'mid',rn:'逆变器/储能系统',pew:30},

    {c:'002865',m:0,n:'钧达股份',rk:'high',rn:'太空光伏概念/亏损',pew:0},

  ],etfs:[{c:'159875',m:0,n:'新能源ETF'},{s:'TAN',n:'Invesco Solar',us:true,note:'全球太阳能'}]},

  chip:{name:'💾 半导体',watchlist:[

    {c:'688981',m:1,n:'中芯国际',rk:'mid',rn:'晶圆代工 先进制程布局',pew:50},

    {c:'002371',m:0,n:'北方华创',rk:'mid',rn:'半导体设备 刻蚀/薄膜/炉管(年报)',pew:60},

    {c:'603986',m:1,n:'兆易创新',rk:'mid',rn:'存储/MCU/景气周期',pew:55},

    {c:'688012',m:1,n:'中微公司',rk:'mid',rn:'刻蚀设备/国产替代',pew:70},

    {c:'300782',m:0,n:'卓胜微',rk:'high',rn:'射频芯片/消费电子周期',pew:80},

    {c:'688008',m:1,n:'澜起科技',rk:'mid',rn:'内存接口/AI服务器',pew:65},

      {c:'688629',m:1,n:'华丰科技',rk:'high',rn:'高速连接器 华为第一大客户[E1] 防务核心供应商[E1] 年报未提224G',pew:150},

  ],etfs:[{c:'159995',m:0,n:'芯片ETF'},{s:'SOXX',n:'iShares半导体',us:true,note:'费城半导体指数'}]},

  consumer:{name:'📱 消费电子',watchlist:[

    {c:'002475',m:0,n:'立讯精密',rk:'mid',rn:'精密智造全球第四/中国大陆榜首(年报)',pew:25},

    {c:'300433',m:0,n:'蓝思科技',rk:'mid',rn:'玻璃盖板/机器人/航天',pew:30},

    {c:'601138',m:1,n:'工业富联',rk:'mid',rn:'AI服务器/云计算',pew:20},

    {c:'002241',m:0,n:'歌尔股份',rk:'mid',rn:'VR/AR/声学组件',pew:35},

    {c:'300136',m:0,n:'信维通信',rk:'high',rn:'天线/卫星通信/XR 年报未提SpaceX',pew:97},

    {c:'600745',m:1,n:'闻泰科技',rk:'mid',rn:'ODM/半导体/汽车',pew:40},

  ],etfs:[{c:'159732',m:0,n:'消费电子ETF'},{s:'AAPL',n:'Apple',us:true,note:'消费电子标杆'}]},

  power:{name:'⚡ 电力能源',watchlist:[

    {c:'603191',m:1,n:'望变电气',rk:'mid',pew:35,rn:'[T4]取向硅钢 国内唯一全产业链布局(年报/E1)'},

    {c:'600362',m:1,n:'江西铜业',rk:'mid',pew:15,rn:'[T4]国内最大阴极铜供应商[E1] LME唯一认定测试厂[E1]'},

    {c:'603290',m:1,n:'斯达半导',rk:'mid',pew:60,rn:'[T4]IGBT模块车规出口Tier1[E1] 汇川/阳光供应商[E1]'},

    {c:'002270',m:0,n:'华明装备',rk:'mid',pew:30,rn:'[T4]变压器分接开关 国内唯一两大基地 打破国外垄断(年报/E1)'},

    {c:'600869',m:1,n:'远东股份',rk:'mid',pew:25,rn:'[T3]线缆产业10强+特种电缆龙头(年报)'},

    {c:'603606',m:1,n:'东方电缆',rk:'mid',pew:30,rn:'[T3]±500kV柔直海缆全球首根[E1] 海陆缆核心供应商[E1]'},

    {c:'600089',m:1,n:'特变电工',rk:'mid',pew:15,rn:'[T3]输变电龙头 多产业集团(年报/E1)'},

    {c:'601179',m:1,n:'中国西电',rk:'mid',pew:40,rn:'[T3]特高压国网集招行业第一[E1]'},

    {c:'600312',m:1,n:'平高电气',rk:'mid',pew:35,rn:'[T3]超高压开关唯一金奖[E1] 特高压GIS领先'},

    {c:'688676',m:1,n:'金盘科技',rk:'mid',pew:45,rn:'[T2]数据中心干变 百度/阿里客户[E1] 年报未提字节'},

    {c:'600406',m:1,n:'国电南瑞',rk:'mid',pew:30,rn:'[T2]电网调度自动化份额领先[E1] AgentSphere能源唯一[E1]'},

    {c:'000400',m:0,n:'许继电气',rk:'mid',pew:35,rn:'[T2]换流阀国家首台套[E1] 计量国网份额第一[E1]'},

    {c:'002335',m:0,n:'科华数据',rk:'mid',pew:40,rn:'[T2]UPS国内第一[E1:CCID/Omdia] 储能PCS全球第一[E1:S&P]'},

    {c:'002364',m:0,n:'中恒电气',rk:'mid',pew:50,rn:'[T2]阿里腾讯数据中心电源供应商[E1]'},

    {c:'002028',m:0,n:'思源电气',rk:'mid',pew:35,rn:'[T2]±800kV柔直中标[E1] SVG构网中标[E1] 海外+86%'},

    {c:'300153',m:0,n:'科泰电源',rk:'mid',pew:55,rn:'[T2]柴发备用电源 数据中心行业领先[E1] 年报未提字节'},

    {c:'600131',m:1,n:'国网信通',rk:'mid',pew:40,rn:'[T1.5]电网数字化+算电协同'},

    {c:'600875',m:1,n:'东方电气',rk:'mid',pew:25,rn:'[T1.5]发电设备央企 燃机到2028'},

    {c:'601126',m:1,n:'四方股份',rk:'mid',pew:35,rn:'[T1.5]字节火山引擎算力中心客户[E1] 市场份额前列[E1]'},

    {c:'601877',m:1,n:'正泰电器',rk:'mid',pew:20,rn:'[T2]低压电器三细分市场第一[E1] 业内唯一全产品商[E1]'},

    {c:'688248',m:1,n:'南网科技',rk:'mid',pew:50,rn:'[T2]储能+智能配用电 南方电网旗下'},

  ],etfs:[{c:'159611',m:0,n:'电力ETF'}]},

  cxmt:{name:'🏭 长鑫存储链',watchlist:[

    {c:'603986',m:1,n:'兆易创新',rk:'mid',pew:55,rn:'[T2]DRAM设计+持股长鑫1.8%'},

    {c:'002371',m:0,n:'北方华创',rk:'mid',pew:60,rn:'[设备]刻蚀/薄膜/TSV DRAM扩产核心'},

    {c:'688012',m:1,n:'中微公司',rk:'mid',pew:70,rn:'[设备]刻蚀 DRAM制程'},

    {c:'300567',m:0,n:'精测电子',rk:'mid',pew:60,rn:'[设备]平板显示检测龙头[E1] 半导体量检测领军[E1]'},

    {c:'300604',m:0,n:'长川科技',rk:'mid',pew:55,rn:'[设备]DRAM分选机'},

    {c:'300666',m:0,n:'江丰电子',rk:'mid',pew:65,rn:'[T4]高纯靶材 DRAM关键材料'},

    {c:'688019',m:1,n:'安集科技',rk:'mid',pew:55,rn:'[T4]CMP抛光液 DRAM制程'},

    {c:'600584',m:1,n:'长电科技',rk:'mid',pew:35,rn:'[T2]DRAM封测'},

    {c:'002156',m:0,n:'通富微电',rk:'mid',pew:50,rn:'[T2]DRAM封测 Chiplet'},

  ],etfs:[{c:'159995',m:0,n:'芯片ETF'}]},

  cooling:{name:'❄️ 液冷散热',watchlist:[

    {c:'002837',m:0,n:'英维克',rk:'mid',pew:45,rn:'[T2]液冷 UQD进英伟达MGX生态[E1] 华为中兴客户[E1]'},

    {c:'301018',m:0,n:'申菱环境',rk:'mid',pew:60,rn:'[T2]CDU双料第一(赛迪)[E1] 华为字节腾讯客户[E1]'},

    {c:'300499',m:0,n:'高澜股份',rk:'mid',pew:55,rn:'[T3]直流输电阀冷龙头[E1] 液冷数据中心 年报未提英伟达认证'},

    {c:'300249',m:0,n:'依米康',rk:'mid',pew:80,rn:'[T2]字节/阿里客户[E1] 风墙市场第一(赛迪)[E1]'},

    {c:'002536',m:0,n:'飞龙股份',rk:'mid',pew:50,rn:'[T3]液冷泵 深度绑定头部'},

    {c:'301086',m:0,n:'鸿富瀚',rk:'high',pew:70,rn:'[T3]液冷板 苹果/微软/联想供应链[E1] 年报无Meta/Amazon'},

    {c:'002126',m:0,n:'银轮股份',rk:'mid',pew:30,rn:'[T3]液冷板 数据中心液冷模组 聚焦北美客户(年报)'},

    {c:'688668',m:1,n:'鼎通科技',rk:'mid',pew:55,rn:'[T3]液冷连接器 订单饱和扩产'},

    {c:'300990',m:0,n:'同飞股份',rk:'mid',pew:50,rn:'[T2]精密温控 数据中心液冷配套'},

  ],etfs:[]},

  semimat:{name:'🧪 半导体材料',watchlist:[

    {c:'688268',m:1,n:'华特气体',rk:'mid',pew:50,rn:'[T4]电子特气 国内唯一通过ASML认证(年报/E1)'},

    {c:'688146',m:1,n:'中船特气',rk:'mid',pew:45,rn:'[T4]三氟化氮+电子特气 年报未称全球第一'},

    {c:'300346',m:0,n:'南大光电',rk:'mid',pew:70,rn:'[T4]ArF光刻胶+电子特气 年报未称唯一量产'},

    {c:'300655',m:0,n:'晶瑞电材',rk:'mid',pew:60,rn:'[T4]高纯双氧水国内第一 市占40%+ G5(年报/E1)'},

    {c:'688019',m:1,n:'安集科技',rk:'mid',pew:55,rn:'[T4]CMP抛光液打破国外垄断[E1] 国内领先供应商'},

    {c:'300666',m:0,n:'江丰电子',rk:'mid',pew:65,rn:'[T4]溅射靶材国内唯一核心技术[E1] 全球领先[E1]'},

    {c:'688126',m:1,n:'沪硅产业',rk:'mid',pew:80,rn:'[T4]硅片打破国际垄断[E1] 200mm MEMS全球领先[E1]'},

    {c:'300054',m:0,n:'鼎龙股份',rk:'mid',pew:50,rn:'[T4]CMP抛光垫 国内唯一全品类(年报/E1) 国产龙头'},

    {c:'603650',m:1,n:'彤程新材',rk:'mid',pew:55,rn:'[T4]半导体光刻胶国内第一(沙利文)[E1] ArF/KrF全线量产[E1]'},

    {c:'002378',m:0,n:'章源钨业',rk:'mid',pew:45,rn:'[T4]钨铜合金芯片封装材料[E1] 硬质合金刀具国产替代 上游钨矿资源'},

    {c:'300260',m:0,n:'新莱应材',rk:'mid',pew:45,rn:'[T4]国际半导体龙头一级供应商[E1] 超高纯管阀件'},

  ],etfs:[]},

  optical:{name:'🔗 光通信CPO',watchlist:[

    {c:'000988',m:0,n:'华工科技',rk:'mid',pew:40,rn:'[T1.5]CPO光引擎/激光 年报未提NVIDIA'},

    {c:'301165',m:0,n:'锐捷网络',rk:'mid',pew:45,rn:'[T1.5]交换机市占第三(IDC)[E1] 以太光网络第一[E1]'},

    {c:'688498',m:1,n:'源杰科技',rk:'high',pew:80,rn:'[T3]800G/1.6T光芯片 年报未提英伟达认证'},

    {c:'601869',m:1,n:'长飞光纤',rk:'mid',pew:25,rn:'[T3]光纤行业唯一国家重点实验室[E1] 首批领航级智能工厂[E1]'},

    {c:'600487',m:1,n:'亨通光电',rk:'mid',pew:20,rn:'[T3]跨洋海缆唯一中国企业[E1] MPO华为/阿里供货[E1]'},

    {c:'000938',m:0,n:'紫光股份',rk:'mid',pew:35,rn:'[T2]51.2T CPO批量交付[E1] 企业网交换机第一(IDC)[E1]'},

    {c:'300570',m:0,n:'太辰光',rk:'mid',pew:50,rn:'[T3]MPO/MTP连接器核心供应商[E1] 全球数据中心客户'},

    {c:'300620',m:0,n:'光库科技',rk:'mid',pew:60,rn:'[T3]铌酸锂调制器全球核心供应商[E1] 隔离器市占领先[E1]'},

    {c:'002281',m:0,n:'光迅科技',rk:'mid',pew:40,rn:'[T2]光器件 全球份额7.8%(Omdia/年报)'},

  ],etfs:[{c:'159659',m:0,n:'通信ETF'}]},

  storage:{name:'🔋 储能/虚拟电厂',watchlist:[

    {c:'000682',m:0,n:'东方电子',rk:'mid',pew:20,rn:'电网调度/电表市占率名列前茅[E1] 虚拟电厂布局'},

    {c:'301162',m:0,n:'国能日新',rk:'mid',pew:60,rn:'功率预测市占率领先[E1] 6029家电站 年报未称第一'},

    {c:'300712',m:0,n:'永福股份',rk:'high',pew:80,rn:'电力EPC+虚拟电厂+抽水蓄能'},

    {c:'300040',m:0,n:'九洲集团',rk:'mid',pew:40,rn:'绿电直连+HVDC+储能200MW'},

  ],etfs:[{c:'159865',m:0,n:'储能ETF'}]},

  datacenter:{name:'🏗️ 数据中心建设',watchlist:[

    {c:'600496',m:1,n:'精工钢构',rk:'mid',pew:20,rn:'钢结构品牌 海外业务+140%[E1] 数据中心厂房'},

    {c:'600477',m:1,n:'杭萧钢构',rk:'mid',pew:25,rn:'钢结构+绿色建筑'},

    {c:'002135',m:0,n:'东南网架',rk:'mid',pew:30,rn:'空间钢结构 数据中心基建'},

    {c:'601789',m:1,n:'宁波建工',rk:'mid',pew:20,rn:'建筑工程总包 年报未提数据中心业务'},

    {c:'600126',m:1,n:'杭钢股份',rk:'mid',pew:15,rn:'阿里云客户(1.07亿应收)[E1] 钢铁+数据中心'},

  ],etfs:[]},

  subcable:{name:'🌊 海底光缆',watchlist:[

    {c:'600487',m:1,n:'亨通光电',rk:'mid',pew:20,rn:'跨洋海缆唯一中国企业[E1] 行业唯一央视年度案例[E1]'},

    {c:'600522',m:1,n:'中天科技',rk:'mid',pew:20,rn:'阿里/腾讯/华为核心供应商[E1] OPGW市占率领先[E1]'},

    {c:'603606',m:1,n:'东方电缆',rk:'mid',pew:30,rn:'±500kV柔直海缆全球首根[E1] 海陆缆核心供应商[E1]'},

  ],etfs:[]},

  idc:{name:'🏢 IDC运营',watchlist:[

    {c:'300383',m:0,n:'光环新网',rk:'mid',pew:35,rn:'AWS中国(北京)运营[E1] 上海首个T4认证[E1]'},

    {c:'603881',m:1,n:'数据港',rk:'mid',pew:40,rn:'网络中立IDC服务商 年报未提阿里为客户'},

    {c:'600804',m:1,n:'*ST鹏博士',rk:'critical',pew:0,rn:'转型IDC 风险极高'},

    {c:'300738',m:0,n:'奥飞数据',rk:'mid',pew:40,rn:'[T2]第三方IDC 北京/广州布局[E1] 年报未提字节'},

  ],etfs:[]},

  env:{name:'💧 水务/电子回收',watchlist:[

    {c:'300070',m:0,n:'碧水源',rk:'mid',pew:30,rn:'MBR-DF国内唯一大规模应用[E1] 膜技术打破国外垄断[E1]'},

    {c:'600008',m:1,n:'首创环保',rk:'mid',pew:20,rn:'北京环保唯一数据空间试点[E1] 水务综合服务商'},

    {c:'002340',m:0,n:'格林美',rk:'mid',pew:25,rn:'全球唯一核壳前驱体量产[E1] 循环经济领军企业[E1]'},

    {c:'300779',m:0,n:'惠城环保',rk:'high',pew:60,rn:'危废处理 电子废弃物'},

  ],etfs:[]},

  musk:{name:'⚡ 马斯克生态',watchlist:[

    {c:'300136',m:0,n:'信维通信',rk:'high',rn:'[T2星链]北美大客户送样[E1] 独家供应商仅互动易声称(年报未提)',pew:97},

    {c:'002149',m:0,n:'西部材料',rk:'high',rn:'[T3火箭]核级控制棒国内唯一合格供应方[E1] 钛合金中船金牌供应商[E1] 年报未提SpaceX',pew:344},

    {c:'688102',m:1,n:'斯瑞新材',rk:'high',rn:'[T3火箭]蓝箭航天供应商(朱雀三号)[E1] 电接触材料全球第一[E1]',pew:156},

    {c:'600456',m:1,n:'宝钛股份',rk:'mid',rn:'[T3火箭]航天钛合金 NASA认证',pew:40},

    {c:'603601',m:1,n:'再升科技',rk:'high',rn:'[T3火箭]高硅氧纤维 SpaceX稳定供应 月供>50吨 合同至2028(互动易/E1)',pew:80},

    {c:'301522',m:0,n:'上大股份',rk:'mid',rn:'[T3火箭]高温合金 年报未提SpaceX',pew:60},

    {c:'688333',m:1,n:'铂力特',rk:'mid',rn:'[T3火箭]增材制造 服务航空航天客户(年报)',pew:100},

    {c:'605123',m:1,n:'派克新材',rk:'mid',rn:'[T2火箭]锻件 NASA+SpaceX双认证',pew:45},

    {c:'603308',m:1,n:'应流股份',rk:'mid',rn:'[T2火箭]猛禽发动机涡轮泵铸件 单箭1800-2200万(E2产业链分析)',pew:50},

    {c:'301005',m:0,n:'超捷股份',rk:'critical',rn:'[T2火箭]互动易否认SpaceX供应商 仅国内(E1证伪)',pew:1281},

    {c:'300855',m:0,n:'图南股份',rk:'mid',rn:'[T2火箭]高温合金精铸 年报未称垄断',pew:55},

    {c:'300395',m:0,n:'菲利华',rk:'mid',rn:'[T3]石英材料 年报未提及星链',pew:45},

    {c:'603212',m:1,n:'赛伍技术',rk:'mid',rn:'[T3星链]PI膜 卫星太阳翼',pew:60},

    {c:'002792',m:0,n:'通宇通讯',rk:'high',rn:'[T2星链]MacroWiFi 通过SpaceX认证 小批量订单(互动易)',pew:80},

    {c:'603305',m:1,n:'旭升集团',rk:'mid',rn:'[T3特斯拉]铝合金压铸 一级供应商',pew:30},

    {c:'603348',m:1,n:'文灿股份',rk:'mid',rn:'[T3特斯拉]一体化压铸 车身结构',pew:50},

    {c:'601689',m:1,n:'拓普集团',rk:'mid',rn:'[T2特斯拉+Optimus]底盘+执行器',pew:35},

    {c:'002050',m:0,n:'三花智控',rk:'mid',rn:'[T2特斯拉+Optimus]热管理+旋转执行器',pew:40},

    {c:'600699',m:1,n:'均胜电子',rk:'mid',rn:'[T2特斯拉+Optimus]安全+关节模组',pew:25},

    {c:'002036',m:0,n:'联创电子',rk:'mid',rn:'[T2]车载摄像头 年报未提及特斯拉',pew:50},

    {c:'002920',m:0,n:'德赛西威',rk:'mid',rn:'[T2特斯拉]FSD域控制器',pew:45},

    {c:'688017',m:1,n:'绿的谐波',rk:'mid',rn:'[T3 Optimus]谐波减速器全球唯一全自主[E1] 市场占有率全球领先[E1]',pew:80},

    {c:'603662',m:1,n:'柯力传感',rk:'mid',rn:'[T3 Optimus]六维力传感器',pew:60},

    {c:'600143',m:1,n:'金发科技',rk:'mid',rn:'[T3 Optimus]特种工程塑料 耐高温',pew:30},

    {c:'002466',m:0,n:'天齐锂业',rk:'mid',rn:'[T4特斯拉]锂矿/碳酸锂',pew:20},

    {c:'603799',m:1,n:'华友钴业',rk:'mid',rn:'[T4特斯拉]钴/三元前驱体',pew:25},

    {c:'000970',m:0,n:'中科三环',rk:'mid',rn:'[T4特斯拉]钕铁硼永磁 驱动电机',pew:30},

    {c:'300748',m:0,n:'金力永磁',rk:'mid',rn:'[T4特斯拉]稀土永磁 新能源车',pew:35},

    {c:'000977',m:0,n:'浪潮信息',rk:'mid',rn:'[T2 xAI]AI服务器 潜在供应商',pew:30},

  ],etfs:[

    {c:'563230',m:1,n:'富国卫星ETF'},{s:'TSLA',n:'Tesla',us:true,note:'马斯克生态核心'},

    {s:'SPCX',n:'SpaceX',us:true,note:'6/12上市'},

  ]},

  nvidia:{name:'🔷 英伟达生态',watchlist:[

    {c:'601208',m:1,n:'东材科技',rk:'mid',rn:'[T4]碳氢树脂 配套英伟达(年报p.31)',pew:40},

    {c:'688300',m:1,n:'联瑞新材',rk:'mid',rn:'[T4]硅微粉 全球份额约15%(E2产业链分析)',pew:50},

    {c:'301389',m:0,n:'隆扬电子',rk:'mid',rn:'[T4]HVLP5铜箔 样品阶段(年报/E1) 产业链称HVLP4量产M9认证(E2)',pew:55},

    {c:'605589',m:1,n:'圣泉集团',rk:'mid',rn:'[T4]酚醛/呋喃树脂国内第一世界前列[E1] PPO市占领先[E1]'},

    {c:'600183',m:1,n:'生益科技',rk:'mid',rn:'[T3]CCL覆铜板 高速材料布局',pew:30},

    {c:'300395',m:0,n:'菲利华',rk:'mid',rn:'[T3]石英材料 M9石英布认证 全球仅3-4家量产(E2产业链分析)',pew:45},

    {c:'603256',m:1,n:'宏和科技',rk:'mid',rn:'[T3]4μm极薄电子布 年报未称龙头',pew:50},

    {c:'688535',m:1,n:'华海诚科',rk:'mid',rn:'[T3]环氧塑封料 MG15F/GR15F全球独家供应(年报)',pew:60},

    {c:'300408',m:0,n:'三环集团',rk:'mid',rn:'[T3]陶瓷基板 年报未披露GPU市占',pew:40},

    {c:'300476',m:0,n:'胜宏科技',rk:'mid',rn:'[T2]全球PCB第6/内资第3(Prismark)[E1] AI算力PCB全球领先[E1]',pew:35},

    {c:'002463',m:0,n:'沪电股份',rk:'mid',rn:'[T2]AI PCB 高端产品布局',pew:35},

    {c:'002916',m:0,n:'深南电路',rk:'mid',rn:'[T2]IC载板 FC-BGA 16层(年报)',pew:45},

    {c:'600584',m:1,n:'长电科技',rk:'mid',rn:'[T2]封测 中国大陆第一全球第三(年报)',pew:35},

    {c:'688153',m:1,n:'英诺赛科',rk:'mid',rn:'[T2]射频前端芯片 并非GaN/英诺赛科(港股02577)',pew:80},

    {c:'601138',m:1,n:'工业富联',rk:'mid',rn:'[T1.5]AI服务器代工 全球AI算力核心供应商(年报)',pew:20},

    {c:'300308',m:0,n:'中际旭创',rk:'mid',rn:'[T1.5]800G/1.6T光模块 独家1.6T供应商(互动易)',pew:40},

    {c:'300394',m:0,n:'天孚通信',rk:'mid',rn:'[T1.5]CPO光引擎 年报未披露订单额',pew:55},

    {c:'300502',m:0,n:'新易盛',rk:'mid',rn:'[T1.5]800G/1.6T光模块 CPO布局(年报)',pew:40},

    {c:'002837',m:0,n:'英维克',rk:'mid',rn:'[T1.5]液冷 UQD/MQD进英伟达MGX生态[E1]',pew:45},

    {c:'002851',m:0,n:'麦格米特',rk:'mid',rn:'[T1.5]33kW电源 GB300配套(年报技术参数)',pew:35},

    {c:'002156',m:0,n:'通富微电',rk:'mid',rn:'[T2]Chiplet先进封装',pew:50},

    {c:'300567',m:0,n:'精测电子',rk:'mid',rn:'[设备]HBM老化测试研发中 MicroOLED检测独家订单(年报)',pew:60},

    {c:'300604',m:0,n:'长川科技',rk:'mid',rn:'[设备]HBM/DRAM测试分选机',pew:55},

    {c:'300346',m:0,n:'南大光电',rk:'mid',rn:'[T4]前驱体/电子特气',pew:70},

    {c:'688012',m:1,n:'中微公司',rk:'mid',rn:'[设备]刻蚀机 先进封装',pew:70},

    {c:'002371',m:0,n:'北方华创',rk:'mid',rn:'[设备]刻蚀/薄膜/TSV 年报未披露市占',pew:60},

  ],etfs:[

    {c:'159995',m:0,n:'芯片ETF'},{s:'NVDA',n:'NVIDIA',us:true,note:'英伟达'},

    {s:'SMH',n:'VanEck半导体',us:true,note:'全球半导体'},

  ]},

  ai_domestic:{name:'🧠 国产AI算力',watchlist:[

    {c:'688629',m:1,n:'华丰科技',rk:'high',rn:'高速连接器 华为第一大客户[E1] 防务核心供应商[E1] 年报未提224G',pew:150},

    {c:'002916',m:0,n:'深南电路',rk:'mid',rn:'PCB 910C基板份额超60%(互动易) 华为客户',pew:45},

    {c:'600584',m:1,n:'长电科技',rk:'mid',rn:'全球封测第三/大陆第一(ChipInsights)[E1] 年报未提昇腾/910C',pew:35},

    {c:'002156',m:0,n:'通富微电',rk:'mid',rn:'昇腾备份供应商',pew:50},

    {c:'301018',m:0,n:'申菱环境',rk:'mid',rn:'华为液冷客户之一 年报未称第一大',pew:60},

    {c:'002281',m:0,n:'光迅科技',rk:'mid',rn:'光模块 年报未提昇腾/华为',pew:45},

    {c:'002843',m:0,n:'泰嘉股份',rk:'mid',rn:'电源业务 年报未提昇腾/910C',pew:50},

    {c:'002837',m:0,n:'英维克',rk:'mid',rn:'液冷 华为/中兴客户[E1] 跨生态',pew:45},

  ],etfs:[{c:'159995',m:0,n:'芯片ETF'}]},

  space_domestic:{name:'🛰️ 中国商业航天',watchlist:[

    {c:'001270',m:0,n:'铖昌科技',rk:'high',rn:'星载/低轨相控阵芯片 进入核心供应商名录持续批量交付(互动易)',pew:120},

    {c:'600118',m:1,n:'中国卫星',rk:'mid',rn:'星网60%卫星制造',pew:80},

    {c:'002179',m:0,n:'中航光电',rk:'mid',rn:'防务首选供应商[E1] 高压连接器国内前列[E1] 年报未提蓝箭',pew:35},

    {c:'002361',m:0,n:'神剑股份',rk:'mid',rn:'复合材料 年报未提朱雀/蓝箭',pew:60},

    {c:'301517',m:0,n:'陕西华达',rk:'mid',rn:'射频连接器 星网二期',pew:55},

    {c:'300342',m:0,n:'天银机电',rk:'mid',rn:'星敏感器 互动易否认SpaceX合作',pew:50},

    {c:'300699',m:0,n:'光威复材',rk:'mid',rn:'碳纤维>60% 跨生态',pew:45},

  ],etfs:[{c:'563230',m:1,n:'富国卫星ETF'}]},

  robot_domestic:{name:'🤖 国产机器人',watchlist:[

    {c:'688017',m:1,n:'绿的谐波',rk:'high',rn:'谐波减速器全球唯一全自主[E1] 国内市场占有率全球领先[E1]',pew:200},

    {c:'603662',m:1,n:'柯力传感',rk:'mid',rn:'六维力传感器 50+家送样',pew:80},

    {c:'601689',m:1,n:'拓普集团',rk:'mid',rn:'线性执行器 跨生态 Tesla+国产',pew:40},

    {c:'601100',m:1,n:'恒立液压',rk:'mid',rn:'行星滚柱丝杠',pew:35},

    {c:'300124',m:0,n:'汇川技术',rk:'mid',rn:'新能源动力系统全球第三中国第一[E1:沙利文] PLC国内唯一安全认证[E1]',pew:45},

    {c:'300660',m:0,n:'江苏雷利',rk:'mid',rn:'[T2]国内唯一两种结构灵巧手量产[E1] 机器人电机组件 汽零+工控',pew:55},

  ],etfs:[]},

  lowalt_domestic:{name:'🚁 低空经济',watchlist:[

    {c:'688631',m:1,n:'莱斯信息',rk:'high',rn:'空管60-80% 物理开关13分',pew:100},

    {c:'000099',m:0,n:'中信海直',rk:'mid',rn:'海上油气直升机份额领先[E1] 低空经济布局 年报未称唯一',pew:50},

    {c:'688070',m:1,n:'纵横股份',rk:'mid',rn:'工业无人机 低空经济布局',pew:80},

    {c:'600038',m:1,n:'中直股份',rk:'mid',rn:'直升机总装 年报未披露份额',pew:45},

    {c:'600862',m:1,n:'中航高科',rk:'mid',rn:'预浸料80% 28家eVTOL供应商',pew:50},

  ],etfs:[]},



  custom:{name:'⭐ 自选',watchlist:[],etfs:[]},

};



// ═══ 参数配置（所有阈值集中管理，便于回测校准）═══

var PARAMS={

  // 评分权重

  wRSI_base:0.25,wMA_base:0.25,wVol_base:0.20,wBB_base:0.15,wFund_base:0.15,

  wRSI_trend:0.15,wMA_trend:0.35,wBB_trend:0.10,         // 趋势市调权

  wRSI_range:0.30,wMA_range:0.20,wBB_range:0.20,         // 震荡市调权

  wRSI_vol:0.20,wMA_vol:0.20,wVol_vol:0.10,wFund_vol:0.30, // 异常市调权

  wFin:0.08, // 财务维度固定权重

  // 技术指标参数

  rsiPeriod:14,maShort:5,maLong:20,bbPeriod:20,bbStd:2,

  // 环境判断阈值

  envTrendMA:0.05,envVolAnnual:0.08,envVolExtreme:2.5,envVolShrink:0.3,

  // 基本面过滤

  peWarn:200,pePenalty:10,criticalPenalty:15,criticalCap:40,highPenalty:5,

  // 回撤控制

  coolDays:30,coolCap:45,dynDays:90,dynLosses:2,dynCap:55,

  etfWeakDiscount:0.75,weeklyDivDiscount:0.88,volatileDiscount:0.85,

  // 资金流硬规则

  flowPersistCap:65,flowPersistDays:5,flowReverseCap:35,

  // 风控

  stopLoss:-0.08,takeProfit:0.15,ddTier1:5,ddTier2:8,ddTier3:10,

  ddScale1:0.6,ddScale2:0.3,

  // 仓位

  kellyDefault:15,kellyMax:30,positionMax:0.30,

  // 评分阈值

  buyThreshold:75,holdThreshold:60,sellThreshold:40,warnThreshold:25,

};

// ═══ 状态 ═════════════════════════════════════════

let cur='musk',prices={},kline={},scores={},pos=[],budget=2000,simPos=[],simBudget=100000,simMode=false,devicePixelRatio=window.devicePixelRatio||1;

let alerts=[],news=[],srcs={},klChart=null,klCode='',klPeriod='day',volHealth={};

let fc=0,runs=0,tradeHist=[],peakVal=0,ddLevel=0,smoothScores={},icMult={};



// ═══ 工具 ═════════════════════════════════════════

const $=s=>document.querySelector(s);

const fn=(n,d=2)=>Number(n).toFixed(d);

const fp=n=>(n>0?'+':'')+fn(n)+'%';

const fm=n=>{n=Number(n);return Math.abs(n)>=1e8?fn(n/1e8)+'亿':Math.abs(n)>=1e4?fn(n/1e4)+'万':fn(n)};var fmtM=fm;

const cv=s=>getComputedStyle(document.documentElement).getPropertyValue('--'+s).trim();



// ═══ 持久化 ═══════════════════════════════════════

function save(){

  try{localStorage.setItem('mx_p',JSON.stringify(prices));localStorage.setItem('mx_k',JSON.stringify(kline));localStorage.setItem('mx_o',JSON.stringify(pos));localStorage.setItem('mx_b',budget);localStorage.setItem('mx_h',JSON.stringify(tradeHist));localStorage.setItem('mx_pv',peakVal);localStorage.setItem('mx_cust',JSON.stringify(INDUSTRIES.custom.watchlist));localStorage.setItem('mx_sp',JSON.stringify(simPos));localStorage.setItem('mx_sb',simBudget);localStorage.setItem('mx_ss',JSON.stringify(smoothScores))}catch(e){}

}

function load(){

  try{const p=localStorage.getItem('mx_p');if(p)prices=JSON.parse(p);const k=localStorage.getItem('mx_k');if(k)kline=JSON.parse(k);const o=localStorage.getItem('mx_o');if(o)pos=JSON.parse(o);const b=localStorage.getItem('mx_b');if(b)budget=parseInt(b);const h=localStorage.getItem('mx_h');if(h)tradeHist=JSON.parse(h);const cu=localStorage.getItem('mx_cust');if(cu)INDUSTRIES.custom.watchlist=JSON.parse(cu);const sh=localStorage.getItem('mx_sh');if(sh)scoreHist=JSON.parse(sh);const nv=localStorage.getItem('mx_nv');if(nv)nvHistory=JSON.parse(nv);const sl=localStorage.getItem('mx_sl');if(sl)sigLog=JSON.parse(sl);const pv=localStorage.getItem('mx_pv');if(pv)peakVal=parseFloat(pv);const sp=localStorage.getItem('mx_sp');if(sp)simPos=JSON.parse(sp);const sb=localStorage.getItem('mx_sb');if(sb)simBudget=parseFloat(sb);const ss=localStorage.getItem('mx_ss');if(ss)smoothScores=JSON.parse(ss)}catch(e){}

}



// ═══ 数据获取（激进模式: 全试一遍） ═══════════════

var apiErrors={}, dataStale={}; // API统计+数据过期

async function tryFetch(url,opts={}){

  try{const r=await fetch(url,{cache:'no-cache',...opts});if(!r.ok){var h=new URL(url).hostname;apiErrors[h]=(apiErrors[h]||0)+1;return null}return r}catch(e){var h2='';try{h2=new URL(url).hostname}catch(x){}if(h2)apiErrors[h2]=(apiErrors[h2]||0)+1;return null}

}



async function doFetch(){

  const ind=INDUSTRIES[cur];let ok=0,total=ind.watchlist.length+ind.etfs.filter(e=>!e.us).length;



  // 源1: 腾讯HTTP（直连，不走代理，已确认能通）

  const aCodes=[...ind.watchlist,...ind.etfs.filter(e=>!e.us)];

  const tx=aCodes.map(s=>(s.m===1?'sh':'sz')+s.c).join(',');

  let r=await tryFetch('http://qt.gtimg.cn/q='+tx);

  if(r){const t=await r.text();for(const s of aCodes){const pf=s.m===1?'sh':'sz';const re=new RegExp('v_'+pf+s.c+'="([^"]*)"');const m=t.match(re);if(m){const f=m[1].split('~');if(f.length>=5){const pr=parseFloat(f[3]),pv=parseFloat(f[4]);prices[s.c]={n:f[1],p:pr,ch:pv?((pr-pv)/pv*100):0,o:parseFloat(f[5]),h:pr,l:pr,pc:pv,pe:0,mc:0,vol:f.length>6?parseFloat(f[6])||0:0};ok++}}}}

  srcs.tx={on:ok>0,n:'腾讯行情'};



  // 源2: 东方财富 via代理 (分批请求，避免URL过长)

  {var nonEtf=aCodes.filter(function(s){return!INDUSTRIES[cur].etfs.some(function(e){return e.c===s.c})});

    var batchSize=15;for(var bi=0;bi<nonEtf.length;bi+=batchSize){var batch=nonEtf.slice(bi,bi+batchSize);var emSecids=batch.map(function(s){return s.m+'.'+s.c}).join(',');

    r=await tryFetch(P+'/api/em/qt/ulist.np/get?fltt=2&secids='+emSecids+'&fields=f2,f3,f4,f5,f6,f12,f14,f15,f16,f17,f18,f20,f37,f38,f39,f40,f41,f42,f45,f116,f117,f124,f125,f137,f162&_='+Date.now());if(r){try{var j=await r.json();if(j.data&&j.data.diff){var items=j.data.diff;for(var di2=0;di2<items.length;di2++){var it=items[di2];var c2=it.f12;if(c2.charAt(0)=='5'||c2.charAt(0)=='1')continue;if(!prices[c2]){prices[c2]={};ok++}var pd=prices[c2];pd.n=it.f14;pd.p=it.f2;pd.ch=it.f3;pd.o=it.f17;pd.h=it.f15;pd.l=it.f16;pd.pc=it.f18;pd.pe=it.f117||it.f162;pd.mc=it.f20;pd.roe=it.f37;pd.eps=it.f38;pd.revG=it.f39;pd.prfG=it.f40;pd.grossM=it.f41;pd.debtR=it.f42;pd.netM=it.f45;pd.margin=it.f124;pd.marginChg=it.f137;if(!pd.vol)pd.vol=(it.f5||0)*100}}}catch(e){}}}}

  srcs.em={on:false,n:'东方财富'};



  // 美股ETF via代理

  for(const e of ind.etfs.filter(x=>x.us)){

    r=await tryFetch(P+'/api/yh/chart/'+e.s+'?interval=1d&range=2d');

    if(r){try{const j=await r.json();const m=j.chart.result[0].meta;prices[e.s]={n:e.n,p:m.regularMarketPrice,ch:0,pc:m.chartPreviousClose||m.previousClose,h:m.regularMarketDayHigh,l:m.regularMarketDayLow,pe:0,mc:0,us:true};ok++}catch(ee){}}

  }

  srcs.yh={on:ind.etfs.some(e=>e.us&&prices[e.s]),n:'Yahoo美股'};



  // K线: 腾讯 + Sina via代理

  // K线: 腾讯(并行加载+8秒超时)

  var klTasks=[];

  for(var si=0;si<ind.watchlist.length;si++){var s=ind.watchlist[si];

    if(kline[s.c]&&kline[s.c].length>=20)continue;

    var pf=s.m===1?'sh':'sz';

    klTasks.push((function(stock,pfx){

      return new Promise(function(resolve){

        var url=P+'/api/txk?param='+encodeURIComponent(pfx+stock.c+',day,,,60,qfq');

        var tid=setTimeout(function(){resolve()},8000);

        fetch(url,{cache:'no-cache'}).then(function(r){return r.json()}).then(function(j){

          clearTimeout(tid);

          if(j&&j.data&&j.data[pfx+stock.c]&&j.data[pfx+stock.c].qfqday){

            var raw=j.data[pfx+stock.c].qfqday;var arr=[];

            for(var di=0;di<raw.length;di++){var d=raw[di];arr.push({d:d[0],o:parseFloat(d[1]),c:parseFloat(d[2]),h:parseFloat(d[3]),l:parseFloat(d[4]),v:parseFloat(d[5])})}

            if(arr.length>0)kline[stock.c]=arr;

          }

          resolve();

        }).catch(function(){clearTimeout(tid);resolve()});

      });

    })(s,pf));

  }

  // 分批并行(每批3个)，避免打崩代理

  if(klTasks.length>0){for(var bi=0;bi<klTasks.length;bi+=5){await Promise.all(klTasks.slice(bi,bi+5))}}

  // 价格累积K线

  for(const s of aCodes){

    if(!prices[s.c])continue;var d=prices[s.c];

    if(!kline[s.c])kline[s.c]=[];

    var last=kline[s.c].length>0?kline[s.c][kline[s.c].length-1]:null;

    var today=new Date().toISOString().slice(0,10);

    if(!last||last.d!==today){kline[s.c].push({d:today,o:d.o||d.p,c:d.p,h:d.h||d.p,l:d.l||d.p,v:d.vol||0})}

    else{last.c=d.p;if(d.p>last.h)last.h=d.p;if(d.p<last.l)last.l=d.p}

    if(kline[s.c].length>200)kline[s.c].shift();

  }

  srcs.kl={on:Object.values(kline).some(function(k){return k&&k.length>=10}),n:'K线'};



  // 新闻 + 资金流向 (VPN已通, 走代理)

  // 新闻: 新浪财经(已确认可通)

  news=[];

  var kw=ind.name.slice(2);if(kw==='马斯克生态')kw='SpaceX';if(kw==='英伟达生态')kw='英伟达';

  r=await tryFetch(P+'/api/snews?pageid=153&lid=2509&k='+encodeURIComponent(kw)+'&num=6&page=1');

  if(r){try{var nj=await r.json();if(nj.result&&nj.result.data){var items=nj.result.data;for(var ndi=0;ndi<items.length;ndi++){var nd=items[ndi];if(nd.title)news.push({t:nd.title,url:nd.url||'',s:'新浪财经'})}}}catch(e){}}

  if(news.length===0){news.push({t:'📊 东方财富-板块行情',url:'https://quote.eastmoney.com/',s:'链接'});news.push({t:'📡 巨潮资讯',url:'http://www.cninfo.com.cn/',s:'链接'})}

  srcs.nw={on:news.length>2,n:'新闻(新浪)'};



  // 主力资金流向 — 浏览器直连HTTP(走VPN)

  var ffSecids=ind.watchlist.map(function(s){return s.m+'.'+s.c}).join(',');

  var ffUrl='http://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&secids='+ffSecids+'&fields=f12,f62,f63,f64,f184,f66&_='+Date.now();

  // 源1: 浏览器直连 源2: 代理

  r=await tryFetch(ffUrl);

  if(!r)r=await tryFetch(P+'/api/em/qt/ulist.np/get?fltt=2&secids='+ffSecids+'&fields=f12,f62,f63,f64,f184&_='+Date.now());

  if(r){try{var fj2=await r.json();if(fj2.data&&fj2.data.diff){for(var dfi=0;dfi<fj2.data.diff.length;dfi++){var di=fj2.data.diff[dfi];var code=di.f12;if(!prices[code])prices[code]={};var superF=di.f64||0,largeF=di.f63||0,totalF=di.f62||0;

    // 集中度: 超大单占总主力流的比例

    var conc='分散';if(Math.abs(superF)>Math.abs(totalF)*0.6&&Math.abs(totalF)>0)conc='集中';

    // 持续性: 追踪连续流入天数

    if(!prices[code]._flowHist)prices[code]._flowHist=[];prices[code]._flowHist.push(totalF>0?1:0);if(prices[code]._flowHist.length>10)prices[code]._flowHist.shift();

    var recent=prices[code]._flowHist;var streak=0;for(var fi2=recent.length-1;fi2>=0;fi2--){if(recent[fi2]===1)streak++;else break}

    var persist=streak>=5?'持续'+streak+'天':streak>=3?'跟踪'+streak+'天':streak>=1?'第'+streak+'天':'';

    var rating='';var score=0;if(conc==='分散')score+=2;if(streak>=5)score+=3;else if(streak>=3)score+=2;else if(streak>=1)score+=1;if(sizeNote==='大额')score+=3;else if(sizeNote==='正常')score+=2;else if(sizeNote==='小额')score+=1;if(totalF<0)score=0;

    if(score>=7)rating='机构建仓';else if(score>=5)rating='资金关注';else if(score>=3)rating='跟踪观察';else if(score>=1)rating='信号弱';else rating='';

    // 市值归一化: 主力净流入/流通市值

    var flowPctMC=0;if(prices[code].mc&&prices[code].mc>0)flowPctMC=(totalF/prices[code].mc*100);

    var sizeNote='';if(flowPctMC>0.5)sizeNote='大额';else if(flowPctMC>0.1)sizeNote='正常';else if(totalF!==0)sizeNote='小额';

    prices[code]._ff={main:totalF,ratio:di.f63||0,super:superF,large:largeF,small:di.f184||0,conc:conc,persist:persist,sizeNote:sizeNote,rating:rating}}}}catch(e){}}

  srcs.ff={on:ind.watchlist.some(function(s){return prices[s.c]&&prices[s.c]._ff&&prices[s.c]._ff.main!==undefined}),n:'资金流向'};if(srcs.ff.on)srcs.em.on=true;

  // 拉取真实财报数据(走代理避免CORS)

  for(var fii=0;fii<ind.watchlist.length;fii++){var fs2=ind.watchlist[fii];var prefix=fs2.m===1?'SH':'SZ';

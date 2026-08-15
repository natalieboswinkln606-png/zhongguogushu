# -*- coding: utf-8 -*-
"""l3_chenggu.py — L3-3 称骨算命（Rule-ID cg-01..cg-03）。
底本：《称骨歌》——托名袁天罡，无官方正典，通行口诀体系，版本异文较多（本模块 docstring 声明 + 输出 notes 声明）。

cg-01 四值骨重表（数据驱动）：
  年骨重：六十甲子各一支两数。口径=农历年（正月初一换年，shuowang.csv lunar_year）；
    异文=部分版本按立春年换年（与 M1 年柱同口径）——默认农历年并标注。
  月骨重：正月..十二月（闰月按同月骨重，与 oracle 声明一致）。
  日骨重：初一..三十（农历日）。
  时骨重：子..亥（子时统一=一两六钱）。异文=部分版本分早子晚子（23-24 点晚子配次日日柱）；
    本项目按 M1 时柱口径一致处理（真太阳时+子正换日），时支即 M1 时柱地支，不拆早晚子并标注。
cg-02 总骨重：四值求和（10 钱=1 两进位），输出"X两Y钱"。
cg-03 断语：《称骨歌》2.1~7.1 两共 51 档 + 7.2 两异文档（部分版本有 7.2，通行版止于 7.1；
    实测最大总骨重=1.9+1.8+1.8+1.6=7.1 两，7.2 无输入可达，仅附档供异文对照）。
    男女异文：通行版男女各一套（女版称"女命称骨歌"），男版=卜易居通行版、女版=astrologybazi 主流网络版；
    女版 2.1~7.1 档与男版逐档不同，男版档与女版档互不为异文，而是两套独立歌诀（男女别传版本异文）。

主数据=两 oracle 互证：卜易居（m.buyiju.com/cgsm/cgbiao.asp 2026-08-16 抓取）+ astrologybazi（astrologybazi.com/chenggu 同天抓取），年表 60 干两源全一致。
已知异文（详见 report/l3_chenggu_report.txt）：
  a) 二十日骨重：卜易居+通行版=1两5钱，astrologybazi=1两——主数据取 1两5钱，astrologybazi 值入 alt；
  b) 男命 3.6/3.9 两档诗：卜易居=通行版（3.6"不须劳碌过平生…"、3.9"此命终身运不通…"），astrologybazi 两档对调——主数据取卜易居，差异入 alt；
  c) 年骨重表另有异文版本（如癸卯六钱、甲辰一两四钱、丙午五钱、辛亥一两二钱派），主数据=两 oracle 互证值，异文派仅报告列名不查表。
输入=北京时间+东经（复用 m1 四柱内核：真太阳时+子正换日；年柱立春换年仅供显示对照，骨重不用）。
运行：python l3_chenggu.py --datetime '1984-02-02 10:00' --gender 男；--compare 对拍卜易居+astrologybazi。"""
import argparse, csv, json, os, random, re, sys, time
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m1

BASE = os.path.dirname(os.path.abspath(__file__))
MONTH_CN = "正二三四五六七八九十冬腊"  # 11 月=冬月、12 月=腊月（显示用）

# ---- cg-01 年骨重表（六十甲子，单位=钱；1 两=10 钱）。两 oracle（卜易居/astrologybazi）2026-08-16 抓取互证一致 ----
_Y = [12, 9, 6, 7, 12, 5, 9, 8, 7, 8, 15, 9, 16, 8, 8, 19, 12, 6, 8, 7, 5, 15, 6, 16, 15, 7, 9, 12, 10, 7,
      15, 6, 5, 14, 14, 9, 7, 7, 9, 12, 8, 7, 13, 5, 14, 5, 9, 17, 5, 7, 12, 8, 8, 6, 19, 6, 8, 16, 10, 6]
YEAR_BONE = {m1.GAN[(i % 10)] + m1.ZHI[(i % 12)]: v for i, v in enumerate(_Y)}  # 甲子=0 起 60 支
YEAR_SRC = "称骨歌年骨重表（卜易居+astrologybazi 两 oracle 互证一致，2026-08-16）"
YEAR_ALT = "异文：部分版本按立春年换年（M1 年柱口径）；另有癸卯六钱/甲辰一两四钱/丙午五钱/辛亥一两二钱派年表（本模块不采用）"

# ---- cg-01 月/日/时骨重表（钱）----
MONTH_BONE = [6, 7, 18, 9, 5, 16, 9, 15, 18, 8, 9, 5]        # 正月..十二月；闰月按同月（oracle 同口径）
DAY_BONE = [5, 10, 8, 15, 16, 15, 8, 16, 8, 16, 9, 17, 8, 17, 10, 8, 9, 18, 5, 15,  # 初一..二十
             10, 9, 8, 9, 15, 18, 7, 8, 16, 6]                                     # 廿一..三十
HOUR_BONE = [16, 6, 7, 10, 9, 16, 10, 8, 8, 9, 6, 6]          # 子..亥；子时统一（早子晚子异文见模块 docstring）
HOUR_SRC = "称骨歌时骨重表（两 oracle 一致）：子时一两六钱、丑时六钱、寅时七钱、卯时一两、辰时九钱、巳时一两六钱、午时一两、未时八钱、申时八钱、酉时九钱、戌时六钱、亥时六钱"

# ---- cg-03 断语：《称骨歌》男命版（卜易居通行版全文，2026-08-16 抓取；key=总钱数 21..71）----
MALE = {
    21: "短命非业谓大空，平生灾难事重重；凶祸频临陷逆境，终世困苦事不成。",
    22: "身寒骨冷苦伶仃，此命推来行乞人；劳劳碌碌无度日，终年打拱过平生。",
    23: "此命推来骨格轻，求谋作事事难成；妻儿兄弟应难许，别处他乡作散人。",
    24: "此命推来福禄无，门庭困苦总难荣；六亲骨肉皆无靠，流浪他乡作老翁。",
    25: "此命推来祖业微，门庭营度似稀奇；六亲骨肉如冰炭，一世勤劳自把持。",
    26: "平生衣禄苦中求，独自营谋事不休；离祖出门宜早计，晚来衣禄自无休。",
    27: "一生作事少商量，难靠祖宗作主张；独马单枪空做去，早年晚岁总无长。",
    28: "一生行事似飘蓬，祖宗产业在梦中；若不过房改名姓，也当移徒二三通。",
    29: "初年运限未曾亨，纵有功名在后成；须过四旬才可立，移居改姓始为良。",
    30: "劳劳碌碌苦中求，东奔西走何日休；若使终身勤与俭，老来稍可免忧愁。",
    31: "忙忙碌碌苦中求，何日云开见日头；难得祖基家可立，中年衣食渐无忧。",
    32: "初年运蹇事难谋，渐有财源如水流；到得中年衣食旺，那时名利一齐收。",
    33: "早年做事事难成，百年勤劳枉费心；半世自如流水去，后来运到始得金。",
    34: "此命福气果如何，僧道门中衣禄多；离祖出家方为妙，朝晚拜佛念弥陀。",
    35: "生平福量不周全，祖业根基觉少传；营事生涯宜守旧，时来衣食胜从前。",
    36: "不须劳碌过平生，独自成家福不轻；早有福星常照命，任君行去百般成。",
    37: "此命般般事不成，弟兄少力自孤行；虽然祖业须微有，来得明时去不明。",
    38: "一身骨肉最清高，早入簧门姓氏标；待到年将三十六，蓝衫脱去换红袍。",
    39: "此命终身运不通，劳劳作事尽皆空；苦心竭力成家计，到得那时在梦中。",
    40: "平生衣禄是绵长，件件心中自主张；前面风霜多受过，后来必定享安康。",
    41: "此命推来自不同，为人能干异凡庸；中年还有逍遥福，不比前时运来通。",
    42: "得宽怀处且宽怀，何用双眉皱不开；若使中年命运济，那时名利一起来。",
    43: "为人心性最聪明，作事轩昂近贵人；衣禄一生天注定，不须劳碌是丰亨。",
    44: "万事由天莫苦求，须知福碌赖人修；当年财帛难如意，晚景欣然便不优。",
    45: "名利推求竟若何？前番辛苦后奔波；命中难养男和女，骨肉扶持也不多。",
    46: "东西南北尽皆通，出姓移居更觉隆；衣禄无穷无数定，中年晚景一般同。",
    47: "此命推求旺末年，妻荣子贵自怡然；平生原有滔滔福，可卜财源若水泉。",
    48: "初年运道未曾通，几许蹉跎命亦穷；兄弟六亲无依靠，一生事业晚来整。",
    49: "此命推来福不轻，自成自立显门庭；从来富贵人钦敬，使婢差奴过一生。",
    50: "为利为名终日劳，中年福禄也多遭；老来是有财星照，不比前番目下高。",
    51: "一世荣华事事通，不须劳碌自亨通；弟兄叔侄皆如意，家业成时福禄宏。",
    52: "一世亨通事事能，不须劳苦自然宁；宗族欣然心皆好，家业丰亨自称心。",
    53: "此格推来福泽宏，兴家立业在其中；一生衣食安排定，却是人间一福翁。",
    54: "此格详采福泽宏，诗书满腹看功成；丰衣足食多安稳，正是人间有福人。",
    55: "走马扬鞭争利名，少年作事费筹论；一朝福禄源源至，富贵荣华显六亲。",
    56: "此格推来礼义通，一身福禄用无穷；甜酸苦辣皆尝过，滚滚财源盈而丰。",
    57: "福禄丰盈万事全，一生荣耀显双亲；名扬威震人争羡，此世逍遥宛似仙。",
    58: "平生福禄自然来，名利兼全福寿偕；金榜题名为贵客，紫袍玉带走金阶。",
    59: "细推此格妙且清，必定才高礼义通；甲第之中应有分，扬鞭走马显威荣。",
    60: "一朝金榜快题名，显祖荣宗大器成；衣禄定然原裕足，田园财帛更丰盈。",
    61: "不作朝中金榜客，定为世上大财翁；聪明天赋经书熟，名显高科自是荣。",
    62: "此命生来福不穷，读书必定显亲宗；紫衣金带为卿相，富贵荣华熟与同。",
    63: "命主为官福禄长，得来富贵实丰常；名题雁塔传金榜，大显门庭天下扬。",
    64: "此格威权不可当，紫袍金带尘高堂；荣华富贵谁能及，万古留名姓氏扬。",
    65: "细推此命福非轻，富贵荣华孰与争；定国安邦人极品，威声显赫震寰瀛。",
    66: "此格人间一福人，堆金积玉满堂春；从来富贵由天定，正笏垂绅谒圣君。",
    67: "此命生来福自宏，田园家业最高隆；平生衣禄丰盈足，一世荣华万事通。",
    68: "富贵由天莫苦求，万金家计不须谋；十年不比前番事，祖业根基水上舟。",
    69: "君是人间衣禄星，一生富贵众人钦；总然福禄由天定，安享荣华过一生。",
    70: "此命推来福禄宏，不须愁虑苦劳心；一生天定衣与禄，富贵荣华主一生。",
    71: "此命生成大不同，公侯卿相在其中；一生自有逍遥福，富贵荣华极品隆。",
}
# 异文档：astrologybazi 男命版 3.6/3.9 两档诗与通行版对调、4.1/4.3/4.7 等个别字词不同（详见报告异文清单）
MALE_ALT = {36: "astrologybazi 版此档为：此命终身运不通，劳劳作事尽皆空；苦心竭力成家计，到得那时在梦中。",
            39: "astrologybazi 版此档为：不须劳碌过平生，独自成家福不轻；早有福星常照命，任君行去百般成。"}

# ---- cg-03 女命称骨歌（女命版主流网络版=astrologybazi 2026-08-16 抓取；2.1..7.1 + 7.2 异文档）----
FEMALE = {
    21: "生身此命运不通，乌云盖月黑朦胧，莫向故园载花木，可来幽地种青松。",
    22: "此命孤冷有凄伶，此命推来路乞人，操心烦恼度平日，一生辛苦度光阴。",
    23: "此命推来骨肉轻，求财谋事事难成。弟妹六亲无有靠，繁绱家事难以持。",
    24: "此命推来福禄无，家务辛苦难以扶。丈夫儿女皆无靠，流落他乡作游孤。",
    25: "此命一身八字轻，六庭艰辛多苦凄。娘家六友冷如灰，一生操劳多忧心。",
    26: "平生衣禄苦寻求，女命生来带忧愁。辛酸苦辣皆尝过，晚年衣钵本无忧。",
    27: "生平做事少商量，难靠夫君做主张。心问口来口问心，自做主张过光阴。",
    28: "女命生来八字经，行善做事一无情。你把别人当亲生，别人对你假殷情。",
    29: "花枝艳来硬性身，自奔自力不求人。若向求财方可止，有苦有甜度光阴。",
    30: "此命推来比郎强，婚姻大事碍无妨。中年走过坎坷运，末年渐比先前强。",
    31: "早年行运在忙碌，劳碌奔波苦中求。自奔自愁把家立，后来晚景无忧愁。",
    32: "时逢吉神在运中，纵有凶处不为凶。真变假来假变真，结拜弟妹当亲生。",
    33: "八字命来张张薄，勤俭持家皆可过。年华空如流水过，末年运至受福禄。",
    34: "矮巴勾枣难捞枝，好人寻命不投机。谋望献身最费力，婚姻同移总是虚。",
    35: "女子走冰怕冰薄，交易出行犯琢磨。婚姻周郎休此意，官司口舌须要知。",
    36: "忧愁常锁两眉间，女命万绪挂心头。从今以后防口角，任意行而不相欠。",
    37: "此命来时运费多，此作推车受折磨。山路崎岖吊下耳，左插右安安不着。",
    38: "凤鸣岐山闻四方，女命逢之大吉昌。走失夫君音有信，晚年衣禄人财多。",
    39: "此命推来运不通，劳碌奔波一场空。好似俊鸟关笼中，中年末限起秋风。",
    40: "目上月令如运关，千心万苦受煎熬。女子苦难受过来，晚年福康比花艳。",
    41: "此命推来一般般，女子为人很非凡。中年逍遥多自在，晚年更比中年强。",
    42: "枯井破废已多年，一朝泉水出来鲜。资生济竭人称美，来运转喜自然时。",
    43: "推车靠涯道路赶，女命求财也费难。婚姻出行无阴碍，疾病口舌多安宁。",
    44: "夜梦金银醒来空，女子谋事运不能。婚姻难成交易获，夫君走失不见踪。",
    45: "此命终身驳杂多，六亲骨肉不相助。命中男妇都难养，劳碌辛苦还奔波。",
    46: "孤舟得水离沙滩，女命出外早远家。是非口舌皆无碍，婚姻合伙更不差。",
    47: "时来运转吉气发，多年枯木又开花。枝叶重生多茂盛，凡人见了凡人夸。",
    48: "一朵鲜花镜中开，看着极好取不来。劝你休把镜花想，女命推业主可怪。",
    49: "此命推来福不轻，女子随君显门庭。容貌美满热人爱，银钱富足过一生。",
    50: "马氏太公不相和，好命逢之尤凝多。恩人无义反成怨，是非平地起风波。",
    51: "肥羊失群入山岗，饿虎逢之把口张。适口充肠心欢喜，女命八安大吉昌。",
    52: "顺风行舟扯起棚，上天又助一顺风。不用费力逍遥去，任意而行大亨通。",
    53: "此命相貌眉活秀，文武双全功名成。一生衣禄皆无愁，可算世上有福人。",
    54: "学问满腹运气强，谋望求财大吉祥。交易出行大得意，是非口舌皆无妨。",
    55: "吉祥平安志量高，女命求财任逍遥。交易婚姻大有意，夫君在外有音耗。",
    56: "明珠书士离埃来，女命口角消散开。走失郎君当两归，交易有成水无灾。",
    57: "游鱼戏水被网惊，跳过龙门秧化龙。三根杨柳垂金线，万朵桃花显价能。",
    58: "此命推来转悠悠，时运未来莫强求。幸得今日重反点，自有好运在后头。",
    59: "雨雪载途泥泞至，交易不定难出行。疾病还拉慢婚姻，谋望求财事不成。",
    60: "女命八字喜气和，谋事求财吉庆多。口舌渐消疾病少，夫君走别归老窝。",
    61: "缘木求鱼事多端，虽不得鱼无后害。若是行险弄巧地，事不遂心枉安排。",
    62: "指日升高气象新，走来走去贵人亲。好命遇事遂心好，伺病口舌皆除根。",
    63: "五官脱运难抬头，女命须当把财求。交易少行有人助，疾病口舌不须愁。",
    64: "俊鸟曾得出笼中，脱离灾难显威风。一朝得意福立至，东南西北任意行。",
    65: "此命推来福不轻，慈善为事受人敬。天降文王开基业，富贵荣华八百年。",
    66: "时来运转锐气周，贤惠淑女君子求。钏鼓乐之大吉庆，女名逢之吉悠悠。",
    67: "乱丝无头定有头，碰着闲磨且暂推。交易出有无好处，谋事求财心不遂。",
    68: "水庭明月不可捞，女命早限命不高。交易出行难获得，末限命运渐渐好。",
    69: "太公封祖不非凡，女子求财稳如山。交易合伙大吉庆，疾病口角消除安。",
    70: "此命推来喜气新，郎君遇着多遂心。女命交了顺当运，富贵衣禄平乐生。",
    71: "此命推来鸿运交，再不需愁来苦劳。一生身有衣禄福，按享荣华在其中。",
    72: "此格世间罕有生，万中无一最超群。富贵荣华人敬仰，一生事业定乾坤。",  # 7.2 异文档（部分版本有；本模块 7.2 无输入可达，仅附对照）
}
POEM_SRC = {"男": "《称骨歌》男命版——卜易居通行版全文（2026-08-16 抓取）",
            "女": "《女命称骨歌》——astrologybazi 主流网络版（2026-08-16 抓取）"}
POEM_ALT = {"男": "异文：astrologybazi 男命版 3.6/3.9 两档诗对调、4.1/4.3/4.7 等个别字词不同（详见报告）；有版本 7.2 两档（本表不入档）",
            "女": "异文：女命歌诀无官方正典，网络各版 2.1~4.5 两档字句出入较多，此为主流网络版；男女两套歌诀为男女别传版本异文"}


def fmt(qian):
    """钱数 → "X两Y钱"（整两省略钱、纯钱省略两；qian=12→"1两2钱"、6→"6钱"）。"""
    l, q = qian // 10, qian % 10
    return f"{l}两" if q == 0 else f"{l}两{q}钱" if l else f"{q}钱"


def load_shuowang():
    """shuowang.csv（只读共享表）→ [(朔日 date, 月序, 闰标志, 农历年干支)]，按朔日排序。"""
    with open(os.path.join(BASE, "data", "shuowang.csv"), encoding="utf-8") as f:
        rows = [(datetime.strptime(r["shuo_time"][:10], "%Y-%m-%d").date(), int(r["month"]),
                 r["is_ruen"] == "1", r["lunar_year"]) for r in csv.DictReader(f)]
    rows.sort(key=lambda x: x[0])
    return rows


def lunar_of(shuo, d):
    """公历日期 → (农历年干支, 月序, 闰, 日序)。朔日表 1948-2101；d 取真太阳时日期（M1 子正换日口径）。"""
    for i, (s0, mo, ruen, ly) in enumerate(shuo):
        s1 = shuo[i + 1][0] if i + 1 < len(shuo) else s0 + timedelta(days=60)
        if s0 <= d < s1:
            return ly, mo, ruen, (d - s0).days + 1
    return None, None, None, None


def compute(dt, lon=120.0, gender="男", shuo=None):
    """(北京时 datetime, 东经, 性别) → 称骨 JSON dict；非法输入返回 {"error": ...}。"""
    r = m1.compute(dt, lon)
    if "error" in r:
        return r
    shuo = shuo if shuo is not None else load_shuowang()
    ts = datetime.strptime(r["true_solar_time"][:16], "%Y-%m-%dT%H:%M")  # 真太阳时（同 M1）
    lyr, lmo, lruen, lday = lunar_of(shuo, ts.date())
    if lyr is None:
        return {"error": f"错误: 真太阳时 {ts.date()} 落 shuowang 朔日表外（1948-2101）"}
    hzhi = m1.GAN.index  # noqa 保留导入可读性
    hour_zhi = r["pillars"]["hour"]["ganzhi"][1]  # M1 时柱地支（真太阳时+子正口径），骨重取子时统一表
    # cg-01 四值骨重
    yq = YEAR_BONE[lyr]                                   # 农历年（shuowang lunar_year，正月初一换年）
    mq = MONTH_BONE[lmo - 1]                              # 农历月（闰月按同月）
    dq = DAY_BONE[lday - 1]                               # 农历日
    hq = HOUR_BONE[m1.ZHI.index(hour_zhi)]                # 时辰
    bones = {
        "year": {"key": lyr, "weight": fmt(yq), "qian": yq, "rule_id": "cg-01",
                 "source": YEAR_SRC, "alt": YEAR_ALT},
        "month": {"key": ("闰" if lruen else "") + MONTH_CN[lmo - 1] + "月", "weight": fmt(mq), "qian": mq,
                  "rule_id": "cg-01", "source": "称骨歌月骨重表（两 oracle 一致）：正月六钱、二月七钱、三月一两八钱、四月九钱、五月五钱、六月一两六钱、七月九钱、八月一两五钱、九月一两八钱、十月八钱、十一月九钱、十二月五钱",
                  "alt": "异文：闰月取骨重有两种口径——按同月（本模块+oracle 声明）或按次月（不采用）"},
        "day": {"key": f"{lday}日", "weight": fmt(dq), "qian": dq, "rule_id": "cg-01",
                "source": "称骨歌日骨重表（初一五钱..三十日六钱；卜易居+通行版一致）",
                "alt": "异文：二十日骨重 astrologybazi 取 1两（卜易居+通行版=1两5钱，本模块取通行版）"},
        "hour": {"key": hour_zhi + "时", "weight": fmt(hq), "qian": hq, "rule_id": "cg-01",
                 "source": HOUR_SRC, "alt": "异文：早子晚子——部分版本分早晚子（23-24 点晚子按次日日柱起时），本模块按 M1 时柱口径统一子时骨重并标注；另有时辰取北京时间 vs 真太阳时两派，本模块同 M1 真太阳时"},
    }
    # cg-02 总骨重
    tot = yq + mq + dq + hq
    total = {"liang": tot // 10, "qian": tot % 10, "weight": fmt(tot), "rule_id": "cg-02",
             "source": "cg-02 四值求和：10 钱=1 两进位（年+月+日+时）"}
    # cg-03 断语（男女两套歌诀）
    table = MALE if gender == "男" else FEMALE
    poem = {"level": fmt(tot), "text": table.get(tot, f"此骨重 {fmt(tot)} 超出 2两1钱~7两1钱通行断语档（7两2钱为异文档，无输入可达）"),
            "gender": gender, "rule_id": "cg-03", "source": POEM_SRC[gender], "alt": POEM_ALT[gender]}
    if gender == "男" and tot in MALE_ALT:
        poem["alt"] += "；" + MALE_ALT[tot]
    return {
        "input": {"datetime": r["input"]["datetime"], "lon": lon, "tz": "UTC+8 北京时间",
                  "gender": gender, "true_solar_time": r["true_solar_time"]},
        "lunar": {"year_ganzhi": lyr, "month_name": ("闰" if lruen else "") + MONTH_CN[lmo - 1] + "月",
                  "day": lday, "is_ruen": bool(lruen), "source": "shuowang.csv（朔日表）"},
        "pillar_note": "年柱(m1 r3 立春换年)=" + r["pillars"]["year"]["ganzhi"] + "（仅对照；年骨重按农历年 cg-01 口径）",
        "bones": bones, "total": total, "poem": poem,
        "notes": ["底本：《称骨歌》——托名袁天罡，无官方正典，通行口诀体系，版本异文较多",
                  "年骨重按农历年（正月初一换年，shuowang.csv lunar_year）；异文=部分版本按立春年",
                  "时柱按 M1 口径（真太阳时+子正）；子时统一取一两六钱（不拆早晚子，异文已标注）"],
    }


def han_num(s):
    """汉字数字 → int（一~十；空→0）。"""
    if not s:
        return 0
    return {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}.get(s, 0)


def buyiju_oracle(yq, mq, dq, hq, timeout=20):
    """卜易居 oracle（m.buyiju.com/cgsm/，2026-08-16 实测）：表单 value=四值骨重钱数，服务器求和返回断语。
    返回 (总骨重文本, 断语歌诀首行)；需 ASPSESSIONID cookie（GET 后带 cookie POST，浏览器同构）。"""
    import urllib.request
    import urllib.parse
    import http.cookiejar
    cj = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    op.addheaders = [("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/151.0.0.0"),
                     ("Origin", "https://m.buyiju.com"), ("Referer", "https://m.buyiju.com/cgsm/"),
                     ("Accept", "text/html,*/*;q=0.8"), ("Accept-Language", "zh-CN,zh;q=0.9")]
    try:
        op.open("https://m.buyiju.com/cgsm/", timeout=timeout).read()  # 先 GET 取 ASP session cookie
        data = urllib.parse.urlencode({"year": yq, "month": mq, "day": dq, "hour": hq,
                                       "submit": "开始算命"}).encode()
        html = op.open("https://m.buyiju.com/cgsm/", data=data, timeout=timeout).read().decode("utf-8", "ignore")
    except Exception as e:
        return None, f"HTTP 失败: {e}"
    m = re.search(r"您的称骨算命结果如下：</p>\s*<p>\s*<b>([^<]+)</b>", html)
    if not m:
        m = re.search(r"骨重\s*<b>([^<]+)</b>", html)
    if m:
        return m.group(1).strip(), ""
    return None, "未匹配到结果（需人工检查页面）"


def compare():
    """对拍：5 锚点（农历四值→本地查表→卜易居）+ 15 随机样本，比总骨重（档位由总钱数决定）。
    astrologybazi 全链路（公历→农历→四值→总和→断语）对拍结果由浏览器侧写入 temp/cg_oracle_samples.json（见报告）。"""
    shuo = load_shuowang()
    out = []
    # 锚点 5 例（农历四值；期望=本地查表钱数，全链手算见报告）
    anchors = [  # (年干支, 月, 日, 时支序, 说明)
        ("甲子", 1, 1, 0, "甲子年正月初一子时"),
        ("癸亥", 12, 30, 6, "癸亥年腊月三十巳时"),
        ("庚午", 5, 15, 7, "庚午年五月十五午时"),
        ("庚辰", 7, 3, 2, "庚辰年七月初三寅时"),
        ("癸卯", 3, 20, 10, "癸卯年三月二十戌时"),
    ]
    cases = [(YEAR_BONE[g], MONTH_BONE[m - 1], DAY_BONE[d - 1], HOUR_BONE[z], note)
             for g, m, d, z, note in anchors]
    cases += [(yq, mq, dq, hq, "随机 " + note) for yq, mq, dq, hq, note in random_picks(shuo, 15)]
    same = diff = fail = 0
    for i, (yq, mq, dq, hq, note) in enumerate(cases):
        got, err = buyiju_oracle(yq, mq, dq, hq)
        if err or got is None:
            fail += 1
            out.append(f"  [{i + 1:02d}] {note} 年{yq}钱+月{mq}钱+日{dq}钱+时{hq}钱: oracle 失败 {err}")
            continue
        m = re.search(r"骨重([一二三四五六七八九十0-9.]+)两(?:([一二三四五六七八九十0-9.]+)钱)?", got)
        oq = (han_num(m.group(1)) * 10 if m.group(1) in "一二三四五六七八九十" else int(round(float(m.group(1)) * 10)))
        if m.group(2):
            oq += han_num(m.group(2)) if m.group(2) in "一二三四五六七八九十" else int(round(float(m.group(2))))
        exp = yq + mq + dq + hq
        if oq == exp:
            same += 1
        else:
            diff += 1
            out.append(f"  [分歧] {note} 本地 {exp}钱 vs oracle {oq}钱（oracle 文本: {got}）")
    out.insert(0, f"卜易居 oracle 对拍（农历四值直查，比总骨重与档位）：{len(cases)} 例，一致 {same}，分歧 {diff}，oracle 失败 {fail}")
    return out


def random_picks(shuo, n, seed=20260816):
    """1949-2100 均匀 15 例：随机公历日期 → 本地农历四值钱数+说明（供 buyiju POST 与 astrologybazi 全链路共用）。"""
    import random as rnd
    rnd.seed(seed)
    picked = []
    while len(picked) < n:
        y, mo = rnd.randint(1949, 2100), rnd.randint(1, 12)
        d = rnd.randint(1, 28)
        dt = datetime(y, mo, d, rnd.choice((8, 10, 12, 14, 16)))
        ts = m1.true_solar(dt, 120.0)
        lyr, lmo, lruen, lday = lunar_of(shuo, ts.date())
        if lyr is None:
            continue
        hz = m1.shichen(ts.hour)                     # 真太阳时 → 时辰支序（子正口径）
        picked.append((YEAR_BONE[lyr], MONTH_BONE[lmo - 1], DAY_BONE[lday - 1], HOUR_BONE[hz],
                       f"{dt:%Y-%m-%d %H:%M}→农历{lyr}年{('闰' if lruen else '') + MONTH_CN[lmo - 1] + '月'}{lday}日 {m1.ZHI[hz]}时"))
    return picked


def main():
    ap = argparse.ArgumentParser(description="称骨算命（Rule-ID cg-01..cg-03；底本《称骨歌》托名袁天罡，版本异文较多）")
    ap.add_argument("--datetime", help="北京时间 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0)
    ap.add_argument("--gender", choices=("男", "女"), default="男")
    ap.add_argument("--compare", action="store_true", help="对拍卜易居 oracle（农历四值直查总骨重/档位）")
    a = ap.parse_args()
    if a.compare:
        print("\n".join(compare()))
        return
    dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    print(json.dumps(compute(dt, a.lon, a.gender), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""l3_liuren.py — L3-3 六壬四课三传。底本：《六壬大全》卷一起例（日干寄宫/贼克/比用/涉害/遥克/昴星/别责/八专/伏吟/返吟口诀）
+ 卷三贵神式（贵神加于天盘贵人之支）；月将=中气换将（solar_terms.csv 中气，nr-01）；贵人歌诀（nr-02）；
四课 nr-03；三传九宗门 nr-04。占时=北京时间时辰（与易安居 oracle 同口径）；四柱=北京时易安居口径
（日干支=北京时当日、年柱=北京时立春判界、月柱=北京时节换月、时柱=北京时时支五鼠遁；跨子时窗口自洽）。
易安居实测口径：壬癸夜贵=亥；布向=落宫（亥子丑寅卯辰顺/巳午未申酉戌逆）。
差异无处藏身：每输出项带 Rule-ID/底本；对拍见 assert_l3_liuren.py。"""
import bisect, csv, json, os
from datetime import datetime, timedelta
from rules import GAN, ZHI, wx_of_gan, wx_of_zhi

BASE = os.path.dirname(os.path.abspath(__file__))
JIE, ZHONG = "节", "中气"

# ---- nr-01 月将：中气→月将（雨水亥、春分戌、谷雨酉、小满申、夏至未、大暑午、处暑巳、秋分辰、霜降卯、小雪寅、冬至丑、大寒子）----
ZHONG_QI = ["雨水", "春分", "谷雨", "小满", "夏至", "大暑", "处暑", "秋分", "霜降", "小雪", "冬至", "大寒"]
JIANG_OF = {q: ZHI[(11 - i) % 12] for i, q in enumerate(ZHONG_QI)}  # 雨水(0)→亥(11)…大寒(11)→子(0)

# ---- nr-02 贵人歌诀（《六壬大全》：甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸蛇兔藏，六辛逢马虎）----
# 易安居 oracle 实测校正：壬癸夜贵=亥（传统"蛇兔藏"为卯；易安居口径=巳/亥），nr-a01。
# 证据：十干昼夜贵全表本地断言 20 项 + 缓存 14 例对拍（昼贵样本）一致；夜贵未入网络对拍样本（按 nr-a01 口径锚定）。
GUIREN_OF = {"甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
             "乙": ("子", "申"), "己": ("子", "申"),
             "丙": ("亥", "酉"), "丁": ("亥", "酉"),
             "壬": ("巳", "亥"), "癸": ("巳", "亥"),
             "辛": ("午", "寅")}  # (昼贵, 夜贵)

# 日干寄宫（《六壬大全》：甲课寅兮乙课辰，丙戊课巳不须论，丁己课未庚申上，辛戌壬亥是其真，癸课原来丑宫坐，分明不用四正神）
JIGONG = {"甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳", "己": "未",
          "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"}

TIANJIANG = "贵蛇雀合勾龙空虎常玄阴后"  # 十二天将序：贵人起，顺/逆布
LIUQIN = ("比和", "父母", "官鬼", "子孙", "妻财")  # 六亲名：三传支五行对日干（生我父母、克我官鬼、同我兄弟、我生子孙、我克妻财）

def load_terms():
    """solar_terms.csv 全部行（节+中气）按 datetime 排序；中气=月将换将点。"""
    with open(os.path.join(BASE, "data", "solar_terms.csv"), encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f)]
    return sorted(rows, key=lambda r: r["datetime"])

_TERMS = None
def terms():
    global _TERMS
    if _TERMS is None:
        _TERMS = load_terms()
    return _TERMS

def hour_zhi_of(dt):
    """占时支（北京时，23/0→子…22→亥，子初口径=23 点起，与易安居一致）。"""
    return ZHI[(dt.hour + 1) // 2 % 12]

# 日柱锚点：2010-09-13=丙寅（易安居页面实测，13 例对拍锚点）
_DAY_ANCHOR = datetime(2010, 9, 13)

def day_ganzhi_of(dt):
    """易安居口径日柱：北京时日期当日干支（0 点换日，页面实测 9-23 23:00=丙子当日、12-29 00:00=癸丑当日，
    与 m1 真太阳时子正换日不同——跨子时窗口以北京时为准）。锚点法：2010-09-13=丙寅（干支序=2）。"""
    n = (2 + (dt.date() - _DAY_ANCHOR.date()).days) % 60
    return GAN[n % 10] + ZHI[n % 12]

def hour_ganzhi_of(dt, day_gan):
    """易安居口径时柱：时支=(h+1)//2（23 点=子时）；时干=五鼠遁（子时干=(2g)%10，逐时+1）。"""
    z = hour_zhi_of(dt)
    return GAN[(2 * GAN.index(day_gan) + ZHI.index(z)) % 10] + z

# ---- W2：四柱统一北京时口径（易安居页面同口径）。日干支=北京时当日（day_ganzhi_of 已实现）；
# 年柱=北京时日期立春判界、月柱=北京时节换月。旧实现年/月柱沿用 m1 真太阳时口径，跨子时窗口
# （北京时 23:5x，真太阳时已跨日）月柱按次日定位节气、日柱按当日，四柱不同日不自洽，已统一。----
_JIE_ORDER = ["立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "小寒"]  # 12 节月支序：寅=0…丑=11

def year_ganzhi_of(dt, term_rows=None):
    """北京时口径年柱：dt 时刻 ≥ 当年立春（北京时）→ 当年干支，否则上年；年干支=(y-4)%60（甲子=0）。"""
    term_rows = term_rows if term_rows is not None else terms()
    lc = next(r["datetime"] for r in term_rows if r["year"] == str(dt.year) and r["term"] == "立春")
    y = dt.year if dt.strftime("%Y-%m-%d %H:%M") >= lc else dt.year - 1
    return GAN[(y - 4) % 10] + ZHI[(y - 4) % 12]

def month_ganzhi_of(dt, year_gan, term_rows=None):
    """北京时口径月柱：dt 时刻 ≤ 最近上一 12 节（节换月）→ 月支序 m（寅=0…丑=11）；月干五虎遁=(2·年干+2+m)%10。"""
    term_rows = term_rows if term_rows is not None else terms()
    jie = sorted((r for r in term_rows if r["jie_zhong"] == "节"), key=lambda r: r["datetime"])
    i = bisect.bisect_right([r["datetime"] for r in jie], dt.strftime("%Y-%m-%d %H:%M")) - 1
    m = _JIE_ORDER.index(jie[i]["term"])
    return GAN[(2 * GAN.index(year_gan) + 2 + m) % 10] + ZHI[(2 + m) % 12]

def month_jiang(dt, term_rows=None):
    """nr-01 月将：中气交时刻换将（按 solar_terms.csv 精确时刻，交后即换）。
    证据：断言 B 组按表值交时 ±15min 锚定（大寒/谷雨 2024）+ 缓存 14 例月将对拍一致。"""
    term_rows = term_rows if term_rows is not None else terms()
    s = dt.strftime("%Y-%m-%d %H:%M")
    i = bisect.bisect_right([r["datetime"] for r in term_rows], s) - 1
    while i >= 0 and term_rows[i]["jie_zhong"] != ZHONG:
        i -= 1
    if i < 0:
        return None
    return JIANG_OF[term_rows[i]["term"]]

def gui_ren(day_gan, dt, zhouye=None):
    """nr-02 贵人：day_gan→(昼贵,夜贵)；占时卯~申=昼贵、酉~寅=夜贵（《六壬大全》旦暮分界；
    易安居 oracle 实测 17:00 整=酉时起夜贵，与卯酉分界一致）。zhouye 显式 '昼'/'夜' 时忽略占时。
    返回 (贵人支, 昼夜)。"""
    z = (dt.hour + 1) // 2 % 12
    is_day = 3 <= z <= 8  # 卯(3)~申(8)
    if zhouye == "昼":
        is_day = True
    elif zhouye == "夜":
        is_day = False
    return GUIREN_OF[day_gan][0 if is_day else 1], ("昼" if is_day else "夜")

def tian_pan(jiang, hour_zhi):
    """天盘[12]：月将加时——天盘 jiang 支加于地盘时支宫，余顺布；天盘[宫]=支。宫序=地支序（子=0）。"""
    j, h = ZHI.index(jiang), ZHI.index(hour_zhi)
    return [ZHI[(j + (i - h)) % 12] for i in range(12)]

def shen_jiang_pan(gui_zhi, zhouye, hour, pan):
    """天将[12]：贵神加于"天盘贵人之支所临之宫"（《六壬大全·贵神式》原文）起贵人，
    落宫=贵支在天盘所临之宫=pan.index(贵支)（四课 HTML 课3 上巳将空验证）。
    布向=落宫口诀（缓存 14 例对拍 + 贵人反推双向验证一致，与昼夜/zhouye 无关）：
    落宫亥子丑寅卯辰（宫序 11,0,1,2,3,4）→ 顺布；落宫巳午未申酉戌（宫序 5..10）→ 逆布。
    注：《六壬大全》本为"昼顺夜逆"，《六壬大全》卷三贵神式另有"临亥子丑寅卯辰顺行"一说，
    易安居采用后者（亦见"贵人式"口诀差异，详见报告与对拍日志）。zhouye 只影响贵支选择（gui_ren）。
    天将[宫]=天将名。"""
    pos = pan.index(gui_zhi)
    step = 1 if pos in (11, 0, 1, 2, 3, 4) else -1
    sj = [None] * 12
    for i in range(12):
        sj[(pos + i * step) % 12] = TIANJIANG[i]
    return sj

def si_ke(day_gan, day_zhi, pan, sj):
    """nr-03 四课：一课=干上神（日干寄宫的天盘支）、二课=一课支上神、三课=支上神、四课=三课支上神。
    返回 [ke1..ke4]，每课 {upper(上支), lower(下支/干), jiang(上支所乘天将)}；干课 lower=日干字。"""
    g = ZHI.index(JIGONG[day_gan])
    d = ZHI.index(day_zhi)
    u1 = pan[g]          # 一课：干寄宫宫位天盘支
    u2 = pan[ZHI.index(u1)]  # 二课
    u3 = pan[d]          # 三课：日支宫位天盘支
    u4 = pan[ZHI.index(u3)]  # 四课
    return [
        {"upper": u1, "lower": day_gan, "jiang": sj[g]},
        {"upper": u2, "lower": u1, "jiang": sj[ZHI.index(u1)]},
        {"upper": u3, "lower": day_zhi, "jiang": sj[d]},
        {"upper": u4, "lower": u3, "jiang": sj[ZHI.index(u3)]},
    ]

def ke_ke(upper, lower):
    """课内上下相克：返回 '克'(上克下)/'贼'(下贼上)/None。
    干课（课1）下神=日干五行（《六壬大全》涉害课例"午加庚金"：干课以下神五行论克，
    非日干寄宫支五行——易安居对拍修正）；余课下神=上支五行。"""
    if lower in GAN:
        uw, lw = wx_of_zhi(upper), wx_of_gan(lower)
    else:
        uw, lw = wx_of_zhi(upper), wx_of_zhi(lower)
    if uw == lw:
        return None
    from rules import ke as _ke
    if _ke(uw, lw):
        return "克"
    if _ke(lw, uw):
        return "贼"
    return None

def ke_lessons(sk):
    """四课中上下相克之课：[(课序0-3, '克'/'贼')]；干课按干寄宫支论克。"""
    out = []
    for i, k in enumerate(sk):
        r = ke_ke(k["upper"], k["lower"])
        if r:
            out.append((i, r))
    return out

def liu_qin(day_gan, zhi):
    """三传支五行对日干六亲：生我=父母、克我=官鬼、同我=兄弟、我生=子孙、我克=妻财。"""
    from rules import rel as _rel
    r = _rel(wx_of_zhi(zhi), wx_of_gan(day_gan))
    return {"比和": "兄弟", "生": "父母", "泄": "子孙", "克": "官鬼", "耗": "妻财"}[r]

def xun_shou(day_ganzhi):
    """日柱所在旬之首（甲子=0 甲戌=10…）：干支序 n=(6·干序−5·支序)%60（验证：甲午序 30、丙申序 32）；
    旬首=去个位（丙申序 32→30=甲午旬）。"""
    n = (6 * GAN.index(day_ganzhi[0]) - 5 * ZHI.index(day_ganzhi[1])) % 60
    return n - n % 10

def dun_gan(day_ganzhi, zhi):
    """三传遁干：支在日旬内→旬遁干，旬外→None（易安居口径：日旬遁干 scpf=0）。"""
    n = xun_shou(day_ganzhi)
    i = (ZHI.index(zhi) - n % 12) % 12
    if i >= 10:
        return None
    return GAN[(n + i) % 10]

# ---- nr-04 三传九宗门（《六壬大全》卷一起例口诀）----
XING = {}  # 地支三刑链：寅刑巳、巳刑申、申刑寅；丑刑戌、戌刑未、未刑丑；子刑卯、卯刑子
for a, b in [("寅", "巳"), ("巳", "申"), ("申", "寅"), ("丑", "戌"), ("戌", "未"), ("未", "丑"), ("子", "卯"), ("卯", "子")]:
    XING[a] = b
ZIXING = set("辰午酉亥")  # 自刑
MA = {"申": "寅", "子": "寅", "辰": "寅", "寅": "申", "午": "申", "戌": "申",
      "巳": "亥", "酉": "亥", "丑": "亥", "亥": "巳", "卯": "巳", "未": "巳"}  # 驿马
HE = {"甲": "己", "乙": "庚", "丙": "辛", "丁": "壬", "戊": "癸", "己": "甲", "庚": "乙", "辛": "丙", "壬": "丁", "癸": "戊"}  # 五合
BAZHUAN_DAYS = set("甲寅 乙卯 丁未 己未 庚申 辛酉 壬戌 癸丑".split())  # 八专日（干支同阴阳）

def san_zhong_mo(chu, pan):
    """中末传（《六壬大全》：初传之上名中次，中上加临是末居）：中传=初传上神、末传=中传上神。"""
    z = pan[ZHI.index(chu)]
    m = pan[ZHI.index(z)]
    return z, m

def _to_chuan(chu, pan, day_gan, day_ganzhi):
    """初传→三传列表 [{zhi, jiang_zi?}]；天将名须由调用方补（天将[宫]）。"""
    z, m = san_zhong_mo(chu, pan)
    return [chu, z, m]

def _bi_yong(sk, cands, day_gan):
    """比用（知一）：候选(课序, 克/贼)中上支与日干比和（同阴阳）者；返回比者列表（空=俱不比）。"""
    g_parity = GAN.index(day_gan) % 2
    return [c for c in cands if ZHI.index(sk[c[0]]["upper"]) % 2 == g_parity]

# 涉害藏干表（《六壬大全》涉害课原文例证实测破译：寅甲丙/卯乙/辰乙/巳丙戊/午丁/未己丁/申庚/酉辛/戌空/亥壬/子癸/丑己癸；
# 4 个原文例子全验证："丑加卯木，前行历辰中乙木一重"、"午加庚金，前行历酉辛金二重"（酉宫+戌中辛）、
# "戌加子水，前行历癸水一重"（丑中癸）、"巳上戊土、未土、未上己土，前又戌土，共四重"）
_CG2 = {
    "寅": ["甲", "丙"], "卯": ["乙"], "辰": ["乙"],
    "巳": ["丙", "戊"], "午": ["丁"], "未": ["己", "丁"],
    "申": ["庚"], "酉": ["辛"], "戌": [],
    "亥": ["壬"], "子": ["癸"], "丑": ["己", "癸"],
}

def _lower_wx(sk, lesson_i, day_gan):
    """课下神五行：课1=日干五行；课2=课1上支；课3=日支；课4=课3上支（均支五行）。"""
    if lesson_i == 0:
        return wx_of_gan(day_gan)
    if lesson_i == 1:
        return wx_of_zhi(sk[0]["upper"])
    if lesson_i == 2:
        return wx_of_zhi(sk[2]["lower"])
    return wx_of_zhi(sk[2]["upper"])

def _she_hai_depth(sk, pan, lesson_i, kind, day_gan):
    """涉害深度（《六壬大全》："涉害行来本家止，路逢多克为用取"——实测破译）：
    上神从加临宫顺行至本家（不含加临宫、含本家），途中每宫：
    宫位五行=下神五行→+1；宫中藏干五行=下神五行→+1。
    取深者用；深浅相等→见机（孟）察微（仲）复等（刚日干上/柔日支上）。"""
    upper = sk[lesson_i]["upper"]
    lwx = _lower_wx(sk, lesson_i, day_gan)
    start = pan.index(upper)
    end = ZHI.index(upper)
    cnt = 0
    i = (start + 1) % 12
    while True:
        b = ZHI[i]
        if wx_of_zhi(b) == lwx:
            cnt += 1
        for g in _CG2[b]:
            if wx_of_gan(g) == lwx:
                cnt += 1
        if i == end:
            break
        i = (i + 1) % 12
    return cnt

CHONG = {z: ZHI[(ZHI.index(z) + 6) % 12] for z in ZHI}  # 六冲

def san_chuan(sk, pan, day_gan, day_zhi, day_ganzhi):
    """九宗门三传主流程 → (课名/宗门, 三传支列表)。返吟/伏吟课体优先。"""
    fu = pan == list(ZHI)                       # 伏吟：天盘=地盘（月将=时支）
    fan = all(pan[i] == ZHI[(i + 6) % 12] for i in range(12))  # 返吟：天盘=地盘冲
    kl = ke_lessons(sk)                          # [(课序, '克'/'贼')]
    if fu:
        # 伏吟课体（页面原文实测 2026-08-16）：有克照常贼克——2010-07-24 乙亥课1 辰贼乙→初传辰/中亥/末巳、
        # 2010-08-03 乙酉→辰/酉/卯（初传=贼课上神，中末按伏吟刑推）；无克刚日干上/柔日支上直起。
        # 与《六壬大全》"伏吟有克照常贼克"一致（旧实现无条件走无克直起，有克初传分歧，已修）。
        if kl:
            chu, _ = _zei_ke_chu(sk, pan, day_gan, day_ganzhi, kl)
            return "伏吟课", _fu_yin_zhong_mo(chu, sk, pan)
        return _fu_yin_no_ke(sk, pan, day_gan, day_ganzhi)
    if fan:
        if kl:
            return _zei_ke_flow(sk, pan, day_gan, day_ganzhi, kl, "返吟")
        return _fan_yin_no_ke(sk, pan, day_gan, day_zhi, day_ganzhi)
    if kl:
        return _zei_ke_flow(sk, pan, day_gan, day_ganzhi, kl, None)
    # 无克：先遥克（蒿矢/弹射）→ 无遥克 → 八专/别责(课不全) → 昴星(课全)
    yaos = _yao_ke(sk, pan, day_gan, day_ganzhi)
    if yaos:
        return yaos
    if (day_gan + day_zhi) in BAZHUAN_DAYS:  # 八专日（壬戌等课全日亦在表内，须先查表）
        return _ba_zhuan(sk, pan, day_gan, day_ganzhi)
    uppers = set(k["upper"] for k in sk)
    if len(uppers) <= 2:          # 课不全=两课（八专：寄宫=日支，如甲寅/癸丑）
        return _ba_zhuan(sk, pan, day_gan, day_ganzhi)
    if len(uppers) == 3:          # 课不全=三课（别责）
        return _bie_ze(sk, pan, day_gan, day_zhi, day_ganzhi)
    return _ang_xing(sk, pan, day_gan, day_ganzhi)

def _zei_ke_chu(sk, pan, day_gan, day_ganzhi, kl):
    """有克链取初传（贼克→比用→涉害，《六壬大全》：取课先从下贼呼，如无下贼上克初…
    常将天日比神用…立法别有涉害陈）→ (初传支, 细分课名)。返吟/伏吟课体复用（照常贼克）。"""
    zei = [c for c in kl if c[1] == "贼"]
    ke = [c for c in kl if c[1] == "克"]
    if zei:
        base = "重审课" if len(zei) == 1 else None
        cands = zei
    else:
        base = "元首课" if len(ke) == 1 else None
        cands = ke
    if base:
        return sk[cands[0][0]]["upper"], base
    bi = _bi_yong(sk, cands, day_gan)
    if len(bi) == 1:
        return sk[bi[0][0]]["upper"], "知一课"
    # 俱比/俱不比：涉害
    depths = [(_she_hai_depth(sk, pan, i, kind, day_gan), i, kind) for i, kind in cands]
    mx = max(d[0] for d in depths)
    top = [d for d in depths if d[0] == mx]
    if len(top) == 1:
        return sk[top[0][1]]["upper"], "涉害课"
    # 深浅相等：孟神→见机；仲→察微；皆季→复等（柔辰刚日）
    meng = [d for d in top if pan.index(sk[d[1]]["upper"]) in (2, 5, 8, 11)]
    zhong = [d for d in top if pan.index(sk[d[1]]["upper"]) in (0, 3, 6, 9)]
    if meng:
        return sk[meng[0][1]]["upper"], "见机课"
    if zhong:
        return sk[zhong[0][1]]["upper"], "察微课"
    chu = sk[0]["upper"] if GAN.index(day_gan) % 2 == 0 else sk[2]["upper"]
    return chu, "复等课"

def _zei_ke_flow(sk, pan, day_gan, day_ganzhi, kl, body):
    """有克流程：贼克→比用→涉害取初传，中末=初传上神递推；课名按 body 归一（返吟课/伏吟课）。"""
    chu, name = _zei_ke_chu(sk, pan, day_gan, day_ganzhi, kl)
    name = {"返吟": "返吟课", "伏吟": "伏吟课"}.get(body, name)
    return name, _to_chuan(chu, pan, day_gan, day_ganzhi)

def _she_hai(sk, pan, day_gan, day_ganzhi, cands, body):
    depths = [(_she_hai_depth(sk, pan, i, kind, day_gan), i, kind) for i, kind in cands]
    mx = max(d[0] for d in depths)
    top = [d for d in depths if d[0] == mx]
    name = None
    if len(top) == 1:
        chu = sk[top[0][1]]["upper"]
        name = "涉害课"
    else:
        # 深浅相等：孟神（寅申巳亥）→见机；仲（子午卯酉）→察微；皆季→复等（柔辰刚日）
        meng = [d for d in top if pan.index(sk[d[1]]["upper"]) in (2, 5, 8, 11)]  # 临地盘为孟
        zhong = [d for d in top if pan.index(sk[d[1]]["upper"]) in (0, 3, 6, 9)]   # 临地盘为仲
        if meng:
            chu = sk[meng[0][1]]["upper"]
            name = "见机课"
        elif zhong:
            chu = sk[zhong[0][1]]["upper"]
            name = "察微课"
        else:
            chu = sk[0]["upper"] if GAN.index(day_gan) % 2 == 0 else sk[2]["upper"]  # 复等：刚日干上神、柔日支上神
            name = "复等课"
    if body:
        # 返吟有克（含涉害细分见机/察微/复等）课名一律归一"返吟课"（《六壬大全》返吟课体；
        # 原实现把涉害细分拼进课名输出"返吟见机"等非规范名，收尾修正）
        name = {"返吟": "返吟课", "伏吟": "伏吟课"}.get(body, name)
    return name, _to_chuan(chu, pan, day_gan, day_ganzhi)

def _yao_ke(sk, pan, day_gan, day_ganzhi):
    """遥克（无克课全）：蒿矢=二三四课上神遥克日干；弹射=日干遥克上神。
    多者→比用（知一）；俱比/俱不比→涉害（《六壬大全》遥克：无与日干比者涉害）。
    无遥克返回 None。"""
    from rules import ke as _ke
    gw = wx_of_gan(day_gan)
    yaos = []
    for i in (1, 2, 3):   # 二三四课之上神遥克日干（蒿矢）；日干遥克上神（弹射）
        if _ke(wx_of_zhi(sk[i]["upper"]), gw):
            yaos.append((i, "he"))
    if not yaos:
        for i in (1, 2, 3):
            if _ke(gw, wx_of_zhi(sk[i]["upper"])):
                yaos.append((i, "wo"))
    if not yaos:
        return None
    bi = _bi_yong(sk, yaos, day_gan)
    if len(bi) == 1:
        chu = sk[bi[0][0]]["upper"]
        name = "蒿矢课" if yaos[0][1] == "he" else "弹射课"
        return name, _to_chuan(chu, pan, day_gan, day_ganzhi)
    return _she_hai(sk, pan, day_gan, day_ganzhi, [(i, "克") for i, _ in yaos], None)

def _ang_xing(sk, pan, day_gan, day_ganzhi):
    """昴星（无克无遥克课全）：阳日=地盘酉宫之上神（虎视课），阴日=天盘酉所临地盘支（冬蛇掩目课）。
    中末传：阳日=支上/干上，阴日=干上/支上（《六壬大全》昴星：阳日先辰而后日，阴日先日而后辰）。"""
    if GAN.index(day_gan) % 2 == 0:
        chu = pan[9]  # 酉宫=9
        name = "虎视课"
        z, m = sk[2]["upper"], sk[0]["upper"]
    else:
        chu = ZHI[pan.index("酉")]
        name = "冬蛇掩目课"
        z, m = sk[0]["upper"], sk[2]["upper"]
    return name, [chu, z, m]

def _bie_ze(sk, pan, day_gan, day_zhi, day_ganzhi):
    """别责（课不全三课，无克无遥克）：刚日=日干五合之干寄宫上神为用（"刚日干合"）；
    柔日=日支三合局"前"一合支为用（本支，非其上神——易安居 2010-04-21 辛丑实测初传=巳=丑之三合前位）；
    中末传=干上神（"阴阳中末干中寄"）。
    锚点：1 例缓存对拍（2010-03-07 20:00 戊辰→寅=亥午午）+ 2 例手算（丙辰→亥、戊午→寅）。"""
    if GAN.index(day_gan) % 2 == 0:
        chu = pan[ZHI.index(JIGONG[HE[day_gan]])]
    else:
        # 支前三合：日支三合局中"前"一合支（申子辰局：辰前=申…即顺数四支；亥卯未局：未前=亥）
        he_zhi = {"申": "辰", "子": "申", "辰": "子", "寅": "戌", "午": "寅", "戌": "午",
                  "巳": "酉", "酉": "丑", "丑": "巳", "亥": "卯", "卯": "未", "未": "亥"}
        chu = he_zhi[day_zhi]
    return "别责课", [chu, sk[0]["upper"], sk[0]["upper"]]

def _ba_zhuan(sk, pan, day_gan, day_ganzhi):
    """八专（两课无克，干支同阴阳）：阳日=干上神顺数三（连本位数）、阴日=支上神逆数三；中末传=干上神。"""
    if GAN.index(day_gan) % 2 == 0:
        chu = ZHI[(ZHI.index(sk[0]["upper"]) + 2) % 12]
    else:
        chu = ZHI[(ZHI.index(sk[2]["upper"]) - 2) % 12]
    return "八专课", [chu, sk[0]["upper"], sk[0]["upper"]]

def _fu_yin_zhong_mo(chu, sk, pan):
    """伏吟中末刑推（《六壬大全》：迤逦刑之作中末）。
    初传非自刑→中=XING[初]；初传自刑：XING[初]有值（巳→申，寅巳申局）→中=XING[初]（丙子巳/申/寅）；
    无刑出（辰午酉亥）→日辰颠倒为中传（初=干上→中=支上；初=支上→中=干上）。
    末传：中在刑且 XING[中]≠初→XING[中]；XING[中]=初回环→中传之冲（己卯：刑[子]=卯=初→末=午）；
    中自刑（辰午酉亥）→中传之冲（壬午：中=午→末=子；乙亥：中=亥→末=巳；乙酉：中=酉→末=卯）。
    页面原文实测（2026-08-16 抓取）：2010-07-24 乙亥伏吟=辰/亥/巳、2010-08-03 乙酉伏吟=辰/酉/卯。"""
    if chu in ZIXING:
        if chu in XING:
            z = XING[chu]             # 巳刑申（寅巳申刑局）
        else:                          # 辰午酉亥：日辰颠倒
            z = sk[2]["upper"] if chu == sk[0]["upper"] else sk[0]["upper"]
    else:
        z = XING[chu]
    if z in XING and XING[z] != chu:
        m = XING[z]
    elif z in XING and XING[z] == chu:
        m = CHONG[z]          # 刑反指初传（回环）→中传之冲
    elif z in ZIXING:
        m = CHONG[z]          # 中传自刑（辰午酉亥）→中传之冲
    else:
        m = CHONG[chu]
    return [chu, z, m]

def _fu_yin_no_ke(sk, pan, day_gan, day_ganzhi):
    """伏吟无克（《六壬大全》伏吟：刚日干上神为用、柔日支上神为用，迤逦刑之作中末）。
    锚点：壬申亥/申/寅、丙子巳/申/寅、己酉酉/未/丑、己卯卯/子/午、壬午亥/午/子（5 例手算）；
    有克案例（乙亥/乙酉）见 san_chuan 伏吟有克路径与页面原文。"""
    chu = sk[0]["upper"] if GAN.index(day_gan) % 2 == 0 else sk[2]["upper"]
    return "伏吟课", _fu_yin_zhong_mo(chu, sk, pan)

def _fan_yin_no_ke(sk, pan, day_gan, day_zhi, day_ganzhi):
    """返吟无克（无依课）：初传=日支驿马（"井栏射"）；中传=日支宫上神（=日支之冲，返吟盘互冲）；
    末传=干上神。锚点：1 例缓存对拍（2010-01-21 12:00 辛未→巳/丑/辰）+ 2 例手算（丁丑亥/未/丑、己丑亥/未/丑）。"""
    chu = MA[day_zhi]
    z = pan[ZHI.index(day_zhi)]
    m = sk[0]["upper"]
    return "无依课", [chu, z, m]

def xing_nian(birth_year, sex, now_year):
    """行年本命（可选）：本命=生年干支（m1 年柱公式 (y-4)%60）；行年=易安居 oracle 实测公式：
    行年干支序=(now-birth+2)%60（男）、+4（女）。底本出处待考（《六壬大全》未载行年算法，nr-a04）。
    证据：本地断言 4 例 + 缓存页面实测 1 例（2010-09-13 1978 男→戊戌）。"""
    yg = GAN[(birth_year - 4) % 10] + ZHI[(birth_year - 4) % 12]
    n = (now_year - birth_year + (4 if sex == "女" else 2)) % 60
    return {"benming": yg, "xingnian": GAN[n % 10] + ZHI[n % 12],
            "rule_id": "nr-04（行年）", "source": "易安居 oracle 实测公式（男+2/女+4），底本出处待考"}

def compute(dt, lon=120.0, birth_year=None, sex="男", zhouye=None, term_rows=None):
    """(北京时 datetime, 东经) → 六壬四课三传 JSON。占时=北京时时支（易安居 oracle 同口径）。
    四柱=北京时易安居口径：日干支=北京时当日（day_ganzhi_of）、年柱=北京时立春判界（year_ganzhi_of）、
    月柱=北京时节换月（month_ganzhi_of）、时柱=北京时时支五鼠遁——跨子时窗口（23:5x-24:00 真太阳时跨日）
    四柱不自相矛盾（旧实现年/月柱沿用 m1 真太阳时口径与日柱不同日，W2 已统一）；
    月将=solar_terms.csv 中气。"""
    dgz = day_ganzhi_of(dt)
    day_gan, day_zhi = dgz[0], dgz[1]
    ygz = year_ganzhi_of(dt, term_rows)
    mgz = month_ganzhi_of(dt, ygz[0], term_rows)
    hz = hour_zhi_of(dt)
    jg = month_jiang(dt, term_rows)
    if jg is None:
        return {"error": f"错误: {dt} 之前无中气（月将无法定）"}
    gr, dn = gui_ren(day_gan, dt, zhouye)
    pan = tian_pan(jg, hz)
    sj = shen_jiang_pan(gr, zhouye, dt.hour, pan)
    sk = si_ke(day_gan, day_zhi, pan, sj)
    name, chuan = san_chuan(sk, pan, day_gan, day_zhi, dgz)
    chuan_out = [{"zhi": c, "jiang": sj[pan.index(c)], "liu_qin": liu_qin(day_gan, c),
                  "dun_gan": dun_gan(dgz, c)} for c in chuan]
    out = {
        "input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "lon": lon,
                  "tz": "UTC+8 北京时间", "birth_year": birth_year, "sex": sex},
        "pillars": {"year": ygz, "month": mgz,
                    "day": dgz, "hour": hour_ganzhi_of(dt, day_gan)},
        "month_jiang": {"zhi": jg, "rule_id": "nr-01",
                        "source": "《六壬大全》月将·太阳过宫（中气换将：雨水亥将…），solar_terms.csv 中气"},
        "gui_ren": {"zhi": gr, "day_night": dn, "rule_id": "nr-02",
                    "source": "《六壬大全》贵人歌诀：甲戊庚牛羊，乙己鼠猴乡，丙丁猪鸡位，壬癸蛇兔藏，六辛逢马虎；贵神加于天盘贵人之支，落宫亥子丑寅卯辰顺布、巳午未申酉戌逆布（易安居口径）"},
        "tiandi_pan": {"tian_pan": pan, "shen_jiang": sj,
                       "rule_id": "nr-01/nr-02", "source": "月将加时布天盘；贵神加临布天将"},
        "si_ke": {"ke": sk, "rule_id": "nr-03",
                  "source": "《六壬大全》日干寄宫：甲课寅兮乙课辰…；一课干上神、二课干上之上、三课支上神、四课支上之上"},
        "san_chuan": {"method": name, "chuan": chuan_out, "rule_id": "nr-04",
                      "source": "《六壬大全》卷一起例：贼克（取课先从下贼呼）→比用（常将天日比神用）→涉害（涉害行来本家止）→遥克（蒿矢/弹射）→昴星（阳仰阴俯）→别责（刚日干合）→八专（顺行三连本位数）→伏吟（刑）→返吟（井栏射）"},
        "xing_nian": xing_nian(birth_year, sex, dt.year) if birth_year else None,
        "notes": ["四柱=北京时易安居口径（日干支=北京时当日、年柱=北京时立春判界、月柱=北京时节换月、时柱=北京时时支五鼠遁；m1 真太阳时仅月将参考，跨 23-24 点子时窗口四柱不自相矛盾）",
                  "中末传=初传上神递推（《六壬大全》：初传之上名中次，中上加临是末居）"],
    }
    return out

def main():
    import argparse, sys
    ap = argparse.ArgumentParser(description="L3-3 六壬四课三传（九宗门）")
    ap.add_argument("--datetime", required=True, help="北京时间 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0)
    ap.add_argument("--birth-year", type=int, default=None)
    ap.add_argument("--sex", default="男", choices=["男", "女"])
    ap.add_argument("--zhouye", default=None, choices=["昼", "夜"])
    a = ap.parse_args()
    try:
        dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    except ValueError:
        sys.exit(f"错误: 日期格式应为 YYYY-MM-DD HH:MM，收到 {a.datetime!r}")
    print(json.dumps(compute(dt, a.lon, a.birth_year, a.sex, a.zhouye), ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()

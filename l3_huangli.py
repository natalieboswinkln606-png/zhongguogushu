# -*- coding: utf-8 -*-
"""l3_huangli.py — 黄历择吉模块（L3-8）：建除十二神(hl-01)/黄黑道十二神(hl-02)/每日宜忌神煞(hl-03)/择日接口(hl-04)。
底本：《协纪辨方书》（清乾隆官修，卷三建除月建、卷五黄黑道等神煞条）为主，辅《玉匣记》。
口径实测裁定（oracle：www.wnl.suanweilai.com 万年历黄历，2026-08 十日 + 2026-02 + 2020-01 互证，见 report/l3_huangli_report.txt）：
  ① 建除=节气月建：立春建寅、惊蛰建卯…小寒建丑，节当天整天换月（2026-08-07 立秋 19:43 当日即申月、02-04 立春当日即寅月实测）；
  ② 日黄黑道=按月建起：《协纪辨方书》卷五《考原》「寅申青龙起子、卯酉起寅、辰戌起辰、巳亥起午、子午起申、丑未起戌，顺行十二辰，月起日则建寅之月子日为青龙」；黄道六（青龙明堂金匮天德玉堂司命）黑道六（天刑朱雀白虎天牢玄武勾陈）；
  ③ 时黄黑道=按日支起：《考原》「日起时则子日申时起青龙」；任务书「寅日青龙起于申」系时辰口诀误植于日（异文标注）；
  ④ 月德/天德/月恩/咸池/驿马/劫煞/亡神/归忌/往亡/天德合/月德合=按农历月（2026-02-05 立春后腊月庚戌日 天德月德双命中实测，系农历丑月口径）；天赦/四废=按节气四季；
  ⑤ 建除配黄黑道（《协纪》卷七按语「今人以除危定执成开为黄道，建破平收满闭为黑道」）另列，与值神黄黑道并存。
差异无处藏身：每输出项带 rule_id/source/diff（异文标注）；宜忌为组合规则（项目规则化，非古籍逐字）。
输入=日期 YYYY-MM-DD（北京时间整天制）。运行 python l3_huangli.py --date 2026-08-16 / --pick / --compare。"""
import argparse, csv, json, os, random, re, sys, time
from datetime import datetime, date, timedelta

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from rules import GAN, ZHI

LUNAR_DAY = {1: "初一", 2: "初二", 3: "初三", 4: "初四", 5: "初五", 6: "初六", 7: "初七", 8: "初八", 9: "初九", 10: "初十",
             11: "十一", 12: "十二", 13: "十三", 14: "十四", 15: "十五", 16: "十六", 17: "十七", 18: "十八", 19: "十九",
             20: "二十", 21: "廿一", 22: "廿二", 23: "廿三", 24: "廿四", 25: "廿五", 26: "廿六", 27: "廿七", 28: "廿八",
             29: "廿九", 30: "三十"}

JIE = ["立春", "惊蛰", "清明", "立夏", "芒种", "小暑", "立秋", "白露", "寒露", "立冬", "大雪", "小寒"]  # 12 节（月建换月点），序=月支序-2
JIANCHU = "建除满平定执破危成收开闭"                 # 建除十二神序：建=0…闭=11
HUANGHEI = ("青龙", "明堂", "天刑", "朱雀", "金匮", "天德", "白虎", "玉堂", "天牢", "玄武", "司命", "勾陈")  # 黄黑道十二神序
HUANG = {"青龙", "明堂", "金匮", "天德", "玉堂", "司命"}   # 黄道六；黑道六=其余
JC_HH = {p: ("黄道" if p in "除危定执成开" else "黑道") for p in JIANCHU}  # 《协纪》卷七按语建除配黄黑道
# 建除吉凶属性表（吉/平/凶+宜忌要点）：整理口径=《协纪辨方书》建除条要旨+现代黄历通行，要点为规则化
BIG = {"建": ("吉", "宜出行、赴任、嫁娶；忌动土、开仓"), "除": ("吉", "宜扫舍、沐浴、治病、除旧布新"),
       "满": ("吉", "宜开市、交易、纳财、祈福；忌安葬"), "平": ("平", "宜平治道涂、修整；余事勿取"),
       "定": ("吉", "宜定盟、纳采、嫁娶、会亲友"), "执": ("平", "宜捕捉、安葬；忌开市、开仓"),
       "破": ("凶", "诸事不宜，忌行大事"), "危": ("凶", "宜祭祀；忌出行、嫁娶"),
       "成": ("吉", "宜嫁娶、开市、入学、上任、安葬"), "收": ("平", "宜纳财、收账、安葬；忌出行、开市"),
       "开": ("吉", "宜开市、出行、嫁娶、动土、上任"), "闭": ("凶", "宜安葬、塞穴；忌开市、出行")}

def load_terms():
    """solar_terms.csv 12 节 → {(date): 月支序}（立春→寅…小寒→丑）；lru 由调用方承担。"""
    out = {}
    with open(os.path.join(BASE, "data", "solar_terms.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["jie_zhong"] == "节":
                out[date.fromisoformat(r["datetime"][:10])] = (JIE.index(r["term"]) + 2) % 12
    return out

@__import__("functools").lru_cache(maxsize=None)
def load_shuo():
    """shuowang.csv 朔表 → [(朔date, 农历月号1-12, 闰标记, 农历年干支)] 按时间升序。"""
    rows = []
    with open(os.path.join(BASE, "data", "shuowang.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((date.fromisoformat(r["shuo_time"][:10]), int(r["month"]),
                         int(r["is_ruen"]), r["lunar_year"]))
    return sorted(rows)

def lunar_of(d):
    """公历日 → (农历月号, 闰?, 农历年, 农历日)；朔当天=初一（整天制）。"""
    prev = None
    for s in load_shuo():
        if s[0] > d:
            break
        prev = s
    return (prev[1], prev[2], prev[3], (d - prev[0]).days + 1)

def month_build(d):
    """节气月建支序：最近上一节（含当天）→ 寅=2…丑=1；节当天整天换月（oracle 实测口径）。"""
    m, last = month_build.terms, -2
    for k in sorted(m):
        if k <= d:
            last = m[k]
        else:
            break
    return last
month_build.terms = load_terms()

def jianchu_of(d, zhi):
    """建除序 = (日支−月建支) mod 12 → 建/除/满…；月建支=节气月建（hl-01）。"""
    return (ZHI.index(zhi) - month_build(d)) % 12

def huanghei_of(d, zhi):
    """日黄黑道序：青龙位=(2·月建−4) mod 12（寅申起子/卯酉起寅/辰戌起辰/巳亥起午/子午起申/丑未起戌），
    值神=(日支−青龙位) mod 12（hl-02，《协纪》卷五《考原》）。"""
    ql = (2 * month_build(d) - 4) % 12
    return (ZHI.index(zhi) - ql) % 12

def huanghei_hour_of(zhi, hour_zhi):
    """时黄黑道：按日支起（《考原》「子日申时起青龙」，青龙时支=(2·日支−4) mod 12），子时起轮排。"""
    ql = (2 * ZHI.index(zhi) - 4) % 12
    return (ZHI.index(hour_zhi) - ql) % 12

# ============================ hl-03 每日宜忌神煞（15 项） ============================
# 逐项：name → (rule_id, 判定函数返回命中与否, source, method, diff)。月均按农历月（oracle 实测口径）。
TIANDE = {"寅": "丁", "卯": "申", "辰": "壬", "巳": "辛", "午": "亥", "未": "甲",
          "申": "癸", "酉": "寅", "戌": "丙", "亥": "乙", "子": "巳", "丑": "庚"}   # 天德（干支兼取）
YUEDE = {"寅": "丙", "午": "丙", "戌": "丙", "申": "壬", "子": "壬", "辰": "壬",
         "亥": "甲", "卯": "甲", "未": "甲", "巳": "庚", "酉": "庚", "丑": "庚"}    # 月德（三合局）
YUEEN = {"寅": "丙", "卯": "丁", "辰": "庚", "巳": "己", "午": "戊", "未": "辛",
         "申": "壬", "酉": "癸", "戌": "庚", "亥": "乙", "子": "甲", "丑": "辛"}    # 月恩（月建所生，阴阳同配）
HE_GAN = {"甲": "己", "乙": "庚", "丙": "辛", "丁": "壬", "戊": "癸", "己": "甲", "庚": "乙", "辛": "丙", "壬": "丁", "癸": "戊"}
HE_ZHI = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
          "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
SANHE = {"寅": 0, "午": 0, "戌": 0, "申": 1, "子": 1, "辰": 1, "巳": 2, "酉": 2, "丑": 2, "亥": 3, "卯": 3, "未": 3}
YIMA = ("申", "寅", "亥", "巳")       # 驿马：三合局位序 → 马支
XIANCHI = ("卯", "酉", "午", "子")    # 咸池/桃花
JIESHA = ("亥", "巳", "寅", "申")     # 劫煞
WANGSHEN = ("巳", "亥", "申", "寅")   # 亡神
HONGYAN = {"甲": "午", "乙": "申", "丙": "寅", "丁": "未", "戊": "辰", "己": "辰",
           "庚": "戌", "辛": "酉", "壬": "子", "癸": "申"}                           # 红艳（日干起查日支）
SHIE = ("甲辰", "乙巳", "丙申", "丁亥", "戊戌", "己丑", "庚辰", "辛巳", "壬申", "癸亥")   # 十恶大败十日
TSHED = {0: "戊寅", 1: "甲午", 2: "戊申", 3: "甲子"}     # 天赦：节气四季（寅卯辰春…亥子丑冬）
SIFEI = {0: ("庚申", "辛酉"), 1: ("壬子", "癸亥"), 2: ("甲寅", "乙卯"), 3: ("丙午", "丁巳")}  # 四废
GUIJI = {1: "丑", 2: "寅", 3: "子", 4: "丑", 5: "寅", 6: "子", 7: "丑", 8: "寅", 9: "子", 10: "丑", 11: "寅", 12: "子"}
WANGWANG = {1: "寅", 2: "巳", 3: "申", 4: "亥", 5: "卯", 6: "午", 7: "酉", 8: "子", 9: "辰", 10: "未", 11: "戌", 12: "丑"}

def season_of(d):
    """节气四季序：寅卯辰=春0、巳午未=夏1、申酉戌=秋2、亥子丑=冬3（天赦/四废用）。"""
    return (month_build(d) - 2) % 12 // 3

def shensha_of(d):
    """每日神煞命中列表（hl-03，15 项）：各项含 rule_id/source/method/diff；月均=农历月支。"""
    gz = load_days().get(d.isoformat())
    if not gz:
        return None
    g, z = gz[0], gz[1]
    lm, ruen, ly, ld = lunar_of(d)
    mz = ZHI[(lm + 1) % 12]            # 农历月支（正月寅…腊月丑；闰月同号）
    sea = season_of(d)
    hits = []

    def add(rule_id, name, on, source, method, diff):
        if on:
            hits.append({"name": name, "rule_id": rule_id, "source": source, "method": method, "diff": diff})

    td = TIANDE[mz]
    add("hl-03-01", "月德", g == YUEDE[mz], "《协纪辨方书》月德条（三合局）",
        "寅午戌月丙、申子辰月壬、亥卯未月甲、巳酉丑月庚；日干命中之日",
        "异文：古法按节气月建起，oracle 实测按农历月（2026-02-05 腊月庚日命中）")
    add("hl-03-02", "天德", g == td if td in GAN else False, "《协纪辨方书》天德条",
        "正丁二申三壬四辛五亥六甲七癸八寅九丙十乙冬巳腊庚；oracle 实测民间黄历只认天德干（日干命中）",
        "异文①《协纪》原文干支兼取（二月申日亦为天德日），oracle 实测只认干：2026-03-11 卯月申日/1964-04-05 甲申日均无天德；②古法按节气月建起，oracle 按农历月（2026-02-05 腊月庚日命中）")
    add("hl-03-03", "月恩", g == YUEEN[mz], "《协纪辨方书》月恩条（月建所生之干，阴阳同配）",
        "正丙二丁三庚四己五戊六辛七壬八癸九庚十乙冬甲腊辛；日干命中",
        "异文①个别传本『冬丙腊丁』（子月取丙，五行不合）；②oracle 实测农历月口径")
    add("hl-03-04", "天赦", gz in TSHED.values() and TSHED[sea] == gz, "《协纪辨方书》天赦条",
        "春戊寅、夏甲午、秋戊申、冬甲子（按节气四季，日柱全配）",
        "异文：亦有按农历四季起派；oracle 对拍按节气四季")
    s = SANHE[mz]
    add("hl-03-05", "驿马", z == YIMA[s], "《协纪辨方书》驿马条（《历例》）",
        "寅午戌马申、申子辰马寅、巳酉丑马亥、亥卯未马巳（按月支三合）",
        "异文：日支起派/年支起派（八字神煞口径）；黄历实测按月支")
    add("hl-03-06", "咸池(桃花)", z == XIANCHI[s], "《协纪辨方书》咸池条（《历例》）",
        "寅午戌见卯、申子辰见酉、巳酉丑见午、亥卯未见子（按月支三合）",
        "异文：日支/年支起派；黄历实测按月支（2026-08-06 未月子日命中）")
    add("hl-03-07", "红艳", z == HONGYAN[g], "《渊海子平·论红艳煞》",
        "日干起查日支：甲午乙申丙寅丁未戊辰己辰庚戌辛酉壬子癸申",
        "异文：版本一致；黄历吉神凶煞多不列红艳，对拍不覆盖")
    add("hl-03-08", "劫煞", z == JIESHA[s], "《协纪辨方书》劫煞条",
        "寅午戌见亥、申子辰见巳、巳酉丑见寅、亥卯未见申（按月支三合）",
        "异文：日支/年支起派；黄历实测按月支")
    add("hl-03-09", "亡神", z == WANGSHEN[s], "《协纪辨方书》亡神条",
        "寅午戌见巳、申子辰见亥、巳酉丑见申、亥卯未见寅（按月支三合）",
        "异文：日支/年支起派；黄历实测按月支")
    add("hl-03-10", "四废", gz in SIFEI[sea], "《协纪辨方书》四废条",
        "春庚申辛酉、夏壬子癸亥、秋甲寅乙卯、冬丙午丁巳（按节气四季，日柱全配）",
        "异文：个别版本四季从农历起；oracle 实测 2026-08-06 夏壬子命中")
    add("hl-03-11", "十恶大败", gz in SHIE, "《三命通会·论十恶大败》（黄历择日同用）",
        "日柱逢甲辰乙巳丙申丁亥戊戌己丑庚辰辛巳壬申癸亥十日之一",
        "异文：个别传本『辛巳』作『辛亥』")
    th = TIANDE[mz]
    th2 = HE_GAN[th] if th in GAN else HE_ZHI[th]
    add("hl-03-12", "天德合", (g == th2 if th in GAN else z == th2), "《协纪辨方书》天德合条",
        "天德之合：正壬二巳三丁四丙五寅六己七戊八亥九辛十庚冬申腊乙（日干/日支命中）",
        "异文：个别传本末月『腊庚』；oracle 对拍按合化口径")
    add("hl-03-13", "月德合", g == HE_GAN[YUEDE[mz]], "《协纪辨方书》月德合条",
        "月德之五合：寅午戌月辛、申子辰月丁、亥卯未月己、巳酉丑月乙（日干命中）",
        "异文：版本一致")
    add("hl-03-14", "归忌", z == GUIJI[lm], "《协纪辨方书》归忌条（《玉匣记》同）",
        "正丑二寅三子循环（农历月）：忌嫁娶、移徙、入宅",
        "异文：按节气月起派；黄历实测按月（2026-08-06 六月子日命中）")
    add("hl-03-15", "往亡", z == WANGWANG[lm], "《协纪辨方书》往亡条",
        "正寅二巳三申四亥五卯六午七酉八子九辰十未冬戌腊丑（农历月）：忌出行、赴任",
        "异文：按节气月起派；黄历实测按月")
    return hits

# ============================ hl-01/02 日排（每日黄历主体） ============================
def daily(d, hour=None):
    """单日黄历 JSON（hl-01 建除+hl-02 黄黑道+hl-03 神煞+宜忌组合）；hour=时支（可选，时黄黑道）。"""
    gz = load_days().get(d.isoformat())
    if not gz:
        return {"error": f"{d} 落 ganzhi_days.csv 表外（1900-01-01~2100-12-31）"}
    lm, ruen, ly, ld = lunar_of(d)
    jc, hh = jianchu_of(d, gz[1]), huanghei_of(d, gz[1])
    jcn, hhn = JIANCHU[jc], HUANGHEI[hh]
    yi, ji = yi_ji_of(d, jc, hhn, gz)
    r = {"date": d.isoformat(), "ganzhi": gz,
         "lunar": f"{ly}年{'闰' if ruen else ''}农历{'一二三四五六七八九十冬腊'[lm - 1]}月{LUNAR_DAY[ld]}",
         "jianchu": {"name": jcn, "ji": BIG[jcn][0], "yiji_yao": BIG[jcn][1],
                     "rule_id": "hl-01", "source": "《协纪辨方书》卷三建除（节气月建：立春建寅…小寒建丑，节当天整天换月）",
                     "diff": "异文：民间黄历有按农历月建派（正月建寅，闰月同号）；oracle 实测节气口径（2026-08-07 立秋当日即申月）"},
         "huanghei": {"name": hhn, "dao": "黄道" if hhn in HUANG else "黑道", "rule_id": "hl-02",
                      "source": "《协纪辨方书》卷五黄黑道引《考原》：『寅申青龙起子、卯酉起寅、辰戌起辰、巳亥起午、子午起申、丑未起戌，顺行十二辰；月起日则建寅之月子日为青龙』",
                      "diff": "异文①任务书『寅日青龙起于申』系时辰口诀（日起时：子日申时起青龙）误植于日值神；②《玉匣记》日表派另有『辰戌起丑』传本，oracle 实测起辰"},
         "jianchu_huanghei": {"name": JC_HH[jcn], "rule_id": "hl-02b",
                              "source": "《协纪辨方书》卷七按语：『今人以除危定执成开为黄道，建破平收满闭为黑道』（建除配黄黑道，与值神黄黑道并存）",
                              "diff": "民间两套黄黑道并存：值神（青龙…勾陈）按月建起；建除配黄黑道按建除神名"},
         "shensha": {"rule_id": "hl-03", "source": "15 项择日神煞（月德/天德/月恩/天赦/驿马/咸池/红艳/劫煞/亡神/四废/十恶大败/天德合/月德合/归忌/往亡），月系项按农历月（oracle 实测），四季项按节气",
                     "hits": shensha_of(d)},
         "yi_ji": {"yi": yi, "ji": ji, "rule_id": "hl-03b",
                   "source": "宜忌生成=建除吉凶属性（hl-01 表）+神煞组合规则（项目规则化，非古籍原文逐字；与 oracle 宜忌列表重合率见对拍报告）",
                   "diff": "各黄历宜忌条目有出入（本站/汉程/中华万年历互异），组合规则以建除+神煞为准"}}
    if hour:
        r["huanghei_hour"] = {"hour_zhi": hour, "name": HUANGHEI[huanghei_hour_of(gz[1], hour)],
                              "rule_id": "hl-02h", "source": "《协纪辨方书》卷五黄黑道引《考原》：『日起时则子日申时起青龙』（按日支起，子时起轮排）",
                              "diff": "任务书『寅日青龙起于申』即此口诀（寅申日青龙起于子时）"}
    return r

def yi_ji_of(d, jc, hhn, gz):
    """宜忌组合规则（hl-03b）：建除吉凶（BIG）+神煞吉凶。吉神：天德/月德/月德合/天德合/天赦/月恩/驿马；凶神：四废/十恶大败/劫煞/亡神/归忌/往亡。"""
    hits = {h["name"] for h in shensha_of(d)}
    yi = set()
    if hhn in HUANG:          # 值神黄道
        yi.add("开光")
    jn = JIANCHU[jc]
    if BIG[jn][0] == "吉":
        yi |= {"祭祀", "祈福", "出行", "会亲友"}
    elif BIG[jn][0] == "平":
        yi |= {"祭祀"}
    if hits & {"天德", "月德"}:
        yi |= {"祈福", "嫁娶", "开市"}
    if hits & {"天德合", "月德合"}:
        yi |= {"订盟", "纳采"}
    if hits & {"天赦"}:
        yi |= {"解除", "沐浴"}
    if hits & {"月恩"}:
        yi |= {"栽种", "纳财"}
    if hits & {"驿马"}:
        yi |= {"出行", "赴任"}
    if "成" == jn or "开" == jn:
        yi |= {"开市", "嫁娶"}
    if "定" == jn:
        yi |= {"定盟", "纳采"}
    if "除" == jn:
        yi |= {"扫舍", "沐浴"}
    if "满" == jn:
        yi |= {"交易", "纳财"}
    ji = set()
    if hhn not in HUANG:      # 值神黑道
        ji.add("远行")
    if BIG[jn][0] == "凶":
        ji |= {"动土", "开市", "出行"}
    elif "破" == jn:
        ji |= {"诸事不宜"}
    if "危" == jn:
        ji |= {"出行", "嫁娶"}
    if "闭" == jn:
        ji |= {"开市", "出行"}
    if hits & {"四废"}:
        ji |= {"开市", "嫁娶", "安葬"}
    if hits & {"十恶大败"}:
        ji |= {"开市", "安葬"}
    if hits & {"归忌"}:
        ji |= {"嫁娶", "移徙", "入宅"}
    if hits & {"往亡"}:
        ji |= {"出行", "赴任"}
    if hits & {"劫煞", "亡神"}:
        ji |= {"开市", "嫁娶"}
    return sorted(yi) if yi else ["馀事勿取"], sorted(ji) if ji else ["诸事不宜"]

def load_days():
    """ganzhi_days.csv → {date: 干支}（只读共享）。"""
    with open(os.path.join(BASE, "data", "ganzhi_days.csv"), encoding="utf-8") as f:
        return {r["date"]: r["ganzhi"] for r in csv.DictReader(f)}

# ============================ hl-04 择日接口 ============================
PURPOSE = {  # 用途 → (宜吉神, 宜建除, 忌凶神, 忌建除)；组合规则为项目规则化（异文：各黄历用途匹配不一）
    "嫁娶": (("天德", "月德", "天德合", "月德合"), ("成", "定", "开"), ("四废", "十恶大败", "归忌"), ("破", "闭", "危")),
    "出行": (("驿马",), ("开", "满", "成"), ("往亡", "四废", "十恶大败"), ("破", "危", "闭")),
    "开工": (("天德", "月德", "月恩"), ("开", "成", "满"), ("四废", "十恶大败"), ("破", "闭")),
    "动土": (("月恩", "天赦"), ("除", "满", "定", "成"), ("四废", "十恶大败"), ("破", "危")),
    "交易": (("月恩", "天德合", "月德合"), ("满", "定", "成"), ("四废",), ("破", "闭")),
    "开市": (("天德", "月德", "月恩"), ("开", "成", "满"), ("四废", "十恶大败"), ("破", "闭")),
    "入宅": (("天德", "月德", "驿马"), ("开", "成", "定"), ("四废", "十恶大败", "归忌"), ("破", "闭")),
    "安葬": (("天德", "月德", "天赦"), ("成", "收", "定"), ("四废", "十恶大败"), ("破", "开", "闭")),
}

def pick_days(start, end, purpose, top=10):
    """择日接口（hl-04）：时段[start,end]+用途 → 按分值降序 TopN 吉日候选（每候选附依据神煞）。
    评分=黄道+6 吉建除+4 吉神+2/项 黑道−6 凶建除−4 凶神−4/项（组合规则为启发式，非神断）。"""
    gy, gj, bj, bjc = PURPOSE.get(purpose, ((), (), (), ()))
    out = []
    d = start
    while d <= end:
        gz = load_days().get(d.isoformat())
        if not gz:
            d += timedelta(days=1)
            continue
        jc, hh = jianchu_of(d, gz[1]), huanghei_of(d, gz[1])
        jcn, hhn = JIANCHU[jc], HUANGHEI[hh]
        names = {h["name"] for h in shensha_of(d)}
        score = 6 if hhn in HUANG else -6
        score += 4 if jcn in gj else -4 if jcn in bjc else 0
        for n in names:
            score += 2 if n in gy else -4 if n in bj else 0
        basis = {"jianchu": jcn, "huanghei": f"{hhn}（{'黄道' if hhn in HUANG else '黑道'}）",
                 "ji_shen": sorted(names & set(gy)), "xiong_shen": sorted(names & set(bj))}
        out.append((score, d, basis))
        d += timedelta(days=1)
    out.sort(key=lambda x: -x[0])
    return {"purpose": purpose, "range": [start.isoformat(), end.isoformat()], "top": top,
            "rule_id": "hl-04",
            "source": "择日评分=值神黄黑道+建除吉凶+神煞组合（规则启发式，非神断；宜忌组合规则为项目规则化）",
            "diff": "各家择日评分体系不一，本模块为公开口径的组合启发式，供参考",
            "candidates": [{"date": d.isoformat(), "ganzhi": load_days()[d.isoformat()], "score": s, "basis": b}
                           for s, d, b in out[:top]]}

# ============================ 对拍（--compare） ============================
URL = "http://www.wnl.suanweilai.com/wnl/{y}{m}{d}.html"   # 万年历黄历 oracle（支持 1949-2100 历史日期，实测 2020/2026 均通）

def fetch_oracle(ds):
    """抓 oracle 单日：建除/值神/吉神宜趋/凶煞宜忌 → dict 或 None。"""
    d = date.fromisoformat(ds)
    try:
        h = __import__("requests").get(URL.format(y=d.year, m=f"{d.month:02d}", d=f"{d.day:02d}"), timeout=30).text
    except Exception:
        return None
    jc = re.search(r"jianchuTxt\">\s*([建除满平定执破危成收开闭])日", h)
    zs = re.search(r"zsTxt\">\s*([青龙明堂天刑朱雀金匮天德白虎玉堂天牢玄武司命勾陈]{2})（([黄黑])道日）", h)
    if not jc or not zs:
        return None
    js = re.search(r"jsTxt\">\s*([^<]{2,120}?)</div>", h)
    xs = re.search(r"xsTxt\">\s*([^<]{2,120}?)</div>", h)
    return {"jianchu": jc.group(1), "huanghei": zs.group(1),
            "js": set(js.group(1).split()) if js else set(),
            "xs": set(xs.group(1).split()) if xs else set()}

# oracle 万年历黄历吉神/凶煞列表实测仅覆盖：月德/天德/月恩/驿马/咸池/四废/归忌/劫煞；
# 亡神/往亡/天赦/十恶大败/天德合/月德合/红艳 oracle 不列，对拍不覆盖（同 l3_shensha 红鸾处理）
O_MAP = {"月德": "月德", "天德": "天德", "月恩": "月恩", "驿马": "驿马",
         "咸池(桃花)": "咸池", "四废": "四废", "归忌": "归忌", "劫煞": "劫煞"}

def cmp_case(ds):
    o, m = fetch_oracle(ds), daily(date.fromisoformat(ds))
    if o is None or "error" in m:
        return None, "oracle 抓取失败" if o is None else "自研 out_of_range"
    diffs = []
    if o["jianchu"] != m["jianchu"]["name"]:
        diffs.append(f"建除 oracle[{o['jianchu']}] vs 自研[{m['jianchu']['name']}]")
    if o["huanghei"] != m["huanghei"]["name"]:
        diffs.append(f"值神 oracle[{o['huanghei']}] vs 自研[{m['huanghei']['name']}]")
    mc = {O_MAP[x["name"]] for x in m["shensha"]["hits"] if x["name"] in O_MAP}
    oc = (o["js"] | o["xs"]) & set(O_MAP.values())
    if oc != mc:
        diffs.append(f"神煞 oracle[{'/'.join(sorted(oc)) or '无'}] vs 自研[{'/'.join(sorted(mc)) or '无'}]")
    return ("same" if not diffs else "diff"), "；".join(diffs) or "一致"

def rnd_cases(seed, count):
    """随机日期集（1949-2100 均匀，random.seed 固定可复现）。"""
    random.seed(seed)
    out = []
    while len(out) < count:
        d = date(random.randint(1949, 2100), random.randint(1, 12), random.randint(1, 28))
        if d.isoformat() not in out:
            out.append(d.isoformat())
    return out

def verify_batch(cases, tag):
    """对拍一组用例：cases=日期列表，tag=申报 ID 前缀（hl-a 锚点/hl-r 主段随机/hl-v 复验）。
    比对项：建除神名/黄黑道值神/神煞命中集（oracle 吉神凶煞并集 ∩ 共同名集）；分歧按 I-8 申报（幂等）。"""
    same = diff = out = 0
    nd, arbs, brows = [], [], []
    for i, ds in enumerate(cases):
        kind, note = cmp_case(ds)
        if kind is None:
            out += 1
            continue
        if kind == "same":
            same += 1
        else:
            diff += 1
            nd.append((ds, note))
            cid = f"hl-{tag}{i + 1:02d}"
            arbs.append([cid, "黄历建除/黄黑道/神煞", "oracle 侧", "自研侧", "复核者", "alt",
                         f"黄历分歧 {ds}：{note}", "oracle 对拍", "自研 l3_huangli.py（hl-01..03）", "算未来万年历 suanweilai.com"])
            brows.append([cid, "黄历分歧", ds, "oracle 万年历黄历", "自研黄历", "arbitrated", note])
    return same, diff, out, nd, arbs, brows

def compare():
    """对拍：5 锚点（2026-08-12..16 手算+oracle 双查）+15 随机（seed=20260816）+复验 15 随机（seed=999）；
    两段共 35 例（1949-2100 均匀，随机序列 seed 固定可复现）；分歧按 I-8 申报（幂等）。"""
    ANCHORS = ["2026-08-12", "2026-08-13", "2026-08-14", "2026-08-15", "2026-08-16"]
    a_same, a_diff, a_out, a_nd, a_arbs, a_brows = verify_batch(ANCHORS, "a")
    r_same, r_diff, r_out, r_nd, r_arbs, r_brows = verify_batch(rnd_cases(20260816, 15), "r")
    v_same, v_diff, v_out, v_nd, v_arbs, v_brows = verify_batch(rnd_cases(999, 15), "v")
    arbs, brows = a_arbs + r_arbs + v_arbs, a_brows + r_brows + v_brows
    def existing(path):
        try:
            return {x["case_id"] for x in csv.DictReader(open(os.path.join(BASE, path), encoding="utf-8"))
                    if x.get("case_id") and not x["case_id"].startswith("#")}
        except FileNotFoundError:
            return set()
    for fn, rows in (("data/arbitration_log.csv", arbs), ("report/boundary_cases.csv", brows)):
        seen = existing(fn)
        rows = [x for x in rows if x[0] not in seen]
        if rows:
            with open(os.path.join(BASE, fn), "a", encoding="utf-8", newline="") as f:
                csv.writer(f).writerows(rows)
    s, d, o = a_same + r_same + v_same, a_diff + r_diff + v_diff, a_out + r_out + v_out
    tot = 5 + 15 + 15
    rep = [f"L3-8 黄历择吉对拍（l3_huangli.py）：{tot} 例 = 5 锚点（2026-08-12..16）+30 随机（1949-2100 均匀，seed=20260816 与 seed=999 各 15）",
           f"算未来万年历黄历：建除/值神/神煞共同名集比对 一致 {s}/{tot - o}；分歧 {d}；oracle 抓取失败 {o}"]
    rep.append(f"  主段 20/20（锚点 5+seed=20260816 随机 15）：一致 {a_same + r_same}/{20 - a_out - r_out}")
    rep.append(f"  复验 15 例（seed=999 另一种子）：一致 {v_same}/{15 - v_out}")
    for ds, note in a_nd + r_nd + v_nd:
        rep.append(f"  分歧：{ds} {note}")
    rep.append(f"申报：arbitration_log.csv hl- 新增 {len(arbs)} 条；boundary_cases.csv hl- 新增 {len(brows)} 条（幂等）")
    return rep

def main():
    ap = argparse.ArgumentParser(description="黄历择吉（建除/黄黑道/神煞/择日，Rule-ID hl-01..04）")
    ap.add_argument("--date", help="单日黄历 YYYY-MM-DD")
    ap.add_argument("--hour", help="时支（可选，输出时黄黑道）")
    ap.add_argument("--pick", nargs="*", help="择日：起 止 用途 [top]")
    ap.add_argument("--compare", action="store_true", help="对拍算未来万年历黄历")
    a = ap.parse_args()
    if a.compare:
        print("\n".join(compare()))
        return
    if a.pick:
        p = a.pick
        r = pick_days(date.fromisoformat(p[0]), date.fromisoformat(p[1]), p[2], int(p[3]) if len(p) > 3 else 10)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    d = date.fromisoformat(a.date)
    print(json.dumps(daily(d, a.hour), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

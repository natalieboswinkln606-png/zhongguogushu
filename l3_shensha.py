# -*- coding: utf-8 -*-
"""l3_shensha.py — 八字神煞模块（L3-2）：23 项主流神煞（Rule-ID ss-01..ss-23），每项带底本出处+起法口诀+异文标注。
起法口径=易安居 zhouyi.cc 四柱神煞实测裁定（2026-08-16 探样 15 例全口径互证，见 report/l3_shensha_report.txt）：
  日干起查四支：天乙(ss-01)/文昌(ss-02)/羊刃(ss-06)/禄神(ss-08)/金舆(ss-09)/国印(ss-14)；
  年支+日支双起查四支（排除起法支自身）：咸池桃花(ss-03)/驿马(ss-04)/华盖(ss-05)/将星(ss-07)/劫煞(ss-15)/亡神(ss-16)/灾煞(ss-17)；
  年支起查四支：孤辰(ss-12)/寡宿(ss-13)/红鸾(ss-10)/天喜(ss-11，后二者易安居不报，民间口诀年支起，无专篇)；
  月支起：天德(ss-21 查四柱干支并集)/月德(ss-22 查四柱天干)；
  日干五行论：天罗(ss-18 丙丁忌戌亥)/地网(ss-19 戊己壬癸忌辰巳，金木无)；
  日柱查表：魁罡(ss-20 四日)/十恶大败(ss-23 十日)。
输入=北京时间+东经（复用 m1 四柱）。运行 python l3_shensha.py --compare 对拍易安居。"""
import argparse, csv, json, os, random, re, sys, time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m1
from rules import GAN, ZHI

BASE = os.path.dirname(os.path.abspath(__file__))
K = ("年上", "月上", "日上", "时上")

# 三合局一支 → (咸池, 驿马, 华盖, 将星, 劫煞, 亡神, 灾煞)；《渊海子平·论咸池/驿马/华盖/劫煞》等
SANHE = {z: t for t, group in (
    (("卯", "申", "戌", "午", "亥", "巳", "子"), "寅午戌"),   # 寅午戌局
    (("酉", "寅", "辰", "子", "巳", "亥", "午"), "申子辰"),   # 申子辰局
    (("午", "亥", "丑", "酉", "寅", "申", "卯"), "巳酉丑"),   # 巳酉丑局
    (("子", "巳", "未", "卯", "申", "寅", "酉"), "亥卯未"))   # 亥卯未局
    for z in group}

# 日干表（渊海/三命口径；异文见 SPEC.diff）
TIANYI = {"甲": "丑未", "戊": "丑未", "庚": "午寅", "乙": "子申", "己": "子申",
          "丙": "亥酉", "丁": "亥酉", "壬": "卯巳", "癸": "卯巳", "辛": "午寅"}
WENCHANG = {"甲": "巳", "乙": "巳", "丙": "申", "丁": "酉", "戊": "申", "己": "酉",
            "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯"}
YANGREN = {"甲": "卯", "乙": "寅", "丙": "午", "丁": "巳", "戊": "午", "己": "巳",
           "庚": "酉", "辛": "申", "壬": "子", "癸": "亥"}
LUSHEN = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳", "己": "午",
          "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
JINYU = {"甲": "辰", "乙": "巳", "丙": "未", "丁": "申", "戊": "未", "己": "申",
         "庚": "戌", "辛": "亥", "壬": "丑", "癸": "寅"}
GUOYIN = {"甲": "戌", "乙": "亥", "丙": "丑", "丁": "寅", "戊": "丑", "己": "寅",
          "庚": "辰", "辛": "巳", "壬": "未", "癸": "申"}
# 年支组 → (孤辰, 寡宿)；寅卯辰→孤巳寡丑 等（渊海子平《论孤辰寡宿》）
GUGUA = {z: g for g, group in ((("巳", "丑"), "寅卯辰"), (("申", "辰"), "巳午未"),
                               (("亥", "未"), "申酉戌"), (("寅", "戌"), "亥子丑")) for z in group}
TIANDE = {"寅": "丁", "卯": "申", "辰": "壬", "巳": "辛", "午": "亥", "未": "甲",
          "申": "癸", "酉": "寅", "戌": "丙", "亥": "乙", "子": "巳", "丑": "庚"}
YUEDE = {"寅": "丙", "午": "丙", "戌": "丙", "申": "壬", "子": "壬", "辰": "壬",
         "亥": "甲", "卯": "甲", "未": "甲", "巳": "庚", "酉": "庚", "丑": "庚"}
KUI = ("庚辰", "庚戌", "壬辰", "戊戌")
SHIE = ("甲辰", "乙巳", "丙申", "丁亥", "戊戌", "己丑", "庚辰", "辛巳", "壬申", "癸亥")

SPEC = {  # 每项 Rule-ID+底本出处+起法口诀+异文
    "天乙贵人": {"rule_id": "ss-01", "source": "《三命通会·论天乙贵人》（易安居实测口径）",
        "method": "日干起：甲戊见丑未（牛羊），庚辛见午寅（马虎），乙己见子申（鼠猴），丙丁见亥酉（猪鸡），壬癸见卯巳（兔蛇）",
        "diff": "异文①《渊海子平》口诀「六辛逢马虎」（庚见丑未、辛见午寅）；②「甲戊庚牛羊」与「庚辛逢马虎」两口诀庚之归属各派不一；③易安居实测庚→午寅（2024-06-15 庚日午支与 2029-01-20 庚日丑支对拍实证）；④古法亦按年干起"},
    "文昌贵人": {"rule_id": "ss-02", "source": "民间口诀，无专篇；据《协纪辨方书》日表类整理（易安居实测口径，异文见 diff）",
        "method": "日干起：甲巳乙巳丙戊申，丁己酉庚亥辛子，壬寅癸卯（查四支）",
        "diff": "异文：主流口诀「乙见午」（甲巳乙午丙戊申），易安居实测乙见巳（乙巳日/乙亥月两例复验一致），取 oracle 口径"},
    "桃花(咸池)": {"rule_id": "ss-03", "source": "《渊海子平·论咸池》",
        "method": "寅午戌见卯，申子辰见酉，巳酉丑见午，亥卯未见子；年支+日支双起查四支",
        "diff": "异文：古法按年支起，亦有按日支起派；易安居实测年支+日支双起"},
    "驿马": {"rule_id": "ss-04", "source": "《渊海子平·论驿马》",
        "method": "寅午戌见申，申子辰见寅，巳酉丑见亥，亥卯未见巳；年支+日支双起查四支",
        "diff": "异文：古法按年支起，亦有按日支起派；易安居实测双起"},
    "华盖": {"rule_id": "ss-05", "source": "《渊海子平·论华盖》",
        "method": "寅午戌见戌，申子辰见辰，巳酉丑见丑，亥卯未见未；年支+日支双起，排除起法支自身",
        "diff": "异文：按年支/日支单起派；「见」是否含自身各派不一（易安居实测排除起法支自身）"},
    "羊刃": {"rule_id": "ss-06", "source": "《渊海子平·论羊刃》",
        "method": "日干起：甲卯乙寅丙午丁巳戊午己巳庚酉辛申壬子癸亥（查四支）",
        "diff": "异文：阴干（乙丁己辛癸）刃有「无刃」派（阳刃说），主流含阴刃；易安居含阴刃"},
    "将星": {"rule_id": "ss-07", "source": "《渊海子平·论将星》",
        "method": "寅午戌见午，申子辰见子，巳酉丑见酉，亥卯未见卯；年支+日支双起，排除起法支自身",
        "diff": "异文：按年支/日支单起派；易安居实测双起且排除起法支自身"},
    "禄神": {"rule_id": "ss-08", "source": "《渊海子平·论禄》",
        "method": "日干起：甲禄寅乙禄卯丙戊禄巳丁己禄午庚禄申辛禄酉壬禄亥癸禄子（查四支）",
        "diff": "异文：亦按年干起（岁禄），易安居按日干起"},
    "金舆": {"rule_id": "ss-09", "source": "《三命通会·论金舆》",
        "method": "日干起：甲辰乙巳丙未丁申戊未己申庚戌辛亥壬丑癸寅（查四支）",
        "diff": "异文：个别版本丙戊→未、丁己→申 以「甲龙乙蛇丙戊羊，丁己猴歌庚犬方」口诀（两版一致）"},
    "红鸾": {"rule_id": "ss-10", "source": "民间口诀，无专篇；据《协纪辨方书》嫁娶类整理（年支起，异文见 diff）",
        "method": "年支起：子卯丑寅寅丑卯子辰亥巳戌午酉未申申未酉午戌巳亥辰（查四支）",
        "diff": "异文：亦有按日支起派；易安居四柱神煞不报红鸾，按民间口诀年支起，对拍申报不覆盖"},
    "天喜": {"rule_id": "ss-11", "source": "民间口诀，无专篇；据《协纪辨方书》嫁娶类整理（红鸾对宫，年支起，异文见 diff）",
        "method": "年支起：红鸾对宫（子酉丑申寅未卯午辰巳巳辰午卯未寅申丑酉子戌亥亥戌）",
        "diff": "异文：亦有按日支起派；易安居四柱神煞不报天喜，按民间口诀年支起，对拍申报不覆盖"},
    "孤辰": {"rule_id": "ss-12", "source": "《渊海子平·论孤辰寡宿》",
        "method": "年支起：寅卯辰见巳，巳午未见申，申酉戌见亥，亥子丑见寅（查四支）",
        "diff": "异文：亦有按日支起派；易安居实测仅年支起"},
    "寡宿": {"rule_id": "ss-13", "source": "《渊海子平·论孤辰寡宿》",
        "method": "年支起：寅卯辰见丑，巳午未见辰，申酉戌见未，亥子丑见戌（查四支）",
        "diff": "异文：亦有按日支起派；易安居实测仅年支起"},
    "国印": {"rule_id": "ss-14", "source": "《三命通会·论国印》",
        "method": "日干起：甲戌乙亥丙丑丁寅戊丑己寅庚辰辛巳壬未癸申（查四支）",
        "diff": "异文：版本一致，无重大分歧"},
    "劫煞": {"rule_id": "ss-15", "source": "《渊海子平·论劫煞》",
        "method": "寅午戌见亥，申子辰见巳，巳酉丑见寅，亥卯未见申；年支+日支双起查四支",
        "diff": "异文：按年支/日支单起派；易安居实测双起"},
    "亡神": {"rule_id": "ss-16", "source": "《渊海子平·论亡神》",
        "method": "寅午戌见巳，申子辰见亥，巳酉丑见申，亥卯未见寅；年支+日支双起查四支",
        "diff": "异文：按年支/日支单起派；易安居实测双起"},
    "灾煞": {"rule_id": "ss-17", "source": "《渊海子平·论灾煞》",
        "method": "寅午戌见子，申子辰见午，巳酉丑见卯，亥卯未见酉；年支+日支双起查四支",
        "diff": "异文：按年支/日支单起派；灾煞=将星对冲位（寅午戌将星午灾煞子），易安居实测双起"},
    "天罗": {"rule_id": "ss-18", "source": "《渊海子平·论天罗地网》（日干五行论，易安居实测口径）",
        "method": "戌亥为天罗：日干丙丁（火命人）忌，查四支见戌亥",
        "diff": "异文①《三命通会》同「火命人天罗、水土命人地网、金木命人无」；②一说按日柱纳音五行论；③一说辰为天罗戌为地网（男忌天罗女忌地网）"},
    "地网": {"rule_id": "ss-19", "source": "《渊海子平·论天罗地网》（日干五行论，易安居实测口径）",
        "method": "辰巳为地网：日干戊己壬癸（水土命人）忌，查四支见辰巳",
        "diff": "异文同 ss-18：纳音论/辰戌论两说并存"},
    "魁罡": {"rule_id": "ss-20", "source": "《渊海子平·论魁罡》",
        "method": "日柱为庚辰、庚戌、壬辰、戊戌四日之一",
        "diff": "异文：少数版本增丙辰、丙戌（主流四日，易安居同）"},
    "天德贵人": {"rule_id": "ss-21", "source": "《渊海子平·论天德贵人》",
        "method": "月支起：正丁二坤(申)三壬四辛五乾(亥)六甲七癸八艮(寅)九丙十乙十一巽(巳)十二庚；查四柱干支并集",
        "diff": "异文：个别版本查四柱天干（易安居实测干支并集，子月见巳地支命中）"},
    "月德贵人": {"rule_id": "ss-22", "source": "《渊海子平·论月德贵人》",
        "method": "月支起：寅午戌月见丙，申子辰月见壬，亥卯未月见甲，巳酉丑月见庚；查四柱天干",
        "diff": "异文：版本一致（个别查四支派），易安居查天干"},
    "十恶大败": {"rule_id": "ss-23", "source": "《三命通会·论十恶大败》",
        "method": "日柱逢甲辰乙巳丙申丁亥戊戌己丑庚辰辛巳壬申癸亥十日之一",
        "diff": "异文：个别传本「辛巳」作「辛亥」（口诀「戊戌癸亥加辛巳」版本不一）"},
}

def _hit(gan, table, zhiz):  # 日干起查四支（含起法支自身）
    want = table[gan]
    return [i for i, z in enumerate(zhiz) if z in want]

def _sanhe_hit(target, zhiz):  # 年支+日支双起查四支，排除起法支自身
    out = set()
    for base in (0, 2):
        want = SANHE[zhiz[base]][target]
        out |= {i for i, z in enumerate(zhiz) if z == want and i != base}
    return sorted(out)

def compute(dt, lon):
    """(北京时, 东经) → 四柱神煞 JSON：按年上/月上/日上/时上分组（易安居四柱神煞口径，任务书三组+时上列）；每项带 Rule-ID+出处+口诀+异文。"""
    r = m1.compute(dt, lon)
    if "error" in r:
        return r
    p = r["pillars"]
    gz = [p[k]["ganzhi"] for k in ("year", "month", "day", "hour")]
    gans, zhiz = [x[0] for x in gz], [x[1] for x in gz]
    dm, day_gz = gz[2][0], gz[2]
    groups = {k: [] for k in K}

    def add(name, hits):
        s = SPEC[name]
        for i in hits:
            groups[K[i]].append({"name": name, "rule_id": s["rule_id"], "source": s["source"],
                                 "method": s["method"], "diff": s["diff"]})

    add("天乙贵人", _hit(dm, TIANYI, zhiz))
    add("文昌贵人", _hit(dm, WENCHANG, zhiz))
    add("桃花(咸池)", _sanhe_hit(0, zhiz))
    add("驿马", _sanhe_hit(1, zhiz))
    add("华盖", _sanhe_hit(2, zhiz))
    add("将星", _sanhe_hit(3, zhiz))
    add("劫煞", _sanhe_hit(4, zhiz))
    add("亡神", _sanhe_hit(5, zhiz))
    add("灾煞", _sanhe_hit(6, zhiz))
    add("羊刃", _hit(dm, YANGREN, zhiz))
    add("禄神", _hit(dm, LUSHEN, zhiz))
    add("金舆", _hit(dm, JINYU, zhiz))
    add("国印", _hit(dm, GUOYIN, zhiz))
    add("红鸾", [i for i, z in enumerate(zhiz) if z == ZHI[(3 - ZHI.index(zhiz[0])) % 12]])   # 年支起
    add("天喜", [i for i, z in enumerate(zhiz) if z == ZHI[(9 - ZHI.index(zhiz[0])) % 12]])   # 红鸾对宫
    gu, gua = GUGUA[zhiz[0]]
    add("孤辰", [i for i, z in enumerate(zhiz) if z == gu])
    add("寡宿", [i for i, z in enumerate(zhiz) if z == gua])
    tdm = TIANDE[zhiz[1]]
    add("天德贵人", [i % 4 for i, x in enumerate(gans + zhiz) if x == tdm])  # 干支并集
    add("月德贵人", [i for i, x in enumerate(gans) if x == YUEDE[zhiz[1]]])
    if dm in "丙丁":  # 火命人忌天罗（戌亥）
        add("天罗", [i for i, z in enumerate(zhiz) if z in "戌亥"])
    if dm in "戊己壬癸":  # 水土命人忌地网（辰巳）
        add("地网", [i for i, z in enumerate(zhiz) if z in "辰巳"])
    if day_gz in KUI:
        add("魁罡", [2])
    if day_gz in SHIE:
        add("十恶大败", [2])
    total = sum(len(v) for v in groups.values())
    return {"input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "lon": lon},
            "pillars": p, "ten_gods": r["ten_gods"],
            "shensha": {"rule_id": "ss-00", "source": "23 项主流神煞，Rule-ID ss-01..ss-23；底本《渊海子平》《三命通会》，口径易安居实测裁定（见各项 source/diff）",
                        "groups": groups, "hit_total": total},
            "notes": ["分组=神煞命中的柱（易安居四柱神煞口径）；任务书三组外并列时上组（对拍所需）",
                      "红鸾/天喜：易安居四柱神煞不报，民间口诀年支起法（无专篇，据《协纪辨方书》嫁娶类目整理），对拍申报不覆盖"]}

def my_sz(t):  # 对拍侧：自研 → {柱: {神煞名}}
    r = compute(datetime(*t), 120.0)
    if "error" in r:
        return None
    return {k: {x["name"] for x in v} for k, v in r["shensha"]["groups"].items()}

# ============================ 对拍（--compare） ============================
URL = "https://www.zhouyi.cc/bazi/pp/Bazi.php"
O_NAME = {"天乙贵人": "天乙", "文昌贵人": "文昌", "桃花(咸池)": "咸池", "驿马": "驿马", "华盖": "华盖",
          "羊刃": "羊刃", "将星": "将星", "禄神": "禄神", "金舆": "金舆", "孤辰": "孤辰", "寡宿": "寡宿",
          "国印": "国印", "劫煞": "劫煞", "亡神": "亡神", "灾煞": "灾煞", "天罗": "天罗", "地网": "地网",
          "魁罡": "魁罡", "天德贵人": "天德", "月德贵人": "月德", "十恶大败": "十恶大败"}  # 红鸾/天喜 oracle 不报，不比对

def fetch_sz(t, sex="1"):
    d = {"data_type": "0", "cboYear": str(t[0]), "cboMonth": str(t[1]), "cboDay": str(t[2]),
         "cboHour": f"{t[3]}-{ZHI[(t[3] + 1) // 2 % 12]}", "cboMinute": str(t[4]),
         "pid": "", "cid": "", "zty": "0", "txtName": "某人", "rdoSex": sex}
    for _ in range(3):  # 网络抖动重试
        try:
            html = __import__("requests").post(URL, data=d, timeout=30).content.decode("utf-8")
            break
        except Exception:
            time.sleep(2)
    m = re.search(r"四柱神煞</span><br/>(.*?)<span[^>]*>大运神煞", html, re.S)
    if not m:
        return None
    rows = re.findall(r"([年月日时])柱：&nbsp;(.*?)<br", m.group(1))
    return {k: {x for x in v.split("&nbsp;") if x} for k, v in rows}

def cmp_case(t):
    o, s = fetch_sz(t), my_sz(t)
    if o is None:
        return None, "oracle 抓取失败"
    if s is None:
        return None, "自研 out_of_range"
    diffs = []
    for zh in ("年", "月", "日", "时"):
        oc = {x for x in o[zh] if x in set(O_NAME.values())}  # 只比共同名集
        mc = {O_NAME[x] for x in s["年上" if zh == "年" else "月上" if zh == "月" else "日上" if zh == "日" else "时上"] if x in O_NAME}
        if oc != mc:
            diffs.append(f"{zh}柱 oracle[{'/'.join(sorted(oc)) or '无'}] vs 自研[{'/'.join(sorted(mc)) or '无'}]")
    return ("same" if not diffs else "diff"), "；".join(diffs) or "一致"

def compare():
    """对拍：5 锚点（含 2024-02-10 甲辰日等已知案例）+20 随机（1949-2100 均匀，避 23-24 时/12 节±30 分/立春日整天）；
    21 项共同神煞逐柱比对（红鸾/天喜 oracle 不报除外）；分歧按 I-8 申报 data/arbitration_log.csv（ss- 前缀）+report/boundary_cases.csv（幂等）。"""
    ANCHORS = [(2024, 2, 10, 8, 0), (2024, 6, 15, 12, 0), (2000, 2, 5, 12, 0),
               (1990, 1, 1, 10, 0), (1949, 10, 1, 10, 0)]
    random.seed(20260816)
    tds = [datetime.strptime(x["datetime"], "%Y-%m-%d %H:%M") for x in m1.load_terms()]
    rnd = []
    while len(rnd) < 20:  # 随机：避 23-24 时、12 节 ±30 分、立春日整天（防年柱口径连锁）
        y, mo = random.randint(1949, 2100), random.randint(1, 12)
        t = (y, mo, random.randint(1, 28), random.choice((8, 10, 12, 14, 16)), 0)
        dto = datetime(*t)
        if dto.strftime("%m-%d") in ("02-04", "02-05") or min(abs((dto - x).total_seconds()) for x in tds) <= 1800:
            continue
        rnd.append(t)
    cases = ANCHORS + rnd
    same = diff = out = 0
    arbs, brows, nd = [], [], []
    for i, t in enumerate(cases):
        kind, note = cmp_case(t)
        if kind is None:
            out += 1
            continue
        if kind == "same":
            same += 1
        else:
            diff += 1
            nd.append((t, note))
            cid = f"ss-a{i + 1:02d}" if i < 5 else f"ss-r{i - 4:02d}"
            fdt = f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}"
            note2 = f"神煞分歧 {fdt}：{note}"
            arbs.append([cid, "四柱神煞", "oracle 侧", "自研侧", "复核者", "alt", note2, "oracle 对拍",
                         "自研 l3_shensha.py（ss-01..23）", "易安居 zhouyi.cc"])
            brows.append([cid, "神煞分歧", fdt, "oracle 四柱神煞", "自研四柱神煞", "arbitrated", note2])
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
    rep = [f"L3-2 八字神煞对拍（l3_shensha.py）：{len(cases)} 例（5 锚点+20 随机 1949-2100，避 23-24 时/12 节±30 分/立春日）",
           f"易安居四柱神煞 21 项共同名集逐柱比对：一致 {same}/{len(cases) - out}；分歧 {diff}；oracle 抓取失败 {out}",
           f"申报：arbitration_log.csv ss- 新增 {len(arbs)} 条；boundary_cases.csv ss- 新增 {len(brows)} 条（幂等）"]
    for t, note in nd[:8]:
        rep.append(f"  分歧：{t[0]:04d}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:00 {note}")
    return rep

def main():
    ap = argparse.ArgumentParser(description="八字神煞（23 项主流，Rule-ID ss-01..23）")
    ap.add_argument("--datetime", help="北京时间 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0)
    ap.add_argument("--compare", action="store_true", help="对拍易安居四柱神煞")
    a = ap.parse_args()
    if a.compare:
        print("\n".join(compare()))
        return
    dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    print(json.dumps(compute(dt, a.lon), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

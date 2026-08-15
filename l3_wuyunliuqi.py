# -*- coding: utf-8 -*-
"""l3_wuyunliuqi.py — 五运六气模块（L3）：底本《黄帝内经·素问》运气七篇
（《天元纪大论》《五运行大论》《六微旨大论》《气交变大论》《五常政大论》《六元正纪大论》《至真要大论》）。
功能 wylq-01..05 全字段 rule_id/source/alt（异文标注），输出 JSON。
口径（2026-08-16 双 oracle 实测裁定，见 report/l3_wuyunliuqi_report.txt）：
  岁首=大寒（运气岁首，fate-craft 实测口径）；六步节点=大寒/春分/小满/大暑/秋分/小雪
  （定气历表 solar_terms.csv，唯一权威）；岁运/司天在泉/相合随运气岁干支。
运行：python l3_wuyunliuqi.py --datetime "2026-07-15 12:00" [--json]
      python l3_wuyunliuqi.py --compare   # 对拍 WYLQ oracle + 申报口径分歧"""
import argparse, bisect, csv, json, os, random, sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rules import GAN, ZHI

BASE = os.path.dirname(os.path.abspath(__file__))
RANGE_LO, RANGE_HI = "1949-01-01 00:00", "2100-12-31 23:59"  # 有效输入（与 m1 同范围）

# ---- wylq-01 天干化运：《天元纪大论》「甲己之岁，土运统之；乙庚之岁，金运统之；丙辛之岁，水运统之；丁壬之岁，木运统之；戊癸之岁，火运统之」----
YUN_WX = {g: ("土", "金", "水", "木", "火")[i % 5] for i, g in enumerate(GAN)}  # 甲己土乙庚金丙辛水丁壬木戊癸火（隔 5 成组）
# 《五常政大论》十名目：太过（发生/赫曦/敦阜/坚成/流衍）、不及（委和/伏明/卑监/从革/涸流）
JI = {("木", 1): "发生之纪", ("火", 1): "赫曦之纪", ("土", 1): "敦阜之纪", ("金", 1): "坚成之纪", ("水", 1): "流衍之纪",
      ("木", 0): "委和之纪", ("火", 0): "伏明之纪", ("土", 0): "卑监之纪", ("金", 0): "从革之纪", ("水", 0): "涸流之纪"}

# ---- 主气六步（wylq-02）：初之气大寒起，每气 60.875 日=365.25/6（《六微旨大论》六步、《类经》注「初之气起于大寒」）----
MAIN_QI = ("厥阴风木", "少阴君火", "少阳相火", "太阴湿土", "阳明燥金", "太阳寒水")  # 主气序（君相火相邻）
NODE_TERMS = ("大寒", "春分", "小满", "大暑", "秋分", "小雪")  # 六步分界中气（定气）
STEP_NAME = ("初之气", "二之气", "三之气", "四之气", "五之气", "终之气")

# ---- 客气三阴三阳序（厥阴一阴→少阴二阴→太阴三阴→少阳一阳→阳明二阳→太阳三阳，《六微旨大论》）----
QI_SEQ = ("厥阴风木", "少阴君火", "太阴湿土", "少阳相火", "阳明燥金", "太阳寒水")
# wylq-03 地支化气（司天）：《五运行大论》「子午之上，少阴主之；丑未之上，太阴主之；寅申之上，少阳主之；
# 卯酉之上，阳明主之；辰戌之上，太阳主之；巳亥之上，厥阴主之」；在泉=对宫（司天+3）
SI_TIAN = {z: QI_SEQ[(i + 1) % 6] for i, z in enumerate(ZHI)}        # 子(0)→少阴、丑(1)→太阴、寅(2)→少阳、卯(3)→阳明、辰(4)→太阳、巳(5)→厥阴…
ZAI_QUAN = {z: QI_SEQ[(i + 4) % 6] for i, z in enumerate(ZHI)}        # 在泉=司天对宫：午(6+1+3)→阳明、未→太阳…

def _wuxing(qi):  # 六气名末两字取五行：「厥阴风木」→木、「少阴君火」→火（君火相火皆火）
    return {"风木": "木", "君火": "火", "相火": "火", "湿土": "土", "燥金": "金", "寒水": "水"}[qi[2:]]

@__import__("functools").lru_cache(maxsize=None)
def _load_nodes():
    """solar_terms.csv 中气六节点 → 按 datetime 排序 [(时刻串, 节点名)]；表 1948-2101 录满，唯一运行期权威。"""
    with open(os.path.join(BASE, "data", "solar_terms.csv"), encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["term"] in NODE_TERMS]
    return sorted((r["datetime"], r["term"]) for r in rows)

def _luck_year(dt):
    """运气岁首=大寒（裁定口径）：最近 ≤dt 的大寒节点所在公历年 → 干支（甲子=0，(y-4)%60）。"""
    for t, name in _load_nodes()[::-1]:
        if name == "大寒" and t <= dt.strftime("%Y-%m-%d %H:%M"):
            return (int(t[:4]) - 4) % 60, int(t[:4])
    return (int(dt.year) - 4) % 60, dt.year  # 表首兜底（输入范围外不可达）

def _nodes_of_year(y):
    """公历年 y 的六节点（当年大寒~小雪）→ 列表[(时刻串, 名)]，含岁首大寒。"""
    out = [(t, n) for t, n in _load_nodes() if t[:4] == str(y) and n in NODE_TERMS]
    return out  # 六节点按公历年内排序（大寒→…→小雪）

def _keqi_steps(gz):
    """客气六步（wylq-03）：三之气=司天，终之气=在泉，余者按三阴三阳序从司天倒推轮排（与 fate-craft/WYLQ 互证）。"""
    s = SI_TIAN[gz[1]]
    seq = [QI_SEQ[(QI_SEQ.index(s) - 2 + i) % 6] for i in range(6)]  # 初气=司天-2，逐位+1
    return seq

# ---- wylq-04 运气相合（《六微旨大论》天符/岁会/太一天符；《六元正纪大论》同天符/同岁会），表驱动 = 逻辑表 ----
def _xianghe(gz):
    yun_wx = YUN_WX[gz[0]]
    too = gz[0] in "甲丙戊庚壬"
    st_wx, zq_wx = _wuxing(SI_TIAN[gz[1]]), _wuxing(ZAI_QUAN[gz[1]])
    zhi_wx = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
              "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}[gz[1]]
    # 岁会=《六微旨大论》「木运临卯，火运临午，土运临四季，金运临酉，水运临子」——四正+四季
    # （寅申巳亥四孟同气不属岁会：壬寅/癸巳/辛亥 均非岁会，fate-craft/WYLQ 60 甲子图互证）
    suihui = yun_wx == zhi_wx and gz[1] in "子午卯酉辰戌丑未"
    tianfu = yun_wx == st_wx
    types = []
    if tianfu and suihui:
        types.append("太一天符")            # 天符∩岁会，三气会同（六微旨）
    elif tianfu:
        types.append("天符")
    if suihui and not (tianfu and suihui):
        types.append("岁会")                # 岁会 8 年：甲辰甲戌乙酉丙子丁卯戊午己丑己未
    if too and yun_wx == zq_wx:
        types.append("同天符")              # 岁运太过而适与在泉相同（六元正纪）
    if not too and yun_wx == zq_wx:
        types.append("同岁会")              # 岁运不及与在泉相同（六元正纪）
    return types

def compute(dt):
    """(北京时 datetime，整分钟) → 五运六气 JSON；非法输入返回 {"error": ...}。"""
    if dt.second or dt.microsecond:
        return {"error": f"错误: 输入不含秒精度，收到 {dt.strftime('%Y-%m-%d %H:%M:%S')}"}
    s = dt.strftime("%Y-%m-%d %H:%M")
    if not RANGE_LO <= s <= RANGE_HI:
        return {"error": f"错误: {s} 超出有效范围 {RANGE_LO} ~ {RANGE_HI}（out_of_range）"}
    idx, y = _luck_year(dt)
    gz = GAN[idx % 10] + ZHI[idx % 12]
    yun_wx, too = YUN_WX[gz[0]], gz[0] in "甲丙戊庚壬"
    level = "太过" if too else "不及"
    # 当前步：该岁六节点里最近 ≤dt 的一个 → 步序 0..5
    nodes = _nodes_of_year(y)
    ts = [t for t, _ in nodes]
    i = max(0, bisect.bisect_right(ts, s) - 1)
    cur_t, cur_name = nodes[i]
    nxt = nodes[i + 1] if i + 1 < 6 else _nodes_of_year(y + 1)[0]  # 终之气止于次岁大寒
    keqi = _keqi_steps(gz)
    steps = []
    for k in range(6):
        st = nodes[k]
        en = nodes[k + 1] if k + 1 < 6 else _nodes_of_year(y + 1)[0]
        steps.append({"step": STEP_NAME[k], "zhu_qi": MAIN_QI[k], "ke_qi": keqi[k],
                      "start": st[0], "end": en[0], "start_term": st[1], "end_term": en[1],
                      "si_tian": k == 2, "zai_quan": k == 5})
    he = _xianghe(gz)
    return {
        "input": {"datetime": s, "tz": "UTC+8 北京时间（运气历法按官方定气历表）"},
        "sui_yun": {"ganzhi": gz, "yun": yun_wx, "level": level, "name": f"{yun_wx}运{level}",
                    "ji": JI[(yun_wx, int(too))], "rule_id": "wylq-01",
                    "source": "《素问·天元纪大论》天干化运「甲己之岁土运统之…戊癸之岁火运统之」+《五常政大论》十纪名目",
                    "alt": "异文①岁运交接有「大寒换年」（本实现，fate-craft 实测口径）与「立春换年」（干支纪年口径，WYLQ oracle）两派，大寒~立春间两口径岁运不同；②水运不及「涸流」（通行本）一作「涫流」"},
        "zhu_qi": {"current": {"step": STEP_NAME[i], "qi": MAIN_QI[i], "start": cur_t, "end": nxt[0],
                               "start_term": cur_name, "end_term": nxt[1]},
                   "steps": steps, "rule_id": "wylq-02",
                   "source": "《素问·六微旨大论》六步分治+《六元正纪大论》各岁六气叙列；每气 60.875 日=365.25/6，初之气起于大寒（《类经》注）",
                   "alt": "异文：六步起点「大寒」（本实现，运气学主流+fate-craft）vs「立春」（WYLQ oracle，立春+60 日近似）；节点时刻=定气历表（solar_terms.csv）vs 60 日等分近似（WYLQ）"},
        "ke_qi": {"si_tian": SI_TIAN[gz[1]], "zai_quan": ZAI_QUAN[gz[1]],
                  "current": {"step": STEP_NAME[i], "qi": keqi[i], "start": cur_t, "end": nxt[0]},
                  "steps": steps, "rule_id": "wylq-03",
                  "source": "《素问·五运行大论》地支化气「子午之上少阴主之…巳亥之上厥阴主之」+《六微旨大论》三阴三阳序轮排；在泉=司天对宫（三之气↔终之气）",
                  "alt": "异文：客气轮排另有「以司天在泉起首气」等少数派（李阳波流派），主流=司天定三之气倒推（fate-craft/WYLQ 互证）"},
        "xiang_he": {"types": [{"name": x, "rule_id": "wylq-04",
                                "source": "《素问·六微旨大论》天符/岁会/太一天符（岁会=「木运临卯，火运临午，土运临四季，金运临酉，水运临子」，四正+四季共 8 年）+《六元正纪大论》同天符/同岁会",
                                "alt": "异文：岁会若按「运与支同气即可」（含四孟寅申巳亥）则壬寅/癸巳/辛亥亦岁会——主流（fate-craft/WYLQ 60 甲子图）不取，本实现从主流"} for x in he],
                     "rule_id": "wylq-04",
                     "source": "《素问·六微旨大论》《六元正纪大论》运气同化定义",
                     "alt": ""},
        "nodes": {"year": gz, "current": {"node": cur_name, "time": cur_t},
                  "next": {"node": nxt[1], "time": nxt[0]},
                  "rule_id": "wylq-05",
                  "source": "solar_terms.csv 定气中气时刻（大寒/春分/小满/大暑/秋分/小雪 六节点）",
                  "alt": ""},
        "notes": ["运气推演为理论体系，非医学诊断，不构成任何诊疗建议",
                  "岁首=大寒（运气岁首，fate-craft 实测裁定）；大寒~立春间与干支纪年（m1 立春换年）口径不同，已申报 wylq-001",
                  "六步分界按定气历表时刻（solar_terms.csv 权威），非 60 日等分（异文口径申报 wylq-002/003）"],
    }

def _oracle_tables():
    """oracle 固化表（WYLQ GitHub 读码 2026-08-16）：岁运 10 干/司天 12 支/在泉 12 支/同化 24 年。"""
    yun = {'甲': '土运太过', '乙': '金运不及', '丙': '水运太过', '丁': '木运不及', '戊': '火运太过',
           '己': '土运不及', '庚': '金运太过', '辛': '水运不及', '壬': '木运太过', '癸': '火运不及'}
    st = {'子': '少阴君火', '丑': '太阴湿土', '寅': '少阳相火', '卯': '阳明燥金', '辰': '太阳寒水', '巳': '厥阴风木',
          '午': '少阴君火', '未': '太阴湿土', '申': '少阳相火', '酉': '阳明燥金', '戌': '太阳寒水', '亥': '厥阴风木'}
    zq = {'子': '阳明燥金', '丑': '太阳寒水', '寅': '厥阴风木', '卯': '少阴君火', '辰': '太阴湿土', '巳': '少阳相火',
          '午': '阳明燥金', '未': '太阳寒水', '申': '厥阴风木', '酉': '少阴君火', '戌': '太阴湿土', '亥': '少阳相火'}
    he = {'丁卯': '岁会', '庚午': '同天符', '辛未': '同岁会', '壬申': '同天符', '癸酉': '同岁会', '甲戌': '岁会同天符',
          '丙子': '岁会', '戊寅': '天符', '乙酉': '太一天符', '丙戌': '天符', '丁亥': '天符', '戊子': '天符',
          '己丑': '太一天符', '庚子': '同天符', '辛丑': '同岁会', '壬寅': '同天符', '癸卯': '同岁会', '甲辰': '岁会同天符',
          '乙卯': '天符', '丙辰': '天符', '丁巳': '天符', '戊午': '太一天符', '己未': '太一天符', '癸亥': '同岁会'}
    return yun, st, zq, he

def _oracle_keqi(gz, st, zq):
    """WYLQ calculate_guest_qi 原逻辑（读码复制）：司天=三之气、在泉=终之气，余者倒推。"""
    base = ['厥阴风木', '少阴君火', '太阴湿土', '少阳相火', '阳明燥金', '太阳寒水']
    si, za = base.index(st), base.index(zq)
    gq = list(base)
    gq[2], gq[5] = base[si], base[za]
    gq[1], gq[0] = base[si - 1], base[si - 2]
    gq[3], gq[4] = base[za - 2], base[za - 1]
    return gq

def _oracle_types(s):
    """oracle 同化串 → 类型集合（'岁会同天符'→{岁会,同天符}；'太一天符'→{太一天符}；'0'→空；匹配后吃掉长串防子串冲突）。"""
    if s == '0':
        return set()
    if '太一天符' in s:
        return {'太一天符'}
    out = set()
    for x in ('同天符', '同岁会'):
        if x in s:
            out.add(x)
            s = s.replace(x, "")
    if '天符' in s:
        out.add('天符')
    if '岁会' in s:
        out.add('岁会')
    return out

def compare():
    """对拍：5 手工锚点（手算）+15 随机干支年（1949-2100 均匀，年中日期避开换年界）；
    岁运干支/太过不及/司天/在泉/相合五类/客气六步 全字段比对（WYLQ 表 + fate-craft 2026 丙午页面锚点）；
    口径分歧（换年界/六步起点/历法精度）按 I-8 申报 arbitration_log（wylq- 前缀）+boundary_cases（幂等）；
    返回报告文本并写入 report/l3_wuyunliuqi_report.txt。"""
    yun_t, st_t, zq_t, he_t = _oracle_tables()
    ANCHORS = [  # 5 手工锚点：(日期, 期望干支)
        ("2026-01-10 12:00", "乙巳"), ("2026-07-15 12:00", "丙午"), ("2026-12-31 12:00", "丙午"),
        ("2000-02-05 12:00", "庚辰"), ("1949-10-01 12:00", "己丑")]
    random.seed(20260816)
    rnd = []
    while len(rnd) < 15:  # 年中日期（8 月 15 日）避大寒~立春换年界
        y = random.randint(1949, 2100)
        gz = GAN[(y - 4) % 10] + ZHI[(y - 4) % 12]
        if gz not in {x[1] for x in ANCHORS}:
            rnd.append((f"{y}-08-15 12:00", gz))
    # oracle 表遗漏补遗：戊申=天符、癸巳=同岁会（《六元正纪大论》定义+fate-craft 算法推导，WYLQ 手工表缺）
    FIX = {"戊申": "天符", "癸巳": "同岁会"}

    def he_expect(gz):
        return _oracle_types(he_t.get(gz, FIX.get(gz, '0')))

    cases = ANCHORS + rnd
    same = diff = 0
    nd = []
    for s, want_gz in cases:
        r = compute(datetime.strptime(s, "%Y-%m-%d %H:%M"))
        assert "error" not in r, r
        gz = r["sui_yun"]["ganzhi"]
        ok = gz == want_gz
        ok &= r["sui_yun"]["name"] == yun_t[gz[0]]
        ok &= r["ke_qi"]["si_tian"] == st_t[gz[1]]
        ok &= r["ke_qi"]["zai_quan"] == zq_t[gz[1]]
        ok &= set(x["name"] for x in r["xiang_he"]["types"]) == he_expect(gz)
        ok &= [s2["ke_qi"] for s2 in r["ke_qi"]["steps"]] == _oracle_keqi(gz, st_t[gz[1]], zq_t[gz[1]])
        if ok:
            same += 1
        else:
            diff += 1
            nd.append((s, gz, f"自研 vs oracle 不符"))
    # fate-craft 页面锚点：2026 丙午 初之气客=太阳寒水（三之气=司天少阴君火倒推）
    fc_ok = compute(datetime(2026, 7, 15, 12, 0))["ke_qi"]["steps"][0]["ke_qi"] == "太阳寒水"
    same += int(fc_ok)
    # 口径分歧申报（I-8，幂等）
    arbs, brows = [], []
    for cid, field, note in [
        ("wylq-001", "运气岁首（换年界）",
         "换年界口径差异：fate-craft「运气岁首在大寒」vs 干支纪年/WYLQ oracle 立春换年；自研按大寒（fate-craft 实测口径+运气学主流），大寒~立春间两口径岁运/司天在泉不同"),
        ("wylq-002", "六步起点",
         "六步起点口径差异：主气客气初之气起于大寒（本实现，运气学主流+fate-craft 节气窗口）vs 立春（WYLQ oracle get_main_qi_lichun）；大寒~立春间当前步序不同"),
        ("wylq-003", "六步历法精度",
         "六步历法精度差异：定气节气时刻（solar_terms.csv，fate-craft「定气」档同口径）vs 60 日等分近似（WYLQ oracle 立春+60 天）；每步差 0~5 日，节点附近当前步可不同"),
        ("wylq-004", "相合-天符（戊申）",
         "oracle 表分歧：WYLQ 同化表缺戊申（火运太过+申年少阳相火司天），自研按《六微旨大论》天符定义+fate-craft $e 算法判=天符（戊申为传统天符 12 年之一）；取自研+理论推导"),
        ("wylq-005", "相合-同岁会（癸巳）",
         "oracle 表分歧：WYLQ 同化表缺癸巳（火运不及+巳年少阳相火在泉），自研按《六元正纪大论》「岁运不及而与地气相同」判=同岁会（fate-craft 算法同）；取自研+理论推导")]:
        arbs.append([cid, field, "fate-craft/WYLQ 口径", "自研口径", "复核者", "alt", note, "oracle 对拍",
                     "自研 l3_wuyunliuqi.py（wylq-01..05）", "fate-craft(profound.fate-craft.com)+WYLQ(GitHub Carrie-HuYY/WYLQ)"])
        brows.append([cid, "口径分歧", "全区间", f"oracle({field})", f"自研({field})", "arbitrated", note])
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
    rep = [f"L3 五运六气对拍（l3_wuyunliuqi.py）：{len(cases)} 例（5 手工锚点+15 随机干支年 1949-2100 年中日期）+fate-craft 2026 丙午页面锚点",
           f"字段：岁运干支/太过不及名、司天、在泉、相合五类、客气六步全序列——一致 {same}/{len(cases) + 1}；分歧 {diff}",
           "oracle 1=fate-craft 五运六气（profound.fate-craft.com，页面锚点+JS 算法逆读：$e 函数天符/岁会/太一天符/同天符/同岁会、he 函数客气轮排）",
           "oracle 2=WYLQ（GitHub Carrie-HuYY/WYLQ 读码：calculate_qi/calculate_relationship 表与轮排）",
           "分歧申报 5 条（wylq-001~005）：口径类 3 条（岁首大寒 vs 立春；六步起点大寒 vs 立春；定气历表 vs 60 日近似）+值分歧 2 条（WYLQ 表缺戊申天符/癸巳同岁会，自研+fate-craft 算法补遗）",
           "底本：《黄帝内经·素问》运气七篇（天元纪大论/五运行大论/六微旨大论/气交变大论/五常政大论/六元正纪大论/至真要大论）；节点权威=solar_terms.csv 定气中气时刻",
           "异文标注：水运不及「涸流」（通行本）一作「涫流」；岁会=四正+四季 8 年（四孟同气不算，fate-craft/WYLQ 60 甲子图互证）；客气轮排有李阳波「司天在泉起首气」少数派",
           "边界声明：运气推演为理论体系，非医学诊断，不构成任何诊疗建议",
           f"申报：arbitration_log.csv wylq- 新增 {len(arbs)} 条；boundary_cases.csv wylq- 新增 {len(brows)} 条（幂等）"]
    for s, gz, n in nd:
        rep.append(f"  分歧：{s} {gz} {n}")
    txt = "\n".join(rep) + "\n"
    with open(os.path.join(BASE, "report", "l3_wuyunliuqi_report.txt"), "w", encoding="utf-8") as f:
        f.write(txt)
    return rep

def main():
    ap = argparse.ArgumentParser(description="五运六气（岁运/主气六步/客气六步/司天在泉/运气相合，Rule-ID wylq-01..05）")
    ap.add_argument("--datetime", help="北京时间 YYYY-MM-DD HH:MM（整分钟）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--compare", action="store_true", help="对拍 WYLQ oracle + 申报口径分歧并写报告")
    a = ap.parse_args()
    if a.compare:
        print("\n".join(compare()))
        return
    dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    r = compute(dt)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif "error" in r:
        print(r["error"])
    else:
        sy = r["sui_yun"]
        print(f"输入: {r['input']['datetime']}")
        print(f"岁运(wylq-01): {sy['ganzhi']}年 {sy['name']}（{sy['ji']}）")
        print(f"司天/在泉(wylq-03): {r['ke_qi']['si_tian']} / {r['ke_qi']['zai_quan']}")
        print(f"相合(wylq-04): {'/'.join(x['name'] for x in r['xiang_he']['types']) or '无'}")
        c = r["zhu_qi"]["current"]
        print(f"当前(wylq-02/03/05): {c['step']} {c['start_term']}~{c['end_term']}（{c['start']}~{r['ke_qi']['current']['end']}）"
              f"主气{c['qi']} 客气{r['ke_qi']['current']['qi']}")
        for n in r["notes"]:
            print(f"  · {n}")

if __name__ == "__main__":
    main()

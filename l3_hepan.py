# -*- coding: utf-8 -*-
"""l3_hepan.py — 人际合盘模块：任意两人（婚姻/合伙人/朋友/相处）的缘分结构分析，泛化非婚姻专用（Rule-ID hp-01..hp-07）。
系统理念"差异无处藏身"：每个输出项带 Rule-ID/底本出处/异文标注；验证多源对拍（易安居八字合婚 hehun.php 为 oracle）。
输入=北京时间+东经（复用 m1 四柱内核）；任一方出生时辰未知 → 时柱输出双候选（早子时按当日日干、晚子时按次日日干推时柱，
日柱照常定），标注"时辰未知，双盘参考"。运行 python l3_hepan.py --compare 对拍易安居。"""
import argparse, csv, json, os, random, re, sys, time
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m1
from rules import GAN, ZHI, WX, wx_of_gan, wx_of_zhi, rel, sheng, ke

BASE = os.path.dirname(os.path.abspath(__file__))
GAN_SHENGXIAO = "鼠牛虎兔龙蛇马羊猴鸡狗猪"
SCENES = ("婚姻", "合作", "朋友", "相处")

# ============================ 规则表（数据驱动，每表带底本） ============================
# 天干五合（《渊海子平·十干合》《三命通会·论十干合》：甲己合土、乙庚合金、丙辛合水、丁壬合木、戊癸合火）
WU_HE = {("甲", "己"): "土", ("乙", "庚"): "金", ("丙", "辛"): "水", ("丁", "壬"): "木", ("戊", "癸"): "火"}
# 天干相克（《三命通会·论十干》同性相克：甲戊、乙己、丙庚、丁辛、戊壬、己癸、庚甲、辛乙、壬丙、癸丁）
GAN_KE = {("甲", "戊"), ("乙", "己"), ("丙", "庚"), ("丁", "辛"), ("戊", "壬"), ("己", "癸"),
          ("庚", "甲"), ("辛", "乙"), ("壬", "丙"), ("癸", "丁")}
# 地支六合（《三命通会·论六合》：子丑合土、寅亥合木、卯戌合火、辰酉合金、巳申合水、午未合土）
LIU_HE = {("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")}
# 地支三合局（《三命通会·论三合》：申子辰水局、寅午戌火局、巳酉丑金局、亥卯未木局；两人间同局=半合）
SAN_HE = [("申子辰", "水"), ("寅午戌", "火"), ("巳酉丑", "金"), ("亥卯未", "木")]
SAN_HE_SET = {z: wx for group, wx in SAN_HE for z in group}
# 地支六冲（《三命通会·论冲》：子午、丑未、寅申、卯酉、辰戌、巳亥）
LIU_CHONG = {("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")}
# 地支三刑（《渊海子平·论三刑》：寅巳申无恩、丑戌未恃势、子卯无礼、辰午酉亥自刑）
SAN_XING = {("寅", "巳"): "无恩之刑", ("巳", "申"): "无恩之刑", ("申", "寅"): "无恩之刑",
            ("丑", "戌"): "恃势之刑", ("戌", "未"): "恃势之刑", ("未", "丑"): "恃势之刑",
            ("子", "卯"): "无礼之刑", ("卯", "子"): "无礼之刑",
            ("辰", "辰"): "自刑", ("午", "午"): "自刑", ("酉", "酉"): "自刑", ("亥", "亥"): "自刑"}
# 地支六害（《三命通会·论六害》：子未、丑午、寅巳、卯辰、申亥、酉戌）
LIU_HAI = {("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")}
# 咸池桃花（《渊海子平·论咸池》：寅午戌见卯、申子辰见酉、巳酉丑见午、亥卯未见子）
TAOHUA = {"寅": "卯", "午": "卯", "戌": "卯", "申": "酉", "子": "酉", "辰": "酉",
          "巳": "午", "酉": "午", "丑": "午", "亥": "子", "卯": "子", "未": "子"}
# 红鸾/天喜（《渊海子平》年支起：红鸾=(3-年支序)%12，天喜=红鸾对宫）——与 l3_shensha ss-10/11 同口径

def _pair_rel(a, b, table, name):
    """地支关系判定：a、b 无序对（一正一反命中同项，避免双计）。"""
    return (a, b) in table or (b, a) in table

def _sanhe_rel(a, b):
    return SAN_HE_SET.get(a) if SAN_HE_SET.get(a) and SAN_HE_SET[a] == SAN_HE_SET.get(b) else None

# 三刑三字组（《三命通会·论三刑》：寅巳申无恩/丑戌未恃势 三字俱全方成刑；子卯无礼仅两字；辰午酉亥同支自刑）
XING_3 = ({"寅", "巳", "申"}, {"丑", "戌", "未"})

def _xing_ok(x, y, pool):
    """(x, y) 是否构成三刑。pool=可用地支全集（去重后），三字组须三字俱全；
    同支自刑（辰午酉亥）两字即可；子卯无礼之刑仅两字。"""
    if x == y:
        return (x, y) in SAN_XING  # 自刑（辰午酉亥）
    pair = frozenset((x, y))
    for grp in XING_3:
        if pair <= grp:
            return grp <= pool  # 三字俱全方成刑
    return pair in (frozenset(("子", "卯")),)

def _zhi_list(p):
    """盘结构的四柱地支列表（无时柱取早子时盘）。"""
    return [p["pillars"][k][1] for k in ("year", "month", "day", "hour")] if p["pillars"]["hour"] \
        else [p["pillars"]["year"][1], p["pillars"]["month"][1], p["pillars"]["day"][1],
              p["hour_candidates"][0]["hour"][1]]

# ============================ 输入解析（含无时柱模式） ============================
def parse_person(s, lon):
    """'YYYY-MM-DD [HH:MM]' + 东经 → {datetime(参考), hour_unknown, lon}；无时间 → 时辰未知（参考 12:00 判年/月柱，日柱照常）。"""
    s = s.strip()
    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M")
        return {"dt": dt, "hour_unknown": False, "lon": lon}
    except ValueError:
        pass
    dt = datetime.strptime(s, "%Y-%m-%d")
    return {"dt": dt.replace(hour=12, minute=0), "hour_unknown": True, "lon": lon}  # 正午判年/月柱不跨日界

def get_pillars(p):
    """m1 四柱 → 本模块盘结构；无时柱时输出双候选（早子时=当日日干五鼠遁、晚子时=次日日干五鼠遁），标注双盘参考。"""
    r = m1.compute(p["dt"], p["lon"])
    if "error" in r:
        return {"error": r["error"]}
    pils = r["pillars"]
    gz = {k: pils[k]["ganzhi"] for k in ("year", "month", "day", "hour")}
    if p["hour_unknown"]:
        day_gz = gz["day"]
        nxt = (p["dt"] + timedelta(days=1)).strftime("%Y-%m-%d")
        nxt_days = m1.load_days()
        cands = [
            {"label": "早子时盘", "hour": m1.hour_pillar(day_gz, 0),
             "note": "子正口径（m1）：时柱按当日日干五鼠遁子时"},
            {"label": "晚子时盘", "hour": m1.hour_pillar(nxt_days.get(nxt, day_gz), 0),
             "note": "晚子时派（易安居 23:00 子初口径）：时柱按次日日干五鼠遁子时，日柱照常定"},
        ]
        return {"pillars": {**gz, "hour": None}, "day_master": gz["day"][0], "hour_unknown": True,
                "hour_candidates": cands, "nayin": gz["year"], "true_solar_time": r["true_solar_time"]}
    return {"pillars": gz, "day_master": gz["day"][0], "hour_unknown": False, "nayin": gz["year"],
            "hour_candidates": None, "true_solar_time": r["true_solar_time"]}

def load_nayin():
    """nayin.csv（键='甲子乙丑'双柱对）→ 拆成 {(单柱两字): 纳音五行名}；《渊海子平》纳音表。"""
    out = {}
    with open(os.path.join(BASE, "data", "nayin.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            pair, nm = r["ganzhi_pair"], r["wuxing_name"]
            if len(pair) == 4:  # 双柱对 → 拆两单柱同纳音
                out[pair[:2]], out[pair[2:]] = nm, nm
            else:
                out[pair] = nm
    return out

NAYIN_WX = {  # 纳音名末字 → 五行（《三命通会·论纳音》末字诀：海中金=金…）
    "金": "金", "火": "火", "木": "木", "水": "水", "土": "土"}

def nayin_wx(name):
    return name[-1] if name and name[-1] in NAYIN_WX else None

# ============================ hp-01 结构互动 ============================
HP1_SOURCE = "《渊海子平》（十干合/论三刑）《三命通会》（论六合/论冲/论三合/论六害）"
HP1_METHOD = ("A 四柱×B 四柱逐柱两两计数：天干五合（甲己合土…戊癸合火）、天干相克（同性相克：甲戊…癸丁）、"
              "地支六合（子丑合土…午未合土）、三合半合（申子辰…亥卯未同局）、六冲（子午…巳亥）、"
              "三刑（寅巳申无恩/丑戌未恃势/子卯无礼/辰午酉亥自刑）、六害（子未…酉戌）")
HP1_ALT = ("异文①三刑口径（2026-08-16 修正）：《三命通会·论三刑》「寅巳申何以謂之無恩」「辰午酉亥何以謂之自刑——"
           "寅申巳亥有寅巳申互相刑，內有亥無刑」，三刑三字俱全方成刑（子卯无礼之刑仅两字、辰午酉亥同支自刑除外），"
           "寅巳申/丑戌未仅见两字不判刑，落入其他关系（寅巳两字按六害）；此口径经易安居 hehun.php 实测证实"
           "（两字寅巳报相害、三字寅巳申报无恩之刑）；旧口径「两字相见即刑」弃用；"
           "②天干相克亦作「七冲」（甲庚乙辛丙壬丁癸）仅四对，取十干同性相克十对口径；"
           "③三合两人间为半合（缺一字），全合须三支齐全（身内三支论）；"
           "④支关系优先级链（hp-01/03/05 一致）：六合>同支自刑>三合半合>六冲>三刑（三字俱全）>六害；"
           "hp-07 夫妻宫另为单盘链（六冲>六合>三刑>六害，无三合半合/自刑分支）；"
           "巳申取合、寅申/丑未取冲、寅巳两字取害（寅巳申三字俱全时寅巳取刑）")

def hp01(a, b):
    """双方四柱干支逐对互动计数（无时柱方取早子时盘为默认，双候选另列）。"""
    ah = a["pillars"]["hour"] or a["hour_candidates"][0]["hour"]  # 时柱 ganzhi 串（无时柱取早子时盘）
    bh = b["pillars"]["hour"] or b["hour_candidates"][0]["hour"]
    ga = [a["pillars"]["year"][0], a["pillars"]["month"][0], a["pillars"]["day"][0], ah[0]]
    za = [a["pillars"]["year"][1], a["pillars"]["month"][1], a["pillars"]["day"][1], ah[1]]
    gb = [b["pillars"]["year"][0], b["pillars"]["month"][0], b["pillars"]["day"][0], bh[0]]
    zb = [b["pillars"]["year"][1], b["pillars"]["month"][1], b["pillars"]["day"][1], bh[1]]
    PN = ("年", "月", "日", "时")
    out = {"rule_id": "hp-01", "source": HP1_SOURCE, "method": HP1_METHOD, "alt": HP1_ALT,
           "counts": {"天干五合": 0, "天干相克": 0, "地支六合": 0, "地支三合": 0, "地支六冲": 0, "地支三刑": 0, "地支六害": 0},
           "pairs": {}}
    seen_zh = set()  # 地支无序对去重（一正一反只计一次，与 oracle 口径同）
    for i, (xg, xz) in enumerate(zip(ga, za)):
        for j, (yg, yz) in enumerate(zip(gb, zb)):
            wh = WU_HE.get((xg, yg)) or WU_HE.get((yg, xg))  # 五合单向表 → 双向查
            if wh:
                out["counts"]["天干五合"] += 1
                out["pairs"].setdefault("天干五合", []).append(
                    {"a": f"甲{PN[i]}干{xg}", "b": f"乙{PN[j]}干{yg}", "desc": f"{xg}{yg}合化{wh}",
                     "rule_id": "hp-01", "source": "《渊海子平·十干合》"})
            if (xg, yg) in GAN_KE or (yg, xg) in GAN_KE:
                out["counts"]["天干相克"] += 1
                out["pairs"].setdefault("天干相克", []).append(
                    {"a": f"甲{PN[i]}干{xg}", "b": f"乙{PN[j]}干{yg}", "desc": f"{xg}{yg}同性相克",
                     "rule_id": "hp-01", "source": "《三命通会·论十干》"})
            k = tuple(sorted((xz, yz)))
            if k in seen_zh:
                continue
            if _pair_rel(xz, yz, LIU_HE, "六合"):
                seen_zh.add(k)
                out["counts"]["地支六合"] += 1
                out["pairs"].setdefault("地支六合", []).append(
                    {"a": f"甲{PN[i]}支{xz}", "b": f"乙{PN[j]}支{yz}", "desc": f"{xz}{yz}六合",
                     "rule_id": "hp-01", "source": "《三命通会·论六合》"})
            elif xz == yz and (xz, yz) in SAN_XING:  # 同支自刑（辰午酉亥）优先于同局半合（oracle 同口径）
                seen_zh.add(k)
                out["counts"]["地支三刑"] += 1
                out["pairs"].setdefault("地支三刑", []).append(
                    {"a": f"甲{PN[i]}支{xz}", "b": f"乙{PN[j]}支{yz}", "desc": f"{xz}{yz}同支相刑（自刑）",
                     "rule_id": "hp-01", "source": "《渊海子平·论三刑》辰午酉亥自刑"})
            elif _sanhe_rel(xz, yz):
                seen_zh.add(k)
                out["counts"]["地支三合"] += 1
                out["pairs"].setdefault("地支三合", []).append(
                    {"a": f"甲{PN[i]}支{xz}", "b": f"乙{PN[j]}支{yz}",
                     "desc": f"{xz}{yz}属{_sanhe_rel(xz, yz)}局（半合）",
                     "rule_id": "hp-01", "source": "《三命通会·论三合》"})
            elif _pair_rel(xz, yz, LIU_CHONG, "六冲"):
                seen_zh.add(k)
                out["counts"]["地支六冲"] += 1
                out["pairs"].setdefault("地支六冲", []).append(
                    {"a": f"甲{PN[i]}支{xz}", "b": f"乙{PN[j]}支{yz}", "desc": f"{xz}{yz}六冲",
                     "rule_id": "hp-01", "source": "《三命通会·论冲》"})
            elif _xing_ok(xz, yz, set(za) | set(zb)):  # 三刑须三字俱全（寅巳申/丑戌未），子卯两字、辰午酉亥自刑除外
                seen_zh.add(k)
                out["counts"]["地支三刑"] += 1
                nm = SAN_XING.get((xz, yz)) or SAN_XING[(yz, xz)]
                out["pairs"].setdefault("地支三刑", []).append(
                    {"a": f"甲{PN[i]}支{xz}", "b": f"乙{PN[j]}支{yz}", "desc": f"{xz}{yz}相刑（{nm}）",
                     "rule_id": "hp-01", "source": "《渊海子平·论三刑》"})
            elif _pair_rel(xz, yz, LIU_HAI, "六害"):
                seen_zh.add(k)
                out["counts"]["地支六害"] += 1
                out["pairs"].setdefault("地支六害", []).append(
                    {"a": f"甲{PN[i]}支{xz}", "b": f"乙{PN[j]}支{yz}", "desc": f"{xz}{yz}六害",
                     "rule_id": "hp-01", "source": "《三命通会·论六害》"})
    return out

# ============================ hp-02 十神互定位（核心） ============================
HP2_SOURCE = "《渊海子平·论十神》《三命通会》十神定位法（r5 十神表：生我印、我生食伤、克我官杀、我克财、同我比劫）"
SHISHEN_ROLE = {  # 十神 → 关系角色注解（合婚/合作/相处性质）
    "正财": "财星：利益合作倾向，务实互补（我克，财为妻/利源）",
    "偏财": "财星：利益合作倾向，大方不拘（我克，偏财主横财/人脉）",
    "正官": "官星：约束/责任/管理倾向，对方持重（克我，官主规矩）",
    "七杀": "七杀：强势/压力倾向，对方有威压（克我，杀主竞争压制）",
    "正印": "印星：庇护/支持倾向，长辈缘厚（生我，印主扶持）",
    "偏印": "印星：庇护/独思倾向（生我，枭神主偏执智谋）",
    "比肩": "比肩：平等并肩/同辈竞争倾向（同我，比主朋友）",
    "劫财": "劫财：竞争分利/内耗倾向（同我，劫主争夺）",
    "食神": "食神：轻松相处/表达输出倾向（我生，食主享受）",
    "伤官": "伤官：挑剔消耗/创意对抗倾向（我生，伤主锋芒）",
}

def hp02(a, b):
    """A 日干入 B 盘十神位、B 日干入 A 盘（核心）；年干/月干/日支主气互定位简表。"""
    cg = m1.load_canggan()

    def cross(da, a_dm, db, b_dm):
        return {"looker_dm": a_dm, "target_dm": b_dm, "god": m1.ten_god(b_dm, a_dm)}

    def side(s, o):  # s 方日干在 o 盘中的定位
        god = m1.ten_god(o["day_master"], s["day_master"])
        brief = {"正财": "财", "偏财": "财", "正官": "官", "七杀": "杀", "正印": "印", "偏印": "印",
                 "比肩": "比", "劫财": "劫", "食神": "食", "伤官": "伤"}[god]
        return {"god": god, "brief": brief, "role": SHISHEN_ROLE[god]}

    def brief_god(o_dm, g):
        god = m1.ten_god(o_dm, g)
        return {"god": god, "role": SHISHEN_ROLE[god]}

    r = {"rule_id": "hp-02", "source": HP2_SOURCE,
         "main": {  # 日干互定位（核心两项）；subject=被定位方日干、viewed_by=视方、god=视方对 subject 的十神
             "a_in_b": {"subject": "A 日干", "dm": a["day_master"], "viewed_by": f"B（日干{b['day_master']}）",
                        "god": m1.ten_god(b["day_master"], a["day_master"]),
                        "role": SHISHEN_ROLE[m1.ten_god(b["day_master"], a["day_master"])],
                        "interpretation": f"B 视 A 为{m1.ten_god(b['day_master'], a['day_master'])}：B 对 A 的关系立场（见 role）"},
             "b_in_a": {"subject": "B 日干", "dm": b["day_master"], "viewed_by": f"A（日干{a['day_master']}）",
                        "god": m1.ten_god(a["day_master"], b["day_master"]),
                        "role": SHISHEN_ROLE[m1.ten_god(a["day_master"], b["day_master"])],
                        "interpretation": f"A 视 B 为{m1.ten_god(a['day_master'], b['day_master'])}：A 对 B 的关系立场（见 role）"}}}
    # 简表：A 年干/月干/日支主气 在 B 盘；B 年干/月干/日支主气 在 A 盘
    zhi_master = {z: cg[z][0] for z in ZHI}  # 藏干主气（canggan.csv 首干）
    r["brief"] = {
        "a_in_b": [{"pos": "年干", "gan": a["pillars"]["year"][0], **brief_god(b["day_master"], a["pillars"]["year"][0])},
                   {"pos": "月干", "gan": a["pillars"]["month"][0], **brief_god(b["day_master"], a["pillars"]["month"][0])},
                   {"pos": "日支主气", "gan": zhi_master[a["pillars"]["day"][1]],
                    **brief_god(b["day_master"], zhi_master[a["pillars"]["day"][1]])}],
        "b_in_a": [{"pos": "年干", "gan": b["pillars"]["year"][0], **brief_god(a["day_master"], b["pillars"]["year"][0])},
                   {"pos": "月干", "gan": b["pillars"]["month"][0], **brief_god(a["day_master"], b["pillars"]["month"][0])},
                   {"pos": "日支主气", "gan": zhi_master[b["pillars"]["day"][1]],
                    **brief_god(a["day_master"], zhi_master[b["pillars"]["day"][1]])}]}
    return r

# ============================ hp-03 夫妻宫与通用 ============================
HP3_SOURCE = "《渊海子平》《三命通会》婚配口诀；纳音：data/nayin.csv（《渊海子平》纳音表）"
def hp03(a, b, nayin_tab):
    """日支冲合（婚姻重点）+ 生肖六合六冲三合（通用亲疏）+ 纳音互配 + 五行互补。"""
    ar, br = a["pillars"]["day"][1], b["pillars"]["day"][1]
    r = {"rule_id": "hp-03", "source": "《渊海子平》《三命通会》婚配口诀；data/nayin.csv 纳音"}
    # 1) 日支冲合（夫妻宫）
    if _pair_rel(ar, br, LIU_HE, "六合"):
        fqg = ("六合", "日支夫妻宫六合：姻缘亲密，婚姻场景强正项")
    elif ar == br and (ar, br) in SAN_XING:  # 同支自刑（辰午酉亥）优先于同局半合
        fqg = ("三刑", f"日支夫妻宫{ar}{br}同支自刑：婚姻场景负项")
    elif _sanhe_rel(ar, br):
        fqg = ("三合", f"日支夫妻宫三合（{_sanhe_rel(ar, br)}局半合）：姻缘契合，婚姻场景正项")
    elif _pair_rel(ar, br, LIU_CHONG, "六冲"):
        fqg = ("六冲", "日支夫妻宫六冲：婚配易生摩擦聚少离多，婚姻场景强负项")
    elif _xing_ok(ar, br, set(_zhi_list(a)) | set(_zhi_list(b))):  # 三刑须三字俱全（与 hp-01 一致口径）
        fqg = ("三刑", f"日支夫妻宫相刑（{SAN_XING.get((ar, br)) or SAN_XING[(br, ar)]}）：婚姻场景负项")
    elif _pair_rel(ar, br, LIU_HAI, "六害"):
        fqg = ("六害", "日支夫妻宫六害：婚姻场景负项")
    else:
        fqg = ("无特殊", "日支无冲合刑害关系")
    r["ri_zhi"] = {"a_day_zhi": ar, "b_day_zhi": br, "relation": fqg[0], "note": fqg[1],
                   "rule_id": "hp-03", "source": "《三命通会》论六合/论冲/论三刑（日支为夫妻宫）"}
    # 2) 生肖（年支）六合六冲三合相害（通用亲疏）
    ay, by = a["pillars"]["year"][1], b["pillars"]["year"][1]
    if _pair_rel(ay, by, LIU_HE, "六合"):
        sx = ("六合", f"生肖{ay}{by}六合：亲缘合和，通用正项")
    elif ay == by and (ay, by) in SAN_XING:  # 同支自刑（辰午酉亥）
        sx = ("自刑", f"生肖{ay}{by}同支自刑：亲缘多磨，通用负项")
    elif _sanhe_rel(ay, by):
        sx = ("三合", f"生肖{ay}{by}三合（{_sanhe_rel(ay, by)}局）：亲缘默契，通用正项")
    elif _pair_rel(ay, by, LIU_CHONG, "六冲"):
        sx = ("六冲", f"生肖{ay}{by}六冲（生年相冲）：亲缘疏离，通用负项")
    elif _xing_ok(ay, by, set(_zhi_list(a)) | set(_zhi_list(b))):  # 三刑须三字俱全（与 hp-01/ri_zhi 一致口径）
        sx = ("三刑", f"生肖{ay}{by}相刑（{SAN_XING.get((ay, by)) or SAN_XING[(by, ay)]}）：亲缘刑克，通用负项")
    elif _pair_rel(ay, by, LIU_HAI, "六害"):
        sx = ("相害", f"生肖{ay}{by}相害：亲缘不睦，通用负项")
    else:
        sx = ("无特殊", f"生肖{ay}{by}无冲合刑害")
    r["sheng_xiao"] = {"a_year_zhi": ay, "b_year_zhi": by, "relation": sx[0], "note": sx[1],
                       "rule_id": "hp-03", "source": "《三命通会》生肖六合（子丑合…）、三合、六冲（子午…）"}
    # 3) 纳音互配（年柱纳音生克）
    an, bn = nayin_tab.get(a["nayin"], ""), nayin_tab.get(b["nayin"], "")
    aw, bw = nayin_wx(an), nayin_wx(bn)
    if aw and bw:
        if sheng(aw, bw):
            nay = ("相生", f"{an}（{aw}）生 {bn}（{bw}）：纳音相生，滋养对方")
        elif sheng(bw, aw):
            nay = ("相生", f"{bn}（{bw}）生 {an}（{aw}）：纳音相生，滋养对方")
        elif ke(aw, bw):
            nay = ("相克", f"{an}（{aw}）克 {bn}（{bw}）：纳音相克，损耗对方")
        elif ke(bw, aw):
            nay = ("相克", f"{bn}（{bw}）克 {an}（{aw}）：纳音相克，损耗对方")
        else:
            nay = ("比和", f"{an}（{aw}）与 {bn}（{bw}）比和：纳音相类，平平")
    else:
        nay = ("未知", f"纳音查表缺失：{a['nayin']}/{b['nayin']}")
    r["nayin"] = {"a_year_gz": a["nayin"], "a_nayin": an or "查表缺失", "b_year_gz": b["nayin"], "b_nayin": bn or "查表缺失",
                  "relation": nay[0], "note": nay[1], "rule_id": "hp-03", "source": "data/nayin.csv（《渊海子平》纳音表，30 对）"}
    # 4) 五行互补（A 缺 B 旺统计；8 字计五行=天干4+地支4，不含藏干）
    def wu_count(p):
        cnt = {w: 0 for w in WX}
        for k in ("year", "month", "day", "hour"):
            gz = p["pillars"][k] or p["hour_candidates"][0]["hour"]
            cnt[wx_of_gan(gz[0])] += 1
            cnt[wx_of_zhi(gz[1])] += 1
        return cnt
    ca, cb = wu_count(a), wu_count(b)
    comp = []
    for w in WX:
        if ca[w] == 0 and cb[w] >= 2:
            comp.append({"a_missing": w, "b_strong": cb[w], "desc": f"A 缺{w}、B {w}旺({cb[w]})：互补可取"})
        if cb[w] == 0 and ca[w] >= 2:
            comp.append({"b_missing": w, "a_strong": ca[w], "desc": f"B 缺{w}、A {w}旺({ca[w]})：互补可取"})
    r["wuxing"] = {"a_counts": ca, "b_counts": cb, "complementary": comp, "count_basis": "天干4+地支4=8 字（不含藏干）",
                   "rule_id": "hp-03", "source": "五行互补统计（r5 五行表）"}
    return r

# ============================ hp-04 关系倾向结论 ============================
HP4_SOURCE = "《渊海子平》《三命通会》合婚/关系判断综合；结构分+十神角色分+互补分 加权启发式"
HP4_DISCLAIMER = "规则启发式，非神断：倾向结论为规则计分加权综合，仅供参考，不构成任何决策依据"
# 场景侧重：{场景: (权重(结构,十神,互补,夫妻宫), 侧重文字)}
SCENE_W = {
    "婚姻": ((0.5, 0.5, 0.5, 2.5), "侧重：日支夫妻宫冲合（权重最高）、生肖六合三合、纳音互配"),
    "合作": ((0.5, 1.5, 1.5, 0.5), "侧重：十神互定位财官印（利益/管理角色）、五行互补、纳音生克"),
    "朋友": ((1.5, 1.0, 0.5, 1.0), "侧重：天干五合/地支六合三合、比肩食神角色、生肖六合三合"),
    "相处": ((2.0, 0.5, 0.5, 1.0), "侧重：六冲/三刑/六害（负面结构权重最高）、日支关系、七杀伤官角色"),
}
ROLE_SCORE = {"正财": 2, "偏财": 2, "正官": 1, "七杀": -1, "正印": 2, "偏印": 2, "比肩": 0, "劫财": -1, "食神": 1, "伤官": -1}

def hp04(a, b, h1, h2, h3):
    """结构分+十神角色分+互补分+夫妻宫分 → 总倾向三档（相合/平/相冲）；四场景加权倾向。"""
    c = h1["counts"]
    structure = (1 * c["天干五合"] + 1 * c["地支六合"] + 1 * c["地支三合"]
                 - 1 * c["天干相克"] - 1 * c["地支六冲"] - 1 * c["地支三刑"] - 1 * c["地支六害"])
    shishen = ROLE_SCORE[h2["main"]["a_in_b"]["god"]] + ROLE_SCORE[h2["main"]["b_in_a"]["god"]]
    comp = 2 * len(h3["wuxing"]["complementary"])
    nayin_score = {"相生": 1, "相克": -1, "比和": 0}.get(h3["nayin"]["relation"], 0)
    fqg_score = {"六合": 2, "三合": 2, "六冲": -2, "三刑": -2, "六害": -1, "无特殊": 0}[h3["ri_zhi"]["relation"]]
    total = structure + shishen + comp + nayin_score + fqg_score
    def band(score):
        return "相合" if score >= 4 else ("相冲" if score <= -4 else "平")
    scenes = {}
    for sc, (w, note) in SCENE_W.items():
        s = w[0] * structure + w[1] * shishen + w[2] * (comp + nayin_score) + w[3] * fqg_score
        scenes[sc] = {"score": round(s, 1), "tendency": band(s), "focus": note}
    return {"rule_id": "hp-04", "source": HP4_SOURCE,
            "scores": {"structure": structure, "shishen": shishen, "complementary": comp,
                       "nayin": nayin_score, "day_branch(fqg)": fqg_score, "total": total},
            "score_rule": "结构(五合+1/六合+1/三合+1/天干克-1/六冲-1/三刑-1/六害-1) + 十神(财+2 官+1 杀-1 印+2 比0 劫-1 食+1 伤-1，双向) + 互补每对+2 + 纳音生+1 克-1 + 日支(六合+2 三合+2 六冲-2 三刑-2 六害-1)",
            "tendency": band(total), "disclaimer": HP4_DISCLAIMER,
            "scene_tendencies": scenes, "scene": None}

# ============================ hp-05 流年合盘 ============================
HP5_SOURCE = "《三命通会·论太岁》（流年太岁章）：流年干支对命局引动；规则启发式，非神断"
def hp05(a, b, year):
    """流年合盘：target_year（公历或干支）→ 流年干支、对双方日干十神引动、对双方年支/日支冲合刑害、三档倾向。"""
    if isinstance(year, int):
        y = year
        ly = GAN[(y - 4) % 10] + ZHI[(y - 4) % 12]
        label = f"{y}年"
    else:  # 干支
        ly = year
        y = None
        label = year
    lg, lz = ly
    events, score = [], 0
    for nm, p in (("A", a), ("B", b)):
        g = m1.ten_god(p["day_master"], lg)
        s = ROLE_SCORE[g]
        score += s
        events.append({"target": nm, "type": "流年干十神引动",
                       "desc": f"{label}天干{lg}对{nm}日干{p['day_master']}为{g}：{SHISHEN_ROLE[g]}",
                       "score": s})
        for pos, z in (("年支", p["pillars"]["year"][1]), ("日支", p["pillars"]["day"][1])):
            if _pair_rel(z, lz, LIU_HE, "六合"):
                ev, sc = ("六合", 1), 1
            elif z == lz and (z, lz) in SAN_XING:  # 同支自刑优先
                ev, sc = ("三刑", -1), -1
            elif _sanhe_rel(z, lz):
                ev, sc = ("三合", 1), 1
            elif _pair_rel(z, lz, LIU_CHONG, "六冲"):
                ev, sc = ("六冲", -1), -1
            elif _xing_ok(z, lz, set(_zhi_list(p)) | {lz}):  # 三刑须三字俱全（流年支+命局支），与 hp-01 一致口径
                ev, sc = ("三刑", -1), -1
            elif _pair_rel(z, lz, LIU_HAI, "六害"):
                ev, sc = ("六害", -1), -1
            else:
                ev, sc = ("无特殊", 0), 0
            if sc:
                score += sc
                events.append({"target": nm, "type": f"流年支对{pos}",
                               "desc": f"{label}地支{lz} 与 {nm} {pos}{z}：{ev[0]}{ev[1]}", "score": sc})
    tendency = "顺" if score >= 2 else ("阻" if score <= -2 else "平")
    return {"rule_id": "hp-05", "source": HP5_SOURCE, "target_year": label, "liunian_gz": ly,
            "tai_sui": {"zhi": lz, "desc": f"{ly}年值年太岁为{lz}（{GAN_SHENGXIAO[ZHI.index(lz)]}年）"
                                         f"，《三命通会·论太岁》：「太岁者，岁之君」，流年支与命局支冲合刑害为引动主轴"},
            "events": events, "score": score, "tendency": tendency,
            "disclaimer": "规则启发式，非神断：流年倾向为十神引动+地支冲合加权综合"}

# ============================ hp-06 六爻测事接口（接线 l3_liuyao） ============================
HP6_USE = {  # 问事分类 → 用神取法（六爻代占规则，数据驱动）
    "求财": "妻财爻（财为用神）",
    "合作": "妻财爻（利分利）+ 兄弟爻（合伙同行），兼看应爻（对方）",
    "谋事": "官鬼爻（事之成败，官鬼为事业用神），兼看父母爻（文书合同）",
    "姻缘代占女测男": "官鬼爻（女测男以官鬼为夫）",
    "姻缘代占男测女": "妻财爻（男测女以妻财为妻）",
    "测朋友": "兄弟爻（朋友同辈以兄弟为用）",
}
HP6_SOURCE = "《增删卜易·用神章》：用神取法（女测男官鬼、男测女妻财、测朋友兄弟、求财妻财）；起卦=l3_liuyao.py 时间起卦（《梅花易数》）"
def hp06(ask_type, ask_dt, lon=120.0):
    """六爻测事：问事分类 + 当前时间 → 起卦入口（接线 l3_liuyao.compute）；l3_liuyao 未就绪则输出桩位。"""
    use = HP6_USE.get(ask_type, "未收录分类，参考同类取用")
    r = {"rule_id": "hp-06", "source": HP6_SOURCE, "ask_type": ask_type, "use_god": use,
         "note": "代占取用：女测男姻缘官鬼、男测女姻缘妻财、测朋友兄弟、求财妻财（规则表数据驱动）"}
    try:
        import l3_liuyao
        gua = l3_liuyao.compute(ask_dt, lon, "lunar")
        if isinstance(gua, dict) and "ben_gua" in gua:
            bg, vg = gua["ben_gua"], gua["bian_gua"]
            dong = [l["pos"] for l in gua["lines"] if l["dong"]]
            r.update({"engine": "l3_liuyao.compute（时间起卦·农历）", "ask_time": ask_dt.strftime("%Y-%m-%d %H:%M"),
                      "ben_gua": bg["name"], "palace": bg["palace"], "bian_gua": vg["name"],
                      "dong_yao": dong, "shi_pos": bg["shi_pos"], "ying_pos": bg["ying_pos"],
                      "liuqin": [{"pos": l["pos"], "qin": l.get("qin") or l.get("liuqin") or l.get("liu_qin"),
                                  "zhi": l.get("zhi")} for l in gua["lines"]],
                      "interpret": f"{ask_type}：用神取「{use}」，看用神爻旺衰与世应关系"})
        else:
            r.update({"engine": "桩位", "note": "l3_liuyao.compute 未返回排盘（接口未就绪/半成品），待六爻引擎完成后接线"})
    except Exception as e:  # l3_liuyao 并发中：半成品/缺失 → 桩位输出，绝不自己实现六爻引擎
        r.update({"engine": "桩位", "stub": True,
                  "note": f"l3_liuyao.py 未就绪（{type(e).__name__}），此接口为桩位；待六爻引擎完成后接线。"
                          f"起卦入口：时间起卦（《梅花易数》）→ 本卦/变卦/动爻 → 用神「{use}」断应期"})
    return r

# ============================ hp-07 代占/直断姻缘（单盘） ============================
HP7_SOURCE = "《渊海子平》（夫妻宫=日支、官星/财星引动、咸池桃花）；《三命通会》红鸾天喜；应期为流年引动近似"
HP7_MONTH_HINT = {"子": "农历十一月", "丑": "农历十二月", "寅": "农历正月", "卯": "农历二月", "辰": "农历三月",
                  "巳": "农历四月", "午": "农历五月", "未": "农历六月", "申": "农历七月", "酉": "农历八月",
                  "戌": "农历九月", "亥": "农历十月"}
def hp07(p, sex, year0, nayin_tab):
    """单盘直断姻缘：夫妻宫 + 官星（女）/财星（男）引动 + 桃花/红鸾/天喜 + 未来 5 年应期窗口。
    对象八字未知 → 指向 hp-06 六爻代占（用神取法规则表）。"""
    dm = p["day_master"]
    cg = m1.load_canggan()
    pils = p["pillars"]
    dz = pils["day"][1]
    r = {"rule_id": "hp-07", "source": HP7_SOURCE, "sex": sex, "day_master": dm}
    # 1) 夫妻宫（日支）：主气十神 + 日支与年月时支冲合
    master = cg[dz][0]
    r["fuqigong"] = {"day_zhi": dz, "master_gan": master, "master_god": m1.ten_god(dm, master),
                     "note": f"日支{dz}为夫妻宫，主气{master}对日干{dm}为{m1.ten_god(dm, master)}"
                             f"（{SHISHEN_ROLE[m1.ten_god(dm, master)]}）；日支被冲合为配偶宫动象"}
    r["fuqigong"]["zhi_rels"] = []
    for pos in ("year", "month", "hour"):
        gz = pils[pos]
        if gz is None:
            continue
        z = gz[1]
        if _pair_rel(dz, z, LIU_CHONG, "六冲"):
            r["fuqigong"]["zhi_rels"].append({"pos": pos, "zhi": z, "rel": "六冲",
                                              "note": f"日支{dz}与{pos}支{z}六冲：夫妻宫逢冲，婚期/关系易波动"})
        elif _pair_rel(dz, z, LIU_HE, "六合"):
            r["fuqigong"]["zhi_rels"].append({"pos": pos, "zhi": z, "rel": "六合",
                                              "note": f"日支{dz}与{pos}支{z}六合：夫妻宫逢合，姻缘顺"})
        elif _xing_ok(dz, z, set(_zhi_list(p))):  # 三刑须三字俱全（单盘四支内），与 hp-01/03 一致口径
            r["fuqigong"]["zhi_rels"].append({"pos": pos, "zhi": z, "rel": "三刑",
                                              "note": f"日支{dz}与{pos}支{z}相刑：夫妻宫逢刑，婚内多磨"})
        elif _pair_rel(dz, z, LIU_HAI, "六害"):
            r["fuqigong"]["zhi_rels"].append({"pos": pos, "zhi": z, "rel": "六害",
                                              "note": f"日支{dz}与{pos}支{z}六害：夫妻宫逢害，婚内不睦"})
    # 2) 官星（女）/财星（男）引动：四柱天干+地支主气统计
    want = "官杀" if sex == "女" else "财星"
    hits = []
    for pos in ("year", "month", "day", "hour"):
        gz = pils[pos]
        if gz is None:
            continue
        for g, tag in ((gz[0], "干"), (cg[gz[1]][0], "支主气")):
            god = m1.ten_god(dm, g)
            if sex == "女" and god in ("正官", "七杀"):
                hits.append({"pos": pos, "tag": tag, "gan": g, "god": god,
                             "note": f"{pos}{tag}{g}为{god}：夫星引动"})
            elif sex == "男" and god in ("正财", "偏财"):
                hits.append({"pos": pos, "tag": tag, "gan": g, "god": god,
                             "note": f"{pos}{tag}{g}为{god}：妻星引动"})
    r["guan_cai"] = {"want": want, "hits": hits,
                     "note": "官星（女）/财星（男）为姻缘用神：引动越明显，姻缘信息越强" if hits else f"{want}无明显引动（四柱不见或弱）"}
    # 3) 桃花/红鸾/天喜
    yz = pils["year"][1]
    tz, hong = TAOHUA[yz], ZHI[(3 - ZHI.index(yz)) % 12]
    tian = ZHI[(9 - ZHI.index(yz)) % 12]
    got = {z: nm for nm, z in (("咸池桃花", tz), ("红鸾", hong), ("天喜", tian))}
    hits2 = []
    for pos in ("year", "month", "day", "hour"):
        gz = pils[pos]
        if gz is None:
            continue
        z = gz[1]
        if z in got:
            hits2.append({"pos": pos, "zhi": z, "shen": got[z],
                          "note": f"{pos}支{z}为{got[z]}（{HP7_MONTH_HINT[z]}）"})
    r["taohua"] = {"basis": {"咸池桃花": tz, "红鸾": hong, "天喜": tian}, "hits": hits2,
                   "source": "咸池=《渊海子平·论咸池》年支起；红鸾/天喜=《渊海子平》年支起（与 l3_shensha ss-03/10/11 同口径）"}
    # 4) 未来 5 年应期窗口（流年干引动官/财 + 流年支命中桃花/红鸾/天喜 或 与日支六合）
    wins = []
    for y in range(year0, year0 + 5):
        ly = GAN[(y - 4) % 10] + ZHI[(y - 4) % 12]
        why = []
        g = m1.ten_god(dm, ly[0])
        if (sex == "女" and g in ("正官", "七杀")) or (sex == "男" and g in ("正财", "偏财")):
            why.append(f"流年干{ly[0]}为{g}（{['正官','七杀','正财','偏财'][['正官','七杀','正财','偏财'].index(g)] if g in ('正官','七杀','正财','偏财') else ''}引动）")
        if ly[1] in (tz, hong, tian):
            why.append(f"流年支{ly[1]}临{got[ly[1]]}")
        if _pair_rel(dz, ly[1], LIU_HE, "六合"):
            why.append(f"流年支{ly[1]}与日支{dz}六合（夫妻宫逢合）")
        if why:
            wins.append({"year": y, "liunian": ly, "why": why})
    r["yingqi"] = {"window": wins, "note": "应期窗口=未来 5 年流年干引动官/财 或 流年支临桃花/红鸾/天喜/日支六合 的年份（近似，非精确应期）"}
    r["unknown_target"] = {"if_unknown": "若对象八字未知：改用 hp-06 六爻代占——女测男官鬼、男测女妻财、测朋友兄弟（规则表数据驱动）"}
    return r

# ============================ 主入口 compute ============================
def compute(a_in, b_in=None, lon_a=120.0, lon_b=120.0, scene="婚姻", year=None,
            single_in=None, single_sex="女", single_year=None, ask=None, ask_dt=None):
    """合盘主入口：双盘（hp-01..05）+ 可选流年 hp-05 + 单盘代占 hp-07 + 六爻 hp-06。
    返回 JSON，全字段带 rule_id/source/alt（差异无处藏身）。"""
    nayin_tab = load_nayin()
    out = {"rule_id": "hp-00",
           "source": "人际合盘模块 l3_hepan.py：底本《渊海子平》《三命通会》《滴天髓》（十神定位）；hp-01..07 各项见各自 source/alt",
           "disclaimer": "规则启发式，非神断：合盘倾向/应期为规则计分综合，仅供文化参考",
           "input": {}, "notes": []}
    if b_in is not None and a_in is not None:  # 双盘合盘
        pa, pb = parse_person(a_in, lon_a), parse_person(b_in, lon_b)
        A, B = get_pillars(pa), get_pillars(pb)
        if "error" in A or "error" in B:
            return {"error": A.get("error") or B.get("error")}
        out["input"] = {"a": {"input": a_in, "lon": lon_a, "hour_unknown": A["hour_unknown"]},
                        "b": {"input": b_in, "lon": lon_b, "hour_unknown": B["hour_unknown"]},
                        "scene": scene if scene in SCENES else "婚姻"}
        out["persons"] = [{"name": "A", **{k: v for k, v in A.items() if k != "pillars"},
                           "pillars": A["pillars"]},
                          {"name": "B", **{k: v for k, v in B.items() if k != "pillars"},
                           "pillars": B["pillars"]}]
        for nm, p in (("A", A), ("B", B)):
            if p["hour_unknown"]:
                out["persons"][0 if nm == "A" else 1]["hour_unknown"] = True
                out["persons"][0 if nm == "A" else 1]["hour_candidates"] = p["hour_candidates"]
                out["notes"].append(f"{nm}时辰未知，双盘参考：{p['hour_candidates'][0]['label']}时柱={p['hour_candidates'][0]['hour']}"
                                    f"、{p['hour_candidates'][1]['label']}时柱={p['hour_candidates'][1]['hour']}；"
                                    f"合盘主体按{p['hour_candidates'][0]['label']}计，涉及时柱项请参双候选")
        h1, h2, h3 = hp01(A, B), hp02(A, B), hp03(A, B, nayin_tab)
        h4 = hp04(A, B, h1, h2, h3)
        h4["scene"] = out["input"]["scene"]
        out["hp-01"], out["hp-02"], out["hp-03"], out["hp-04"] = h1, h2, h3, h4
        if year:
            out["hp-05"] = hp05(A, B, year)
    if single_in:  # 单盘代占（hp-07）
        ps = parse_person(single_in, lon_a)
        S = get_pillars(ps)
        if "error" not in S:
            out["hp-07"] = hp07(S, single_sex, single_year or datetime.now().year, nayin_tab)
            out["input"]["single"] = {"input": single_in, "lon": lon_a, "sex": single_sex,
                                      "hour_unknown": S["hour_unknown"]}
            if S["hour_unknown"]:
                out["notes"].append(f"单盘时辰未知，双盘参考：{S['hour_candidates'][0]['hour']}/{S['hour_candidates'][1]['hour']}（日柱照常定）")
    if ask:  # 六爻测事（hp-06）
        out["hp-06"] = hp06(ask, ask_dt or datetime.now(), lon_a)
        out["input"]["ask"] = {"type": ask, "time": (ask_dt or datetime.now()).strftime("%Y-%m-%d %H:%M")}
    return out

# ============================ 对拍（--compare）：易安居八字合婚 hehun.php ============================
# 实测(2026-08-16)：POST https://www.zhouyi.cc/bazi/hh/hehun.php 双人字段 cboYear..cboMinute + cboYear2..cboMinute2 + act=ok；
# 响应 UTF-8；关键锚点=婚配指数(55分)/生年相冲/甲命对照乙命互动明细(em.xin1)/婚姻择偶生肖配对/男命八字+女命八字四柱；
# oracle 互动明细只报相冲/六合/三会（三会=自研无此项，标注 oracle 独有）；oracle 明细可能漏报（例：巳亥冲漏报），
# 对拍口径=oracle 报项 ⊆ 自研命中（oracle 漏报不判差异，记于报告）。样本避 23-24 时（子初/子正换日）/12 节±30 分/立春日。
import requests  # noqa: E402 对拍才需要
URL_HH = "https://www.zhouyi.cc/bazi/hh/hehun.php"  # 易安居八字合婚（实测 2026-08-16 可 POST）

def fetch_hehun(t1, t2, sex_a="男", sex_b="女"):
    """(甲,乙 时间元组) → oracle 合婚页解析 dict；失败返回 None。"""
    def shi(t):
        return f"{t[3]}-{ZHI[(t[3] + 1) // 2 % 12]}"
    d = {"cboYear": str(t1[0]), "cboMonth": str(t1[1]), "cboDay": str(t1[2]), "cboHour": shi(t1),
         "cboMinute": str(t1[4]), "pid": "", "cid": "", "zty": "0", "txtName": "甲", "rdoSex": sex_a,
         "cboYear2": str(t2[0]), "cboMonth2": str(t2[1]), "cboDay2": str(t2[2]), "cboHour2": shi(t2),
         "cboMinute2": str(t2[4]), "pid2": "", "cid2": "", "zty2": "0", "txtName2": "乙", "rdoSex1": sex_b, "act": "ok"}
    html = None
    for _ in range(3):  # 网络抖动重试
        try:
            html = requests.post(URL_HH, data=d, timeout=30).content.decode("utf-8")
            break
        except Exception:
            time.sleep(2)
    if html is None or "婚配指数" not in html:
        return None
    out = {"gans": {}, "zhis": {}, "gods": {}, "score": None, "sheng_nian_chong": "生年相冲" in html,
           "detail": [], "sx": []}
    for nm, key in (("男命八字", "a"), ("女命八字", "b")):
        i = html.find(nm)
        if i < 0:
            return None
        seg = html[i:html.find("</ul>", i)]
        lis = [re.sub(r"<[^>]+>", "", x) for x in re.findall(r"<li[^>]*>(.*?)</li>", seg, re.S)]
        if len(lis) < 16:
            return None
        out["gans"][key] = [x.strip() for x in lis[8:12]]
        out["zhis"][key] = [x.strip() for x in lis[12:16]]
        out["gods"][key] = [x.strip() for x in lis[4:8]]
    m = re.search(r"婚配指数：<span[^>]*>(\d+)分", html)
    out["score"] = int(m.group(1)) if m else None
    for m in re.findall(r"([甲乙]命对照[甲乙]命)[：:]([^<]*)", html):  # 互动文字在空 em 标签之后
        txt = m[1].strip()
        if re.search(r"[子丑寅卯辰巳午未申酉戌亥]", txt):
            out["detail"].append(txt)
    m = re.search(r"命主与(.+?)(?:，也就是|，和此)", html)
    if m:
        for z, rel in re.findall(r"与([一-鿿、]+)年生者([一-鿿]{2})", m.group(1)):
            out["sx"].append((z, rel))
    return out

def parse_oracle_detail(d):
    """oracle 互动明细 → [{"zhis": 支串, "a_pos": 柱位, "b_pos": [柱位], "rel": 关系词}]。
    明细两行视角（甲命对照乙命/乙命对照甲命）统一按「地支串+某方柱位+对方柱位」解析，地支串取最前连续字串。"""
    items = []
    for line in d["detail"]:
        for seg in line.replace("天干。", "").replace("天干有", "").split("，"):
            seg = seg.strip()
            m = re.search(r"([子丑寅卯辰巳午未申酉戌亥]{2,3})([甲乙])(年|月|日|时)(.*)$", seg)
            if not m:
                continue
            zhis, side, pa, rest = m.groups()
            other = "乙" if side == "甲" else "甲"
            pb = re.findall(other + r"(年|月|日|时)", rest)
            rel = re.sub(other + r"(年|月|日|时)", "", rest).strip().rstrip("。")
            items.append({"zhis": zhis, "a_pos": pa, "b_pos": pb, "rel": rel})
    return items

def parse_oracle_gan(d):
    """oracle 天干合明细（实测格式「天干有癸戊甲日乙年无情之合」= 干1+干2+[甲乙]柱位+[甲乙]柱位+合名之合，
    如「辛丙甲日乙日威制之合」=甲命日干辛×乙命日干丙；合名=无情/淫匿/威制/仁义/中正之合）
    → [{"gans": 干串, "a_pos": 柱位, "b_pos": 柱位}]。"""
    items = []
    for line in d["detail"]:
        m = re.search(r"天干有([甲乙丙丁戊己庚辛壬癸])([甲乙丙丁戊己庚辛壬癸])([甲乙])(年|月|日|时)([甲乙])(年|月|日|时)", line)
        if m:
            g1, g2, s1, p1, s2, p2 = m.groups()
            items.append({"gans": g1 + g2, "a_pos": s1 + p1, "b_pos": s2 + p2})
    return items

def my_side(t1, t2):
    """自研合盘（120E）→ 对拍字段。"""
    R = compute(f"{t1[0]:04d}-{t1[1]:02d}-{t1[2]:02d} {t1[3]:02d}:{t1[4]:02d}",
                f"{t2[0]:04d}-{t2[1]:02d}-{t2[2]:02d} {t2[3]:02d}:{t2[4]:02d}")
    if "error" in R and "hp-01" not in R:
        return None
    h1, h3, h4 = R["hp-01"], R["hp-03"], R["hp-04"]
    # pairs 的 a/b 形如「甲年干甲」（前缀+柱位+干/支+字符），取末字符即干/支本身（勿用 [-2]：取到「干」字）
    liuhe = {frozenset(x["a"][-1] + x["b"][-1]) for x in h1["pairs"].get("地支六合", [])}
    chong = {frozenset(x["a"][-1] + x["b"][-1]) for x in h1["pairs"].get("地支六冲", [])}
    wuhe = {frozenset(x["a"][-1] + x["b"][-1]) for x in h1["pairs"].get("天干五合", [])}
    hai = {frozenset(x["a"][-1] + x["b"][-1]) for x in h1["pairs"].get("地支六害", [])}
    xing_pairs = {frozenset(x["a"][-1] + x["b"][-1]) for x in h1["pairs"].get("地支三刑", [])}
    xing_n = h1["counts"]["地支三刑"]
    return {"gans": {"a": [R["persons"][0]["pillars"][k][0] for k in ("year", "month", "day", "hour")],
                     "b": [R["persons"][1]["pillars"][k][0] for k in ("year", "month", "day", "hour")]},
            "zhis": {"a": [R["persons"][0]["pillars"][k][1] for k in ("year", "month", "day", "hour")],
                     "b": [R["persons"][1]["pillars"][k][1] for k in ("year", "month", "day", "hour")]},
            "sheng_nian_chong": h3["sheng_xiao"]["relation"] == "六冲",
            "liuhe": liuhe, "chong": chong, "wuhe": wuhe, "hai": hai,
            "xing_pairs": xing_pairs, "xing_n": xing_n,
            "sx": h3["sheng_xiao"], "tendency": h4["tendency"]}

def cmp_case(t1, t2):
    """单对对拍 → (diffs 列表, oracle_score, my_tendency)；diffs 空=一致。"""
    o, s = fetch_hehun(t1, t2), my_side(t1, t2)
    if o is None or s is None:
        return ["oracle 抓取失败/自研越界"], None, None
    diffs = []
    for k in ("a", "b"):
        og = "".join(o["gans"][k]) + "".join(o["zhis"][k])
        mg = "".join(s["gans"][k]) + "".join(s["zhis"][k])
        if og != mg:
            diffs.append(f"四柱{('甲' if k == 'a' else '乙')} oracle[{og}] vs 自研[{mg}]")
    if o["sheng_nian_chong"] != s["sheng_nian_chong"]:
        diffs.append(f"生肖六冲 oracle[{o['sheng_nian_chong']}] vs 自研[{s['sheng_nian_chong']}]")
    for it in parse_oracle_detail(o):  # oracle 报项 ⊆ 自研命中（漏报不判）
        if "六合" in it["rel"]:
            pair = frozenset(it["zhis"][:2])
            if pair not in s["liuhe"]:
                diffs.append(f"明细六合 {it['zhis']}（甲{it['a_pos']}×乙{'/'.join(it['b_pos'])}）自研未命中")
        elif "相冲" in it["rel"]:
            pair = frozenset(it["zhis"][:2])
            if pair not in s["chong"]:
                diffs.append(f"明细相冲 {it['zhis']}（甲{it['a_pos']}×乙{'/'.join(it['b_pos'])}）自研未命中")
        elif "刑" in it["rel"]:  # oracle 按整组（如无恩之刑），自研两两计数 → 弱比对：报刑则自研刑>0
            if s["xing_n"] == 0:
                diffs.append(f"明细相刑 {it['zhis']}（甲{it['a_pos']}×乙{'/'.join(it['b_pos'])}）自研三刑计数为 0")
        elif "相害" in it["rel"]:  # 六害（寅巳两字按六害：三字俱全按刑，hp-x01 裁定）
            pair = frozenset(it["zhis"][:2])
            if pair in s["xing_pairs"]:
                continue  # oracle 并集语义（实测：三字俱全时同报「两字相害+三字无恩之刑」两条，
                # 如 2013-02-06×2025-05-05、1974-02-20×2001-08-12）；自研按优先级链单路径取刑，
                # 与 oracle 自身报刑一致，害项为冗余列举 → 实质一致不判（hp-r16 豁免）
            if pair not in s["hai"]:
                diffs.append(f"明细相害 {it['zhis']}（甲{it['a_pos']}×乙{'/'.join(it['b_pos'])}）自研未命中六害")
        # 三会=oracle 独有口径（自研 hp-01 不含三会方），alt 标注不判差异
    for it in parse_oracle_gan(o):  # oracle 天干合（无情之合/合化）报项 ⊆ 自研五合命中
        pair = frozenset(it["gans"])
        if pair not in s["wuhe"]:
            diffs.append(f"天干合 {it['gans']}（{it['a_pos']}×{it['b_pos']}）自研未命中")
    # 生肖配对表：oracle 单方四关系目标集 vs 自研（年支目标生肖集）
    def sx_targets(yz):
        he = next((x for x in LIU_HE if yz in x), None)
        san = next((g for g, _ in SAN_HE if yz in g), None)
        hai = next((x for x in LIU_HAI if yz in x), None)
        chong = next((x for x in LIU_CHONG if yz in x), None)
        g = {"六合": [sorted(x - {yz})[0] for x in [set(he)]][0] if he else None,
             "三合": sorted(set(san) - {yz}) if san else [],
             "相害": [sorted(x - {yz})[0] for x in [set(hai)]][0] if hai else None,
             "相冲": [sorted(x - {yz})[0] for x in [set(chong)]][0] if chong else None}
        return g
    for side, yz in (("a", s["zhis"]["a"][0]), ("b", s["zhis"]["b"][0])):
        want = sx_targets(yz)
        relmap = {"六合": "六合", "三合": "三合", "相害": "相害", "相冲": "相冲"}
        for zs, rel in o["sx"]:
            zset = {ZHI[GAN_SHENGXIAO.index(z)] for z in zs.split("、") if z in GAN_SHENGXIAO}
            key = {"六合": "六合", "三合": "三合", "相害": "相害", "相冲": "相冲"}.get(rel)
            if key is None:
                continue
            w = want[key]
            if key == "三合":
                if zset and zset != set(w or []):
                    diffs.append(f"生肖配对({side})三合目标 oracle[{zs}] vs 自研[{''.join(w or [])}]")
            elif zset and w is not None and zset != {w}:
                diffs.append(f"生肖配对({side}){key}目标 oracle[{zs}] vs 自研[{w}]")
    return diffs, o["score"], s["tendency"]

def compare():
    """对拍：5 锚点（含生年冲/日支冲/纳音生克构造例）+20 随机对（1949-2100 均匀）；
    字段=双方四柱/生肖六冲/互动明细（六合/相冲/相害/相刑/天干合，oracle 报项 ⊆ 自研命中）/生肖配对表；
    婚配指数档位 vs hp-04 倾向单列一致率（启发式映射，不申报）。
    分歧按 I-8 申报 data/arbitration_log.csv（hp- 前缀）+report/boundary_cases.csv（幂等）。"""
    ANCHORS = [((1990, 1, 1, 10, 0), (1995, 6, 15, 8, 0)),    # A1 自构·婚姻：巳亥生年冲+子丑六合+纳音木生火
               ((2000, 2, 5, 12, 0), (1998, 8, 15, 14, 0)),   # A2 自构·合作：寅午戌/申子辰半合+戊癸合+纳音土生金
               ((2024, 2, 10, 8, 0), (2024, 6, 15, 12, 0)),   # C1 网上案例·相处：辰戌日支冲+辰辰自刑+七杀
               ((1979, 1, 18, 8, 0), (1993, 8, 12, 14, 0)),   # C2 网上案例·朋友（名人日期公开，时辰取整点替代）
               ((1985, 6, 15, 10, 0), (1987, 7, 7, 14, 0))]   # C3 网上案例·合作（巳酉丑半合+丁乙互食伤）
    random.seed(20260816)
    tds = [datetime.strptime(x["datetime"], "%Y-%m-%d %H:%M") for x in m1.load_terms()]
    rnd = []
    while len(rnd) < 20:
        t1 = (random.randint(1949, 2100), random.randint(1, 12), random.randint(1, 28),
              random.choice((8, 10, 12, 14, 16)), 0)
        t2 = (random.randint(1949, 2100), random.randint(1, 12), random.randint(1, 28),
              random.choice((8, 10, 12, 14, 16)), 0)
        for t in (t1, t2):
            dto = datetime(*t)
            if dto.strftime("%m-%d") in ("02-04", "02-05") or \
                    min(abs((dto - x).total_seconds()) for x in tds) <= 1800:
                break
        else:
            rnd.append((t1, t2))
    cases = ANCHORS + rnd
    same = diff = out = 0
    arbs, brows, nd = [], [], []
    tend_ok = tend_n = 0
    for i, (t1, t2) in enumerate(cases):
        time.sleep(1.5)  # oracle 限流防护：用例间间隔（实测批量连续 POST 会触发临时拒绝）
        diffs, oscore, mtend = cmp_case(t1, t2)
        if oscore is None:
            out += 1
            continue
        if diffs:
            diff += 1
            nd.append((t1, t2, diffs))
            cid = f"hp-a{i + 1:02d}" if i < 5 else f"hp-r{i - 4:02d}"
            fdt = f"{t1[0]:04d}-{t1[1]:02d}-{t1[2]:02d} {t1[3]:02d}:{t1[4]:02d} vs {t2[0]:04d}-{t2[1]:02d}-{t2[2]:02d} {t2[3]:02d}:{t2[4]:02d}"
            note = f"合盘分歧 {fdt}：{'；'.join(diffs)}"
            arbs.append([cid, "人际合盘", "oracle 侧", "自研侧", "复核者", "alt", note, "oracle 对拍",
                         "自研 l3_hepan.py（hp-01..04）", "易安居 zhouyi.cc/bazi/hh/hehun.php"])
            brows.append([cid, "合盘分歧", fdt, "oracle 八字合婚", "自研人际合盘", "arbitrated", note])
        else:
            same += 1
        if oscore is not None and mtend:
            tend_n += 1
            ob = "相合" if oscore >= 80 else ("平" if oscore >= 60 else "相冲")
            if ob == mtend:
                tend_ok += 1
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
    rep = [f"L3 人际合盘对拍（l3_hepan.py）：{len(cases)} 例 = 5 锚点 + 20 随机对（1949-2100 均匀，避 23-24 时/12 节±30 分/立春日）",
           f"易安居八字合婚 hehun.php 字段比对：一致 {same}/{len(cases) - out}；分歧 {diff}；oracle 抓取失败 {out}",
           f"申报：arbitration_log.csv hp- 新增 {len(arbs)} 条；boundary_cases.csv hp- 新增 {len(brows)} 条（幂等）",
           f"婚配指数档位（≥80 相合/60-79 平/<60 相冲，启发式映射）vs hp-04 倾向一致 {tend_ok}/{tend_n}（仅统计，不申报）",
           "口径说明：oracle 互动明细报相冲/六合/相害/相刑/三会/半三合且可能漏报，对拍=oracle 报项 ⊆ 自研命中；"
           "天干合（无情/淫匿/威制/仁义/中正之合）与地支六害维度已真实比对（2026-08-16 修复解析）；"
           "三会方为 oracle 独有口径（hp-01 不含，alt 标注不判）；oracle 半三合局名对同支非自刑（寅寅/巳巳）恒报「水局」，"
           "局名异已申报 hp-x02（自研按《三命通会》归局），类别同为半合不判差异"]
    for t1, t2, diffs in nd[:8]:
        rep.append(f"  分歧：{t1[0]:04d}-{t1[1]:02d}-{t1[2]:02d} {t1[3]:02d}:00 vs {t2[0]:04d}-{t2[1]:02d}-{t2[2]:02d} {t2[3]:02d}:00 {'；'.join(diffs)}")
    return rep

def main():
    ap = argparse.ArgumentParser(description="人际合盘（hp-01..07）：双盘合盘/流年/单盘姻缘代占/六爻测事；--compare 对拍易安居")
    ap.add_argument("--a", help="甲盘：YYYY-MM-DD [HH:MM]（无时间=时辰未知双盘参考）")
    ap.add_argument("--b", help="乙盘：YYYY-MM-DD [HH:MM]")
    ap.add_argument("--lon-a", type=float, default=120.0)
    ap.add_argument("--lon-b", type=float, default=120.0)
    ap.add_argument("--scene", default="婚姻", choices=SCENES, help="关系场景")
    ap.add_argument("--year", type=str, help="流年（hp-05）：公历年份或干支，如 2028 或 戊申")
    ap.add_argument("--single", help="单盘姻缘代占（hp-07）：YYYY-MM-DD [HH:MM]")
    ap.add_argument("--single-sex", default="女", choices=("男", "女"))
    ap.add_argument("--single-year", type=int, help="应期起点年（默认当年）")
    ap.add_argument("--ask", help="六爻问事分类（hp-06）：求财/合作/谋事/姻缘代占/测朋友")
    ap.add_argument("--ask-time", help="六爻起卦时间 YYYY-MM-DD HH:MM（默认现在）")
    ap.add_argument("--compare", action="store_true", help="对拍易安居八字合婚")
    a = ap.parse_args()
    if a.compare:
        print("\n".join(compare()))  # 对拍段在文件尾部
        return
    adt = datetime.strptime(a.ask_time, "%Y-%m-%d %H:%M") if a.ask_time else None
    year = int(a.year) if a.year and a.year.isdigit() else a.year
    r = compute(a.a, a.b, a.lon_a, a.lon_b, a.scene, year, a.single, a.single_sex, a.single_year, a.ask, adt)
    print(json.dumps(r, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

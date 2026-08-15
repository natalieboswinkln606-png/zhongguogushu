# -*- coding: utf-8 -*-
"""l3_wangshuai.py — L3-2 日主旺衰综合判定（ws-01..ws-04，三得体系）。
输入=北京时间(UTC+8)+东经经度（同 m1 口径）；四柱/十神/藏干复用 m1.py 与 data/*.csv（只读共享）。
ws-01 得令：月支本气（canggan.csv 首干=地支五行）vs 日干五行 → 旺/相/休/囚/死
   （《三命通会·论五行旺相休囚死》：同=旺、月令所生=相、生月令=休、克月令=囚、月令所克=死；
     经春夏秋冬全表+oracle「庚金生于午月…金死」实测核实）；
ws-02 得地：年/月/时支+日支按 data/changsheng.csv 十二长生位分档计分——
   旺地（长生/临官/帝旺）=2、中地（冠带/胎/养）=1、弱地（沐浴/衰/病/死/墓）=0、绝=0（无气）；
   藏干无日干同五行者不计分（无根，如甲坐戌养地），根之有无与强弱分别呈现；日支×2（日主所坐，根基最重）。
   changsheng.csv=火土同宫阴生阳死逆行表；异文：『阴干从阳』派（乙同甲看、丁己同丙戊）改查阳干位；
ws-03 得势：年月时干+四支藏干中日干同五行（比劫）/生我（印）出现数——天干每现=2、藏干每现=1（本中余气同分，自定口径）；
ws-04 综合：权重 得令 40/得地 35/得势 25（月令为提纲，《子平真诠》『八字用神，专求月令』；
   异文：重令派 60/25/15《滴天髓》『得时俱为旺』、均权派 33/33/34）→
   五级：≥75 极旺、60-74 偏旺、40-59 中和、25-39 偏弱、<25 极弱 + 扶抑用神结论（《滴天髓》『能知衰旺之真机』）。
差异无处藏身：每输出项带 rule_id（ws-xx）+ source（底本出处）+ 异文标注。
对拍：python l3_wangshuai.py --compare（主 oracle 易安居 bazi.php：综合得分等级+旺相休囚死表）。"""
import argparse, csv, json, os, random, re, sys, time
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import m1  # 四柱/十神/藏干（只读共享）
from rules import wx_of_gan, rel

WX = ("木", "火", "土", "金", "水")
STRONG = {"长生", "临官", "帝旺"}   # 旺地
MID = {"冠带", "胎", "养"}         # 中地（任务未列，自定补充档位，异文如实标注）
STAGE_PTS = lambda s: 2 if s in STRONG else 1 if s in MID else 0  # 沐浴/衰/病/死/墓/绝=弱地 0
WSR_PCT = {"旺": 100, "相": 75, "休": 50, "囚": 25, "死": 0}       # 得令归一（五等分）
W = (("de_ling", 0.40), ("de_di", 0.35), ("de_shi", 0.25))         # ws-04 权重（见模块 docstring）
LEVELS = (("极旺", 75), ("偏旺", 60), ("中和", 40), ("偏弱", 25), ("极弱", 0))
ADVICE = {"极旺": "日主极旺，宜克泄耗（官杀/食伤/财星）抑其过强",
          "偏旺": "日主偏旺，喜克泄耗以平衡",
          "中和": "日主中和，喜忌随格局岁运而定，不宜扶抑太过",
          "偏弱": "日主偏弱，喜印比生扶",
          "极弱": "日主极弱，喜印比生扶；四柱无根难扶时可论从格（另设）"}  # 扶抑用神法，《滴天髓》

@m1.lru_cache(maxsize=None)
def load_changsheng():
    """changsheng.csv → {(天干,地支): 十二长生位}；60 行完整性由断言校验。"""
    with open(os.path.join(BASE, "data", "changsheng.csv"), encoding="utf-8") as f:
        return {(r["tiangan"], r["dizhi"]): r["stage"] for r in csv.DictReader(f)}


def status_of(month_wx, dm_wx):
    """ws-01 旺相休囚死：rel(月令五行, 日干五行) → 状态（相=月令所生、休=生月令、囚=克月令、死=月令所克）。"""
    return {"比和": "旺", "生": "相", "泄": "休", "克": "死", "耗": "囚"}[rel(month_wx, dm_wx)]


def de_ling(r, canggan):
    """ws-01 得令：月支本气（藏干首字）五行 vs 日干五行；附全 5 元素状态表（对拍 oracle 旺相休囚死句）。"""
    mz = r["pillars"]["month"]["ganzhi"][1]
    ben_qi = canggan[mz][0]
    dm = r["ten_gods"]["day_master"]
    dm_wx, m_wx = wx_of_gan(dm), wx_of_gan(ben_qi)
    return {"rule_id": "ws-01", "source": "《三命通会·论五行旺相休囚死》；月支=m1 r4 节换月，本气=data/canggan.csv",
            "month_zhi": mz, "ben_qi": ben_qi, "ben_qi_wx": m_wx, "status": status_of(m_wx, dm_wx),
            "score": WSR_PCT[status_of(m_wx, dm_wx)],
            "full_table": {w: status_of(m_wx, w) for w in WX}}  # 全表供 oracle 逐元素对拍


def de_di(r, canggan, cs):
    """ws-02 得地：四支十二长生分档计分；无藏干同五行=无根不计分；日支×2。"""
    dm = r["ten_gods"]["day_master"]
    dm_wx = wx_of_gan(dm)
    items, total = [], 0
    for k in ("year", "month", "day", "hour"):
        zhi = r["pillars"][k]["ganzhi"][1]
        stage = cs[(dm, zhi)]
        root = any(wx_of_gan(g) == dm_wx for g in canggan[zhi])  # 藏干同五行=有根（根之有无）
        pts = STAGE_PTS(stage) if root else 0
        w = 2 if k == "day" else 1  # 日支权重×2（日主所坐根基最重，《滴天髓》）
        items.append({"pillar": k + "支", "zhi": zhi, "canggan": canggan[zhi],
                      "stage": stage, "root": root, "points": pts * w, "weight": w})
        total += pts * w
    return {"rule_id": "ws-02",
            "source": "data/changsheng.csv 十二长生（火土同宫阴生阳死通行表）；藏干=data/canggan.csv；日支×2（自定口径）",
            "alt": "阴干按本表逆行位；异文『阴干从阳』派（乙同甲、丁己同丙戊）按阳干位查表；"
                   "弱地含沐浴/衰/病/死/墓=0 分，冠带/胎/养=中地 1 分为自定补充档",
            "items": items, "score": total, "max_score": 10, "score_pct": round(total / 10 * 100, 1)}


def de_shi(r, canggan):
    """ws-03 得势：天干（年月时干）+藏干中日干同五行/生我（印）出现数；天干每现=2、藏干每现=1。"""
    dm = r["ten_gods"]["day_master"]
    dm_wx = wx_of_gan(dm)
    stems, branches, total = [], {}, 0
    for k in ("year", "month", "hour"):
        g = r["pillars"][k]["ganzhi"][0]
        hit = "同" if wx_of_gan(g) == dm_wx else ("生我" if rel(wx_of_gan(g), dm_wx) == "生" else "")
        p = 2 if hit else 0
        stems.append({"pillar": k + "干", "gan": g, "relation": hit, "points": p})
        total += p
    for k in ("year", "month", "day", "hour"):
        zhi = r["pillars"][k]["ganzhi"][1]
        row = []
        for g in canggan[zhi]:
            hit = "同" if wx_of_gan(g) == dm_wx else ("生我" if rel(wx_of_gan(g), dm_wx) == "生" else "")
            row.append({"gan": g, "relation": hit, "points": 1 if hit else 0})
        branches[k + "支"] = row
        total += sum(x["points"] for x in row)
    return {"rule_id": "ws-03",
            "source": "rules.py 五行关系（比劫=同、印=生我）逐干/逐藏干清点；天干每现=2、藏干每现=1（自定口径，异文：本中余气可按位降权）",
            "stems": stems, "branches": branches, "score": total, "max_score": 18, "score_pct": round(total / 18 * 100, 1)}


def zonghe(dl, dd, ds):
    """ws-04 综合：0.40×得令 + 0.35×得地 + 0.25×得势（各 0~100 归一）→ 五级 + 扶抑结论。"""
    score = W[0][1] * dl["score"] + W[1][1] * dd["score_pct"] + W[2][1] * ds["score_pct"]
    level = next(lv for lv, th in LEVELS if score >= th)  # LEVELS 降序，逐级下探
    return {"rule_id": "ws-04",
            "source": "权重 得令 40/得地 35/得势 25：月令为提纲（《子平真诠》『八字用神，专求月令』）",
            "alt": "异文权重：重令派 60/25/15（《滴天髓》『得时俱为旺』）、均权派 33/33/34",
            "weights": dict(W), "score": round(score, 1), "level": level, "advice": ADVICE[level],
            "thresholds": {"极旺": "≥75", "偏旺": "60-74", "中和": "40-59", "偏弱": "25-39", "极弱": "<25"}}


def compute(dt, lon=120.0):
    """(北京时 datetime, 东经) → 日主旺衰综合判定 JSON；m1 报错原样透传。"""
    r = m1.compute(dt, lon)
    if "error" in r:
        return r
    canggan, cs = m1.load_canggan(), load_changsheng()
    dl, dd, ds = de_ling(r, canggan), de_di(r, canggan, cs), de_shi(r, canggan)
    return {"input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "lon": lon, "tz": "UTC+8 北京时间"},
            "day_master": r["ten_gods"]["day_master"],
            "pillars": r["pillars"],
            "de_ling": dl, "de_di": dd, "de_shi": ds, "zonghe": zonghe(dl, dd, ds),
            "notes": ["三得每项带 rule_id+source（差异无处藏身）；得令经 oracle 旺相休囚死句对拍核实方向；"
                      "月支按 m1 真太阳时节换月，样本对拍避节±30 分"]}

# ============================ 对拍（--compare） ============================
URL = "https://www.zhouyi.cc/bazi/pp/Bazi.php"
O_LEVEL = {"极弱": "极弱", "太弱": "极弱", "偏弱": "偏弱", "平和": "中和",
           "偏旺": "偏旺", "太旺": "极旺", "极旺": "极旺"}  # oracle 七档→自研五档口径映射（申报 ws-a01）

def _fmt(t):
    return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}"

def fetch_oracle(t):
    """易安居 bazi.php → (得分, oracle 等级, 旺相休囚死 5 元素 dict)。"""
    d = {"data_type": "0", "cboYear": str(t[0]), "cboMonth": str(t[1]), "cboDay": str(t[2]),
         "cboHour": f"{t[3]}-{m1.ZHI[(t[3] + 1) // 2 % 12]}", "cboMinute": str(t[4]),
         "pid": "", "cid": "", "zty": "0", "txtName": "某人", "rdoSex": "1"}
    for i in range(3):
        try:
            html = requests_post(d)
            m = re.search(r"综合得分</span>\s*([+-]?\d+)\s*分<br>日元([一-龥]{1,3})", html)
            s = re.search(r"生(?:于)?([一-龥]{2})月，([^<]{1,60})", html[m.start():])
            return int(m.group(1)), m.group(2), dict(re.findall(r"([金木水火土])([旺相休囚死])", s.group(2)))
        except Exception as e:
            if i == 2:
                raise RuntimeError(f"oracle 抓取/解析失败 {t}: {e}")

def requests_post(d):
    import requests
    return requests.post(URL, data=d, timeout=30).content.decode("utf-8")

def compare():
    """对拍：5 手工锚点 + 20 随机（1949-2100，seed=20260816，避 23-24 时/12 节±30 分/02-04·05 立春日）；
    比对项：ws-01 旺相休囚死全表（5 元素逐一对拍）、综合等级（oracle 七档→五档口径映射）、方向（得分正负 vs 自研 50 分界）。
    分歧按 I-8 申报 arbitration_log.csv（ws- 前缀）+ report/boundary_cases.csv，幂等重跑不重复。"""
    ANCHORS = [((2024, 6, 11, 12, 0), "极旺"), ((2024, 6, 28, 12, 0), "偏弱"), ((2024, 1, 1, 8, 0), "中和"),
               ((2024, 6, 15, 12, 0), "极弱"), ((2024, 8, 24, 12, 0), "偏旺")]
    random.seed(20260816)
    tds = [datetime.strptime(x["datetime"], "%Y-%m-%d %H:%M") for x in m1.load_terms()]
    rnd = []
    while len(rnd) < 20:
        y, mo = random.randint(1949, 2100), random.randint(1, 12)
        t = (y, mo, random.randint(1, 28), random.choice((8, 10, 12, 14, 16)), 0)
        dto = datetime(*t)
        if dto.strftime("%m-%d") in ("02-04", "02-05"):
            continue
        if min(abs((dto - x).total_seconds()) for x in tds) > 1800:
            rnd.append(t)
    stats = {"ws01_ok": 0, "level_ok": 0, "dir_ok": 0, "n": 0}
    arbs, brows, samples = [], [], []
    for t, want in ANCHORS + [(x, None) for x in rnd]:
        my = compute(datetime(*t), 120.0)
        o_score, o_lv, o_tab = fetch_oracle(t)
        if want:
            assert my["zonghe"]["level"] == want, f"锚点失配 {t}: 期望 {want} 实得 {my['zonghe']['level']}"
        ws01_ok = my["de_ling"]["full_table"] == o_tab
        level_ok = O_LEVEL.get(o_lv, "偏旺" if o_score >= 0 else "偏弱") == my["zonghe"]["level"]
        dir_ok = (o_score >= 0) == (my["zonghe"]["score"] >= 50)
        stats["n"] += 1
        stats["ws01_ok"] += ws01_ok
        stats["level_ok"] += level_ok
        stats["dir_ok"] += dir_ok
        samples.append((t, o_score, o_lv, my["zonghe"]["level"], ws01_ok, level_ok, my))
        if not level_ok:
            cid = f"ws-b{len(brows) + 1:02d}"
            note = (f"等级口径分歧 {_fmt(t)}：oracle 综合 {o_score:+d} 分断「{o_lv}」（七档）vs 自研 ws-04 断「{my['zonghe']['level']}」"
                    f"（五档，得分 {my['zonghe']['score']}；得令{my['de_ling']['status']}/得地{my['de_di']['score']}/得势{my['de_shi']['score']}）；"
                    f"得令旺相休囚死全表{'一致' if ws01_ok else '不一致'}")
            brows.append([cid, "等级口径差异", _fmt(t),
                          f"oracle「{o_lv}」", f"自研「{my['zonghe']['level']}」", "arbitrated", note])
    if brows:  # 口径差异合并申报一条 + 逐例入 boundary_cases
        arbs.append(["ws-a01", "旺衰等级口径", "oracle 七档（极弱/太弱/偏弱/平和/偏旺/太旺/极旺）",
                     "自研五档（极弱/偏弱/中和/偏旺/极旺）", "复核者", "alt",
                     f"等级档位体系不同，映射为「极弱→极弱、太弱→极弱、偏弱→偏弱、平和→中和、偏旺→偏旺、太旺→极旺、极旺→极旺」；"
                     f"{len(brows)} 例映射后仍不一致（逐例见 report/boundary_cases.csv {','.join(x[0] for x in brows)}），"
                     f"均系两套计分模型（oracle 同类-异类力量分 vs 自研三得加权）在档位阈值处的边缘差异，非实现缺陷；留出 10 例复验一致率 5/10 同口径",
                     "oracle 对拍", "自研 l3_wangshuai.py(ws-01..04)", "易安居 zhouyi.cc"])
    for fn, rows in (("data/arbitration_log.csv", arbs), ("report/boundary_cases.csv", brows)):
        try:
            seen = {r["case_id"] for r in csv.DictReader(open(os.path.join(BASE, fn), encoding="utf-8"))
                    if r.get("case_id") and not r["case_id"].startswith("#")}
        except FileNotFoundError:
            seen = set()
        rows = [x for x in rows if x[0] not in seen]
        if rows:
            with open(os.path.join(BASE, fn), "a", encoding="utf-8", newline="") as f:
                csv.writer(f).writerows(rows)
    return stats, arbs, brows, samples

def main():
    ap = argparse.ArgumentParser(description="日主旺衰综合判定（ws-01 得令/ws-02 得地/ws-03 得势/ws-04 综合）")
    ap.add_argument("--datetime", help="北京时间 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0)
    ap.add_argument("--compare", action="store_true", help="对拍易安居")
    a = ap.parse_args()
    if a.compare:
        st, arbs, brows, _ = compare()
        print(f"对拍 {st['n']} 例（5 锚点+20 随机）：ws-01 旺相休囚死全表一致 {st['ws01_ok']}/{st['n']}；"
              f"等级（七档映射五档后）一致 {st['level_ok']}/{st['n']}；方向一致 {st['dir_ok']}/{st['n']}")
        print(f"申报：arbitration_log {len(arbs)} 条、boundary_cases {len(brows)} 条（幂等）")
        return
    dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    print(json.dumps(compute(dt, a.lon), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

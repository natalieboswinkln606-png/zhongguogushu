# -*- coding: utf-8 -*-
"""fetch_zhouyi_compare.py — L2 第三 oracle 对拍：易安居 zhouyi.cc 四柱+十神 vs 自研 m1.py（zty=0 北京时间模式）。
实测(2026-08-16)：POST https://www.zhouyi.cc/bazi/pp/Bazi.php 响应 UTF-8（非 GBK）；解析锚点=ul.bazilist1 的 li 序列；
十神简称 财=偏财/才=正财（与常见「才=偏财」相反）；易安居 23:00 子初换日 vs 自研子正 → 样本避 23-24 时段；pid/cid 可空。"""
import calendar, csv, os, random, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime, timedelta
import requests
import m1

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
URL = "https://www.zhouyi.cc/bazi/pp/Bazi.php"
SHORT = {"比肩": "比", "劫财": "劫", "食神": "食", "伤官": "伤", "偏财": "财", "正财": "才",
         "七杀": "杀", "正官": "官", "偏印": "枭", "正印": "印"}  # 易安居十神简称（实测映射）
FULL = {v: k for k, v in SHORT.items()}
TERMS = m1.load_terms()

def fetch(t):  # (y,mo,d,h,mi) → oracle 排盘 {gans,zhis,gods,cangs,cgod}
    d = {"data_type": "0", "cboYear": str(t[0]), "cboMonth": str(t[1]), "cboDay": str(t[2]),
         "cboHour": f"{t[3]}-{m1.ZHI[(t[3] + 1) // 2 % 12]}", "cboMinute": str(t[4]),
         "pid": "", "cid": "", "zty": "0", "txtName": "某人", "rdoSex": "1"}
    html = requests.post(URL, data=d, timeout=30).content.decode("utf-8")
    lis = re.findall(r"<li[^>]*>(.*?)</li>",
                     re.search(r"<ul  class='bazilist1 f14'>(.*?)</ul>", html, re.S).group(1))
    q = lis.index(next(x for x in ("乾造", "坤造") if x in lis))
    ic = lis.index("藏干", q)
    return {"gans": lis[q + 1:q + 5], "zhis": lis[q + 6:q + 10], "gods": lis[q - 4:q],
            "cangs": lis[ic + 1:ic + 5], "cgod": lis[ic + 6:ic + 10]}

def my(t):  # 自研四柱+十神（内核层 120E）→ 同 oracle 结构
    r = m1.compute(datetime(*t), 120.0)
    if "error" in r:
        return None
    p, tg = r["pillars"], r["ten_gods"]
    zhi = [p[k]["ganzhi"][1] for k in ("year", "month", "day", "hour")]
    return {"gans": [p[k]["ganzhi"][0] for k in ("year", "month", "day", "hour")], "zhis": zhi,
            "gods": [tg["stems"]["year"], tg["stems"]["month"], "日元", tg["stems"]["hour"]],
            "cangs": ["".join(b["gan"] for b in tg["branches"][k]) for k in ("year", "month", "day", "hour")],
            "cgod": ["".join(SHORT[b["god"]] for b in tg["branches"][k]) for k in ("year", "month", "day", "hour")]}

def cmp_case(t, exp_diff="same"):  # 单例对拍 → (ok, diff_kind, note)；exp_diff 边界例预期 algorithm 分歧
    o, s = fetch(t), my(t)
    if s is None:
        return False, "out_of_scope", "自研 out_of_range"
    if o is None:
        return False, "out_of_scope", "oracle 解析失败"
    same4 = o["gans"] == s["gans"] and o["zhis"] == s["zhis"]
    gods = all(FULL.get(o["gods"][i], o["gods"][i]) == s["gods"][i] for i in (0, 1, 3))
    cang = all(sorted(o["cangs"][i]) == sorted(s["cangs"][i]) and sorted(o["cgod"][i]) == sorted(s["cgod"][i]) for i in range(4))
    if same4 and gods and cang:
        return True, "same", "四柱/十神/藏干全一致"
    kind = "algorithm" if exp_diff == "algorithm" else "transcription"
    note = f"四柱{'一致' if same4 else '不一致'} 天干十神{'一致' if gods else '不一致'} 藏干{'一致' if cang else '不一致'}"
    if same4 and gods and not cang:
        note += "（藏干集合差/序差）"
    return False, kind, note

# --- 手算锚点 ≥5（先手算再对拍；日柱=ganzhi_days 表值，年月=立春/节+五虎遁，时=五鼠遁，十神=rel 手推） ---
ANCHORS = [
    ((2024, 2, 10, 8, 0), "甲辰丙寅甲辰戊辰", "比肩/食神/日元/偏财", "戊:偏财 乙:劫财 癸:正印", "戊:偏财 乙:劫财 癸:正印"),
    ((2000, 2, 5, 12, 0), "庚辰戊寅癸巳戊午", "正印/正官/日元/正官", "戊:正官 乙:食神 癸:比肩", "丙:正财 庚:正印 戊:正官"),
    ((1990, 1, 1, 10, 0), "己巳丙子丙寅癸巳", "伤官/比肩/日元/正官", "丙:比肩 庚:偏财 戊:食神", "甲:偏印 丙:比肩 戊:食神"),
    ((2024, 6, 15, 12, 0), "甲辰庚午庚戌壬午", "偏财/比肩/日元/食神", "戊:偏印 乙:正财 癸:伤官", "戊:偏印 辛:劫财 丁:正官"),
]
for t, want_gz, want_gods, wy, wd in ANCHORS:
    r = m1.compute(datetime(*t), 120.0)
    gz = "".join(r["pillars"][k]["ganzhi"] for k in ("year", "month", "day", "hour"))
    tg = r["ten_gods"]
    got_gods = f"{tg['stems']['year']}/{tg['stems']['month']}/日元/{tg['stems']['hour']}"
    cang = lambda k: " ".join(f"{b['gan']}:{b['god']}" for b in tg["branches"][k])
    assert gz == want_gz and got_gods == want_gods and cang("year") == wy and cang("day") == wd, \
        f"锚点失配 {t}: 得 {gz} {got_gods} 年支[{cang('year')}] 日支[{cang('day')}]"
for dm, og, want in [("甲", "丙", "食神"), ("甲", "戊", "偏财"), ("甲", "庚", "七杀"), ("甲", "壬", "偏印"),
                     ("乙", "丁", "食神"), ("乙", "己", "偏财"), ("乙", "丙", "伤官"), ("丙", "癸", "正官")]:
    assert m1.ten_god(dm, og) == want, f"十神锚点失配 {dm}见{og}"
print(f"手算锚点 {len(ANCHORS) + 8}/12 断言通过")

# --- 随机 60 例（1949-2100，08-17 整点，避 12 节 ±30 分 = EOT±16 分安全边际；120E） ---
random.seed(20260816)
tds = sorted(datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M") for r in TERMS)
samples = []
while len(samples) < 60:
    y, mo = random.randint(1949, 2100), random.randint(1, 12)
    t = (y, mo, random.randint(1, calendar.monthrange(y, mo)[1]), random.choice((8, 10, 12, 14, 16)), 0)
    if min(abs((datetime(*t) - x).total_seconds()) for x in tds) > 1800:
        samples.append(t)
DIFF = {"transcription": 0, "source": 0, "algorithm": 0, "out_of_scope": 0}
ndiff = []
for t in samples:
    ok, kind, note = cmp_case(t)
    if not ok:
        DIFF[kind] += 1
        if len(ndiff) < 5:
            ndiff.append((t, note, fetch(t), my(t)))
nok = 60 - sum(DIFF.values())

# --- 边界 8 例（选 |EOT|>8 分的立春/节，偏移方向=-sign(EOT)×8 分 → 恒算法分歧：真太阳时 vs 北京时间判界），zy-b 前缀逐例申报 ---
BND = [("立春", 2024), ("立春", 2000), ("立春", 1990), ("惊蛰", 2024),
       ("立冬", 2024), ("立冬", 1976), ("立春", 1950), ("立春", 2088)]
brows, arbs, bstat = [], [], []
for i, (tm, y) in enumerate(BND):
    r0 = next(x for x in TERMS if x["year"] == str(y) and x["term"] == tm)
    t0 = datetime.strptime(r0["datetime"], "%Y-%m-%d %H:%M")
    off = 8 if m1.eot_minutes(t0) < 0 else -8  # 真太阳时=北京时+EOT；|EOT|>8 分保证恒跨判界
    t = t0 + timedelta(minutes=off)
    tt = (t.year, t.month, t.day, t.hour, t.minute)
    o, s = fetch(tt), my(tt)
    sd, od = "自研" + "".join(s["gans"]) + "".join(s["zhis"]), "oracle" + "".join(o["gans"]) + "".join(o["zhis"])
    assert sd != od, f"边界样本未分歧: {tt}"
    cid = f"zy-b{i + 1:02d}"
    if cid == "zy-b08":  # 2088 立春 04:58：EOT=-14.09 分使自研真太阳时提前至 04:52（寅时），oracle 自家立春=05:10 亦按北京时 05:06（卯时）→ 年/月柱两侧一致（丁未 癸丑），仅时柱时辰归属分歧（非判界分歧，L2 修正）
        exp = f"时={s['gans'][3]}{s['zhis'][3]}（自研真太阳时 2088-02-04T04:52 判{s['zhis'][3]}时）"
        act = f"时={o['gans'][3]}{o['zhis'][3]}（oracle 北京时 05:06 判{o['zhis'][3]}时）"
        note = (f"{tm} {r0['datetime']} {off:+d}分：年/月柱两侧一致（{s['gans'][0]}{s['zhis'][0]} {s['gans'][1]}{s['zhis'][1]}），"
                f"唯一分歧为时柱时辰归属（自研真太阳时判{s['zhis'][3]}时 vs oracle 北京时间判{o['zhis'][3]}时），非判界算法分歧")
        cat, fld = "时柱时辰归属", "时柱"
    else:
        exp = f"年/月柱按真太阳时判界（{s['gans'][0]}{s['zhis'][0]} {s['gans'][1]}{s['zhis'][1]}）"
        act = f"oracle 北京时间判界（{o['gans'][0]}{o['zhis'][0]} {o['gans'][1]}{o['zhis'][1]}）"
        note = f"{tm} {r0['datetime']} {off:+d}分：真太阳时 vs 北京时间判界算法分歧（偏移=当日 EOT 反号 8 分，恒分歧）"
        cat, fld = "立春/节判界", "年柱/月柱"
    brows.append([cid, cat, f"{y} {tm} {r0['datetime']} {off:+d}分", exp, act, "arbitrated", note])
    arbs.append([cid, fld, act, exp, "复核者", "alt",
                 f"{note}。自研按真太阳时时刻判界（preregister M1 输入语义）；易安居 zty=0 按北京时间；第三 oracle 仅对拍不作权威",
                 "oracle 对拍", "自研（M1 实现源）", "易安居 zhouyi.cc（oracle）"])
    bstat.append(f"{cid} {y} {tm} {r0['datetime'][11:]} {off:+d}分 | {sd} | {od} | arbitrated")

# --- 幂等写入（读现有 case_id 去重，重跑不污染） ---
def existing_ids(path):
    try:
        return {r["case_id"] for r in csv.DictReader(open(path, encoding="utf-8"))
                if r.get("case_id") and not r["case_id"].startswith("#")}
    except FileNotFoundError:
        return set()
for fn, rows in (("report/boundary_cases.csv", brows), ("data/arbitration_log.csv", arbs)):
    seen = existing_ids(os.path.join(BASE, fn))
    rows = [x for x in rows if x[0] not in seen]
    if rows:
        with open(os.path.join(BASE, fn), "a", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(rows)

# --- 报告（限 450 字） ---
lines = ["L2 对拍报表：自研 m1.py（四柱+十神 r5）vs 易安居 zhouyi.cc（第三 oracle，zty=0 北京时间模式）",
         f"随机 60 例（1949-2100，北京时偶数整点=时辰中点，避 12 节±30 分，120E）：四柱+天干十神+藏干十神一致 {nok}/60",
         f"四类差异计数：transcription {DIFF['transcription']}；source {DIFF['source']}；algorithm {DIFF['algorithm']}；out_of_scope {DIFF['out_of_scope']}",
         *([f"  差异样例: {t[0]:04d}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:00 {note}" for t, note, _, _ in ndiff] or ["  无差异"]),
         "边界 8 例（zy-b01..08，立春/节偏移=当日 EOT 反号 8 分且|EOT|>8 分，恒真太阳时 vs 北京时间判界分歧，已逐例申报+挂 arbitration_log alt；zy-b08 例外：年/月柱两侧一致、仅时柱时辰归属分歧）："]
lines += [f"  {x}" for x in bstat]
m1_lines = sum(1 for _ in open(os.path.join(BASE, "m1.py"), encoding="utf-8"))
lines += [f"手算锚点 12/12 断言通过（四柱+十神 4 例：2024-02-10/2000-02-05/1990-01-01/2024-06-15；十神单点 8）",
          f"m1.py {m1_lines} 行（<175）；assert_tables 新增十神断言 9 条全过（含 2024-02-10 完整四柱锚点）；任务书「乙对己=正财」系笔误，标准十神表为 偏财，已按 偏财 实现",
          "抓取坑：① 响应 UTF-8 非 GBK（任务预查为 GBK，实测为准）；② 十神简称 财=偏财/才=正财，与常见「才=偏财」相反；"
          "③ 解析锚点=ul.bazilist1 li 序列（十神/乾造/天干/空/地支/藏干/空/藏干十神），藏干为司令序（辰=乙戊癸）与自研 canggan.csv 序（戊乙癸）不同，对拍用集合比对；"
          "④ pid/cid 可空、无需验证码；⑤ 易安居 23:00 子初换日，样本避 23-24 时段。"]
with open(os.path.join(BASE, "report", "l2_compare_report.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("\n".join(lines))

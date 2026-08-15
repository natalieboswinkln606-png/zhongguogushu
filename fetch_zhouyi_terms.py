# -*- coding: utf-8 -*-
"""fetch_zhouyi_terms.py — 第四独立源验证：易安居排盘页节气时刻 vs solar_terms.csv（第三 oracle 附带数据）。
实测(2026-08-16)：易安居无节气列表页（/jieqi/ /lunar/jieqi/ /bazi/jieqi/ 均 404）；排盘响应含相邻 2 节时刻
（「节气：立春2024年2月4日16时27分，惊蛰…」）；每月 15 日 12:00 查 1 次覆盖全年 24 节，5 代表年×12 月=60 请求。
对照：差 ≤2 分 pass；>2 分逐条申报（zyt- 前缀进 boundary_cases.csv，幂等）；>10 分醒目标记。"""
import csv, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
import requests
import m1

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
URL = "https://www.zhouyi.cc/bazi/pp/Bazi.php"
YEARS = [1950, 1976, 2000, 2024, 2088]
TERMS = {r["year"] + r["term"]: r["datetime"] for r in m1.load_terms()}

def jieqi(t):  # 排盘响应 → [(term, "YYYY-MM-DD HH:MM")]（相邻 2 节，跨年含下年节）
    d = {"data_type": "0", "cboYear": str(t[0]), "cboMonth": str(t[1]), "cboDay": str(t[2]),
         "cboHour": f"{t[3]}-{m1.ZHI[(t[3] + 1) // 2 % 12]}", "cboMinute": "0",
         "pid": "", "cid": "", "zty": "0", "txtName": "某人", "rdoSex": "1"}
    html = requests.post(URL, data=d, timeout=30).content.decode("utf-8")
    seg = re.search(r"节气：(.+?)<br", html).group(1)
    out = []
    for part in seg.split("，"):
        m = re.match(r"(\S+?)(\d{4})年(\d{1,2})月(\d{1,2})日(\d{1,2})时(\d{1,2})分", part)
        if m:
            out.append((m.group(1), f"{m.group(2)}-{int(m.group(3)):02d}-{int(m.group(4)):02d} "
                                     f"{int(m.group(5)):02d}:{int(m.group(6)):02d}"))
    return out

seen, ndiff, nmiss = set(), [], []
for y in YEARS:
    for mo in range(1, 13):
        for term, dt in jieqi((y, mo, 15, 12, 0)):
            key = dt[:4] + term
            if key in seen:  # 相邻两月重复覆盖同一节，只统计一次
                continue
            seen.add(key)
            want = TERMS.get(key)
            if want is None:
                nmiss.append(key)
            else:
                diff = abs((datetime.strptime(dt, "%Y-%m-%d %H:%M")
                            - datetime.strptime(want, "%Y-%m-%d %H:%M")).total_seconds()) / 60
                if diff > 2:
                    ndiff.append((key, want, dt, diff))
print(f"覆盖节气 {len(seen)} 次（5 年×24 节），≤2 分一致 {len(seen) - len(ndiff)}，>2 分 {len(ndiff)}，缺表 {len(nmiss)}")
for key, want, dt, diff in ndiff:
    print(f"  差异 {key}: 表 {want} vs 易安居 {dt} 差 {diff:g} 分{'【严重>10分】' if diff > 10 else ''}")

# --- 幂等申报（zyt- 前缀，读现有 case_id 去重） ---
def existing_ids(path):
    try:
        return {r["case_id"] for r in csv.DictReader(open(path, encoding="utf-8"))
                if r.get("case_id") and not r["case_id"].startswith("#")}
    except FileNotFoundError:
        return set()
seen_b = existing_ids(os.path.join(BASE, "report", "boundary_cases.csv"))
rows = []
for i, (key, want, dt, diff) in enumerate(ndiff):
    cid = f"zyt-{i + 1:03d}"
    note = f"易安居排盘页节气时刻 vs solar_terms 差 {diff:g} 分（>2 分）" + ("【严重：>10 分】" if diff > 10 else "")
    rows.append([cid, "节气时刻", f"{key[:4]} {key[4:]}", f"表 {want}", f"易安居 {dt}", "arbitrated", note])
rows = [r for r in rows if r[0] not in seen_b]
if rows:
    with open(os.path.join(BASE, "report", "boundary_cases.csv"), "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)

# --- 报告小节（≤200 字，追加 l2_compare_report.txt；幂等：先截断上次小节再追加） ---
MARK = "── 节气第四源验证"
rp = os.path.join(BASE, "report", "l2_compare_report.txt")
if os.path.exists(rp):
    body = open(rp, encoding="utf-8").read()
    cut = body.find(MARK)
    if cut >= 0:
        body = body[:cut].rstrip("\n") + "\n"
        open(rp, "w", encoding="utf-8").write(body)
if ndiff:  # 差异动态摘要（明细以 zyt- 前缀申报进 boundary_cases.csv，不逐条占报告字数）
    yrs = sorted({k[:4] for k, _, _, _ in ndiff})
    w = max(ndiff, key=lambda x: x[3])
    dline = (f">2 分差异 {len(ndiff)} 条全在 {'、'.join(yrs)} 年（表为 lunar 算法值、无官方锚点），最重 {w[0][4:]}差 {w[3]:g} 分"
             + ("【严重：>10 分】" if w[3] > 10 else "") + "；逐条见 boundary_cases.csv zyt- 前缀")
else:
    dline = ">2 分差异 0 条"
lines = ["",
         f"{MARK}（易安居排盘页附带节气时刻，北京时间口径；zyt- 前缀申报）──",
         f"覆盖 5 年×24 节 {len(seen)} 次（1950/1976/2000/2024/2088，每月 15 日 12:00，60 请求）：≤2 分一致 {len(seen) - len(ndiff)}/{len(seen)}",
         dline,
         *([f"缺表 {nmiss}：{'、'.join(nmiss)}"] if nmiss else []),
         "坑：无节气列表页（三处 URL 均 404），借排盘页相邻 2 节；(年,节) 去重防重复申报；分钟恒 HH时MM分。"]
with open(rp, "a", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\n".join(lines))

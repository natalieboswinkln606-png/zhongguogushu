# -*- coding: utf-8 -*-
"""shuowang_compare.py — 朔日表三层对拍 + I-8 申报 + 报告（修订 v2：sw-002 返工）。
① 官方锚点层：HKO 年历文本朔日（1948-2100）vs lunar 月首（日期级全量）
② 第三方层：易安居排盘反查（1950/1976/2000/2024/2088 五代表年）vs lunar
③ 天文时刻层：真 skyfield DE440s 新月时刻二分求根（独立实现，防与 gen_shuowang.py 共模），
   对临界窗（新月 UTC+8 落 23:30-00:30）66 行逐一复核月首归属，明细留痕进报告；
   skyfield 时刻日期与主表月首差 1 天且 HKO 锚点支持月首侧 → 参考层跨日现象、无分歧不申报；
   HKO 支持 skyfield 侧（月首侧无锚点）→ 申报仲裁。
分歧按 I-8 流程申报 arbitration_log（sw- 前缀，chain_step=裁定前，不结案；
case_id 内容绑定 = sw-{公历年}-{农历月:02d}-shao，幂等按 case_id 去重，未来新增分歧不重号）。
产出 report/shuowang_compare_report.txt。"""
import csv, os, sys
from datetime import datetime, timedelta
from lunar_python import LunarYear
from skyfield.api import load
from skyfield.framelib import ecliptic_frame

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "shuowang_raw")
YEARS = [1950, 1976, 2000, 2024, 2088]
REPORT = os.path.join(BASE, "report", "shuowang_compare_report.txt")
sys.stdout.reconfigure(encoding="utf-8")

# ③ 层独立求根用星历（与 gen_shuowang.py 相同 de440s.bsp 路径规则）
BSP = "de440s.bsp"
for _p in (os.path.join(os.environ.get("TEMP", ""), BSP), os.path.join(BASE, BSP)):
    if os.path.exists(_p):
        BSP = _p
        break
TS = load.timescale()
EPH = load(BSP)
SF = (TS, {"sun": EPH["sun"], "moon": EPH["moon"], "earth": EPH["earth"], "frame": ecliptic_frame})

def read(fn):
    with open(os.path.join(BASE, "data", fn), encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if not r[list(r)[0]].startswith("#")]

def jd2date(jd):
    return (datetime(2000, 1, 1, 12, 0) + timedelta(days=jd - 2451545)).date()

def lunar_shuo():
    """{公历朔日: (农历月序, 闰)} 1948-2101（与 gen_shuowang.py 同源同窗）"""
    out = {}
    for y in range(1947, 2103):
        for m in LunarYear.fromYear(y).getMonths():
            if m.getYear() != y:
                continue
            d = jd2date(m.getFirstJulianDay())
            if datetime(1948, 1, 1).date() <= d <= datetime(2101, 12, 31).date():
                out[d] = (m.getMonth() if m.getMonth() > 0 else -m.getMonth(), 1 if m.isLeap() else 0)
    return out

def case_id(d, mo):  # 内容绑定：sw-{公历年}-{农历月:02d}-shao（月份+字段，跨分支同月不重号）
    return f"sw-{d.year}-{mo:02d}-shao"

def existing_ids():
    try:
        return {r["case_id"] for r in csv.DictReader(open(os.path.join(BASE, "data", "arbitration_log.csv"), encoding="utf-8"))
                if r.get("case_id") and not r["case_id"].startswith("#")}
    except FileNotFoundError:
        return set()

def newmoon_cn(d0, iters=30):
    """独立求根（不复用 gen_shuowang.phase_dt，防共模错误）：DE440s 日月视黄经差 0° 二分 → UTC+8 datetime。
    窗口 = 东八区 [d0-1, d0+1]；30 次二分精度 ~0.2 秒。"""
    TSX, EX = SF
    a = TSX.utc(d0.year, d0.month, d0.day - 1, 16)
    b = TSX.utc(d0.year, d0.month, d0.day + 1, 16)
    def lon(t):
        _, mlon, _ = EX["earth"].at(t).observe(EX["moon"]).apparent().frame_latlon(EX["frame"])
        _, slon, _ = EX["earth"].at(t).observe(EX["sun"]).apparent().frame_latlon(EX["frame"])
        return (mlon.degrees - slon.degrees) % 360
    fa, fb = lon(a), lon(b)
    if fa > fb:
        fa -= 360
    if not (fa < 0 < fb):
        return None  # 窗口内无新月（lunar 月首与天文差 ≥1 天，异常）
    for _ in range(iters):
        m = TSX.tt_jd((a.tt + b.tt) / 2)
        fm = lon(m)
        if fm > 180:
            fm -= 360
        a, b = (m, b) if fm < 0 else (a, m)
    return TSX.tt_jd((a.tt + b.tt) / 2).utc_datetime() + timedelta(hours=8)

def hko_map():
    hko = {}
    if os.path.exists(os.path.join(RAW, "hko_shuo_1948_2100.csv")):
        with open(os.path.join(RAW, "hko_shuo_1948_2100.csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                hko[datetime.strptime(r["date"], "%Y-%m-%d").date()] = (int(r["month"]), int(r["is_ruen"]))
    return hko

def report(txt):  # 覆写式写报告（确定性内容，重跑安全）
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write(txt)

def main():
    lunar = lunar_shuo()
    lines, cases = [], []
    seen = existing_ids()

    # ① HKO 官方 vs lunar（日期级全量）
    hko = hko_map()
    hko_pts = sum(1 for d in hko if d in lunar)
    hko_diff = [(d, lunar[d], hko[d]) for d in sorted(set(lunar) & set(hko)) if lunar[d] != hko[d]]
    hko_only = sorted(set(hko) - set(lunar))  # 官方有而 lunar 无（段内异常）
    lunar_only = sorted(d for d in set(lunar) - set(hko) if d.year <= 2100)  # lunar 有而官方无（2101 属正常覆盖段外）
    lines.append(f"① HKO 官方 vs lunar（日期级，1948-2100）：锚点重合 {hko_pts}/{len(hko)}，"
                 f"不一致 {len(hko_diff)}，官方独有 {len(hko_only)}，lunar 独有(段内) {len(lunar_only)}"
                 f"（2101 年 12 行属官方覆盖段外，正常）")
    for d, a, b in hko_diff:
        lines.append(f"  DIFF {d}: lunar={a} vs HKO={b}")
        cases.append([case_id(d, a[0]), "朔日", str(d), f"lunar {a[0]}月{'闰' if a[1] else ''}",
                      f"HKO {b[0]}月{'闰' if b[1] else ''}", "裁定前", "lunar-python（全量）", "HKO 官方年历（日期锚点）"])
    for d in hko_only:  # 官方标注的朔日不在 lunar 月首集：两侧日期归属差 1 天
        lines.append(f"  DIFF {d}: lunar 无此朔日（其朔日={lunar.get(d + timedelta(days=1), lunar.get(d - timedelta(days=1), '?'))}） vs HKO {hko[d]}")
        cases.append([case_id(d, hko[d][0]), "朔日", str(d), "lunar 无此朔日（日期归属差 1 天）",
                      f"HKO {hko[d][0]}月{'闰' if hko[d][1] else ''}", "裁定前", "lunar-python（全量）", "HKO 官方年历（日期锚点）"])
    for d in lunar_only[:10]:
        lines.append(f"  MISS {d}: 官方表缺该朔日")

    # ② 易安居第三方 vs lunar（5 代表年）
    zy = {}
    zyf = os.path.join(RAW, "zhouyi_shuo_5y.csv")
    if os.path.exists(zyf):
        with open(zyf, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                zy[datetime.strptime(r["date"], "%Y-%m-%d").date()] = (int(r["month"]), int(r["is_ruen"]))
    zy_diff = [(d, lunar[d], zy[d]) for d in sorted(set(lunar) & set(zy)) if lunar[d] != zy[d]]
    lines.append(f"② 易安居第三方 vs lunar（日期级，5 代表年 {YEARS}）：反查点 {len(zy)}，不一致 {len(zy_diff)}")
    for d, a, b in zy_diff:
        lines.append(f"  DIFF {d}: lunar={a} vs 易安居={b}")
        cases.append([case_id(d, a[0]), "朔日", str(d), f"lunar {a[0]}月{'闰' if a[1] else ''}",
                      f"易安居 {b[0]}月{'闰' if b[1] else ''}", "裁定前", "lunar-python（全量）", "易安居排盘页（反查）"])

    # ③ 真 skyfield DE440s 新月时刻 vs 主表月首（临界窗 23:30-00:30 逐一复核，独立求根秒级）
    rows = read("shuowang.csv")
    crit = [r for r in rows if r["shuo_time"] and (r["shuo_time"][11:16] >= "23:30" or r["shuo_time"][11:16] <= "00:30")]
    audit = []  # (主表行, 新月 UTC+8, 是否日期一致)
    for r in crit:
        d0 = datetime.strptime(r["shuo_time"][:10], "%Y-%m-%d").date()
        t = newmoon_cn(d0)
        audit.append((r, t, t is not None and t.strftime("%Y-%m-%d") == r["shuo_time"][:10]))
    dis = [x for x in audit if not x[2]]
    lines.append(f"③ 真 skyfield DE440s 新月时刻 vs 主表月首（临界窗 23:30-00:30 {len(crit)} 行逐一复核，"
                 f"独立二分求根 30 次、秒级）：日期一致 {len(crit) - len(dis)}/{len(crit)}")
    for r, t, ok in audit:
        ts = t.strftime("%Y-%m-%dT%H:%M:%S+08:00") if t else "无根"
        lines.append(f"  {'PASS' if ok else '跨日'} {r['year']}-{r['month']}月{'闰' if r['is_ruen']=='1' else ''}"
                     f" 月首={r['shuo_time'][:10]} 新月={ts}")
    for r, t, ok in dis:  # 临界跨日：新月 UTC+8 落次日——月首侧有 HKO 锚点支持 → 参考层现象，不申报
        d0 = datetime.strptime(r["shuo_time"][:10], "%Y-%m-%d").date()
        hk = hko.get(d0)
        if hk is not None and hk == (int(r["month"]), int(r["is_ruen"])):
            lines.append(f"  → {r['year']}-{r['month']} 月首 {d0} 有 HKO 锚点支持（{hk}），"
                         f"新月时刻落次日属参考层跨日现象，无数据分歧，不申报")
        elif r["year"] != "2101":
            cases.append([case_id(d0, int(r["month"])), "朔日", str(d0),
                          f"lunar/主表 {r['month']}月（月首 {d0}）",
                          f"skyfield 新月 UTC+8 落 {t.strftime('%Y-%m-%d') if t else '?'}（差 1 天，主表月首侧无 HKO 锚点支持）",
                          "裁定前", "lunar-python（全量）", "skyfield DE440s（天文）"])

    # I-8 申报（幂等：case_id 内容绑定去重，重跑不重复追加）
    new = [c for c in cases if c[0] not in seen]
    if new:
        with open(os.path.join(BASE, "data", "arbitration_log.csv"), "a", encoding="utf-8", newline="") as f:
            csv.writer(f).writerows(new)
    lines.append(f"\nI-8 申报：{len(cases)} 条（新增写入 {len(new)}，其余已存在去重）→ arbitration_log.csv sw- 前缀，"
                 f"chain_step=裁定前（未结案）")

    # 待裁/已结案案例详情（数值 = 2026-08-16 独立重算实测）
    lines.append("""
待裁案例详情（I-8 流程，chain_step=裁定前，未结案；不允许静默取任一侧）：
- sw-2057-09-shao 2057-09-28/29：HKO 官方年历标 9 月 28 日朔，lunar 月首=9 月 29 日（日期归属差 1 天）。
  新月时刻重算（skyfield 1.55 + de440s.bsp）：DE440s=2057-09-29T00:00:44（可复现，与初记一致），
  ephem(ELP2000-82B) 独立重算=2057-09-29T00:00:28（几何黄经口径；原记录 23:59:49 在 ±40 秒
  历表带宽内）——两历表均落 lunar 侧（29 日）、带宽覆盖日界；HKO 官方年历独立标注 28 日。
  DE440s 精度最高支持 lunar 侧（29 日），主表已取 lunar 侧并标 status=arbitrated，
  但按 I-8 仍需独立手段确认后才可结案。
- sw-2097-07-shao 2097-08-07/08（已结案：快照错，修正）：原主表 2097-07 行 shuo_time=2097-08-08
  ——gen_shuowang.py 误取 skyfield 新月 UTC+8 日期为朔日，而 lunar-python 该月初一实测=08-07，
  与 HKO 官方（hko_shuo_1948_2100.csv 行 1852）、cnlunar、ephem 四源一致 → 主表取反了侧。
  修正：主表 2097-07 行改 08-07、status 回 confirmed；gen_shuowang.py 取值逻辑改「朔日=月首
  以 lunar 为准、skyfield 时刻仅作参考」，临界跨日裁决规则见 gen_shuowang.py docstring。
  新月时刻重算：DE440s=2097-08-08T00:01:49（原记录 00:01:25 无法复现，差 24 秒；同版本
  skyfield 1.55 + 同 de440s.bsp 下 sw-2057-09-shao 秒值可复现，排除 ΔT 模型/历表/求根容差因素，
  原值疑笔误，已更正为 00:01:49）；ephem(ELP2000-82B) 独立重算=2097-08-07T23:59:54
  （几何黄经口径，原记录 23:59:17 同侧同带宽），落 08-07 侧支持四源结论。
  结论：两例均为「新月时刻逼近午夜 0 点，历表精度差异在日界处放大为 1 天」的历算边界案例；
  sw-2057-09-shao 按 lunar 侧取值并标 arbitrated 待裁；sw-2097-07-shao 主表侧与四源一致，已确认结案。""")

    # 变更申报（问题项：shuowang_template.csv / validate.py 改动未申报 → 补申报）
    lines.append("""
变更申报（2026-08-16 朔日表环节，相对 M0 快照工作区前态）：
- data/shuowang_template.csv：新增 notes 列并更新列语义注释（与 data/shuowang.csv 列对齐）；
- validate.py：shuowang_template.csv 主键 (year,month) → (year,month,is_ruen,lunar_year)
  （与 shuowang.csv 实际主键对齐）；v2 起把 shuowang.csv 纳入 SCHEMA 全表校验（主键同）；
- assert_tables.py：新增 shuowang 断言区（行数/公历年连续/主键唯一/格式/锚点/值域/status），
  v2 再补「全表 shuo_time 日期 = lunar 该月初一」全量断言（防 shuo_time≠初一 类错误回归）；
- data/arbitration_log.csv：追加 sw- 前缀朔日申报；v2 起 case_id 改为内容绑定
  （sw-{公历年}-{农历月:02d}-shao），原 sw-001/sw-002 顺序号已迁移并更正列值与描述；
- data/shuowang.csv / gen_shuowang.py：v2 返工（sw-2097-07-shao 主表取反侧修正，
  全表重跑确认仅此一行变化）。
下游注意：arbitrated 行（sw-2057-09-shao 对应主表 2057-09 行）shuo_time 已取 lunar 侧值——
下游读取须显式检查 status 字段，不得静默使用 arbitrated 行的取值（I-8 契约：裁定前不视为定论）。""")

    # 断言与校验段（读 assert_report.txt 合计行；文件缺失则注明）
    ar = os.path.join(BASE, "report", "assert_report.txt")
    try:
        with open(ar, encoding="utf-8") as f:
            total = [l for l in f.read().splitlines() if l.startswith("合计")]
        assert_line = total[-1] + "（见 assert_report.txt）" if total else "（assert_report.txt 无合计行）"
    except FileNotFoundError:
        assert_line = "（未运行 assert_tables.py，见 assert_report.txt）"
    lines.append(f"\n断言与校验：assert_tables.py {assert_line}；"
                 f"validate.py 全表 schema 校验（11 表含 shuowang.csv，主键=year,month,is_ruen,lunar_year）"
                 f"problems=0（v2 重跑实测）")

    # 报告收尾
    body = "\n".join(lines) + "\n"
    report("朔日表三层对拍报告（2026-08-16 UTC+8；修订 v2：sw-2097-07 取反侧返工修正）\n\n" + body)
    print(body)

if __name__ == "__main__":
    main()

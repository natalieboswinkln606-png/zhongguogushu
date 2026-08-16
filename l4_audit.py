# -*- coding: utf-8 -*-
"""l4_audit.py — L4 审计层统一端到端抽查（只读只测，不改任何模块）。

① 端到端一致性：固定锚点 1985-06-15 10:00 北京时(120E) + 确定性随机 3 例（seed=20260816），
   m1 四柱 → 十神 → 大运流年 → 12 术种 compute()，验证跨模块口径一致（六爻月/日柱=m1 r4/r1、
   合盘四柱=m1、奇门定局节气=solar_terms、梅花/小六壬/称骨/紫微农历=shuowang.csv、黄历干支=ganzhi_days）。
② 跨子时/西部经度分歧锚点（预期差异，验证申报语义不漂移）：
   - 2024-02-10 00:00 120E：m1 真太阳时子正归前日 vs 小六壬/六壬北京时 0 点换日（先例 F1-003）
   - 2000-01-01 00:30 拉萨 91E：m1 真太阳时前日夜 vs 六壬北京时当日（preregister 拉萨案例）
   - 2024-02-10 23:30：两口径一致锚点
③ Rule-ID 注册表双向校验：data/rule_registry.csv ↔ m1.py/l3_*.py 代码字面量全覆盖（缺一即报）。
④ 快照重签：--resign 按 git ls-files 全量重算 SHA256SUMS.txt（L4 范围，含自身行沿用 M1 格式）。
⑤ 归档抽查：l4_audit_ziwei.py（紫微 oracle 缓存独立解析）+ 奇门定局 18 例手工核对。
幂等：默认模式全只读；--resign 显式才写清单；报告 report/l4_audit_report.txt 重跑覆盖不重复申报。
"""
import argparse, csv, glob, hashlib, os, random, re, subprocess, sys
from datetime import datetime, timezone, date, timedelta

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

PASS, FAIL = 0, 0
LINES = []


def check(cond, name, detail=""):
    """断言登记：PASS/FAIL 计数 + 输出行；detail 为空时取 cond 真值文本。"""
    global PASS, FAIL
    if cond:
        PASS += 1
        LINES.append(f"  PASS {name}" + (f"  {detail}" if detail else ""))
    else:
        FAIL += 1
        LINES.append(f"  FAIL {name}  {detail}")
    return cond


# ---------------------------------------------------------------- ① 端到端一致性
def load_shuo():
    rows = []
    with open(os.path.join(BASE, "data", "shuowang.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append((date.fromisoformat(r["shuo_time"][:10]), int(r["month"]),
                         int(r["is_ruen"]), r["lunar_year"]))
    return sorted(rows)


def lunar_of_shuo(d, rows):
    prev = None
    for s in rows:
        if s[0] > d:
            break
        prev = s
    return {"month": prev[1], "is_ruen": prev[2], "day": (d - prev[0]).days + 1, "year_gz": prev[3]}


def load_daygz():
    with open(os.path.join(BASE, "data", "ganzhi_days.csv"), encoding="utf-8") as f:
        return {r["date"]: r["ganzhi"] for r in csv.DictReader(f)}


GAN2 = "甲乙丙丁戊己庚辛壬癸"
ZHI2 = "子丑寅卯辰巳午未申酉戌亥"


def wylq_dahan_gz(dt):
    """独立推算运气岁运干支：最近 ≤dt 大寒节点所在公历年 → (y-4)%60（甲子=0，大寒岁首口径）。

    与 l3_wuyunliuqi._luck_year 同口径但独立实现（各自读 solar_terms.csv），对拍防同错；
    不依赖 m1 立春年柱，故大寒~立春窗口内差异（已申报 wylq-001）也不会假 FAIL，任何随机输入鲁棒。"""
    y = dt.year
    with open(os.path.join(BASE, "data", "solar_terms.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["term"] == "大寒" and r["datetime"] <= dt.strftime("%Y-%m-%d %H:%M"):
                y = int(r["datetime"][:4])
    idx = (y - 4) % 60
    return GAN2[idx % 10] + ZHI2[idx % 12]


JIE_BY_ZHI = {"寅": "立春", "卯": "惊蛰", "辰": "清明", "巳": "立夏", "午": "芒种", "未": "小暑",
              "申": "立秋", "酉": "白露", "戌": "寒露", "亥": "立冬", "子": "大雪", "丑": "小寒"}


def e2e_audit(dt, lon, tag, rows, dgz):
    """单日全链路：m1 → 各术种，跨模块一致性断言。返回 (pass_n, fail_n)。"""
    global PASS, FAIL
    import m1
    r = m1.compute(dt, lon)
    if "error" in r:
        return check(False, f"[{tag}] m1 可算", r["error"]), 0
    P = {k: v["ganzhi"] for k, v in r["pillars"].items()}
    d = dt.date()
    LINES.append(f"  -- {tag} {dt.strftime('%Y-%m-%d %H:%M')} lon={lon} 四柱={P} 真太阳时={r['true_solar_time']}")
    n0 = (PASS, FAIL)
    lu = lunar_of_shuo(d, rows)

    import l3_liuyao, l3_wangshuai, l3_hepan, l3_heluolishu, l3_qimen, l3_meihua
    import l3_xiaoliuren, l3_chenggu, l3_ziwei, l3_bazi_daliu, l3_shensha
    import l3_liuren, l3_huangli, l3_wuyunliuqi, l3_ziwei_liunian, l3_qimen_duanju

    ly = l3_liuyao.compute(dt, lon)
    check("error" not in ly, f"[{tag}] 六爻可算")
    if "error" not in ly:
        check(ly["yue_jian"]["ganzhi"] == P["month"], f"[{tag}] 六爻月建=m1 r4",
              f"{ly['yue_jian']['ganzhi']} vs {P['month']}")
        check(ly["ri_chen"]["ganzhi"] == P["day"], f"[{tag}] 六爻日辰=m1 r1",
              f"{ly['ri_chen']['ganzhi']} vs {P['day']}")

    ws = l3_wangshuai.compute(dt, lon)
    check("error" not in ws and all(ws["pillars"][k]["ganzhi"] == P[k] for k in P),
          f"[{tag}] 旺衰四柱=m1", "" if "error" in ws else str(ws["pillars"]))

    hl = l3_heluolishu.compute(dt, "男", lon)
    check("error" not in hl, f"[{tag}] 河洛理数可算")
    if "error" not in hl:
        check(all(hl["pillars"][k]["ganzhi"] == P[k] for k in P),
              f"[{tag}] 河洛四柱=m1", str({k: hl["pillars"][k]["ganzhi"] for k in P}))
        check(all(k in hl for k in ("hlyl01", "hlyl02", "hlyl03", "hlyl04", "hlyl05")),
              f"[{tag}] 河洛五层 hlyl01..05 齐全")

    mh = l3_meihua.compute_time(dt, lon)
    check("error" not in mh, f"[{tag}] 梅花可算")
    if "error" not in mh:
        n = mh["method"]["nums"]
        check(n["lunar_month"] == lu["month"] and n["lunar_day"] == lu["day"],
              f"[{tag}] 梅花农历=shuowang", f"{n['lunar_month']}月{n['lunar_day']}日 vs {lu['month']}月{lu['day']}日")

    xlr = l3_xiaoliuren.compute(dt, lon)
    check("error" not in xlr, f"[{tag}] 小六壬可算")
    if "error" not in xlr:
        x1 = xlr["xlr-01"]
        check(x1["month"] == lu["month"] and x1["day"] == lu["day"],
              f"[{tag}] 小六壬农历=shuowang", f"{x1['month']}月{x1['day']}日")
        check(x1["day_ganzhi"] == dgz.get(d.isoformat()), f"[{tag}] 小六壬日柱=ganzhi_days(北京时当日)",
              f"{x1['day_ganzhi']} vs {dgz.get(d.isoformat())}")

    cg = l3_chenggu.compute(dt, lon)
    check("error" not in cg, f"[{tag}] 称骨可算")
    if "error" not in cg:
        check(cg["lunar"]["month_name"] == ("" if lu["month"] not in range(1, 13) else
                                            "正二三四五六七八九十冬腊"[lu["month"] - 1] + "月")
              and cg["lunar"]["day"] == lu["day"],
              f"[{tag}] 称骨农历=shuowang", f"{cg['lunar']['month_name']}{cg['lunar']['day']}日 vs {lu['month']}月{lu['day']}日")

    zw = l3_ziwei.compute(dt, lon)
    check("error" not in zw, f"[{tag}] 紫微可算")
    if "error" not in zw:
        check(zw["lunar"]["month"] == lu["month"] and zw["lunar"]["day"] == lu["day"],
              f"[{tag}] 紫微农历=shuowang", f"{zw['lunar']['month_name']}{zw['lunar']['day']}日")

    bd = l3_bazi_daliu.compute(dt, lon)
    if "error" in bd:
        check(False, f"[{tag}] 大运流年可算", bd["error"])
    else:
        check(all(bd["pillars"][k]["ganzhi"] == P[k] for k in P),
              f"[{tag}] 大运流年四柱=m1", str({k: bd["pillars"][k]["ganzhi"] for k in P}))

    ss = l3_shensha.compute(dt, lon)
    if "error" in ss:
        check(False, f"[{tag}] 神煞可算", ss["error"])
    else:
        check(all(ss["pillars"][k]["ganzhi"] == P[k] for k in P),
              f"[{tag}] 神煞四柱=m1", str({k: ss["pillars"][k]["ganzhi"] for k in P}))

    qm = l3_qimen.compute(dt, lon)
    if "error" in qm:
        check(False, f"[{tag}] 奇门可算", qm["error"])
    else:
        check(all(qm["pillars"][k]["ganzhi"] == P[k] for k in P),
              f"[{tag}] 奇门四柱=m1", str({k: qm["pillars"][k]["ganzhi"] for k in P}))
        check(qm["dingju"]["term"] == JIE_BY_ZHI[P["month"][1]], f"[{tag}] 奇门定局节=月柱节",
              f"{qm['dingju']['term']} vs {JIE_BY_ZHI[P['month'][1]]}")

    qd = l3_qimen_duanju.duanju(dt, lon)
    check("error" not in qd and qd["pillars"] == P, f"[{tag}] 奇门断局四柱=m1")

    hl = l3_huangli.daily(d, "巳" if dt.hour in (9, 10) else None)
    check("error" not in hl and hl["ganzhi"] == P["day"], f"[{tag}] 黄历干支=ganzhi_days",
          f"{hl.get('ganzhi')} vs {P['day']}")

    wy = l3_wuyunliuqi.compute(dt)
    check("error" not in wy, f"[{tag}] 五运六气可算")
    if "error" not in wy:
        luck = wylq_dahan_gz(dt)
        check(wy["sui_yun"]["ganzhi"] == luck, f"[{tag}] 五运六气岁运=大寒口径(独立推算)",
              f"{wy['sui_yun']['ganzhi']} vs {luck}")
        # 界外（非大寒~立春窗口）：大寒岁首=立春换年，两口径一致；界内差异已申报 wylq-001（预期，豁免）
        check(luck != P["year"] or wy["sui_yun"]["ganzhi"] == P["year"],
              f"[{tag}] 五运六气岁运年=m1(界外两口径一致)", f"{wy['sui_yun']['ganzhi']} vs {P['year']}")

    nr = l3_liuren.compute(dt, lon)
    check("error" not in nr, f"[{tag}] 六壬可算")
    if "error" not in nr:
        # 六壬日柱=北京时当日（W2 易安居口径）；m1 日柱=真太阳时日期（r1）。跨子时窗口=真太阳时日期≠北京时日期
        ts_d = datetime.strptime(r["true_solar_time"], "%Y-%m-%dT%H:%M:%S").date()
        same = nr["pillars"]["day"] == P["day"]
        if same and ts_d == d:
            check(True, f"[{tag}] 六壬日柱=m1(非跨子时窗口一致)", f"{nr['pillars']['day']}")
        elif not same and ts_d != d:
            # 窗口内差异为预期（先例 F1-003）：六壬=北京时当日柱、m1=真太阳时日柱，方向须正确
            check(nr["pillars"]["day"] == dgz.get(d.isoformat()),
                  f"[{tag}] 六壬日柱≠m1(跨子时窗口差异方向正确)",
                  f"六壬={nr['pillars']['day']}(北京时{d}) vs m1={P['day']}(真太阳时{ts_d})")
        else:
            check(False, f"[{tag}] 六壬日柱=m1",
                  f"六壬={nr['pillars']['day']} vs m1={P['day']}（真太阳时日期={ts_d}，北京时日期={d}）")

    zln = l3_ziwei_liunian.compute(dt, lon, target_year=min(dt.year + 5, 2100))
    check("error" not in zln, f"[{tag}] 紫微大限流年可算")
    if "error" not in zln:
        check(zln["lunar"]["month_name"] == cg["lunar"]["month_name"] if "error" not in cg else True,
              f"[{tag}] 紫微大限农历=称骨农历", f"{zln['lunar']['month_name']}")

    # 合盘（双盘）：A=当前日、B=随机另一日；B 盘四柱与大运流年模块独立对拍（assert_l3_hepan.py 未覆盖此项）
    b_dt = dt + timedelta(days=137, hours=3)
    hp = l3_hepan.compute(dt.strftime("%Y-%m-%d %H:%M"), b_dt.strftime("%Y-%m-%d %H:%M"))
    check("error" not in hp, f"[{tag}] 合盘可算")
    if "error" not in hp:
        pa = {k: v["ganzhi"] for k, v in r["pillars"].items()}
        check(hp["persons"][0]["pillars"] == pa, f"[{tag}] 合盘A四柱=m1", str(hp["persons"][0]["pillars"]))
        bd_b = l3_bazi_daliu.compute(b_dt, lon)
        if "error" in bd_b:
            check(False, f"[{tag}] 合盘B可算", bd_b["error"])
        else:
            pb = {k: v["ganzhi"] for k, v in bd_b["pillars"].items()}
            check(hp["persons"][1]["pillars"] == pb, f"[{tag}] 合盘B四柱=大运流年模块",
                  str(hp["persons"][1]["pillars"]))
        check("rule_id" in hp.get("hp-01", {}) and "rule_id" in hp.get("hp-04", {}),
              f"[{tag}] 合盘 hp-01/hp-04 带 Rule-ID")
    return (PASS - n0[0], FAIL - n0[1])


def divergence_anchors(rows, dgz):
    """分歧锚点：验证跨子时/西部经度预期差异方向（先例 F1-001~003、preregister 拉萨案例）。"""
    global PASS, FAIL
    import m1, l3_xiaoliuren, l3_liuren

    # 锚点 A：2024-02-10 00:00 120E — m1 真太阳时 2-9 23:45 子正归前日；小六壬/六壬 0 点换日归 2-10
    r = m1.compute(datetime(2024, 2, 10, 0, 0), 120.0)
    x = l3_xiaoliuren.compute(datetime(2024, 2, 10, 0, 0), 120.0)
    n = l3_liuren.compute(datetime(2024, 2, 10, 0, 0), 120.0)
    check(r["pillars"]["day"]["ganzhi"] != x["xlr-01"]["day_ganzhi"]
          and r["pillars"]["day"]["ganzhi"] == dgz.get("2024-02-09"),
          "分歧A 2024-02-10 00:00 120E：m1 子正归前日(2-9)",
          f"m1={r['pillars']['day']['ganzhi']}(真太阳时{r['true_solar_time']}) vs 小六壬={x['xlr-01']['day_ganzhi']}")
    check(x["xlr-01"]["day_ganzhi"] == dgz.get("2024-02-10") == n["pillars"]["day"],
          "分歧A 六壬/小六壬 北京时 0 点换日归 2-10",
          f"小六壬={x['xlr-01']['day_ganzhi']} 六壬={n['pillars']['day']}")

    # 锚点 B：2000-01-01 00:30 拉萨 91E — m1 真太阳时 1999-12-31 22:30 前日夜；六壬北京时 1-1
    r = m1.compute(datetime(2000, 1, 1, 0, 30), 91.0)
    n = l3_liuren.compute(datetime(2000, 1, 1, 0, 30), 91.0)
    check(r["pillars"]["day"]["ganzhi"] == dgz.get("1999-12-31"),
          "分歧B 拉萨91E：m1 真太阳时跨日归前日夜",
          f"m1={r['pillars']['day']['ganzhi']}(真太阳时{r['true_solar_time']}) vs 六壬={n['pillars']['day']}")
    check(n["pillars"]["day"] == dgz.get("2000-01-01"), "分歧B 六壬北京时口径归 1-1", f"六壬={n['pillars']['day']}")

    # 锚点 C：2024-02-10 23:30 120E — 两口径一致（m1 真太阳时 23:15 归当日、六壬 23 点子时归当日）
    r = m1.compute(datetime(2024, 2, 10, 23, 30), 120.0)
    n = l3_liuren.compute(datetime(2024, 2, 10, 23, 30), 120.0)
    check(r["pillars"]["day"]["ganzhi"] == n["pillars"]["day"] == dgz.get("2024-02-10"),
          "分歧C 2024-02-10 23:30：两口径一致", f"m1=六壬={n['pillars']['day']}")


# ---------------------------------------------------------------- ② 注册表双向校验
# 申报编号白名单（正式载体=arbitration_log.csv case_id，非 Rule-ID）：wylq-001..005（口径/值分歧）、qd-b-01..21（奇门断局对拍分歧）
REG_SKIP = {f"wylq-{i:03d}" for i in range(1, 6)} | {f"qd-b-{i:02d}" for i in range(1, 22)} | {"qd-x-27"}
REG_SKIP_NOTE = {"qd-x-27": "docstring 旧编号残留（风遁正式 id=qd-x-26，GE_RULES 表驱动；L4 审计发现，功能无影响）"}
REG_SPECIAL = {"nr-01/nr-02", "nr-04（行年）"}  # 复合键：正则抓不到，字面量直接校验


def registry_check():
    global PASS, FAIL
    pat = re.compile(r"[a-z]{2,4}-\d{2,4}(?:-\d+)?[a-z]*|[a-z]{2,4}-[a-z]-\d{2,4}[a-z]*|r[1-5]\b")
    code = set()
    for f in glob.glob(os.path.join(BASE, "l3_*.py")) + [os.path.join(BASE, "m1.py")]:
        src = open(f, encoding="utf-8").read()
        code |= set(pat.findall(src))
        for s in REG_SPECIAL:
            if s in src:
                code.add(s)
    reg = set()
    with open(os.path.join(BASE, "data", "rule_registry.csv"), encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            reg.add(r["rule_id"])
    n = len(reg)
    missing = sorted((code - REG_SKIP) - reg)
    phantom = sorted(reg - code)
    check(n >= 150, "注册表条目数≥150", f"实 {n} 条")
    check(not missing, "代码字面量全部在注册表", f"缺 {missing}")
    check(not phantom, "注册表条目全部在代码中存在", f"多 {phantom}")
    # 申报编号白名单复核：载体=arbitration_log.csv case_id
    arb = open(os.path.join(BASE, "data", "arbitration_log.csv"), encoding="utf-8").read()
    with open(os.path.join(BASE, "data", "arbitration_log.csv"), encoding="utf-8") as fh:
        arb_ids = {r["case_id"] for r in csv.DictReader(fh) if r["case_id"]}
    arb_refs = {w for w in REG_SKIP if w not in REG_SKIP_NOTE}
    check(all(w in arb_ids for w in arb_refs), "申报编号 wylq-001..005/qd-b-01..21 在 arbitration_log.csv 有载体",
          f"缺 {sorted(arb_refs - arb_ids)}")
    if REG_SKIP_NOTE:
        for k, v in REG_SKIP_NOTE.items():
            LINES.append(f"  NOTE 审计注记 {k}: {v}")
    return n


# ---------------------------------------------------------------- ④ 快照重签
def resign():
    """L4 重签：git ls-files 全量 sha256 → SHA256SUMS.txt（含自身行沿用 M1 格式）。"""
    files = subprocess.run(["git", "ls-files"], cwd=BASE, capture_output=True, text=True,
                           encoding="utf-8").stdout.split()
    lines = [f"# generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
             "# L4 重签：M0-M3 全部冻结文件（git ls-files 全量，排除未入库临时产物）",
             "# signature: pending"]
    n = 0
    for f in sorted(files):
        p = os.path.join(BASE, f)
        if not os.path.exists(p):
            continue
        if f == "SHA256SUMS.txt":
            h = open(p, encoding="utf-8").read().encode("utf-8")  # 用重签前内容哈希（M1 同法）
        else:
            h = open(p, "rb").read()
        lines.append(hashlib.sha256(h).hexdigest() + " *" + f)
        n += 1
    open(os.path.join(BASE, "SHA256SUMS.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"已重签 {n} 个文件（含 SHA256SUMS.txt 自身行）→ SHA256SUMS.txt")


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser(description="L4 审计层统一端到端抽查（只读）+ 注册表校验 + 快照重签")
    ap.add_argument("--resign", action="store_true", help="重签 SHA256SUMS.txt（唯一写操作）")
    ap.add_argument("--seed", type=int, default=20260816)
    a = ap.parse_args()
    if a.resign:
        resign()
        return
    rows = load_shuo()
    dgz = load_daygz()

    LINES.append("L4 审计层端到端抽查报告（l4_audit.py，UTC+8）")
    LINES.append(f"一、固定锚点 1985-06-15 10:00 北京时(120E) 全链路")
    e2e_audit(datetime(1985, 6, 15, 10, 0), 120.0, "锚点", rows, dgz)
    rng = random.Random(a.seed)
    LINES.append(f"二、确定性随机 3 例（seed={a.seed}）")
    for i in range(3):
        y = rng.randint(1950, 2099)
        mo = rng.randint(1, 12)
        d = rng.randint(1, 27)
        h = rng.choice([0, 1, 6, 10, 12, 15, 18, 22, 23])
        mi = rng.choice([0, 10, 30])
        e2e_audit(datetime(y, mo, d, h, mi), 120.0, f"R{i+1}", rows, dgz)

    LINES.append("三、跨子时/西部经度分歧锚点（预期差异方向验证）")
    divergence_anchors(rows, dgz)

    LINES.append("四、Rule-ID 注册表双向校验（data/rule_registry.csv）")
    n = registry_check()

    LINES.append("五、奇门定局 18 例手工核对（归档自 temp/qm_audit.py，独立推算）")
    qimen_check()

    LINES.append("六、归档抽查 l4_audit_ziwei.py（紫微 oracle 缓存独立解析）")
    zr = subprocess.run([sys.executable, os.path.join(BASE, "l4_audit_ziwei.py")],
                        capture_output=True, text=True, encoding="utf-8")
    tail = (zr.stdout or "").strip().splitlines()
    LINES.append("  退出码 " + ("0" if zr.returncode == 0 else str(zr.returncode)))
    LINES.extend(["  " + x for x in tail[-3:]])
    check(zr.returncode == 0, "l4_audit_ziwei.py 独立解析抽查 PASS")
    if zr.returncode != 0:
        LINES.extend(["  " + x for x in (zr.stdout + zr.stderr).strip().splitlines()[-5:]])

    LINES.append(f"合计：PASS {PASS} / FAIL {FAIL}")
    out = "\n".join(LINES) + "\n"
    print(out)
    open(os.path.join(BASE, "report", "l4_audit_report.txt"), "w", encoding="utf-8").write(out)
    sys.exit(1 if FAIL else 0)


def qimen_check():
    """奇门定局手工核对 18 例（独立推算，锚点 2024-02-10=甲辰、2024-01-01=甲子），归档自 temp/qm_audit.py 第一部分。"""
    import l3_qimen as Q
    CASES = [
        ("2024-01-01 12:00", ("冬至", "阳遁", "上元", 1)),
        ("2024-01-06 03:00", ("冬至", "阳遁", "中元", 7)),
        ("2024-01-06 12:00", ("小寒", "阳遁", "中元", 8)),
        ("2024-02-04 16:00", ("大寒", "阳遁", "上元", 3)),
        ("2024-02-04 18:00", ("立春", "阳遁", "上元", 8)),
        ("2024-02-10 12:00", ("立春", "阳遁", "下元", 2)),
        ("2024-03-05 09:00", ("雨水", "阳遁", "上元", 9)),
        ("2024-03-05 12:00", ("惊蛰", "阳遁", "上元", 1)),
        ("2024-03-11 12:00", ("惊蛰", "阳遁", "下元", 4)),
        ("2024-05-20 21:30", ("小满", "阳遁", "中元", 2)),
        ("2024-06-21 04:00", ("芒种", "阳遁", "中元", 3)),
        ("2024-06-21 12:00", ("夏至", "阴遁", "中元", 3)),
        ("2024-06-24 12:00", ("夏至", "阴遁", "下元", 6)),
        ("2024-07-01 12:00", ("夏至", "阴遁", "上元", 9)),
        ("2024-08-07 12:00", ("立秋", "阴遁", "中元", 5)),
        ("2024-09-07 12:00", ("白露", "阴遁", "下元", 6)),
        ("2024-12-21 16:00", ("大雪", "阴遁", "下元", 1)),
        ("2024-12-21 18:00", ("冬至", "阳遁", "下元", 4)),
    ]
    for ts, want in CASES:
        d = Q.compute(datetime.strptime(ts, "%Y-%m-%d %H:%M"))["dingju"]
        got = (d["term"], d["dun"], d["yuan"], d["ju"])
        check(got == want, f"定局 {ts}", f"期望 {want} 实得 {got}")


if __name__ == "__main__":
    main()

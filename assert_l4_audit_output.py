# -*- coding: utf-8 -*-
"""assert_l4_audit_output.py — L4 输出审计层独立断言（历史真实事故回放为锚，不抄实现）。
覆盖：T1 A 盘大运错位陷阱 / T2 流年公式 / T3 B 盘奇门中五宫与值符值使 /
     T4 reconcile 元测试（证明审计器能抓住历史错误文本、放行修正文本）/
     五条不变量 + 篡改必被抓反向测试 + dump 往返 + CLI 冒烟。
运行：PYTHONIOENCODING=utf-8 python assert_l4_audit_output.py"""
import copy, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
import m1, l3_bazi_daliu as B, l3_qimen as Q
import l4_audit_output as A

RES = []
def check(name, cond, detail=""):
    RES.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), name, detail)

BASE = os.path.dirname(os.path.abspath(__file__))
TEMP = os.path.join(BASE, "temp")
os.makedirs(TEMP, exist_ok=True)

# ---- 共享夹具：A 盘快照（2006-06-25 00:30 女 120E，历史重大错位事故当事盘） ----
SNAP_A = A.snapshot("2006-06-25 00:30", "女", 120.0)
STEPS = SNAP_A["dayun"]["steps"]

# ================= T1 历史错误陷阱：A 盘大运序列 =================
r1 = m1.compute(datetime(2006, 6, 25, 0, 30), 120.0)
dl, y, mo, d, h, jie, jiao, fwd = B.dayun(datetime(2006, 6, 25, 0, 30), 120.0, "女")
check("T1-01 A 盘月柱=甲午（错位事故把月柱当成了首步大运）", r1["pillars"]["month"]["ganzhi"] == "甲午",
      r1["pillars"]["month"]["ganzhi"])
check("T1-02 A 盘阳年女逆排", fwd == "逆", fwd)
check("T1-03 A 盘大运第一步=癸巳 且 !=甲午", STEPS[0]["ganzhi"] == "癸巳" and STEPS[0]["ganzhi"] != "甲午",
      STEPS[0]["ganzhi"])
check("T1-04 A 盘大运第二步=壬辰", STEPS[1]["ganzhi"] == "壬辰", STEPS[1]["ganzhi"])
check("T1-05 A 盘大运前六步完整序列（引擎实证）",
      [s["ganzhi"] for s in STEPS[:6]] == ["癸巳", "壬辰", "辛卯", "庚寅", "己丑", "戊子"],
      " ".join(s["ganzhi"] for s in STEPS[:6]))
check("T1-06 首步起止年 2012-2021", (STEPS[0]["start_year"], STEPS[0]["end_year"]) == (2012, 2021),
      f"{STEPS[0]['start_year']}-{STEPS[0]['end_year']}")

# ================= T2 流年公式抽查 =================
check("T2-01 引擎 year_gz：2026=丙午", B.year_gz(2026) == "丙午", B.year_gz(2026))
check("T2-02 引擎 year_gz：2035=乙卯", B.year_gz(2035) == "乙卯", B.year_gz(2035))
check("T2-03 引擎 year_gz：2036=丙辰", B.year_gz(2036) == "丙辰", B.year_gz(2036))
check("T2-04 本地独立公式 (y-4)%60 与引擎逐年全一致（快照 21 年）",
      all(A.year_gz_formula(e["year"]) == e["ganzhi"] for e in SNAP_A["liunian"]),
      f"{SNAP_A['liunian'][0]['year']}-{SNAP_A['liunian'][-1]['year']}")

# ================= T3 B 盘奇门（2005-10-24 17:02 男 120E，文档转录事故当事盘） =================
qm = Q.compute(datetime(2005, 10, 24, 17, 2), 120.0)
p5, p8 = qm["pan"]["5"], qm["pan"]["8"]
zzs = qm["zhifu_zhishi"]
check("T3-01 中五宫 star/door/shen 全 None（转录曾把值符死门同时写到中五宫）",
      p5["star"] is None and p5["door"] is None and p5["shen"] is None,
      f"{[p5['star'], p5['door'], p5['shen']]}")
check("T3-02 值符宫=艮八宫", zzs["zhifu_palace"] == 8, str(zzs["zhifu_palace"]))
check("T3-03 艮八宫天盘干含辛（旬首六仪）", "辛" in p8["tianpan_gan"], p8["tianpan_gan"])
check("T3-04 艮八宫 star=天芮 door=死门（值符死门只在八宫一处）",
      p8["star"] == "天芮" and p8["door"] == "死门", f"{p8['star']}/{p8['door']}")

# ================= 快照结构 + 五条不变量 =================
inv = A.check_invariants(SNAP_A)
check("S-01 快照四柱与 m1 一致", SNAP_A["pillars"] == {k: r1["pillars"][k]["ganzhi"]
      for k in ("year", "month", "day", "hour")}, str(SNAP_A["pillars"]))
check("S-02 不变量恰五条且 id 齐", [x["id"] for x in inv] == A.INVARIANTS,
      ",".join(x["id"] for x in inv))
for x in inv:
    check(f"S-03 {x['id']} ok", x["ok"], x["detail"])
check("S-04 快照紫微 12 时辰全谱", len(SNAP_A["ziwei_hours"]) == 12
      and [z["hour"] for z in SNAP_A["ziwei_hours"]] == list(range(0, 24, 2)),
      str([z["hour"] for z in SNAP_A["ziwei_hours"]]))
check("S-05 快照流年默认 2020-2040 共 21 年", len(SNAP_A["liunian"]) == 21,
      f"{len(SNAP_A['liunian'])}")
check("S-06 快照含奇门与称骨", bool(SNAP_A.get("qimen")) and bool(SNAP_A.get("chenggu")), "")

# ================= T4 reconcile 元测试（审计器能抓住历史错误） =================
OLD_TEXT = ("A 大运走势：甲午(2012-2021)伤官启运，癸巳(2022-2031)偏印学业，壬辰(2032-2041)正印安家，"
            "辛卯(2042-2051)七杀事业，庚寅(2052-2061)正官成婚，己丑(2062-2071)偏财巅峰。")  # 历史真实犯的错位版本
NEW_TEXT = ("A 大运走势：癸巳(2012-2021)偏印少年，壬辰(2022-2031)正印求学离乡，辛卯(2032-2041)七杀高压，"
            "庚寅(2042-2051)正官稳定，己丑(2052-2061)偏财巅峰，戊子(2062-2071)正财晚景。")  # 修正版
rep_old = A.reconcile(OLD_TEXT, SNAP_A)
rep_new = A.reconcile(NEW_TEXT, SNAP_A)
old_c = {c["ganzhi"] for c in rep_old["conflicts"]}
check("T4-01 旧错误文本被抓（conflicts 或 unverified 非空）",
      len(rep_old["conflicts"]) + len(rep_old["unverified"]) > 0,
      f"conflicts={len(rep_old['conflicts'])} unverified={len(rep_old['unverified'])}")
check("T4-02 命中项包含 甲午（历史错误的错位源头）", "甲午" in old_c
      or any(u.get("value") == "甲午" for u in rep_old["unverified"]), str(sorted(old_c)))
check("T4-03 错位的癸巳/壬辰/辛卯/庚寅/己丑 全部判 shifted",
      {"癸巳", "壬辰", "辛卯", "庚寅", "己丑"} <= old_c
      and all(c["kind"] == "shifted" for c in rep_old["conflicts"] if c["ganzhi"] in
              {"癸巳", "壬辰", "辛卯", "庚寅", "己丑"}), str(len(old_c)))
check("T4-04 修正文本零 conflict 零 unverified",
      len(rep_new["conflicts"]) == 0 and len(rep_new["unverified"]) == 0,
      f"conflicts={len(rep_new['conflicts'])} unverified={len(rep_new['unverified'])}")
check("T4-05 修正文本六个大运配年全部 matched",
      sum(1 for mm in rep_new["matched"] if mm["kind"] == "dayun_range") == 6,
      str(sum(1 for mm in rep_new["matched"] if mm["kind"] == "dayun_range")))
check("T4-06 旧文本 甲午 判定为 not_in_dayun（冒充大运步骤）",
      any(c["ganzhi"] == "甲午" and c["kind"] == "not_in_dayun" for c in rep_old["conflicts"]), "")

# ================= 篡改必被抓（反向测试：防线机械化验证） =================
t = copy.deepcopy(SNAP_A)
t["dayun"]["steps"][0]["ganzhi"] = "甲午"  # 复现历史事故：把月柱当首步
i1 = {x["id"]: x for x in A.check_invariants(t)}
check("X-01 篡改首步为甲午 → aud-inv-01 必 FAIL", not i1["aud-inv-01"]["ok"],
      i1["aud-inv-01"]["detail"][-40:])
t2 = copy.deepcopy(SNAP_A)
t2["dayun"]["steps"][1]["ganzhi"] = "己卯"  # 断链：壬辰→己卯 序差非 -1
i2 = {x["id"]: x for x in A.check_invariants(t2)}
check("X-02 大运链断裂 → aud-inv-02 必 FAIL", not i2["aud-inv-02"]["ok"],
      i2["aud-inv-02"]["detail"][-40:])
t2b = copy.deepcopy(SNAP_A)
t2b["dayun"]["steps"][2]["start_year"] = 2035  # 起年差≠10
i2b = {x["id"]: x for x in A.check_invariants(t2b)}
check("X-03 起年差被改 → aud-inv-02 必 FAIL", not i2b["aud-inv-02"]["ok"], "")
t3 = copy.deepcopy(SNAP_A)
t3["liunian"][5]["ganzhi"] = "甲子"
i3 = {x["id"]: x for x in A.check_invariants(t3)}
check("X-04 流年干支被改 → aud-inv-03 必 FAIL", not i3["aud-inv-03"]["ok"], "")
t4 = copy.deepcopy(SNAP_A)
t4["ziwei_hours"][3]["palaces"] = t4["ziwei_hours"][3]["palaces"][:11]  # 抽掉一宫
i4 = {x["id"]: x for x in A.check_invariants(t4)}
check("X-05 紫微缺宫 → aud-inv-04 必 FAIL", not i4["aud-inv-04"]["ok"], "")
t5 = copy.deepcopy(SNAP_A)
t5["qimen"]["pan"]["5"]["door"] = "死门"  # 复现转录事故：死门写进中五宫
i5 = {x["id"]: x for x in A.check_invariants(t5)}
check("X-06 中五宫出现死门 → aud-inv-05 必 FAIL", not i5["aud-inv-05"]["ok"], "")
t6 = copy.deepcopy(SNAP_A)
t6["qimen"]["zhifu_zhishi"]["zhifu_palace"] = 3  # 值符宫报错
i6 = {x["id"]: x for x in A.check_invariants(t6)}
check("X-07 值符宫申报错误 → aud-inv-05 必 FAIL", not i6["aud-inv-05"]["ok"], "")

# ================= dump 往返 + CLI 冒烟 =================
p_snap = os.path.join(TEMP, "_assert_snap_a.json")
A.dump(SNAP_A, p_snap)
with open(p_snap, encoding="utf-8") as f:
    check("D-01 dump/load 往返一致", json.load(f) == SNAP_A, p_snap)

env = dict(os.environ, PYTHONIOENCODING="utf-8")
out_cli = os.path.join(TEMP, "_assert_cli_snap.json")
rc = subprocess.run([sys.executable, os.path.join(BASE, "l4_audit_output.py"), "snapshot",
                     "--datetime", "2006-06-25 00:30", "--gender", "女", "--out", out_cli],
                    capture_output=True, env=env).returncode
check("C-01 CLI snapshot 退出码 0", rc == 0, out_cli)
txt_old = os.path.join(TEMP, "_text_old.txt")
if not os.path.exists(txt_old):
    with open(txt_old, "w", encoding="utf-8") as f:
        f.write(OLD_TEXT + "\n")
out_rec = os.path.join(TEMP, "_assert_rec_old.json")
rc = subprocess.run([sys.executable, os.path.join(BASE, "l4_audit_output.py"), "reconcile",
                     "--text", txt_old, "--snap", p_snap, "--out", out_rec],
                    capture_output=True, env=env).returncode
with open(out_rec, encoding="utf-8") as f:
    rr = json.load(f)
check("C-02 CLI reconcile 对旧文本退出码 0 且抓到 conflicts", rc == 0 and len(rr["conflicts"]) >= 1,
      f"rc={rc} conflicts={len(rr['conflicts'])}")

npass = sum(1 for _, ok in RES if ok)
print(f"\n断言 {npass}/{len(RES)} PASS")
sys.exit(0 if npass == len(RES) else 1)

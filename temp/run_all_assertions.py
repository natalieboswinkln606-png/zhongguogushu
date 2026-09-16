# -*- coding: utf-8 -*-
import glob
import os
import re
import subprocess
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCRIPTS = [
    ("assert_tables.py", r"PASS\s+(\d+)\s+FAIL\s+(\d+)"),
    ("assert_l3_bazi_daliu.py", r"断言\s+(\d+)/(\d+)\s+PASS"),
    ("assert_l3_bazi_liuri.py", r"assert_l3_bazi_liuri:\s+(\d+)/(\d+)\s+PASS"),
    ("assert_l3_chenggu.py", r"PASS\s+(\d+)\s+\|\s+FAIL\s+(\d+)"),
    ("assert_l3_heluolishu.py", r"assert_l3_heluolishu:\s+(\d+)/(\d+)\s+PASS"),
    ("assert_l3_hepan.py", r"PASS\s+(\d+)，FAIL\s+(\d+)"),
    ("assert_l3_huangli.py", r"PASS\s+(\d+)\s+FAIL\s+(\d+)"),
    ("assert_l3_liuren.py", r"PASS\s+(\d+)\s+\|\s+FAIL\s+(\d+)"),
    ("assert_l3_liuyao.py", r"PASS\s+(\d+)\s+\|\s+FAIL\s+(\d+)"),
    ("assert_l3_meihua.py", r"断言:\s+(\d+)\s+通过,\s+(\d+)\s+失败"),
    ("assert_l3_qimen.py", r"断言\s+(\d+)\s+条全部通过"),
    ("assert_l3_qimen_duanju.py", r"PASS"),
    ("assert_l3_shensha.py", r"PASS\s+(\d+)，FAIL\s+(\d+)"),
    ("assert_l3_tieban.py", r"assert_l3_tieban:\s+(\d+)/(\d+)\s+PASS"),
    ("assert_l3_wangshuai.py", r"assert_l3_wangshuai:\s+(\d+)/(\d+)\s+PASS"),
    ("assert_l3_wuyunliuqi.py", r"PASS\s+(\d+)，FAIL\s+(\d+)"),
    ("assert_l3_xiaoliuren.py", r"(\d+)/(\d+)\s+PASS"),
    ("assert_l3_ziwei.py", r"PASS\s+(\d+)\s+/\s+FAIL\s+(\d+)"),
    ("assert_l3_ziwei_liunian.py", r"(\d+)\s+通过\s+/\s+(\d+)\s+失败"),
    ("assert_l4_audit_output.py", r"断言\s+(\d+)/(\d+)\s+PASS"),
    ("assert_l4_audit_output_v3_rules.py", r"ALL PASS"),
    ("assert_l5_rule9_age_year.py", r"rule9 回归测试:\s+(\d+)/(\d+)\s+PASS"),
    ("assert_mcp.py", r"assert_mcp 测试结果:\s+(\d+)/(\d+)\s+PASS"),
    ("assert_ephemeris_ext.py", r"PASS\s+(\d+)\s+FAIL\s+(\d+)"),
    ("assert_config_engine.py", r"PASS\s+(\d+)\s+/\s+FAIL\s+(\d+)"),
    ("assert_api.py", r"PASS:\s+(\d+)/(\d+)"),
    ("l4_audit.py", r"合计：PASS\s+(\d+)\s+/\s+FAIL\s+(\d+)"),
]

env = dict(os.environ)
env["PYTHONUTF8"] = "1"
env["PYTHONIOENCODING"] = "utf-8"

results = []
total_pass = 0
total_fail = 0

print("=" * 80)
print(f"开始执行全量回归断言套件（共 {len(SCRIPTS)} 个脚本）")
print("=" * 80)

for idx, (script, pat) in enumerate(SCRIPTS, 1):
    path = os.path.join(BASE, script)
    if not os.path.exists(path):
        print(f"[{idx}/{len(SCRIPTS)}] 脚本缺失: {script}")
        results.append((script, -1, 0, 1, "文件不存在", 0))
        total_fail += 1
        continue

    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, script],
        cwd=BASE,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    elapsed = time.time() - t0

    out = proc.stdout + "\n" + proc.stderr
    
    pass_cnt = 0
    fail_cnt = 0
    m = re.search(pat, out)
    if m:
        groups = m.groups()
        if len(groups) == 2:
            if "/" in pat:
                pass_cnt = int(groups[0])
                total = int(groups[1])
                fail_cnt = max(0, total - pass_cnt)
            else:
                pass_cnt = int(groups[0])
                fail_cnt = int(groups[1])
        elif len(groups) == 1:
            pass_cnt = int(groups[0])
            fail_cnt = 0
    else:
        pass_cnt = len(re.findall(r"^\s*(?:\[PASS\]|PASS\b)", out, re.M))
        fail_cnt = len(re.findall(r"^\s*(?:\[FAIL\]|FAIL\b)", out, re.M))

    if proc.returncode != 0:
        fail_cnt = max(1, fail_cnt)

    status = "OK" if proc.returncode == 0 and fail_cnt == 0 else "FAIL"
    summary_line = ""
    for line in reversed(out.strip().splitlines()):
        if any(k in line for k in ("PASS", "FAIL", "通过", "完成", "合计")):
            summary_line = line.strip()
            break

    print(f"[{idx:2d}/{len(SCRIPTS)}] {script:<35} Exit={proc.returncode:<2} {status:<4} (P:{pass_cnt:<3} F:{fail_cnt:<2}) [{elapsed:4.2f}s] {summary_line[:40]}")
    results.append((script, proc.returncode, pass_cnt, fail_cnt, summary_line, elapsed))
    total_pass += pass_cnt
    total_fail += fail_cnt

print("=" * 80)
print(f"全量回归断言汇总: 脚本数 {len(SCRIPTS)} | 累计 PASS={total_pass} | 累计 FAIL={total_fail}")
all_clean = all(r[1] == 0 and r[3] == 0 for r in results)
print(f"最终判定: {'【全部放行 ALL PASS】' if all_clean else '【存在失败 HAS FAIL】'}")
print("=" * 80)

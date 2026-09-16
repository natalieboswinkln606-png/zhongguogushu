# -*- coding: utf-8 -*-
"""l4_strict_commit.py — 书写阶段强校验（v1.0）

规则：草稿提交前必须满足以下条件，否则禁止 commit（退出码非 0）
1. 五条不变量 PASS（check_invariants）
2. 对账 conflicts=0
3. 双源同引一致性 PASS（规则四）
4. 草稿首行必须包含 "# (snapshot-final)" 标签
5. 草稿必须引用 _t4_b_harvest.txt 搬运产物的 ≥ 30 行（引用区段约束）

用法：
  python l4_strict_commit.py --text <draft> --snap <snap> --harvest <harvest> [--rec <rec>]
"""
import argparse
import json
import os
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True, help="草稿 .txt 路径")
    ap.add_argument("--snap", required=True, help="snapshot .json 路径")
    ap.add_argument("--harvest", required=True, help="harvest 产物 .txt 路径")
    ap.add_argument("--rec", default=None, help="可选：指定 rec .json 路径")
    ap.add_argument("--min-harvest-lines", type=int, default=30, help="草稿至少引用 harvest 的行数")
    a = ap.parse_args()

    fails = []

    # 0. 文件存在性
    for p in (a.text, a.snap, a.harvest):
        if not os.path.exists(p):
            fails.append(f"文件不存在: {p}")

    if fails:
        for f in fails:
            print(f"FAIL  {f}")
        sys.exit(1)

    # 1. 跑 check_invariants
    print("[1/4] check_invariants ...")
    res_path = a.snap + ".check.json"
    r = subprocess.run(
        [sys.executable, "l4_audit_output.py", "check", "--snap", a.snap, "--out", res_path],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        fails.append(f"check_invariants 退出码 {r.returncode}（5条不变量未全过）")
        print(r.stdout)
        print(r.stderr)
    else:
        with open(res_path, encoding="utf-8") as f:
            ck = json.load(f)
        bad = [x for x in ck if not x.get("ok")]
        if bad:
            fails.append(f"check_invariants 失败条目: {[x['id'] for x in bad]}")
        else:
            print(f"  OK  5/5 PASS")

    # 2. 跑 reconcile
    print("[2/4] reconcile ...")
    rec_path = a.rec or (a.text + ".rec.json")
    r = subprocess.run(
        [sys.executable, "l4_audit_output.py", "reconcile",
         "--text", a.text, "--snap", a.snap, "--out", rec_path],
        capture_output=True, text=True
    )
    if r.returncode != 0 and r.returncode != 1:  # exit 1 = 仍有 conflict
        print(r.stdout)
        print(r.stderr)
        fails.append(f"reconcile 异常退出 {r.returncode}")
    else:
        with open(rec_path, encoding="utf-8") as f:
            rec = json.load(f)
        n_confl = len(rec.get("conflicts", []))
        n_unver = len(rec.get("unverified", []))
        n_match = len(rec.get("matched", []))
        print(f"  matched={n_match} unverified={n_unver} conflicts={n_confl}")
        if n_confl > 0:
            fails.append(f"reconcile conflicts={n_confl}（须清零）")
            for c in rec["conflicts"][:5]:
                print(f"    - {c.get('kind', '?')} {c.get('ganzhi', c.get('value', ''))}: {c.get('detail', '')[:120]}")
        # 双源同引专项
        dsm = [c for c in rec.get("conflicts", []) if c.get("kind") == "double_source_mismatch"]
        if dsm:
            fails.append(f"双源同引不一致 {len(dsm)} 条")

    # 3. 草稿首行 snapshot-final 标签
    print("[3/4] 草稿首行标签 ...")
    with open(a.text, encoding="utf-8") as f:
        head = f.read(500)
    if "(snapshot-final)" not in head:
        fails.append("草稿首部未含 '# (snapshot-final)' 标签")

    # 4. harvest 引用量
    print("[4/4] harvest 引用检查 ...")
    with open(a.text, encoding="utf-8") as f:
        draft_lines = f.readlines()
    with open(a.harvest, encoding="utf-8") as f:
        harvest_lines = [l.strip() for l in f if l.strip()]
    cited = 0
    for hl in harvest_lines:
        # 草稿行中包含 harvest 行的关键 token（去掉格式字符后 ≥5字）
        key = hl
        if len(key) >= 5:
            # 截取关键 token（避免 markdown 格式干扰）
            clean = key.replace("|", " ").replace("`", "").replace("#", "").strip()
            for dl in draft_lines:
                if clean[:15] in dl:
                    cited += 1
                    break
    print(f"  harvest 关键 token 引用: {cited}/{len(harvest_lines)} 行被草稿引用")
    if cited < min(len(harvest_lines), a.min_harvest_lines):
        fails.append(f"harvest 引用行数 {cited} 不足 {a.min_harvest_lines}（建议把搬运产物作为草稿附录）")

    # 总结
    print()
    if fails:
        print(f"STRICT COMMIT FAIL: {len(fails)} 项")
        for f in fails:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("STRICT COMMIT PASS：草稿可对外输出")
        sys.exit(0)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""assert_l4_audit_output_v3_rules.py — 验证 v3 新增规则五/六/七能抓出回归

测试三件事：
1. Rule 5（ws_score_drift）：草稿中写"21 分偏弱"应被抓出
2. Rule 6（ten_god_mismatch）：草稿中写"辛→戊偏财"应被抓出
3. Rule 7（age_year_mismatch）：草稿中写"20 岁 2025"应被抓出
4. 反向：合规草稿应 conflicts=0
"""
import json
import os
import subprocess
import sys

SNAP = "temp/_t4_b_snap_v3.json"
FAKE = "temp/_test_v3_dirty.txt"
CLEAN = "temp/_test_v3_clean.txt"


def run_reconcile(text_path):
    out = text_path + ".rec.json"
    r = subprocess.run(
        [sys.executable, "l4_audit_output.py", "reconcile",
         "--text", text_path, "--snap", SNAP, "--out", out],
        capture_output=True, text=True
    )
    with open(out, encoding="utf-8") as f:
        rec = json.load(f)
    return rec


def test_rule5_ws_score_drift():
    """Rule 5 抓 ws_score_drift"""
    body = """# 测试：写错的旺衰分值
日主辛金偏弱（21 分），呼吸系统需注意
"""
    with open(FAKE, "w", encoding="utf-8") as f:
        f.write(body)
    rec = run_reconcile(FAKE)
    drifts = [c for c in rec["conflicts"] if c["kind"] == "ws_score_drift"]
    assert drifts, f"Rule 5 应抓出 ws_score_drift，但 conflicts 为空: {rec['conflicts']}"
    assert any(c["claimed_score"] == 21.0 for c in drifts), \
        f"Rule 5 抓出但 score 不对: {drifts}"
    print("  PASS  Rule 5 ws_score_drift 抓到 21 分偏弱")


def test_rule6_ten_god_mismatch():
    """Rule 6 抓 ten_god_mismatch（辛日见戊应为正印）"""
    body = """# 测试：日主辛金，藏干戊应为正印不是偏财
戌本气戊偏财
"""
    with open(FAKE, "w", encoding="utf-8") as f:
        f.write(body)
    rec = run_reconcile(FAKE)
    mism = [c for c in rec["conflicts"] if c["kind"] == "ten_god_mismatch"]
    assert mism, f"Rule 6 应抓出 ten_god_mismatch，但 conflicts 为空: {rec['conflicts']}"
    assert any(c["canggan"] == "戊" and c["claimed_god"] == "偏财" for c in mism), \
        f"Rule 6 抓出但不对: {mism}"
    print("  PASS  Rule 6 ten_god_mismatch 抓到辛日戊偏财（应为正印）")


def test_rule7_age_year_mismatch():
    """Rule 7 抓 age_year_mismatch"""
    body = """# 测试：20岁2025 应为 21 岁（2005+20=2025 实际 2005+20=2025是21岁）
20 岁 2025 转折
"""
    with open(FAKE, "w", encoding="utf-8") as f:
        f.write(body)
    rec = run_reconcile(FAKE)
    mis = [c for c in rec["conflicts"] if c["kind"] == "age_year_mismatch"]
    assert mis, f"Rule 7 应抓出 age_year_mismatch，但 conflicts 为空: {rec['conflicts']}"
    print("  PASS  Rule 7 age_year_mismatch 抓到 20岁2025（应为21岁）")


def test_clean_text_no_conflict():
    """反向：草稿用区间格式"6-15 岁(2011-2020)"应不被误报"""
    body = """# 测试：合法格式
6-15 岁(2011-2020) 学业期
辛金得地 5 分（年酉临官2分+时酉临官2分）
日主辛金中和（55.8 分）
"""
    with open(CLEAN, "w", encoding="utf-8") as f:
        f.write(body)
    rec = run_reconcile(CLEAN)
    # 区间端点 "15 岁" 不该被抓
    bad = [c for c in rec["conflicts"]
           if c.get("kind") in ("age_year_mismatch", "ws_score_drift")]
    assert not bad, f"合法格式应 0 误报，但抓到: {bad}"
    print("  PASS  合法格式无 ws_score_drift / age_year_mismatch 误报")


def main():
    if not os.path.exists(SNAP):
        print(f"FAIL  缺 snap: {SNAP}")
        sys.exit(1)
    print("[S-01] Rule 5 ws_score_drift 抓回归 ...")
    test_rule5_ws_score_drift()
    print("[S-02] Rule 6 ten_god_mismatch 抓回归 ...")
    test_rule6_ten_god_mismatch()
    print("[S-03] Rule 7 age_year_mismatch 抓回归 ...")
    test_rule7_age_year_mismatch()
    print("[S-04] 合法格式 0 误报 ...")
    test_clean_text_no_conflict()
    # 清理
    for p in (FAKE, CLEAN, FAKE + ".rec.json", CLEAN + ".rec.json"):
        if os.path.exists(p):
            os.remove(p)
    print("\nALL PASS — v3 新增规则五/六/七通过回归测试")


if __name__ == "__main__":
    main()

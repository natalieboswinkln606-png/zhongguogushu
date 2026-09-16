# -*- coding: utf-8 -*-
"""temp/qm_audit.py — 独立对抗审查：定局手工核对 + 易安居实时对拍复核 L3-001~004。
只读只测，不碰仓库文件。"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import l3_qimen as Q

# ============ 一、定局手工核对（独立推算，锚点 2024-02-10=甲辰(60序40)、2024-01-01=甲子(0)） ============
# (输入, (节气, 阴阳遁, 上中下, 局数))
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
fails = 0
for ts, want in CASES:
    d = Q.compute(datetime.strptime(ts, "%Y-%m-%d %H:%M"))["dingju"]
    got = (d["term"], d["dun"], d["yuan"], d["ju"])
    ok = got == want
    fails += 0 if ok else 1
    print(f"  {'OK ' if ok else 'FAIL'} {ts} 期望 {want} 实得 {got}")
print(f"定局手工核对: {len(CASES)-fails}/{len(CASES)} 通过")

# ============ 二、易安居实时对拍复核（L3-001~004 落宫一致性与锚点） ============
print("\n=== 易安居实时复核 ===")
import requests
s = requests.Session()
s.get("https://www.zhouyi.cc/zhouyi/qmdj/", timeout=30)

def fetch(t):
    d = {"cboYear": str(t[0]), "cboMonth": str(t[1]), "cboDay": str(t[2]),
         "cboHour": f"{t[3]}-{Q.ZHI[(t[3] + 1) // 2 % 12]}", "cboMinute": str(t[4]),
         "pid": "", "cid": "", "diname": "某人", "thing": "", "rdoSex": "1", "data_type": "0", "rdoPanShi": "0"}
    html = s.post("https://www.zhouyi.cc/zhouyi/qmdj/QiMen.php", data=d, timeout=30).content.decode("utf-8-sig")
    m = re.search(r"※\s*([^<]*?)(?:<|　|$)", html)
    m2 = re.search(r"★\s*([^<]{2,80})", html)
    return (m.group(1).strip() if m else ""), (m2.group(1).strip() if m2 else "")

DIVERGE = [(2011, 6, 29, 14, 0), (2036, 6, 3, 10, 0), (1952, 5, 20, 10, 0), (1995, 11, 26, 10, 0)]
EXP = {  # 自研：旬首(六仪宫) 值符星落宫 值使门落宫 ; oracle 申报值符星
    (2011, 6, 29, 14, 0): ("甲戌", "天芮", 7, "死门", 2, "天蓬", 2),
    (2036, 6, 3, 10, 0): ("甲申", "天辅", 7, "杜门", 4, "天禽", 4),
    (1952, 5, 20, 10, 0): ("甲申", "天心", 9, "开门", 6, "天柱", 6),
    (1995, 11, 26, 10, 0): ("甲申", "天英", 6, "景门", 9, "天任", 9),
}
for t in DIVERGE:
    ju, zf = fetch(t)
    r = Q.compute(datetime(*t))
    zz = r["zhifu_zhishi"]
    xun, star, sp, door, rp, ostar, orp = EXP[t]
    m1 = re.search(r"直符(.{1,3})落(\d)", zf)
    m2 = re.search(r"直使(.{1,3})落(\d)", zf)
    ok = all([
        zz["xunshou"] == xun, zz["zhifu_star"] == star, zz["zhifu_palace"] == sp,
        zz["zhishi_door"] == door, zz["zhishi_palace"] == rp,
        m1 and m1.group(2) == str(sp),      # oracle 值符落宫 == 自研
        m2 and m2.group(2) == str(rp),      # oracle 值使落宫 == 自研（恰好抵消关键）
        m1 and re.sub(r"禽", "", m1.group(1)) != star,  # oracle 星名确实错位
    ])
    print(f"  {'OK ' if ok else 'FAIL'} {t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:00")
    print(f"      自研: 旬首{zz['xunshou']} 值符{zz['zhifu_star']}落{zz['zhifu_palace']} 值使{zz['zhishi_door']}落{zz['zhishi_palace']}")
    print(f"      oracle 定局[{ju}] 值符[{zf}]")
    fails += 0 if ok else 1

# 锚点抽查（局数/值符/值使三字段）
for t, want in [((2024, 2, 10, 8, 0), "阳遁2局"), ((2024, 7, 1, 12, 0), "阴遁9局")]:
    ju, zf = fetch(t)
    print(f"  anchor {t} → oracle[{ju}] 期望[{want}] {'OK' if want in ju else 'FAIL'}")
    fails += 0 if want in ju else 1

print(f"\n总结果: {'PASS 全部通过' if fails == 0 else f'{fails} 项 FAIL'}")

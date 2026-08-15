# -*- coding: utf-8 -*-
"""assert_l3_heluolishu.py — L3 河洛理数断言（hlyl-01..hlyl-05）。
覆盖：5 手工锚点全链（四柱+天数/地数+卦+元堂）、天干 10 干/地支 12 支取数全查、
取卦余数边界（0 取坤/8 取乾）、先天序全查、身命卦 3 例、大运 2 例（男顺女逆+阳9阴6+变卦）、
流年卦 2 例、64 卦表完整性、JSON 项 rule_id/source、oracle 复现 2 样本、申报幂等。
运行：PYTHONIOENCODING=utf-8 python assert_l3_heluolishu.py
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime
import l3_heluolishu as h

BASE = os.path.dirname(os.path.abspath(__file__))
CHECKS = []


def check(name, fn):
    try:
        fn()
        print(f"  PASS {name}")
        CHECKS.append(True)
    except AssertionError as e:
        print(f"  FAIL {name}: {e}")
        CHECKS.append(False)


def C(t, gender="男", lon=120.0):
    r = h.compute(datetime(*t), gender, lon)
    assert "error" not in r, r
    return r


# --- 5 手工锚点全链（手算见 l3_heluolishu.py docstring；与 oracle 对拍见 report） ---
# (时间, 性别, 经度, 四柱, 天数, 地数, 命卦, 元堂爻位)
ANCHORS = [((1990, 12, 19, 12, 0), "男", 121.51, "庚午戊子戊午戊午", 51, 8, "火地晋", 3),
           ((1988, 3, 15, 9, 0), "女", 121.51, "戊辰乙卯己巳戊辰", 29, 18, "风泽中孚", 6),
           ((2000, 1, 1, 8, 0), "男", 120.0, "己卯丙子戊午丙辰", 51, 6, "火水未济", 3),
           ((1965, 7, 20, 14, 0), "女", 120.0, "乙巳癸未乙亥癸未", 10, 40, "泽地萃", 4),
           ((2024, 6, 11, 12, 0), "男", 120.0, "甲辰庚午丙午甲午", 57, 8, "天地否", 3)]


def test_anchors():
    for t, gender, lon, gz, ts, ds, gua, yp in ANCHORS:
        r = C(t, gender, lon)
        got_gz = "".join(r["pillars"][k]["ganzhi"] for k in ("year", "month", "day", "hour"))
        assert got_gz == gz, f"{t} 四柱 {got_gz} != {gz}"
        assert r["hlyl01"]["tianshu"] == ts, f"{t} 天数 {r['hlyl01']['tianshu']} != {ts}"
        assert r["hlyl01"]["dishu"] == ds, f"{t} 地数 {r['hlyl01']['dishu']} != {ds}"
        assert r["hlyl02"]["ming_gua"] == gua, f"{t} 命卦 {r['hlyl02']['ming_gua']} != {gua}"
        assert r["hlyl03"]["yuan_yao"]["pos"] == yp, f"{t} 元堂爻 {r['hlyl03']['yuan_yao']['pos']} != {yp}"


def test_gan_shu_full():
    want = {"甲": 9, "己": 9, "乙": 8, "庚": 8, "丙": 7, "辛": 7, "丁": 6, "壬": 6, "戊": 5, "癸": 5}
    assert len(h.GAN_SHU) == 10, f"天干表应 10 干，实 {len(h.GAN_SHU)}"
    for g, v in want.items():
        assert h.GAN_SHU[g] == v, f"天干 {g} 应 {v}，实 {h.GAN_SHU[g]}"


def test_zhi_shu_full():
    want = {"子": 9, "午": 9, "丑": 8, "未": 8, "寅": 7, "申": 7, "卯": 6, "酉": 6,
            "辰": 5, "戌": 5, "巳": 4, "亥": 4}
    assert len(h.ZHI_SHU) == 12, f"地支表应 12 支，实 {len(h.ZHI_SHU)}"
    for z, v in want.items():
        assert h.ZHI_SHU[z] == v, f"地支 {z} 应 {v}，实 {h.ZHI_SHU[z]}"


def test_qu_gua_boundary():
    # 余数边界：8→坤（余0）、9→乾（余1）、16→坤、17→乾、1→乾、7→艮
    assert h.qu_gua(8, 8)["ming_gua"] == "坤为地", "8%8=0 应取坤"
    assert h.qu_gua(9, 9)["ming_gua"] == "乾为天", "9%8=1 应取乾"
    assert h.qu_gua(16, 16)["ming_gua"] == "坤为地", "16%8=0 应取坤"
    assert h.qu_gua(17, 17)["ming_gua"] == "乾为天", "17%8=1 应取乾"
    r = h.qu_gua(1, 1)
    assert r["shang_gua"] == "乾" and r["shang_shu"] == 1, "天数 1 → 乾 1"
    r = h.qu_gua(7, 7)
    assert r["shang_gua"] == "艮" and r["shang_shu"] == 7, "天数 7 → 艮 7"


def test_xiantian_order():
    assert h.XIANTIAN == ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"], "先天八卦序错"
    for i, g in enumerate(h.XIANTIAN, 1):
        assert h.XIANTIAN_SH[g] == i, f"{g} 序应 {i}"


def test_shen_ming_gua():
    # 身卦=元堂爻变卦（后天卦）：A1 晋九三变→火山旅；A2 中孚上九变→水泽节；A5 否九三变→天山遁
    r = C((1990, 12, 19, 12, 0), "男", 121.51)
    assert r["hlyl03"]["shen_gua"]["shen_gua"] == "火山旅", "晋九三变应=火山旅"
    r = C((1988, 3, 15, 9, 0), "女", 121.51)
    assert r["hlyl03"]["shen_gua"]["shen_gua"] == "水泽节", "中孚上九变应=水泽节"
    r = C((2024, 6, 11, 12, 0), "男")
    assert r["hlyl03"]["shen_gua"]["shen_gua"] == "天山遁", "否九三变应=天山遁"


def test_dayun():
    # A1 男顺：爻序 3,4,5,6,1,2；晋爻阴阳 阴阴阴阳阴阳 → 年数 6,9,6,9,6,6（阳9阴6）；首运=爻3动变卦=火山旅
    r = C((1990, 12, 19, 12, 0), "男", 121.51)
    it = r["hlyl04"]["dayun"]["items"]
    assert [x["pos"] for x in it] == [3, 4, 5, 6, 1, 2], "男命应顺从元堂爻 3→4→5→6→1→2"
    assert [x["years"] for x in it] == [6, 9, 6, 9, 6, 6], "晋爻阴阳 阴阴阴阳阴阳 → 6,9,6,9,6,6"
    assert it[0]["gua"] == "火山旅", "第 1 运=晋九三变卦应=火山旅"
    assert it[0]["start"] == 1990 and it[-1]["end"] == 2031, "A1 大运 1990-2031（42 年）"
    # A2 女逆：爻序 6,5,4,3,2,1；中孚爻阴阳 阳阳阴阴阳阳 → 9,9,6,6,9,9（48 年）
    r = C((1988, 3, 15, 9, 0), "女", 121.51)
    it = r["hlyl04"]["dayun"]["items"]
    assert [x["pos"] for x in it] == [6, 5, 4, 3, 2, 1], "女命应逆从元堂爻 6→5→4→3→2→1"
    assert [x["years"] for x in it] == [9, 9, 6, 6, 9, 9], "中孚爻阴阳 阳阳阴阴阳阳 → 9,9,6,6,9,9"
    assert it[-1]["end"] == 2035, "A2 大运 1988-2035（48 年）"


def test_liunian():
    # 流年卦（流年干支起卦）：2024 甲辰（甲9辰5，天14 地0）→ 上坎下坤=水地比；2025 乙巳（乙8巳4，天0 地12）→ 上坤下震=地雷复
    r = h.liunian_gua("甲辰")
    assert r["ming_gua"] == "水地比", f"2024 甲辰流年应=水地比，实 {r['ming_gua']}"
    r = h.liunian_gua("乙巳")
    assert r["ming_gua"] == "地雷复", f"2025 乙巳流年应=地雷复，实 {r['ming_gua']}"
    r = C((2024, 6, 11, 12, 0))
    assert r["hlyl04"]["liunian_10y"][0] == {"year": 2024, "ganzhi": "甲辰", "gua": "水地比",
                                             "shang": "坎", "xia": "坤"}, "未来 10 年首年=2024 水地比"
    assert len(r["hlyl04"]["liunian_10y"]) == 10, "应输出未来 10 年逐年卦"


def test_json_rule_id_source():
    r = C((2024, 6, 11, 12, 0))
    for key in ("hlyl01", "hlyl02", "hlyl03", "hlyl05"):
        item = r[key]
        rid = item["rule_id"] if "rule_id" in item else item["yuan_yao"]["rule_id"]
        assert rid.startswith("hlyl-"), f"{key} rule_id 应 hlyl- 前缀"
        src = item["source"] if "source" in item else item["yuan_yao"]["source"]
        assert src, f"{key} 缺 source"
    assert r["hlyl04"]["dayun"]["rule_id"] == "hlyl-04" and r["hlyl04"]["dayun"]["source"], "hlyl-04 需 rule_id/source"
    assert "非神断" in r["hlyl05"]["source"], "hlyl-05 须注明规则启发式，非神断"
    assert r["hlyl05"]["rule_id"] == "hlyl-05" and r["hlyl05"]["guaci"], "hlyl-05 需卦辞"


def test_guaci_table():
    assert len(h.GUANAME) == 64, f"64 卦名表应 64 项，实 {len(h.GUANAME)}"
    assert len(set(h.GUANAME.values())) == 64, "64 卦名应互异"
    assert len(h.GUACI) == 64, f"卦辞应 64 条，实 {len(h.GUACI)}"
    assert h.GUACI["乾为天"] == "元亨利贞", "乾卦辞应=元亨利贞"
    assert h.GUACI["地天泰"] == "小往大来，吉亨", "泰卦辞抽点"
    for name in h.GUANAME.values():
        assert name in h.GUACI, f"缺卦辞 {name}"


def test_oracle_school():
    # oracle 复现两样本：28/12→雷地豫（男，元堂1=初六，后卦=震为雷）；31/32→地天泰（女，元堂2=九二，后卦=火地晋）
    p1 = {"year": {"ganzhi": "庚午"}, "month": {"ganzhi": "戊子"},
          "day": {"ganzhi": "戊午"}, "hour": {"ganzhi": "戊午"}}
    o = h.oracle_school(p1, "男")
    assert o["tianshu"] == 28 and o["dishu"] == 12, f"样本1 天数地数 28/12，实 {o['tianshu']}/{o['dishu']}"
    assert o["gua"] == "雷地豫" and o["yuan_pos"] == 1, f"样本1 应=雷地豫 元堂爻1，实 {o['gua']} 爻{o['yuan_pos']}"
    assert o["ht_gua"] == "震为雷", f"样本1 后天卦应=震为雷，实 {o['ht_gua']}"
    p2 = {"year": {"ganzhi": "戊辰"}, "month": {"ganzhi": "乙卯"},
          "day": {"ganzhi": "己巳"}, "hour": {"ganzhi": "戊辰"}}
    o = h.oracle_school(p2, "女")
    assert o["tianshu"] == 31 and o["dishu"] == 32, f"样本2 天数地数 31/32，实 {o['tianshu']}/{o['dishu']}"
    assert o["gua"] == "地天泰" and o["yuan_pos"] == 2, f"样本2 应=地天泰 元堂爻2，实 {o['gua']} 爻{o['yuan_pos']}"
    assert o["ht_gua"] == "火地晋", f"样本2 后天卦应=火地晋，实 {o['ht_gua']}"
    assert o["ht_pos"] == 5, "后天元堂=先天元堂+3：2+3=5"


def test_idempotent_rows():
    # 申报幂等：hlyl- 行 case_id 唯一（compare 重跑不重复）
    for fn in ("data/arbitration_log.csv", "report/boundary_cases.csv"):
        try:
            rows = [r["case_id"] for r in csv.DictReader(open(os.path.join(BASE, fn), encoding="utf-8"))
                    if r.get("case_id") and r["case_id"].startswith("hlyl-")]
        except FileNotFoundError:
            continue
        assert len(rows) == len(set(rows)), f"{fn} hlyl- 行 case_id 重复"


def test_yuan_yao_boundary():
    # 元堂余 0 取 6：A2 女地数 18%6=0 → 爻 6（上爻）
    r = C((1988, 3, 15, 9, 0), "女", 121.51)
    assert r["hlyl03"]["yuan_yao"]["pos"] == 6, "地数 18%6=0 应取上爻 6"
    # 男取天数：A1 51%6=3
    r = C((1990, 12, 19, 12, 0), "男", 121.51)
    assert r["hlyl03"]["yuan_yao"]["pos"] == 3, "天数 51%6=3"


for name, fn in [("5 锚点全链（四柱+天地数+卦+元堂）", test_anchors),
                 ("天干 10 干取数全查", test_gan_shu_full),
                 ("地支 12 支取数全查", test_zhi_shu_full),
                 ("取卦余数边界（0 取坤/8 取乾）", test_qu_gua_boundary),
                 ("先天八卦序全查", test_xiantian_order),
                 ("身命卦 3 例（晋→旅/中孚→节/否→遁）", test_shen_ming_gua),
                 ("大运 2 例（男顺女逆+阳9阴6+变卦）", test_dayun),
                 ("流年卦 2 例（甲辰→水地比/乙巳→地雷复）", test_liunian),
                 ("JSON 每项 rule_id/source+非神断注", test_json_rule_id_source),
                 ("64 卦表完整性+卦辞抽点", test_guaci_table),
                 ("oracle 复现 2 样本（28/12→豫、31/32→泰）", test_oracle_school),
                 ("申报幂等（hlyl- 行唯一）", test_idempotent_rows),
                 ("元堂余 0 取上爻边界", test_yuan_yao_boundary)]:
    check(name, fn)
print(f"\nassert_l3_heluolishu: {sum(CHECKS)}/{len(CHECKS)} PASS")
sys.exit(0 if all(CHECKS) else 1)

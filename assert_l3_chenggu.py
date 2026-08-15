# -*- coding: utf-8 -*-
"""assert_l3_chenggu.py — L3-3 称骨算命断言（Rule-ID cg-01..cg-03）。
覆盖：5 锚点公历全链路手算、60 干支/12 月/30 日/12 时表全覆盖、进位与 fmt 边界、
断语档 21~71 男/女全覆盖、农历年口径（春节前归上一年）、输出结构、幂等。
运行：PYTHONIOENCODING=utf-8 python assert_l3_chenggu.py"""
import json, sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import l3_chenggu as c

P = F = 0


def ok(name, cond, detail=""):
    global P, F
    if cond:
        P += 1
        print(f"  PASS  {name}" + (f"  [{detail}]" if detail else ""))
    else:
        F += 1
        print(f"  FAIL  {name}" + (f"  [{detail}]" if detail else ""))


print("【1】5 锚点公历全链路手算（公历→农历→四值→总和→断语档）")
# (datetime, 期望总钱数, 期望年干支, 期望月序, 期望日序, 期望时支, 说明)
anchors = [
    (datetime(1984, 2, 2, 10, 0), 39, "甲子", 1, 1, "巳", "甲子年正月初一巳时（春节换年）"),
    (datetime(1984, 2, 1, 6, 0), 27, "癸亥", 12, 30, "卯", "癸亥年腊月三十卯时（春节前归上一年）"),
    (datetime(1990, 6, 7, 14, 0), 32, "庚午", 5, 15, "未", "庚午年五月十五未时"),
    (datetime(2000, 8, 2, 2, 0), 35, "庚辰", 7, 3, "丑", "庚辰年七月初三丑时"),
    (datetime(1963, 4, 13, 18, 0), 54, "癸卯", 3, 20, "酉", "癸卯年三月二十酉时（二十日=1两5钱通行版）"),
]
for dt, exp, yg, lmo, lday, hz, note in anchors:
    r = c.compute(dt)
    if "error" in r:
        ok(note, False, r["error"])
        continue
    tot = r["total"]["qian"] + r["total"]["liang"] * 10
    ok(note + f" 总骨重={c.fmt(tot)}", tot == exp, f"期望 {c.fmt(exp)}")
    ok(note + " 年干支=" + r["lunar"]["year_ganzhi"], r["lunar"]["year_ganzhi"] == yg)
    ok(note + " 月名", r["lunar"]["month_name"] == c.MONTH_CN[lmo - 1] + "月", r["lunar"]["month_name"])
    ok(note + " 日序", r["lunar"]["day"] == lday)
    ok(note + " 时支", r["bones"]["hour"]["key"] == hz + "时")
    ok(note + " 四值求和=总（cg-02）",
       r["bones"]["year"]["qian"] + r["bones"]["month"]["qian"] + r["bones"]["day"]["qian"] + r["bones"]["hour"]["qian"] == tot)
    ok(note + " 断语档=总骨重（cg-03）", r["poem"]["level"] == r["total"]["weight"])

print("【2】表全覆盖与取值范围")
ok("年骨重表 60 干支全键", len(c.YEAR_BONE) == 60)
ok("年骨重表值域 1~19 钱", all(1 <= v <= 19 for v in c.YEAR_BONE.values()))
ok("月骨重表 12 行", len(c.MONTH_BONE) == 12)
ok("日骨重表 30 行", len(c.DAY_BONE) == 30)
ok("时骨重表 12 行", len(c.HOUR_BONE) == 12)
ok("月/日/时骨重值域 1~18 钱", all(1 <= v <= 18 for v in c.MONTH_BONE + c.DAY_BONE + c.HOUR_BONE))
ok("时骨重子时=一两六钱（16 钱）", c.HOUR_BONE[0] == 16)

print("【3】进位与 fmt 边界")
ok("fmt(11)=1两1钱", c.fmt(11) == "1两1钱")
ok("fmt(10)=1两（整两省略钱）", c.fmt(10) == "1两")
ok("fmt(6)=6钱（纯钱省略两）", c.fmt(6) == "6钱")
ok("fmt(61)=6两1钱（跨 6 两进位）", c.fmt(61) == "6两1钱")
ok("总骨重上限=7两1钱（19+18+18+16=71）", 19 + 18 + 18 + 16 == 71 and c.fmt(71) == "7两1钱")
ok("年骨重最大值 19 钱（戊午/己卯）", sorted(v for v in c.YEAR_BONE.values())[-1] == 19)

print("【4】断语档全覆盖")
ok("男命 21~71 全档", all(k in c.MALE for k in range(21, 72)))
ok("女命 21~71 全档 + 7.2 异文档", all(k in c.FEMALE for k in range(21, 72)) and 72 in c.FEMALE)
ok("男命异文标注仅 3.6/3.9 两档", set(c.MALE_ALT) == {36, 39})
ok("所有断语非空且含句号", all(len(v) > 10 and "。" in v for v in list(c.MALE.values()) + list(c.FEMALE.values())))
ok("男女断语两套独立（同档不同诗）", all(c.MALE[k] != c.FEMALE[k] for k in range(21, 72)))

print("【5】农历年口径（春节前归上一年）")
r = c.compute(datetime(2022, 1, 24, 12, 0))  # 2022-01-24 辛丑年腊月廿二（春节 2/1 前）——astrologybazi 对拍样本 2
ok("2022-01-24 → 辛丑年（非壬寅）", r["lunar"]["year_ganzhi"] == "辛丑", r["lunar"]["year_ganzhi"])
ok("样本2 总骨重=3两1钱（与 astrologybazi 全链一致）", c.fmt(r["total"]["qian"] + r["total"]["liang"] * 10) == "3两1钱")

print("【6】输出结构（rule_id/source/alt 逐项标注）")
r = c.compute(datetime(1984, 2, 2, 10, 0))
ok("四值均带 rule_id=cg-01", all(b["rule_id"] == "cg-01" for b in r["bones"].values()))
ok("总骨重 rule_id=cg-02", r["total"]["rule_id"] == "cg-02")
ok("断语 rule_id=cg-03", r["poem"]["rule_id"] == "cg-03")
ok("全部输出项带 source+alt", all("source" in b and "alt" in b for b in r["bones"].values())
   and "source" in r["total"] and "source" in r["poem"] and "alt" in r["poem"])
ok("底本声明含『托名袁天罡』", any("托名袁天罡" in n for n in r["notes"]))
ok("年骨重 alt 声明立春年异文", "立春" in r["bones"]["year"]["alt"])
ok("日骨重 alt 声明二十日异文", "二十日" in r["bones"]["day"]["alt"])
ok("时骨重 alt 声明早子晚子异文", "早子" in r["bones"]["hour"]["alt"])
ok("男命 3.6 档 alt 标注 astrologybazi 对调", "此命终身运不通" in c.compute(datetime(1985, 1, 9, 12, 0))["poem"]["alt"])

print("【7】幂等")
r1 = c.compute(datetime(2000, 8, 2, 2, 0))
r2 = c.compute(datetime(2000, 8, 2, 2, 0))
ok("同输入两次 compute 结果完全一致", json.dumps(r1, ensure_ascii=False) == json.dumps(r2, ensure_ascii=False))

print(f"\n断言统计: PASS {P} | FAIL {F}")
sys.exit(1 if F else 0)

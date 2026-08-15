# -*- coding: utf-8 -*-
"""assert_l3_meihua.py — L3-梅花 梅花易数模块独立断言（手算锚点，不联网，幂等）
23 条断言：
  A. 起卦三法全链 6 例（1988-06-15 14:00 时间全链；报数 8,15 / 3,7,5；字数 4 / 5 字）
  B. 体用生克五态 5 例手算（比和/用生体/体克用/体生用/用克体）
  C. 互变卦独立 2 例（expand 手算）
  D. 时间起卦边界 2 例（2100-12-31 上限；1958-02-14 立春后春节前年支口径）
  E. 数据表完整性 2 条（GUA64/GUACI/IMAGE；DUAN×CATEGORIES/NAME_BY）
  F. 四季旺衰囚/死 4 例（通行《五行大义》四时休王：克旺者囚、旺克者死）
  G. 字数起卦方向 2 例（主表上少下多原著口径 vs more_up 异文上多下少）
运行: PYTHONIOENCODING=utf-8 python assert_l3_meihua.py
"""
import sys
from datetime import datetime
import l3_meihua as mh

PASS = FAIL = 0


def chk(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS {name}")
    else:
        FAIL += 1
        print(f"FAIL {name} {detail}")


def gua3(r):
    """排盘 JSON → (本卦, 互卦, 变卦, 动爻)。"""
    return (r["ben_gua"]["name"], r["hu_gua"]["name"], r["bian_gua"]["name"], r["dong"])


# ================= A. 起卦三法全链（5 锚点） =================

# A1 时间起卦全链 1988-06-15 14:00（oracle 已验证 + 手算：辰5+五5+初二2=12→4震；+未8=20→4震；20%6=2）
r = mh.compute_time(datetime(1988, 6, 15, 14, 0))
chk("A1 时间起卦 1988-06-15 14:00 全链", gua3(r) == ("震为雷", "水山蹇", "雷泽归妹", 2), str(gua3(r)))
chk("A1b 换算链 年支5(辰) 农历5月2日 时支8(未) 和12/20",
    r["chain"]["year_zhi"] == 5 and r["chain"]["lunar_month"] == 5 and r["chain"]["lunar_day"] == 2
    and r["chain"]["hour_zhi"] == 8 and r["chain"]["sum_up"] == 12 and r["chain"]["sum_down"] == 20,
    str({k: r["chain"][k] for k in ("year_zhi", "lunar_month", "lunar_day", "hour_zhi", "sum_up", "sum_down")}))

# A2 报数 8,15：上8→坤 下15%8=7→艮 动23%6=5 → 地山谦
r = mh.compute_numbers([8, 15], datetime(2026, 8, 16, 5, 37))
chk("A2 报数 8,15 地山谦/雷水解/水山蹇 动5", gua3(r) == ("地山谦", "雷水解", "水山蹇", 5), str(gua3(r)))

# A3 报数 3,7,5：第三数为动爻 5 → 火山旅
r = mh.compute_numbers([3, 7, 5], datetime(2026, 8, 16, 5, 37))
chk("A3 报数 3,7,5 火山旅/泽风大过/天山遁 动5(第三数)", gua3(r) == ("火山旅", "泽风大过", "天山遁", 5), str(gua3(r)))

# A4 字数 4：上2兑 下2兑 动4 → 兑为泽
r = mh.compute_words("今日大吉", datetime(2026, 8, 16, 5, 37))
chk("A4 字数4 兑为泽/风火家人/水泽节 动4", gua3(r) == ("兑为泽", "风火家人", "水泽节", 4), str(gua3(r)))

# A5 字数 5：主表上2兑 下3离（原著『少一字为上卦』）动5 → 泽火革
r = mh.compute_words("梅花易数占", datetime(2026, 8, 16, 5, 37))
chk("A5 字数5 泽火革/天风姤/雷火丰 动5(上少下多原著口径)", gua3(r) == ("泽火革", "天风姤", "雷火丰", 5), str(gua3(r)))


# ================= B. 体用生克五态（5 例手算） =================

def tiy(r):
    t = r["ti_yong"]
    return (t["name"], t["verdict"], t["relation"], t["ti"]["gua"], t["yong"]["gua"],
            t["ti"]["side"], t["yong"]["side"])

# B1 比和（吉）：震为雷 动2 在下卦 → 用=震木 体=震木 → 比和
r = mh.compute_time(datetime(1988, 6, 15, 14, 0))
chk("B1 震为雷 动2 体用比和 吉",
    tiy(r)[:3] == ("体用比和", "吉", "比和") and tiy(r)[3:5] == ("震", "震"), str(tiy(r)))

# B2 用生体（吉）：火山旅 动5 在上卦 → 用=离火 体=艮土 → 火生土 → 用生体
r = mh.compute_numbers([3, 7, 5], datetime(2026, 8, 16, 5, 37))
chk("B2 火山旅 动5 用生体 吉(火生土)",
    tiy(r)[:3] == ("用生体", "吉", "生") and tiy(r)[3:5] == ("艮", "离") and tiy(r)[6] == "上卦", str(tiy(r)))

# B3 用克体（凶）：天火同人 动2 在下卦 → 用=离火 体=乾金 → 火克金 → 用克体
r = mh.compute_numbers([1, 3, 2], datetime(2026, 8, 16, 5, 37))
chk("B3 天火同人 动2 用克体 凶(火克金)",
    gua3(r)[0] == "天火同人" and tiy(r)[:3] == ("用克体", "凶", "克") and tiy(r)[3:5] == ("乾", "离"), str(tiy(r)))

# B4 体生用（耗泄）：地天泰 动3 在下卦 → 用=乾金 体=坤土 → 土生金 → 体生用
r = mh.compute_numbers([8, 1], datetime(2026, 8, 16, 5, 37))
chk("B4 地天泰 动3 体生用 耗泄(土生金)",
    gua3(r)[0] == "地天泰" and tiy(r)[:3] == ("体生用", "耗泄", "泄") and tiy(r)[3:5] == ("坤", "乾"), str(tiy(r)))

# B5 体克用（中吉）：风地观 动1 在下卦 → 用=坤土 体=巽木 → 木克土 → 体克用
r = mh.compute_numbers([5, 8], datetime(2026, 8, 16, 5, 37))
chk("B5 风地观 动1 体克用 中吉(木克土)",
    gua3(r)[0] == "风地观" and tiy(r)[:3] == ("体克用", "中吉", "耗") and tiy(r)[3:5] == ("巽", "坤"), str(tiy(r)))


# ================= C. 互变卦独立 2 例（expand 手算） =================

# C1 地天泰 动3：爻象 阳阳阳|阴阴阴 → 动3 下卦乾三爻阳变阴 → 下兑 → 地泽临；
#    互卦 二三四爻=阳阳阴(兑) 三四五爻=阳阴阴(震) → 雷泽归妹
ben, hu, bian, dong = mh.expand(8, 1, 3)
chk("C1 expand(8,1,3) 地天泰 互雷泽归妹 变地泽临",
    (ben["name"], hu["name"], bian["name"], dong) == ("地天泰", "雷泽归妹", "地泽临", 3),
    f"{ben['name']}/{hu['name']}/{bian['name']} 动{dong}")

# C2 火山旅 动5：爻象 阴阴阳|阳阴阳 → 动5 上卦离中爻阳变阴 → 上坤 → 天山遁；
#    互卦 二三四爻=阴阳阳(巽) 三四五爻=阳阳阴(兑) → 泽风大过
ben, hu, bian, dong = mh.expand(3, 7, 5)
chk("C2 expand(3,7,5) 火山旅 互泽风大过 变天山遁",
    (ben["name"], hu["name"], bian["name"], dong) == ("火山旅", "泽风大过", "天山遁", 5),
    f"{ben['name']}/{hu['name']}/{bian['name']} 动{dong}")


# ================= D. 时间起卦边界 2 例 =================

# D1 上限边界 2100-12-31 20:00（m1 上限内）：年支9(庚申) 农历12月1日 时支11(戌) → 上22%8=6 下33%8=1 动33%6=3
r = mh.compute_time(datetime(2100, 12, 31, 20, 0))
chk("D1 2100-12-31 20:00 上限 水天需 动3",
    gua3(r) == ("水天需", "火泽睽", "水泽节", 3)
    and r["chain"]["year_zhi"] == 9 and r["chain"]["lunar_month"] == 12 and r["chain"]["lunar_day"] == 1
    and r["chain"]["hour_zhi"] == 11, str(gua3(r)))

# D2 立春后春节前年支口径 1958-02-14 16:20（oracle 实测一致）：
#    节气年=1958 戊戌 → 戌11（起卦年支）；民俗农历年=丁酉腊月廿六 → 酉10（仅展示）
#    上=(11+12+26)=49%8=1乾 下=+申9=58%8=2兑 动58%6=4 → 天泽履 动4；
#    履爻象 阳阳阴|阳阳阳：动4(上卦初位)阳变阴→上巽 → 变卦风泽中孚；互卦 二三四爻=阳阴阳(离) 三四五爻=阴阳阳(巽) → 风火家人
r = mh.compute_time(datetime(1958, 2, 14, 16, 20))
chk("D2 1958-02-14 16:20 年支口径 天泽履/风火家人/风泽中孚 动4(节气年戌11/民俗酉10)",
    gua3(r) == ("天泽履", "风火家人", "风泽中孚", 4)
    and r["chain"]["year_zhi"] == 11 and r["chain"]["lunar_year_zhi"] == 10
    and r["chain"]["lunar_month"] == 12 and r["chain"]["lunar_day"] == 26, str(gua3(r)))


# ================= E. 数据表完整性 2 条 =================

# E1 六十四卦表/卦辞/意象全覆盖
ok_gua = len(mh.GUA64) == 64 and len(mh.GUACI) == 64 and set(mh.GUA64) == set(mh.GUACI)
ok_tg = all(a in mh.TG and b in mh.TG for a, b in mh.GUA64.values())
ok_img = len(mh.IMAGE) == 8 and set(mh.IMAGE) == set(mh.TG)
chk("E1 数据表 GUA64/GUACI 64 键一致 + 上下卦合法 + IMAGE 8 卦", ok_gua and ok_tg and ok_img,
    f"GUA64={len(mh.GUA64)} GUACI={len(mh.GUACI)} IMAGE={len(mh.IMAGE)}")

# E2 断事表 7 分类 × 5 态全覆盖；NAME_BY (上,下) 64 组合无碰撞
ok_duan = set(mh.DUAN) == set(mh.CATEGORIES) and all(set(mh.DUAN[c]) == {"比和", "生", "耗", "泄", "克"} for c in mh.CATEGORIES)
ok_nb = len(mh.NAME_BY) == 64
chk("E2 断事表 7×5 全覆盖 + NAME_BY 无碰撞", ok_duan and ok_nb, f"DUAN={len(mh.DUAN)} 键{len(mh.NAME_BY)}")


# ================= F. 四季旺衰囚/死判定 4 例（通行《五行大义》四时休王：克令者囚、令克者死） =================

def wx_status(month_zhi):
    """任意卦体用的 status 表（与卦无关，仅按月支定季取旺五行）。"""
    return mh.ti_yong("乾", "坤", 1, month_zhi)["status"]


s = wx_status("寅")  # 春木旺：木克土 → 土死；金克木 → 金囚
chk("F1 春(木旺) 土死金囚", s["木"] == "旺" and s["火"] == "相" and s["水"] == "休" and s["金"] == "囚" and s["土"] == "死",
    str(s))
s = wx_status("午")  # 夏火旺：火克金 → 金死；水克火 → 水囚
chk("F2 夏(火旺) 金死水囚", s["火"] == "旺" and s["土"] == "相" and s["木"] == "休" and s["水"] == "囚" and s["金"] == "死",
    str(s))
s = wx_status("酉")  # 秋金旺：金克木 → 木死；火克金 → 火囚
chk("F3 秋(金旺) 木死火囚", s["金"] == "旺" and s["水"] == "相" and s["土"] == "休" and s["火"] == "囚" and s["木"] == "死",
    str(s))
s = wx_status("子")  # 冬水旺：水克火 → 火死；土克水 → 土囚
chk("F4 冬(水旺) 火死土囚", s["水"] == "旺" and s["木"] == "相" and s["金"] == "休" and s["土"] == "囚" and s["火"] == "死",
    str(s))


# ================= G. 字数起卦方向 2 例（原著『少一字为上卦』→ 主表上少下多；上多下少为异文 alt） =================

up, down, dong, info = mh.word_meihua("梅花易数占", 0, "standard")  # 5 字 → 上2兑 下3离
chk("G1 字数5 主表上少下多(原著) 2/3 兑上离下", up == 2 and down == 3 and dong == 5
    and info["up_chars"] == 2 and info["down_chars"] == 3, str((up, down, dong, info)))
up, down, dong, info = mh.word_meihua("梅花易数占", 0, "more_up")  # 5 字 → 上3离 下2兑（异文 alt）
chk("G2 字数5 异文more_up上多下少 3/2 离上兑下", up == 3 and down == 2 and dong == 5
    and info["up_chars"] == 3 and info["down_chars"] == 2, str((up, down, dong, info)))


print(f"\n断言: {PASS} 通过, {FAIL} 失败")
sys.exit(0 if FAIL == 0 else 1)

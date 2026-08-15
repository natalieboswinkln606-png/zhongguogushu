# -*- coding: utf-8 -*-
"""assert_l3_qimen_duanju.py — 奇门遁甲断局模块 l3_qimen_duanju.py 断言（独立，勿改 assert_tables.py）。
覆盖：5 锚点格局、用神结构、吉凶初步边界声明、五不遇时阴阳同、时/月格、地网-八门伏吟互斥、
中宫寄坤（玉女守门/八门反吟/九星反吟-天禽）、大格/上格 2 宫异文、风遁、五假、Rule-ID 标注。
运行：python assert_l3_qimen_duanju.py  （全部 PASS 退出码 0，否则 1）"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l3_qimen import compute
import l3_qimen_duanju as Q

RES = []


def check(name, cond, detail=""):
    RES.append((name, bool(cond), detail))
    print(("PASS" if cond else "FAIL"), name, detail)


def names(r, *want):
    """取指定格名命中集合 (name, palace)。"""
    return {(g["name"], str(g["palace"])) for g in Q.geju(r) if g["name"] in want}


def has(r, name, palace=None):
    for g in Q.geju(r):
        if g["name"] == name and (palace is None or str(g["palace"]) == str(palace)):
            return True
    return False


# ---- 手工锚点 5 例（构造已知格局盘面）----
r = compute(datetime(2023, 1, 1, 4, 0))
check("锚点 青龙返首(2宫)", has(r, "青龙返首", 2))
check("锚点 上格(8宫) 庚+壬", has(r, "上格", 8))
check("锚点 同盘双格（青龙返首+上格）", has(r, "青龙返首", 2) and has(r, "上格", 8))
r = compute(datetime(2023, 1, 1, 16, 0))
check("锚点 飞鸟跌穴(4宫)", has(r, "飞鸟跌穴", 4))
r = compute(datetime(2023, 1, 1, 6, 0))
check("锚点 大格(9宫) 庚+癸", has(r, "大格", 9))
r = compute(datetime(2023, 1, 2, 6, 0))
check("锚点 玉女守门(1宫)", has(r, "玉女守门", 1))

# ---- 用神（qd-01）输出结构 ----
d = Q.duanju(datetime(2025, 6, 1, 10, 0))
check("输出含 yongshen 且含 qd-01 Rule-ID",
      "yongshen" in d and any(y.get("rule_id", "").startswith("qd-01") for y in d["yongshen"]),
      str(list(d.keys())))
check("用神含 日干/时干/值符 三主项",
      any(y.get("use") == "日干" for y in d["yongshen"]) and
      any(y.get("use") == "时干" for y in d["yongshen"]) and
      any(y.get("use") == "值符" for y in d["yongshen"]))
check("用神落宫含 九星/八门/八神 信息",
      all({"star", "door", "shen"} <= set(y.get("detail", {})) for y in d["yongshen"]))
# 吉凶初步（qd-03）带"规则启发式"边界声明
check("吉凶初步含规则启发式声明",
      "chubu" in d and "启发式" in d["chubu"].get("note", ""),
      str(d.get("chubu"))[:80])
check("格局每项含 Rule-ID/底本/异文标注",
      all(g.get("id", "").startswith("qd-") and g.get("source") and "yichwen" in g
          for g in d["geju"]))

# ---- 五不遇时：时干克日干且阴阳同 ----
r = compute(datetime(2026, 4, 26, 0, 0))   # 丙克庚（同阳）→ 报
check("五不遇时 丙时克庚日（同阳）报", has(r, "五不遇时"))
r = compute(datetime(2025, 1, 1, 18, 0))   # 乙木不克庚金（"不克"分支，非"克而阴阳异"）→ 不报
p = r["pillars"]
sg, rg = p["hour"]["ganzhi"][0], p["day"]["ganzhi"][0]
check("五不遇时 %s时%s日 不克不报" % (sg, rg), not has(r, "五不遇时"))

# ---- 时格/月格（庚+时干 / 庚+月干）----
r = compute(datetime(2026, 1, 7, 2, 0))    # 庚+己 时干己 月干己
check("月格+时格+刑格同宫并存(3宫)", names(r, "月格", "时格", "刑格") ==
      {("月格", "3"), ("时格", "3"), ("刑格", "3")})
r = compute(datetime(2026, 5, 22, 4, 0))   # 庚+庚 时干庚（值符宫）
check("时格 庚+庚(7宫)", has(r, "时格", 7))

# ---- 地网遮蔽：值符宫天盘壬且无八门伏吟（伏吟本身不排除）----
r = compute(datetime(2025, 10, 21, 0, 0))  # 8宫壬壬 直符伏吟 无八门伏吟 → 报地网
check("地网遮蔽 壬壬伏吟盘仍报(8宫)", has(r, "地网遮蔽", 8))
r = compute(datetime(2001, 5, 4, 8, 0))    # 9宫壬壬 + 八门伏吟(值使景门落本宫9) → 不报
check("地网遮蔽 八门伏吟盘不报(盘29 dump实测)", not has(r, "地网遮蔽"))

# ---- 中宫寄坤：值使落5宫按2宫判 ----
r = compute(datetime(2025, 5, 28, 0, 0))   # 值使生门落5宫=寄坤2
check("八门反吟 生门落5宫=落2宫(对冲本宫8)", has(r, "八门反吟", 2))
check("玉女守门 值使落5宫按2宫地盘丁", has(r, "玉女守门", 2))
r = compute(datetime(2026, 8, 8, 6, 0))    # 值符天禽落8宫=寄坤2对冲
check("九星反吟 天禽落8宫（寄坤2对冲）", has(r, "九星反吟", 8))
check("八门伏吟 死门落本宫2", has(r, "八门伏吟", 2))

# ---- 大格/上格 2 宫异文（庚+乙/庚+丙/庚+己 落坤2）----
r = compute(datetime(2025, 8, 25, 16, 0))
check("大格 庚+乙落坤2宫(2宫, 异文实测)", has(r, "大格", 2))
r = compute(datetime(2025, 9, 10, 0, 0))
check("上格 庚+丙落坤2宫(2宫, 异文实测)", has(r, "上格", 2))

# ---- 风遁（乙+休门+九地+地盘乙，样本少）----
r = compute(datetime(2025, 10, 21, 0, 0))
check("风遁 乙/乙休门九地(4宫)", has(r, "风遁", 4))

# ---- 五假（实测口径）----
r = compute(datetime(2037, 12, 10, 12, 0))  # 2宫 癸庚/癸 死门 九地 → 鬼假+大格
check("鬼假 死门+九地+癸(2宫)", has(r, "鬼假", 2))
r = compute(datetime(2025, 10, 21, 0, 0))   # 7宫 癸/癸 杜门 六合 → 地假
check("地假 杜门+天盘癸+六合(7宫)", has(r, "地假", 7))

# ---- 对拍采样约束：值符落中宫盘剔除（排盘分歧 qd-b-07）----
ok, total, diff = Q.run_compare(n=8, seed=7, live=False)
check("run_compare 非 live 不抓取（total=0）", total == 0)

n_fail = sum(1 for _, c, _ in RES if not c)
print("\n断言 %d 条，失败 %d 条" % (len(RES), n_fail))
sys.exit(1 if n_fail else 0)

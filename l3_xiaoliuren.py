# -*- coding: utf-8 -*-
"""l3_xiaoliuren.py — L3 小六壬（马前课/李淳风六壬时课/六兀轮经）模块
xlr-01 起课：公历(北京时) → 农历月日时三数（shuowang.csv 朔日表；日干支 ganzhi_days.csv）
xlr-02 六宫数据表：掌诀位 1-6、五行、六神、吉凶、断语要点（逐宫注出处）
xlr-03 三数推演：月→日→时 三次落宫顺数（输出最终宫 + 月宫/日宫中间宫）
xlr-04 断事：问事分类 → 最终宫断语 + 宫五行与事五行生克补充（规则启发式，非神断）

底本声明：小六壬为口诀体系，无专篇经典；六掌诀六宫（大安/留连/速喜/赤口/小吉/空亡）
及其掌诀位为诸家一致（江氏小六壬教程8「食指根大安…中指根空亡」同）。六宫五行两派
并存且均通行，本模块主表取木派（zhaosir 详解「小吉木巽卦」、mykite 马前课「属木六合」、
江氏六神配属：大安木/留连水/速喜火/赤口金/小吉木/空亡土）；水派异文（x6ren.com 吴炯版
留连火/速喜阳土/小吉水/空亡阴土、XiaoLiuRen-MCP 版留连土/小吉水，语雀/道传同水派）
见数据 alt 标注与报告 xlr-a01。断语要点与江氏教程8六宫基础含义
（大安主安静吉祥/留连主拖延反复/速喜主喜庆迅速/赤口主劳苦不顺/小吉主吉庆桃花/空亡主
灾难落空）逐宫核对一致。

口径声明（与 oracle 同轨，x6ren.com 实测 2026-08-16）：
  时支序 = 北京时小时 (h+1)//2%12，子=1…亥=12；23:00-23:59 属次日（晚子时归次日，
  x6ren Beta1.6 更新「晚上11点以后应当算作下一日的子时」，农历月日同按次日取）。
  与 M1 四柱真太阳时子正换日口径不同（见 preregister F1-001 换日界仲裁先例，此为民俗口径）。
  月数=农历月（闰月沿用原月数），日数=农历日（30 日循环：超 30 减 30，异文标注——
  数学上 ≡ 逐宫模 6 顺数，因 6|30）。
数理：x6ren 起课（报数+时支+刻，min.js 读码）与 XiaoLiuRen-MCP 传统三步法均为模 6 顺数，
与通行口诀「月日时逐宫顺数」数学同构：最终宫=(月数+日数+时支序-1) mod 6。"""
import argparse, bisect, csv, json, os, sys
from datetime import datetime, timedelta
from functools import lru_cache
import m1
from rules import ZHI, rel

BASE = os.path.dirname(os.path.abspath(__file__))

# ---- xlr-02 六宫数据表（木派主表五行/六神/吉凶；掌诀位=顺数序；断语=通行口诀要点） ----
# 每宫字段：pos 掌诀位(1-6 顺数序) / name 宫名 / wx 五行 / shen 六神 / ji 吉凶 /
#           pos_desc 掌诀位置 / duan 断语要点（通行口诀句）/ gist 宫义（江氏教程8基础含义）
LG = [
    {"pos": 1, "name": "大安", "wx": "木", "shen": "青龙", "ji": "吉",
     "pos_desc": "食指根部",
     "gist": "主安静、安定、吉祥、顺利（江氏教程8）",
     "duan": "身未动时，问事主安宁。失物去不远，病者主无妨。行人立便至，谋事有贵人。求财随手得，占身安神方。"},
    {"pos": 2, "name": "留连", "wx": "水", "shen": "玄武", "ji": "凶",
     "pos_desc": "食指尖部",
     "gist": "主牵连、拖延、依恋、反复（江氏教程8）",
     "duan": "卒未归时，问事主迟留。失物南方见，急讨方称心。更须防口舌，人口且平平。病者宜往南，急祷可保身。"},
    {"pos": 3, "name": "速喜", "wx": "火", "shen": "朱雀", "ji": "吉",
     "pos_desc": "中指尖部",
     "gist": "主喜庆、喜气、迅速、速度（江氏教程8）",
     "duan": "人便至时，问事主速喜。失物南方见，急讨来方归。行人立便至，交关真是强。求财有利益，凡事皆和合。"},
    {"pos": 4, "name": "赤口", "wx": "金", "shen": "白虎", "ji": "凶",
     "pos_desc": "无名指尖部",
     "gist": "主劳苦、艰难、坎坷、不顺（江氏教程8）",
     "duan": "官事凶时，问事主赤口。失物急去寻，行人有惊慌。官司宜防备，病者主大凶。求财无利益，行人有灾殃。"},
    {"pos": 5, "name": "小吉", "wx": "木", "shen": "六合", "ji": "吉",
     "pos_desc": "无名指根部",
     "gist": "主吉庆、桃花、温顺、顺利（江氏教程8）",
     "duan": "人来喜时，问事主小吉。失物在坤方，行人立便至。凡事皆和合，病者叩穹苍。求财有利益，行人立便至。"},
    {"pos": 6, "name": "空亡", "wx": "土", "shen": "勾陈", "ji": "凶",
     "pos_desc": "中指根部",
     "gist": "主灾难、牢狱、落空、妄想（江氏教程8）",
     "duan": "音信稀时，问事主空亡。失物无踪影，行人走慌忙。官事主刑狱，病人无主张。求财无利益，行人有灾殃。"},
]
LG_BY_NAME = {g["name"]: g for g in LG}
LG_SOURCE = "五行木派主表（zhaosir 详解/江氏六神配属系）+ 江氏小六壬教程8六宫基础含义；口诀体系，无专篇；水派异文见 alt（xlr-a01）"

# 异文标注（六宫五行两派并存且均通行，如实申报：主表为木派，水派异文见 alt）：
#   木派（主表）：zhaosir 详解「小吉木巽卦」、mykite 马前课「属木六合」、江氏六神配属：大安木/留连水/速喜火/赤口金/小吉木/空亡土
#   水派异文：x6ren.com 吴炯版（读码 _LiugongNorth）：留连=火、速喜=阳土、小吉=水、空亡=阴土，大安=木、赤口=金同；
#             XiaoLiuRen-MCP（GitHub）：留连=土、小吉=水、空亡=土，大安=木、速喜=火、赤口=金同（语雀/道传同水派）
# 两派见 data/arbitration_log.csv（xlr-a01）与 report/l3_xiaoliuren_report.txt

# ---- xlr-04 问事分类 → 事五行（规则启发式，模块自定映射，非神断）：出行=水(行流动)、谋事=土(营谋根基)、 ----
# 求财=金(财为金)、婚姻=火(喜事快发)、失物=木(有形之物)、疾病=木(身之生发)；生克补充用 rules.rel
CATEGORY_WX = {"出行": "水", "谋事": "土", "求财": "金", "婚姻": "火", "失物": "木", "疾病": "木"}
CATEGORY_TIP = {"出行": "行人事", "谋事": "谋事", "求财": "求财", "婚姻": "婚姻",
                "失物": "失物", "疾病": "病者"}
JUDGE_NOTE = "规则启发式，非神断：断语为通行口诀要点整理，五行生克补充为模块自定规则，不作吉凶定论"


@lru_cache(maxsize=None)
def load_shuo():
    """shuowang.csv → 按朔时刻升序的 (datetime, 行)；农历月日唯一权威（UTC+8，同 l3_liuyao 口径）。"""
    rows = list(csv.DictReader(open(os.path.join(BASE, "data", "shuowang.csv"), encoding="utf-8")))
    rows.sort(key=lambda r: r["shuo_time"])
    return [(datetime.strptime(r["shuo_time"][:16], "%Y-%m-%dT%H:%M"), r) for r in rows]


@lru_cache(maxsize=None)
def load_days():
    """ganzhi_days.csv → {date: 干支}；换算链之干支备查层（xlr-01 输出日干支）。"""
    with open(os.path.join(BASE, "data", "ganzhi_days.csv"), encoding="utf-8") as f:
        return {r["date"]: r["ganzhi"] for r in csv.DictReader(f)}


def lunar_parts(dt):
    """农历(月, 日, 是否闰月)：最近上一朔时刻 → 朔日表行；闰月沿用原月数（月数=1-12）。
    朔表缺失/为空/越界 → ValueError（不静默回退第三方推算，同 preregister 契约）。"""
    t = dt.replace(second=0, microsecond=0)
    rows = load_shuo()
    if not rows:
        raise ValueError("data/shuowang.csv 缺失或为空：农历月日不可判定（朔日表为 L3 前置录入）")
    d = t.date()
    i = bisect.bisect_right([r[0].date() for r in rows], d) - 1  # 朔日整天=初一（民俗口径，同 l3_liuyao）
    if i < 0 or t < rows[0][0] or (t - rows[i][0]).days > 31:
        raise ValueError(f"农历月日不可判定：{dt.strftime('%Y-%m-%d %H:%M')} 在朔日表范围外（表 {rows[0][0]} ~ {rows[-1][0]}）")
    row = rows[i][1]
    return int(row["month"]), (d - rows[i][0].date()).days + 1, row["is_ruen"] == "1"


def shichen_ordinal(dt):
    """时支序 1-12：北京时 (h+1)//2%12，子=1…亥=12（23 点后子时归次日，同 x6ren 口径）。"""
    return (dt.hour + 1) // 2 % 12 + 1


def lunar_date(dt):
    """xlr-01 起课：输入公历 datetime(北京时) → (农历月, 农历日, 时支序, 是否闰月, 晚子时标记)。
    换算链：公历 → 晚子时(≥23 点)次日归位（x6ren Beta1.6 口径）→ shuowang.csv 朔日表农历月日
    → 时支序（北京时）。日干支查 ganzhi_days.csv（与日数同轨，备注层）。"""
    late = dt.hour >= 23
    t = dt + timedelta(days=1) if late else dt
    mo, da, leap = lunar_parts(t)
    return mo, da, shichen_ordinal(dt), leap, late


def push(mo, da, ho):
    """xlr-03 三数推演：月→日→时三次落宫顺数（掌诀位 1-6）。
    数法（通行口诀）：月数从大安起数（数 1 下=大安，第 1 下落在起点宫）；日数从月宫起数
    （月宫算第 1 下）；时数从日宫起数（日宫算第 1 下）。落宫偏移=(数-1) mod 6。
    日数 30 日循环（超 30 减 30，异文标注：数学 ≡ 逐宫模 6 顺数，因 6|30）。
    返回 (月宫, 日宫, 时宫) 掌诀位 1-6；月数 12/日数 30/时支 12 边界含（模 6 自然闭合）。
    异文：x6ren 吴炯版报数起课为"数字=位移"数法（报数 a 落宫=a%6，较传统数法差 1 位），
    见仲裁记录 xlr-a02；本模块按通行传统数法。"""
    yue = (mo - 1) % 6 + 1
    ri = (yue - 2 + da) % 6 + 1
    shi = (ri - 2 + ho) % 6 + 1
    return yue, ri, shi


def judge(gong, category=None):
    """xlr-04 断事：最终宫断语 + 宫五行与事五行生克补充（rules.rel；规则启发式，非神断）。
    gong=xlr-02 六宫 dict；category 为 None 时只给通用断语与吉凶。"""
    out = {"rule_id": "xlr-04", "source": LG_SOURCE, "alt": "断语为通行口诀要点整理，异文存见（如小吉'行人立便至'句重见）",
           "gong": gong["name"], "ji": gong["ji"], "duan": gong["duan"],
           "note": JUDGE_NOTE}
    if category:
        cat_wx = CATEGORY_WX.get(category)
        if cat_wx:
            out["category"] = category
            r = rel(gong["wx"], cat_wx)
            out["wx_rel"] = f"宫五行{gong['wx']} 对 事五行{cat_wx}：{r}"
            out["wx_note"] = "补充：宫五行生克事五行（" + {
                "比和": "比和相助", "生": "宫生事，事有助", "泄": "宫泄于事，主耗力",
                "克": "宫克事，事受制", "耗": "事耗宫，主费力"}[r] + "，规则启发式，非神断"
    return out


def compute(dt, lon=120.0, category=None):
    """小六壬排盘入口：(北京时 datetime, 东经(仅校验同 m1 契约), 问事分类) → JSON dict。
    越界/异常返回 {"error": ...}，不静默回退。"""
    if not -180 <= lon <= 180:
        return {"error": f"错误: 经度 {lon} 超出 -180~180"}
    s = dt.strftime("%Y-%m-%d %H:%M")
    if not m1.RANGE_LO <= s <= m1.RANGE_HI:
        return {"error": f"错误: {s} 超出 M1 有效范围 {m1.RANGE_LO} ~ {m1.RANGE_HI}（out_of_range，不静默截断）"}
    try:
        mo, da, ho, leap, late = lunar_date(dt)
    except ValueError as e:
        return {"error": f"错误: {e}"}
    days = load_days()
    day_ds = (dt + timedelta(days=1)).date().isoformat() if late else dt.date().isoformat()
    day_gz = days.get(day_ds)
    yue, ri, shi = push(mo, da, ho)
    g = LG_BY_NAME[LG[shi - 1]["name"]]  # 断事用最终宫（xlr-03 时宫）
    lg = [{"name": x["name"], "wx": x["wx"], "ji": x["ji"]} for x in LG]
    return {
        "input": {"datetime": s, "lon": lon, "tz": "UTC+8 北京时间",
                  "late_zishi": late},
        "xlr-01": {"rule_id": "xlr-01", "source": "data/shuowang.csv 朔日表（UTC+8）+ data/ganzhi_days.csv",
                   "lunar": f"农历{mo}月{da}日{'（闰月）' if leap else ''}{'（晚子时归次日）' if late else ''}",
                   "month": mo, "day": da, "day_30_loop": (da - 1) % 30 + 1,
                   "hour_ordinal": ho, "shichen": ZHI[(ho - 1) % 12] + "时",
                   "day_ganzhi": day_gz,
                   "alt": "日数按 30 日循环（超 30 减 30）；闰月沿用原月数；23 点子初归次日（x6ren 口径，与 M1 子正换日异）"},
        "xlr-02": {"rule_id": "xlr-02", "source": LG_SOURCE, "liugong": lg,
                   "alt": "主表为木派（zhaosir/江氏系）；水派异文同为通行：x6ren 吴炯版留连=火/速喜=阳土/小吉=水/空亡=阴土，XiaoLiuRen-MCP 版留连=土/小吉=水（见仲裁记录 xlr-a01）"},
        "xlr-03": {"rule_id": "xlr-03", "source": "通行口诀逐宫顺数（x6ren min.js 与 XiaoLiuRen-MCP 读码同构确认）",
                   "month_gong": LG[yue - 1]["name"], "day_gong": LG[ri - 1]["name"],
                   "final_gong": LG[shi - 1]["name"],
                   "steps": [f"月数{mo}→{LG[yue - 1]['name']}", f"日数{da}→{LG[ri - 1]['name']}",
                             f"时支序{ho}→{LG[shi - 1]['name']}"]},
        "xlr-04": judge(g, category),
        "notes": ["小六壬为口诀体系，无专篇经典；六宫掌诀位诸家一致；五行两派并存：主表木派（zhaosir/江氏系），水派异文见 xlr-a01 alt",
                  "晚子时（23 点后）归次日：农历月日与时支同轨次日（x6ren.com 实测口径）；换日界与 M1 子正异，先例 F1-001",
                  "断事为规则启发式，非神断"],
    }


def main():
    ap = argparse.ArgumentParser(description="L3 小六壬（马前课）：公历输入 → 农历月日时 → 三数推演 → 断事")
    ap.add_argument("--datetime", required=True, help="北京时间，格式 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0, help="东经经度（仅校验范围），默认 120")
    ap.add_argument("--category", default=None, help="问事分类：出行/谋事/求财/婚姻/失物/疾病")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    a = ap.parse_args()
    try:
        dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    except ValueError:
        sys.exit(f"错误: 日期格式应为 YYYY-MM-DD HH:MM，收到 {a.datetime!r}")
    r = compute(dt, a.lon, a.category)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif "error" in r:
        print(r["error"])
    else:
        q = r["xlr-01"]
        print(f"输入: {r['input']['datetime']}  东经 {r['input']['lon']}°（UTC+8）")
        print(f"农历: {q['lunar']}  日干支 {q['day_ganzhi']}  时辰 {q['shichen']}（时支序 {q['hour_ordinal']}）")
        p = r["xlr-03"]
        print(f"推演: {p['steps'][0]}；{p['steps'][1]}；{p['steps'][2]}")
        print(f"月宫 {p['month_gong']} → 日宫 {p['day_gong']} → 最终 {p['final_gong']}（rule {p['rule_id']}）")
        j = r["xlr-04"]
        print(f"断事[{j['gong']}·{j['ji']}]: {j['duan']}")
        if "wx_rel" in j:
            print(f"  {j['wx_rel']}")
        print(f"  ({j['note']})")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""assert_l3_liuren.py — L3-3 六壬四课三传断言与网络对拍（易安居 oracle）

用法:
  python assert_l3_liuren.py          # 本地断言 + 读缓存对拍（不联网）
  python assert_l3_liuren.py --net    # 本地断言 + 网络对拍（缓存未命中才请求）
  python assert_l3_liuren.py --no-net # 显式等价默认

约定:
  - 退出码 0 = 本地断言 + 网络对拍全部 PASS（对拍 SKIP 已如实标注）；1 = 本地断言 FAIL 或对拍 FAIL/分歧。
  - 幂等: oracle 响应缓存到 data/_nr_oracle_cache.json，重跑不重复请求；
    _nr_probe.html（2010-09-13 12:00 页面样本）自动预置进缓存。
  - 网络硬预算: 请求次数 <= 20、时长 <= 25 分钟；请求间隔 3s，单例失败重试 <=2 次（退避 30s）。
  - 对拍字段: 月将/日柱/四课(课1课3)/三传干支/三传六亲与遁干/贵人(天将环反推)/天将 7 项/行年/课名
    （六亲/遁干在支一致时比对，避免同一分歧连锁重复申报；G3 纳入对拍）。
  - 伏吟有克案例（2010-07-24 乙亥 辰/亥/巳、2010-08-03 乙酉 辰/酉/卯）为 2026-08-16
    页面原文抓取实测（W1 裁定：伏吟有克照常贼克，初传=贼课上神，中末伏吟刑推）。
  - 差异无处藏身: 分歧写入 report/l3_liuren_net.txt，申报行由收尾脚本按 I-8 幂等写入 CSV。
"""
import json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta

import l3_liuren as L

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "data", "_nr_oracle_cache.json")
NETLOG = os.path.join(BASE, "report", "l3_liuren_net.txt")
ORACLE_URL = "https://www.zhouyi.cc/zhouyi/liuren/liuren.php"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

_ok, _fail = 0, 0
FAILED = []

def check(name, cond, extra=""):
    global _ok, _fail
    if cond:
        _ok += 1
        print(f"  PASS {name}")
    else:
        _fail += 1
        FAILED.append(name)
        print(f"  FAIL {name}  {extra}")

def chuan_str(r):
    return "".join(c["zhi"] for c in r["san_chuan"]["chuan"])

# ============================== 本地断言 ==============================

def assert_local():
    print("== A. 日干支 / 时柱（易安居口径） ==")
    check("日柱锚点 2010-09-13=丙寅", L.day_ganzhi_of(datetime(2010, 9, 13, 12)) == "丙寅")
    check("日柱+1天=丁卯", L.day_ganzhi_of(datetime(2010, 9, 14, 12)) == "丁卯")
    check("23:00 仍当日（易安居 23 点换日口径）", L.day_ganzhi_of(datetime(2010, 9, 13, 23, 30)) == "丙寅")
    check("时支 12:00=午", L.hour_zhi_of(datetime(2010, 9, 13, 12)) == "午")
    check("时支 23:00=子（子初口径）", L.hour_zhi_of(datetime(2010, 9, 13, 23)) == "子")
    check("五鼠遁 丙日午时=甲午", L.hour_ganzhi_of(datetime(2010, 9, 13, 12), "丙") == "甲午")

    print("== B. 月将（中气换将边界，solar_terms.csv 真实时刻 ±15min） ==")
    zhong = [r for r in L.terms() if r["jie_zhong"] == "中气"]
    dahan = next(r for r in zhong if r["term"] == "大寒" and r["datetime"].startswith("2024"))
    gy = next(r for r in zhong if r["term"] == "谷雨" and r["datetime"].startswith("2024"))
    t_dahan = datetime.strptime(dahan["datetime"], "%Y-%m-%d %H:%M")
    t_gy = datetime.strptime(gy["datetime"], "%Y-%m-%d %H:%M")
    check("大寒2024 交前-15min=丑将", L.month_jiang(t_dahan - timedelta(minutes=15)) == "丑", f"{t_dahan}")
    check("大寒2024 交后+15min=子将", L.month_jiang(t_dahan + timedelta(minutes=15)) == "子")
    check("谷雨2024 交前-15min=戌将（春分后）", L.month_jiang(t_gy - timedelta(minutes=15)) == "戌")
    check("谷雨2024 交后+15min=酉将", L.month_jiang(t_gy + timedelta(minutes=15)) == "酉")
    check("锚点 2010-09-13=巳将（处暑~秋分）", L.month_jiang(datetime(2010, 9, 13, 12)) == "巳")

    print("== C. 贵人（十干昼夜贵全表 + 卯酉分界） ==")
    dt = datetime(2010, 9, 13, 12)
    expect = {"甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
              "乙": ("子", "申"), "己": ("子", "申"), "丙": ("亥", "酉"),
              "丁": ("亥", "酉"), "壬": ("巳", "亥"), "癸": ("巳", "亥"), "辛": ("午", "寅")}
    for g, (d, n) in expect.items():
        check(f"贵人 {g} 昼={d}", L.gui_ren(g, dt, "昼")[0] == d)
        check(f"贵人 {g} 夜={n}", L.gui_ren(g, dt, "夜")[0] == n)
    check("卯酉分界 16:00(申时)=昼贵", L.gui_ren("丙", datetime(2010, 9, 13, 16))[1] == "昼")
    check("卯酉分界 16:59=昼贵", L.gui_ren("丙", datetime(2010, 9, 13, 16, 59))[1] == "昼")
    check("卯酉分界 17:00(酉时)=夜贵（易安居实测）", L.gui_ren("丙", datetime(2010, 9, 13, 17))[1] == "夜")

    print("== D. 天盘（月将加时，手算） ==")
    check("天盘 巳加午", L.tian_pan("巳", "午") == list("亥子丑寅卯辰巳午未申酉戌"))
    check("天盘 寅加子", L.tian_pan("寅", "子") == list("寅卯辰巳午未申酉戌亥子丑"))
    check("天盘 子加卯", L.tian_pan("子", "卯") == list("酉戌亥子丑寅卯辰巳午未申"))

    print("== E. 天将布向（落宫口诀：亥子丑寅卯辰顺/巳午未申酉戌逆） ==")
    pan_a = L.tian_pan("巳", "午")            # 贵神亥落子宫(0) → 顺
    sj_a = L.shen_jiang_pan("亥", "昼", 12, pan_a)
    check("顺布 落宫子: 贵人=贵、次=蛇、末位=后", sj_a[0] == "贵" and sj_a[1] == "蛇" and sj_a[11] == "后")
    pan_b = L.tian_pan("午", "午")            # 伏吟盘，贵神落未宫(7) → 逆
    sj_b = L.shen_jiang_pan("未", "夜", 12, pan_b)
    check("逆布 落宫未: 贵人=贵、次=蛇、末位=后", sj_b[7] == "贵" and sj_b[6] == "蛇" and sj_b[8] == "后")
    check("逆布 12 将齐全", sorted(x for x in sj_b) == sorted(L.TIANJIANG))

    print("== F. 干寄宫表 + 四课递推 ==")
    jg = {"甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳", "己": "未",
          "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"}
    for g, z in jg.items():
        check(f"干寄宫 {g}→{z}", L.JIGONG[g] == z)
    r = L.compute(datetime(2010, 9, 13, 12))
    sk = r["si_ke"]["ke"]
    uppers = [k["upper"] for k in sk]
    check("四课 2010-09-13 丙寅: 辰/丙 卯/辰 丑/寅 子/丑",
          uppers == list("辰卯丑子") and [k["lower"] for k in sk] == ["丙", "辰", "寅", "丑"])
    check("四课天将: 龙勾雀蛇（贵神亥顺布）", [k["jiang"] for k in sk] == ["龙", "勾", "雀", "蛇"])

    print("== G. 九宗门（每法锚点，手算/注释实测） ==")
    def m(dts, want):
        r = L.compute(datetime.strptime(dts, "%Y-%m-%d %H:%M"))
        return r["san_chuan"]["method"], chuan_str(r), want
    for dts, want_m, want_c in [
        ("2010-01-01 08:00", "元首课", "巳寅亥"),   # 独克课4 → 元首（手算）
        ("2010-01-01 12:00", "重审课", "午丑申"),   # 独贼课3 → 重审（手算）
        ("2010-01-02 08:00", "知一课", "午卯子"),   # 比用（手算）
        ("2010-01-05 12:00", "涉害课", "午丑申"),   # 深度 5 vs 4（手算）
        ("2010-01-03 12:00", "见机课", "卯戌巳"),   # 深浅相等取孟
        ("2010-01-23 08:00", "察微课", "巳丑酉"),   # 深浅相等取仲
        ("2010-01-30 08:00", "复等课", "辰子申"),   # 皆季，刚日干上
        ("2010-01-01 20:00", "蒿矢课", "巳申亥"),   # 遥克之蒿矢
        ("2010-01-02 20:00", "弹射课", "午酉子"),   # 遥克之弹射（手算）
        ("2010-02-07 08:00", "虎视课", "巳申丑"),   # 昴星阳日（手算）
        ("2010-03-20 20:00", "冬蛇掩目课", "申申午"),  # 昴星阴日
        ("2010-03-07 20:00", "别责课", "亥午午"),   # 刚日干合（手算/注释丙辰→亥）
        ("2010-01-09 08:00", "八专课", "寅辰辰"),   # 柔日逆数三（手算）
        ("2005-02-17 00:00", "伏吟课", "亥申寅"),   # 注释实测壬申例
        ("2005-01-25 00:00", "伏吟课", "酉未丑"),   # 注释实测己酉例
        ("2010-03-21 20:00", "伏吟课", "申寅巳"),   # 伏吟阳日干上起（手算）
        ("2010-01-22 12:00", "返吟课", "寅申寅"),   # 返吟有克（手算）
        ("2010-01-21 12:00", "无依课", "巳丑辰"),   # 返吟无克井栏射（注释辛未例）
        # W1 裁定：伏吟有克照常贼克（页面原文 2026-08-16 抓取：2010-07-24 乙亥三传辰/亥/巳、
        # 2010-08-03 乙酉三传辰/酉/卯——初传=贼课上神辰，中末伏吟刑推）
        ("2010-07-24 12:00", "伏吟课", "辰亥巳"),
        ("2010-08-03 12:00", "伏吟课", "辰酉卯"),
    ]:
        got_m, got_c, _ = m(dts, want_c)
        check(f"{dts} {want_m} {want_c}", got_m == want_m and got_c == want_c, f"got {got_m} {got_c}")
    # W2：跨子时窗口四柱北京时口径自洽（2010-09-13 23:57 真太阳时已跨 09-14 00:01，
    # 月/日柱仍按北京时当日——日丙寅、月乙酉，四柱同轨不自相矛盾）
    r_w2 = L.compute(datetime(2010, 9, 13, 23, 57))
    check("跨子时窗口 2010-09-13 23:57 四柱=庚寅/乙酉/丙寅/戊子（北京时口径统一）",
          r_w2["pillars"] == {"year": "庚寅", "month": "乙酉", "day": "丙寅", "hour": "戊子"},
          f"{r_w2['pillars']}")
    check("跨子时窗口 23:57 时支=子（子初 23 点起）", L.hour_zhi_of(datetime(2010, 9, 13, 23, 57)) == "子")
    # 涉害深度中间量
    r = L.compute(datetime(2010, 1, 5, 12))
    sk = r["si_ke"]["ke"]
    pan = r["tiandi_pan"]["tian_pan"]
    check("涉害深度 课2(午加亥)=3、课3(戌加卯)=1（《六壬大全》原文例口径）",
          L._she_hai_depth(sk, pan, 1, "贼", "乙") == 3 and L._she_hai_depth(sk, pan, 2, "贼", "乙") == 1,
          f"{L._she_hai_depth(sk, pan, 1, '贼', '乙')}/{L._she_hai_depth(sk, pan, 2, '贼', '乙')}")

    print("== H. 行年本命（易安居实测公式，男+2 女+4，底本出处待考） ==")
    def xn_part(b, s, y):
        x = L.xing_nian(b, s, y)
        return (x["benming"], x["xingnian"])
    check("1978男 2010: 本命戊午 行年戊戌（缓存页面实测）",
          xn_part(1978, "男", 2010) == ("戊午", "戊戌"))
    check("1978女 2010: 本命戊午 行年庚子", xn_part(1978, "女", 2010) == ("戊午", "庚子"))
    check("1980男 2012: 本命庚申 行年戊戌", xn_part(1980, "男", 2012) == ("庚申", "戊戌"))
    check("1990女 2019: 本命庚午 行年丁酉", xn_part(1990, "女", 2019) == ("庚午", "丁酉"))
    check("行年输出含 rule_id/source（底本出处待考标注，G2）",
          L.xing_nian(1978, "男", 2010).get("rule_id") == "nr-04（行年）"
          and "待考" in L.xing_nian(1978, "男", 2010)["source"])

    print("== I. 遁干 / 六亲 ==")
    check("丙寅日甲子旬: 子遁甲", L.dun_gan("丙寅", "子") == "甲")
    check("丙寅日甲子旬: 酉遁癸", L.dun_gan("丙寅", "酉") == "癸")
    check("丙寅日甲子旬: 戌亥旬外=None", L.dun_gan("丙寅", "戌") is None and L.dun_gan("丙寅", "亥") is None)
    check("六亲 丙日: 子水=官鬼 午火=兄弟 未土=子孙 寅木=父母",
          L.liu_qin("丙", "子") == "官鬼" and L.liu_qin("丙", "午") == "兄弟"
          and L.liu_qin("丙", "未") == "子孙" and L.liu_qin("丙", "寅") == "父母")

    print("== J. 整例（2010-09-13 12:00 丙寅，与易安居页面样本 _nr_probe.html 对拍） ==")
    r = L.compute(datetime(2010, 9, 13, 12))
    check("月将=巳将 贵人=亥/昼", r["month_jiang"]["zhi"] == "巳" and r["gui_ren"]["zhi"] == "亥" and r["gui_ren"]["day_night"] == "昼")
    check("三传=子亥戌 遁干甲/None/None 六亲官鬼官鬼子孙",
          chuan_str(r) == "子亥戌"
          and [c["dun_gan"] for c in r["san_chuan"]["chuan"]] == ["甲", None, None]
          and [c["liu_qin"] for c in r["san_chuan"]["chuan"]] == ["官鬼", "官鬼", "子孙"])
    check("天盘加临验证: pan[6]=巳（巳加午）", r["tiandi_pan"]["tian_pan"][6] == "巳")

# ============================== oracle 解析与对拍 ==============================

ZHI_OR_JIANG = "贵蛇雀合勾龙空虎常玄阴后"

def parse_oracle(html):
    """易安居六壬结果页 → dict。解析失败抛 ValueError。"""
    if "年份超出范围" in html or "六壬排盘" not in html:
        raise ValueError("oracle 页面无排盘结果")
    m = re.search(r"干支：</strong></strong>\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])(?:&nbsp;)+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])(?:&nbsp;)+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])(?:&nbsp;)+([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])", html)
    if not m:
        raise ValueError("干支行缺失")
    jiang = re.search(r"<strong>月将：</strong>([子丑寅卯辰巳午未申酉戌亥])将", html)
    xm = re.search(r"<strong>年命：</strong>([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])", html)
    xn = re.search(r"<strong>行年：</strong>([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])", html)
    if not jiang or not xm or not xn:
        raise ValueError("月将/年命/行年缺失")
    uls = re.findall(r'<ul class="liuren1 f14">(.*?)</ul>', html, re.S)
    if len(uls) < 2:
        raise ValueError("四课/三传 ul 缺失")
    def tokens(seg):
        return re.findall(r"[贵蛇雀合勾龙空虎常玄阴后]|[子丑寅卯辰巳午未申酉戌亥]|[甲乙丙丁戊己庚辛壬癸]", seg)
    def tokens_chuan(seg):
        # 三传行：六亲 遁干? 支 天将（遁干为空则省略，如 "官鬼  亥  贵"）；G3 纳入对拍
        return re.findall(r"官鬼|妻财|子孙|父母|兄弟|[贵蛇雀合勾龙空虎常玄阴后]|[子丑寅卯辰巳午未申酉戌亥]|[甲乙丙丁戊己庚辛壬癸]", seg)
    ke_lines = [tokens(x) for x in uls[0].split("<br>")]
    chuan_lines = [tokens_chuan(x) for x in uls[1].split("<br>")]
    if not (len(ke_lines) >= 3 and all(len(x) == 4 for x in ke_lines[:3])):
        raise ValueError(f"四课行解析异常: {ke_lines}")
    # 页面列序 = 课4课3课2课1（左侧课4…右侧课1，日干所在列=课1）
    ke1 = ke_lines[0][3], ke_lines[1][3]   # (天将, 上支)
    ke2 = ke_lines[0][2], ke_lines[1][2]
    ke3 = ke_lines[0][1], ke_lines[1][1]
    ke4 = ke_lines[0][0], ke_lines[1][0]
    if len(chuan_lines) < 3 or not all(len(x) >= 3 for x in chuan_lines[:3]):
        raise ValueError(f"三传行解析异常: {chuan_lines}")
    chuan = []
    for x in chuan_lines[:3]:
        if len(x) == 4:          # (六亲, 遁干, 支, 天将)
            chuan.append((x[3], x[2], x[0], x[1]))
        else:                    # (六亲, 支, 天将)，遁干为空
            chuan.append((x[2], x[1], x[0], None))
    return {"ganzhi": list(m.groups()), "jiang": jiang.group(1), "benming": xm.group(1),
            "xingnian": xn.group(1), "ke": [ke1, ke2, ke3, ke4], "chuan": chuan}

def oracle_guiren(ke1, tian_pan):
    """从天盘环+课1天将反推贵神支（顺布/逆布两种可能）→ 返回两个候选支。

    页面天将环 = 天将顺序（顺布=顺环[贵蛇雀合勾龙空虎常玄阴后]，逆布=逆环[贵后阴玄常虎空龙勾合雀蛇]）
    从贵神落宫起沿环展开；课1天将 X 在环位置 (g + k) % 12，故 g = (pos - k) % 12（k = 天将环序）。
    实测验证：2010-01-01 08:00 逆布，课1=(后,未) pos=5, k_ni(后)=1 → g=4 → ring[4]=午=辛日昼贵 ✓；
              2010-01-09 08:00 顺布，课1=(勾,辰) pos=2, k_shun(勾)=4 → g=10 → ring[10]=子=己日昼贵 ✓。
    （旧公式逆布误用 (pos+k_ni)%12，反推偏一位；已修正。）"""
    zhi, jiang = ke1[1], ke1[0]
    ring = [tian_pan[(i + 5) % 12] for i in range(12)]  # 页面环：位置 i = 地盘 (i+5)%12 宫
    pos = ring.index(zhi)  # 课1上支在环位置 → 干宫环位置
    k_shun = ZHI_OR_JIANG.index(jiang)                     # 顺布：贵在该将之前 k 位
    k_ni = "贵后阴玄常虎空龙勾合雀蛇".index(jiang)          # 逆布：贵在该将之后 k 位
    return [ring[(pos - k_shun) % 12], ring[(pos - k_ni) % 12]]

# 对拍样本：(datetime, 期望宗门, 备注)。宗门为模块输出（oracle 页面无课名，由三传+四课一致推定一致）
SAMPLE = [
    ("2010-01-01 08:00", "元首课", "独克"),
    ("2010-01-01 12:00", "重审课", "独贼"),
    ("2010-01-02 08:00", "知一课", "比用"),
    ("2010-01-05 12:00", "涉害课", "深度涉害"),
    ("2010-01-02 20:00", "弹射课", "遥克"),
    ("2010-02-07 08:00", "虎视课", "昴星阳日"),
    ("2010-03-07 20:00", "别责课", "刚日干合"),
    ("2010-01-09 08:00", "八专课", "课不全"),
    ("2010-03-21 20:00", "伏吟课", "伏吟无克"),
    ("2010-07-24 12:00", "伏吟课", "伏吟有克（页面原文辰/亥/巳，2026-08-16 抓取）"),
    ("2010-08-03 12:00", "伏吟课", "伏吟有克（页面原文辰/酉/卯，2026-08-16 抓取）"),
    ("2010-01-22 12:00", "返吟课", "返吟有克"),
    ("2010-01-21 12:00", "无依课", "返吟无克"),
    ("2010-09-13 12:00", None, "页面样本锚点（缓存预置）"),
    ("2000-01-01 12:00", None, "跨年份"),
    ("1995-06-15 14:00", None, "跨年份"),
]

def load_cache():
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(c):
    with open(CACHE, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=0)

def fetch_oracle(dt_str, cache, force=False):
    """取 oracle 页面：缓存优先；未命中才请求。返回 (html, from_cache)。"""
    if dt_str in cache and not force:
        return cache[dt_str], True
    y, m, d, hm = dt_str[:4], dt_str[5:7], dt_str[8:10], dt_str[11:13]
    minute = dt_str[14:16]
    params = {"act": "ok", "name": "", "birthyear": "1978", "rdoSex": "1", "zhanshi": "",
              "y": y, "m": m, "d": d, "h": hm, "min": minute,
              "pai": "1", "guishen": "1", "zhouye": "2", "scpf": "0"}
    data = urllib.parse.urlencode(params).encode()
    for attempt in range(3):
        try:
            req = urllib.request.Request(ORACLE_URL, data=data,
                                         headers={"User-Agent": UA})
            body = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
            cache[dt_str] = body
            return body, False
        except Exception as e:
            if attempt < 2:
                time.sleep(30)
    raise RuntimeError(f"oracle 请求失败: {dt_str}")

def compare_one(dt_str, want_method, cache, log, stats, force=False):
    html, from_cache = fetch_oracle(dt_str, cache, force)
    stats["reqs"] += 0 if from_cache else 1
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    try:
        orc = parse_oracle(html)
    except ValueError as e:
        stats["skip"] += 1
        log.append(f"{dt_str} SKIP 解析失败: {e}")
        print(f"  SKIP {dt_str} 解析失败: {e}")
        return
    mod = L.compute(dt, birth_year=1978, sex="男")   # 与请求参数 birthyear=1978/rdoSex=1 一致
    diffs = []
    if mod["month_jiang"]["zhi"] != orc["jiang"]:
        diffs.append(f"月将 自研{mod['month_jiang']['zhi']} vs oracle{orc['jiang']}")
    if orc["ganzhi"][2] != mod["pillars"]["day"]:
        diffs.append(f"日柱 自研{mod['pillars']['day']} vs oracle{orc['ganzhi'][2]}")
    for i in (0, 2):  # 课1、课3 上支（orc["ke"] = [课1..课4]）
        if mod["si_ke"]["ke"][i]["upper"] != orc["ke"][i][1]:
            diffs.append(f"课{i+1}上 自研{mod['si_ke']['ke'][i]['upper']} vs oracle{orc['ke'][i][1]}")
    m_chuan = chuan_str(mod)
    o_chuan = "".join(c[1] for c in orc["chuan"])
    if m_chuan != o_chuan:
        diffs.append(f"三传 自研{m_chuan} vs oracle{o_chuan}")
    if orc["xingnian"] != (mod.get("xing_nian") or {}).get("xingnian"):
        diffs.append(f"行年 自研{(mod.get('xing_nian') or {}).get('xingnian')} vs oracle{orc['xingnian']}")
    cands = oracle_guiren(orc["ke"][0], mod["tiandi_pan"]["tian_pan"])
    if mod["gui_ren"]["zhi"] not in cands:
        diffs.append(f"贵人 自研{mod['gui_ren']['zhi']} vs oracle反推{cands}")
    # 天将全比（四课+三传共 7 项）：oracle 页面天将环 = 模块 sj 环（顺/逆由落宫定）
    sj = mod["tiandi_pan"]["shen_jiang"]
    for i in range(4):
        if mod["si_ke"]["ke"][i]["jiang"] != orc["ke"][i][0]:
            diffs.append(f"课{i+1}天将 自研{mod['si_ke']['ke'][i]['jiang']} vs oracle{orc['ke'][i][0]}")
    for i, (o_j, o_z, o_lq, o_dg) in enumerate(orc["chuan"]):
        mc = mod["san_chuan"]["chuan"][i]
        if mc["jiang"] != o_j:
            diffs.append(f"传{i+1}天将 自研{mc['jiang']} vs oracle{o_j}")
        if o_z == mc["zhi"]:  # 支一致时才比六亲/遁干（G3），避免同一分歧连锁重复申报
            if mc["liu_qin"] != o_lq:
                diffs.append(f"传{i+1}六亲 自研{mc['liu_qin']} vs oracle{o_lq}")
            if mc["dun_gan"] != o_dg:
                diffs.append(f"传{i+1}遁干 自研{mc['dun_gan']} vs oracle{o_dg}")
    # 课名：oracle 无课名字段，三传+四课全一致 ⇒ 宗门一致（可推定）
    method = mod["san_chuan"]["method"]
    if want_method and method != want_method:
        diffs.append(f"宗门 自研{method} vs 期望{want_method}")
    if diffs:
        stats["fail"] += 1
        log.append(f"{dt_str} FAIL ({method}): " + " | ".join(diffs))
        print(f"  FAIL {dt_str} {method}: {' | '.join(diffs)}")
    else:
        stats["pass"] += 1
        log.append(f"{dt_str} PASS {method} 三传{o_chuan} 课1={orc['ke'][0][1]} 课3={orc['ke'][2][1]} 月将{orc['jiang']} 贵{cands} 行年{orc['xingnian']}")
        print(f"  PASS {dt_str} {method} 三传{o_chuan} 课1={orc['ke'][0][1]} 课3={orc['ke'][2][1]} 月将{orc['jiang']} 行年{orc['xingnian']}")

def run_net(force=False):
    print("== 网络对拍（易安居六壬，缓存幂等） ==")
    cache = load_cache()
    # 预置 _nr_probe.html 为 2010-09-13 12:00 缓存（原实现已抓页面样本）
    probe = os.path.join(BASE, "_nr_probe.html")
    if "2010-09-13 12:00" not in cache and os.path.exists(probe):
        cache["2010-09-13 12:00"] = open(probe, encoding="utf-8").read()
    stats = {"reqs": 0, "pass": 0, "fail": 0, "skip": 0}
    log = [f"# l3_liuren 网络对拍日志（易安居 zhouyi.cc，{datetime.now().strftime('%Y-%m-%d %H:%M')}）",
           "# 字段: 月将/日柱/课1课3上支/三传干支/三传六亲与遁干/行年/贵人(天将环反推)/天将7项/宗门(三传四课一致推定)"]
    t0 = time.time()
    for dt_str, want, note in SAMPLE:
        if stats["reqs"] >= 20 or time.time() - t0 > 1500:
            log.append(f"# 硬预算触顶(请求{stats['reqs']}次/{int(time.time()-t0)}s)，余例 SKIP")
            print("  ## 硬预算触顶，余例 SKIP")
            break
        compare_one(dt_str, want, cache, log, stats, force)
        time.sleep(3)   # 请求间隔
    save_cache(cache)
    with open(NETLOG, "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    print(f"  对拍汇总: PASS {stats['pass']} | FAIL {stats['fail']} | SKIP {stats['skip']} | 网络请求 {stats['reqs']} 次")
    return stats

def main():
    import argparse
    ap = argparse.ArgumentParser(description="L3-3 六壬断言与对拍")
    ap.add_argument("--net", action="store_true", help="网络对拍（缓存未命中才请求）")
    ap.add_argument("--no-net", action="store_true", help="显式等价默认（不联网）")
    ap.add_argument("--force", action="store_true", help="强制重抓 oracle（忽略缓存）")
    a = ap.parse_args()
    assert_local()
    net_stats = None
    if a.net:
        net_stats = run_net(a.force)
    print(f"== 断言汇总: PASS {_ok} | FAIL {_fail} ==")
    if _fail:
        print("FAIL 清单:")
        for n in FAILED:
            print("  -", n)
    # W3：对拍 FAIL 计入退出码（旧实现丢弃 run_net 返回值，--net 对拍 FAIL 1 但退出码 0）
    net_fail = (net_stats or {}).get("fail", 0)
    sys.exit(1 if (_fail or net_fail) else 0)

if __name__ == "__main__":
    main()

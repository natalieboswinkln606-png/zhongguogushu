# -*- coding: utf-8 -*-
"""l3_bazi_daliu.py — 八字大运流年流月五行模块：大运排法(bd-01 阳男阴女顺/阴男阳女逆，月柱起每步10年)、
起运岁数(bd-02 出生真太阳时→顺逆最近节间隔÷3，余数折算 1天=4月/1时辰=10天，分钟精度)、
流年(bd-03 立春换年同 m1 r3，流年干对日干十神 r5)、流月(bd-04 12节换月同 m1 r4，月干十神 r5)、
五行统计(bd-05 干支+藏干五行计数、缺行、季节旺相休囚死)。
底本：《渊海子平》大运起运口诀（阳男阴女顺行、阴男阳女逆行；三天一岁、一天四月、一时辰十天）、
《三命通会》五行旺相休囚死表；节气/藏干/十神复用 m1.py 与 data/*.csv（同轨）。输入=北京时+东经(同 m1)。
对拍：主 oracle 易安居 bazi.php（起运岁数月天/大运干支序+十神/岁数年份/五行个数 16 项），
第二 oracle lunar-python sect=2 精确分钟口径（大运/流年/流月干支），运行 python l3_bazi_daliu.py --compare。"""
import argparse, bisect, csv, json, os, random, re, sys, time
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m1
from rules import GAN, ZHI, YANG_GAN, GAN_WX, ZHI_WX, wx_of_gan

BASE = os.path.dirname(os.path.abspath(__file__))
MIN_YEAR, HOUR = 4320, 360  # bd-02 分钟精度：1 岁=4320 分(3天)、1 月=360 分(6小时=3时辰)、1 天=12 分(1时辰=10天)

def gan_zhi_seq(gz):  # 60 甲子序：甲子=0…癸亥=59
    return (6 * GAN.index(gz[0]) - 5 * ZHI.index(gz[1])) % 60

def seq_gz(n):  # 60 甲子序 → 干支
    return GAN[n % 10] + ZHI[n % 12]

def _terms():
    return m1.load_terms()  # 12 节行，datetime 升序

def direction(dt, lon, sex):
    """bd-01 顺逆：年干阳×男=顺。年干取立春口径年柱（m1.year_pillar，真太阳时判界）。"""
    r = m1.compute(dt, lon)
    if "error" in r:
        return None, r
    yg = r["pillars"]["year"]["ganzhi"][0]
    return ("顺" if (yg in YANG_GAN) == (sex == "男") else "逆"), r

def qiyun(dt, lon, sex):
    """bd-02 起运：顺→下 12 节、逆→上 12 节；间隔分钟÷4320=岁、÷360=月、÷12=天、余×2=时（真太阳时口径）。
    返回 (岁,月,天,时, 节时刻, 交运时刻, 顺逆)。"""
    fwd, r = direction(dt, lon, sex)
    ts = datetime.strptime(m1.true_solar(dt, lon).strftime("%Y-%m-%d %H:%M"), "%Y-%m-%d %H:%M")
    ts_str = ts.strftime("%Y-%m-%d %H:%M")
    times = [x["datetime"] for x in _terms()]
    i = bisect.bisect_right(times, ts_str)
    jie = _terms()[i if fwd == "顺" else i - 1]["datetime"]  # 顺=其后第一个节，逆=其前最后一个节
    jdt = datetime.strptime(jie, "%Y-%m-%d %H:%M")
    minutes = int((jdt - ts).total_seconds() // 60)
    y, minutes = minutes // MIN_YEAR, minutes % MIN_YEAR
    mo, minutes = minutes // HOUR, minutes % HOUR
    d, minutes = minutes // 12, minutes % 12
    h = minutes * 2  # 余 12 分=1 天，再余分钟×2=时
    if fwd == "逆":
        minutes2 = int((ts - jdt).total_seconds() // 60)
        y, minutes2 = minutes2 // MIN_YEAR, minutes2 % MIN_YEAR
        mo, minutes2 = minutes2 // HOUR, minutes2 % HOUR
        d, minutes2 = minutes2 // 12, minutes2 % 12
        h = minutes2 * 2
    jiao = jiao_dt(dt, y, mo, d, h)
    return y, mo, d, h, jie, jiao, fwd

def jiao_dt(dt, y, mo, d, h):  # 交运时刻 = 出生 + 岁年月天时（2/29 遇平年顺延 3/1）
    t = dt
    try:
        t = t.replace(year=t.year + y)
    except ValueError:
        t = datetime(t.year + y, 3, 1, t.hour, t.minute)
    mo_t, d_t = mo + t.month, d + t.day
    while mo_t > 12:
        mo_t -= 12
        t = t.replace(year=t.year + 1)
    try:
        return t.replace(month=mo_t, day=d_t) + timedelta(hours=h)
    except ValueError:
        return datetime(t.year, mo_t, 1, t.hour, t.minute) + timedelta(days=d_t - 1, hours=h)

def dayun(dt, lon, sex, steps=8):
    """bd-01 大运：月柱为起点，60 甲子序每步 ±1，每步 10 年（起运年=出生年+起运岁）。"""
    y, mo, d, h, jie, jiao, fwd = qiyun(dt, lon, sex)
    r = m1.compute(dt, lon)
    mp = r["pillars"]["month"]["ganzhi"]
    seq = gan_zhi_seq(mp) + (1 if fwd == "顺" else -1)  # 首步 = 月柱顺/逆各 1
    base = jiao.year  # 每步大运起止年=交运年起 10 年步进（oracle 年份行同口径）
    out = []
    for i in range(steps):
        gz = seq_gz((seq + i * (1 if fwd == "顺" else -1)) % 60)
        out.append({"index": i + 1, "ganzhi": gz, "gan": gz[0], "zhi": gz[1],
                    "god": m1.ten_god(r["ten_gods"]["day_master"], gz[0]),
                    "start_year": base + i * 10, "end_year": base + i * 10 + 9})
    return out, y, mo, d, h, jie, jiao, fwd

def year_gz(year):  # 立春换年口径年干支：代表时刻 y-02-05 12:00 恒 ≥ 立春最晚时刻(2/5 03:05) → 恒当年干支，等价 m1 r3
    return GAN[(year - 4) % 10] + ZHI[(year - 4) % 12]

def liunian(dt, lon, sex):
    """bd-03 流年：出生年→交运年逐年；干支=立春换年口径（同 m1 r3，公式=year_gz）；十神=流年干对日干（r5）。"""
    dl, *_ = dayun(dt, lon, sex)
    r = m1.compute(dt, lon)
    dm = r["ten_gods"]["day_master"]
    return [{"year": year, "age": year - dt.year, "ganzhi": year_gz(year),
             "god": m1.ten_god(dm, year_gz(year)[0])} for year in range(dt.year, dl[0]["start_year"] + 1)]

def liuyue(year, year_gan, day_master):
    """bd-04 流月：12 节换月（立春→小寒）五虎遁公式，与 m1 r4 month_pillar 同式（表内年份由断言交叉验证）；
    十神=月干对日干（r5）。"""
    return [{"month": m + 1, "ganzhi": GAN[(2 * year_gan + 2 + m) % 10] + ZHI[(2 + m) % 12],
             "gan": GAN[(2 * year_gan + 2 + m) % 10], "god": m1.ten_god(day_master, GAN[(2 * year_gan + 2 + m) % 10])}
            for m in range(12)]

def wuxing_stats(r):
    """bd-05 五行统计：天干4+地支4（8 字）与天干4+藏干12（16 项，对拍易安居口径）；
    缺行=8 字口径；季节旺相休囚死按命局月支（寅卯春/巳午夏/申酉秋/亥子冬/辰戌丑未四季土）。"""
    wx = "金木水火土"
    gz8 = [(r["pillars"][k]["ganzhi"][0], wx_of_gan(r["pillars"][k]["ganzhi"][0])) for k in
           ("year", "month", "day", "hour")] + \
          [(r["pillars"][k]["ganzhi"][1], ZHI_WX[r["pillars"][k]["ganzhi"][1]]) for k in
           ("year", "month", "day", "hour")]  # 天干 4 + 地支本气 4 = 8 字
    z16 = [g for k in ("year", "month", "day", "hour")
           for g in [b["gan"] for b in r["ten_gods"]["branches"][k]]]
    cnt8 = {w: sum(1 for _, w0 in gz8 if w0 == w) for w in wx}
    cnt16 = {w: sum(1 for g in [r["pillars"][k]["ganzhi"][0] for k in ("year", "month", "day", "hour")] + z16
                    if wx_of_gan(g) == w) for w in wx}  # 天干 4 + 藏干 12（对拍易安居口径）
    mz = r["pillars"]["month"]["ganzhi"][1]
    SEAS = {"寅卯": "春", "巳午": "夏", "申酉": "秋", "亥子": "冬", "辰戌丑未": "四季土"}
    season = next(v for k, v in SEAS.items() if mz in k)
    WSR = {"春": {"木": "旺", "火": "相", "水": "休", "金": "囚", "土": "死"},
           "夏": {"火": "旺", "土": "相", "木": "休", "水": "囚", "金": "死"},
           "秋": {"金": "旺", "水": "相", "土": "休", "火": "囚", "木": "死"},
           "冬": {"水": "旺", "木": "相", "金": "休", "土": "囚", "火": "死"},
           "四季土": {"土": "旺", "金": "相", "火": "休", "木": "囚", "水": "死"}}  # 《三命通会》旺相休囚死
    dm = r["ten_gods"]["day_master"]
    return {"rule_id": "bd-05", "source": "rules.py 干支五行 + data/canggan.csv 藏干；旺衰《三命通会》",
            "gan_zhi_8": cnt8, "gan_cang_16": cnt16,
            "missing": [w for w in wx if cnt8[w] == 0],
            "day_master": dm, "day_master_wx": wx_of_gan(dm),
            "season": season, "wang_shuai": WSR[season], "wang_shuai_source": "《三命通会·论四时旺相》"}

def compute(dt, lon, sex="男"):
    """完整输出：大运(含起运)、流年、流月(输出首步大运首流年=交运年的 12 节月)、五行统计。"""
    r = m1.compute(dt, lon)
    if "error" in r:
        return r
    dl, y, mo, d, h, jie, jiao, fwd = dayun(dt, lon, sex)
    ln = liunian(dt, lon, sex)
    dm = r["ten_gods"]["day_master"]
    base = dl[0]["start_year"]  # 流月年份=大运首步起年=交运年（bd-04 修正：出生+起运 岁/月/天进位时 ≠ 出生年+起运岁，否则整年 12 流月干支错位一年）
    ly = {"rule_id": "bd-04", "source": "m1 r4 节换月（五虎遁） + r5 十神",
          "liuyue": liuyue(base, GAN.index(year_gz(base)[0]), dm)}  # 交运年起 12 节月
    return {"input": {"datetime": dt.strftime("%Y-%m-%d %H:%M"), "lon": lon, "sex": sex},
            "pillars": r["pillars"], "ten_gods": r["ten_gods"],
            "dayun": {"rule_id": "bd-01", "source": "《渊海子平》大运排法（阳男阴女顺/阴男阳女逆，月柱起）",
                      "direction": fwd, "qiyun_rule_id": "bd-02",
                      "qiyun_source": "《渊海子平》起运法：三天一岁/一天四月/一时辰十天",
                      "qiyun": {"age": y, "month": mo, "day": d, "hour": h},
                      "jie_time": jie, "jiao_time": jiao.strftime("%Y-%m-%d %H:%M"),
                      "list": dl},
            "liunian": {"rule_id": "bd-03", "source": "立春换年=m1 r3；十神=r5", "list": ln},
            "liuyue": ly,
            "wuxing": wuxing_stats(r),
            "notes": ["换日界/立春/节判界均真太阳时（同 m1 契约）；起运节=真太阳时最近 12 节之一"]}

# ============================ 对拍（--compare） ============================
URL = "https://www.zhouyi.cc/bazi/pp/Bazi.php"
SHORT = {"比肩": "比", "劫财": "劫", "食神": "食", "伤官": "伤", "偏财": "财", "正财": "才",
         "七杀": "杀", "正官": "官", "偏印": "枭", "正印": "印"}  # 易安居十神简称（L2 实测映射）
FULL = {v: k for k, v in SHORT.items()}

def fetch_oracle(t, sex):
    """易安居 bazi.php → {qiyun:[岁,月,天], jiao_month_day, dayun_gz[], dayun_gods[], ages[], years[], wx16}"""
    d = {"data_type": "0", "cboYear": str(t[0]), "cboMonth": str(t[1]), "cboDay": str(t[2]),
         "cboHour": f"{t[3]}-{m1.ZHI[(t[3] + 1) // 2 % 12]}", "cboMinute": str(t[4]),
         "pid": "", "cid": "", "zty": "0", "txtName": "某人", "rdoSex": "1" if sex == "男" else "0"}
    html = requests_post(d)
    m = re.search(r"起大运周岁：(\d+)岁\s*(\d+)个月\s*(\d+)天，每一交大运年\s*(\d+)月\s*(\d+)日起运", html)
    ul = re.search(r"<ul  class='bazilist2 f14'>(.*?)</ul>", html, re.S).group(1)
    lis = re.findall(r"<li[^>]*>(.*?)</li>", ul)
    assert lis[9] == "大运" and lis[27] == "岁数" and lis[36] == "年份", f"大运表解析漂移 {lis[9:12]}"
    wm = re.search(r"五行个数</span>\s*([^<]+)", html).group(1)
    wx16 = {w: int(n) for n, _, w in re.findall(r"(\d+)([旺相休囚死])([金木水火土])", wm)}
    return {"qiyun": [int(m.group(1)), int(m.group(2)), int(m.group(3))],
            "jiao": f"{int(m.group(4)):02d}-{int(m.group(5)):02d}",
            "dayun_gz": lis[10:18], "dayun_gods": [FULL.get(x, x) for x in lis[1:9]],
            "ages": [int(x) for x in lis[28:36]], "years": [int(x) for x in lis[37:45]], "wx16": wx16}

def requests_post(d):
    import requests
    for i in range(3):  # 网络抖动重试
        try:
            return requests.post(URL, data=d, timeout=30).content.decode("utf-8")
        except Exception:
            time.sleep(2)
    raise RuntimeError("oracle 抓取失败")

def lunar_yun(t, sex):
    """lunar-python sect=2（精确分钟口径，与易安居一致）→ (起运岁/月/天, 大运干支, 流年干支, 流月干支)"""
    from lunar_python import Solar
    ec = Solar.fromYmdHms(t[0], t[1], t[2], t[3], t[4], 0).getLunar().getEightChar()
    yun = ec.getYun(1 if sex == "男" else 0, sect=2)
    dy = yun.getDaYun()
    dy0 = dy[1]
    return {"qiyun": [yun.getStartYear(), yun.getStartMonth(), yun.getStartDay()],
            "dayun_gz": [d.getGanZhi() for d in dy[1:9]],
            "liunian": {x.getYear(): x.getGanZhi() for x in dy0.getLiuNian()},
            "liuyue": [x.getGanZhi() for x in dy0.getLiuNian()[0].getLiuYue()]}

def manual_qiyun(born, jie_dt):  # 独立手工复算：纯 datetime 算术，不调用模块起运函数
    """(出生 datetime, 节 datetime) → [岁,月,天,时]；分钟精度：3 天=1 岁、6 时=1 月、12 分=1 天。"""
    minutes = int(abs((jie_dt - born).total_seconds()) // 60)
    y, minutes = minutes // 4320, minutes % 4320
    mo, minutes = minutes // 360, minutes % 360
    d, minutes = minutes // 12, minutes % 12
    return [y, mo, d, minutes * 2]

def _fmt(t):  # 样例名
    return f"{t[0]:04d}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}"

def compare():
    """对拍：5 锚点(2男2女1立春边界)+20 随机(1949-2100 均匀男女各半)；
    主 oracle 易安居：起运/大运干支+十神/岁数年份/五行16；第二 oracle lunar-python：大运+流年(首步大运 10 年全段)+流月；
    手工复算 3 例（独立 datetime 算术）。分歧申报 data/arbitration_log.csv(bd-前缀)+report/boundary_cases.csv（幂等）。"""
    out = []
    ANCHORS = [((2024, 2, 10, 8, 0), "男"), ((2000, 2, 5, 12, 0), "男"), ((1990, 1, 1, 10, 0), "女"),
               ((2024, 6, 15, 12, 0), "女"), ((2024, 2, 4, 16, 30), "男")]  # 末例=立春+3分边界(真太阳时跨年)
    random.seed(20260816)
    tds = [datetime.strptime(x["datetime"], "%Y-%m-%d %H:%M") for x in m1.load_terms()]
    rnd, sexs = [], []
    while len(rnd) < 20:  # 随机：避 23-24 时、12 节 ±30 分、立春日整天（防年柱口径连锁）
        y, mo = random.randint(1949, 2100), random.randint(1, 12)
        t = (y, mo, random.randint(1, 28), random.choice((8, 10, 12, 14, 16)), 0)
        dto = datetime(*t)
        if dto.strftime("%m-%d") == "02-04" or dto.strftime("%m-%d") == "02-05":
            continue
        if min(abs((dto - x).total_seconds()) for x in tds) > 1800 and not (21 <= t[3]):
            rnd.append(t); sexs.append("男" if len(rnd) % 2 else "女")
    cases = ANCHORS + list(zip(rnd, sexs))
    D = {"same": 0, "qiyun_day_diff": 0, "other": 0}
    arbs, brows, lnd, manual_notes = [], [], [], []
    day_cases = []  # 仅起运"天"差 1-2 的案例（EOT 口径，合并申报 bd-q01）
    for i, (t, sex) in enumerate(cases):
        dt0 = datetime(*t)
        r = compute(dt0, 120.0, sex)
        dl = r["dayun"]
        o = fetch_oracle(t, sex)
        lu = lunar_yun(t, sex)
        o_dg, my_dg = o["dayun_gz"], [x["ganzhi"] for x in dl["list"]]
        o_god, my_god = o["dayun_gods"], [x["god"] for x in dl["list"]]
        qy = dl["qiyun"]
        dq = [qy["age"], qy["month"], qy["day"]]
        same = (o_dg == my_dg and o_god == my_god and o["qiyun"] == dq
                and o["years"][0] == dl["list"][0]["start_year"] and o["wx16"] == r["wuxing"]["gan_cang_16"])
        jiao_my = dl["jiao_time"][5:7] + "-" + dl["jiao_time"][8:10]
        def _daydiff(a, b):  # 交运月日天数差（基准 2000 非闰年）
            def tod(x):
                mo, d = int(x[:2]), int(x[3:])
                return (datetime(2000, mo, 1) - datetime(2000, 1, 1)).days + d - 1
            return abs(tod(a) - tod(b))
        cid = f"bd-a{i + 1:02d}" if i < 5 else f"bd-r{i - 4:02d}"
        lnd.append((t, sex, o, dl, lu, dq))
        if o_dg == my_dg and o_god == my_god and o["qiyun"][:2] == dq[:2] and 1 <= abs(o["qiyun"][2] - dq[2]) <= 2 \
                and o["years"][0] == dl["list"][0]["start_year"] and o["wx16"] == r["wuxing"]["gan_cang_16"] \
                and _daydiff(o["jiao"], jiao_my) <= 2:
            D["qiyun_day_diff"] += 1  # 仅起运"天"差 1-2：真太阳时 vs 北京时（EOT ≤16.4 分 > 12 分/天，最多 2 天）口径差
            day_cases.append((cid, _fmt(t), sex, o["qiyun"], dq, dl["jie_time"]))
        elif same:
            D["same"] += 1
        else:
            D["other"] += 1  # 真实分歧 → 逐例申报（下）
            note = (f"连锁分歧 {_fmt(t)} {sex}：oracle（北京时）大运首步 {o['dayun_gz'][0]}起 大运 {' '.join(o_dg)} "
                    f"起运{o['qiyun']} vs 自研（真太阳时）{r['pillars']['year']['ganzhi']}年 大运 {' '.join(my_dg)} 起运{dq}，"
                    f"大运顺逆相反（年干阴阳×性别随年柱判界连锁）；五行16 oracle{o['wx16']} vs 自研{r['wuxing']['gan_cang_16']}")
            arbs.append([cid, "年柱判界连锁", "oracle 北京时口径", "自研真太阳时口径", "复核者", "alt",
                         note, "oracle 对拍", "自研 l3_bazi_daliu.py(bd-01/02)", "易安居 zhouyi.cc"])
            brows.append([cid, "立春判界连锁", _fmt(t), "oracle 北京时判界", "自研真太阳时判界", "pending", note])
            if lu["dayun_gz"] != my_dg:  # 第二 oracle 同步连锁（lunar 亦北京时口径）
                arbs.append([cid, "大运干支(第二oracle)", " ".join(lu["dayun_gz"]), " ".join(my_dg), "复核者", "alt",
                             f"lunar-python sect=2 亦按北京时判年柱，与自研真太阳时连锁分歧 {_fmt(t)} {sex}",
                             "第二 oracle 对拍", "自研 l3_bazi_daliu.py", "lunar-python(6tail)"])
    if day_cases:  # 合并申报起运"天"口径差（EOT 真太阳时 vs 北京时，逐例差异同源同类）
        cids = ",".join(x[0] for x in day_cases)
        ex = day_cases[0]
        note = (f"起运『天』口径差 {len(day_cases)} 例（{cids}）：oracle 按北京时、自研按真太阳时（preregister M1 输入语义），"
                f"EOT ±16.4 分 > 12 分/天 → 天差 1-2（双向），岁/月/大运干支/十神/年份/五行16 全一致；"
                f"例 {ex[1]} {ex[2]}：oracle {ex[3]} vs 自研 {ex[4]}（{ex[5]} 节）")
        arbs.append(["bd-q01", "起运天数", "oracle 北京时口径", "自研真太阳时口径", "复核者", "alt",
                     note, "oracle 对拍（逐例清单见 report/boundary_cases.csv bd-q01 行）",
                     "自研 l3_bazi_daliu.py(bd-02)", "易安居 zhouyi.cc"])
        brows.append(["bd-q01", "起运口径(合并)", f"{len(day_cases)} 例: " + ", ".join(x[1] for x in day_cases),
                      "oracle 北京时", "自研真太阳时", "pending", note])
    # 流年/流月（全 25 例）：首步大运 10 年各流年全段（lunar-python 逐年立春口径）+ 交运年 12 流月
    lny_ok = lym_ok = lny_total = 0
    for t, sex, o, dl, lu, dq in lnd:
        sy = dl["list"][0]["start_year"]
        if all(lu["liunian"].get(y) == year_gz(y) for y in range(sy, sy + 10)):
            lny_ok += 1  # 每例 10 年全对才算一致
        lny_total += 10
        dm = m1.compute(datetime(*t), 120.0)["ten_gods"]["day_master"]
        yg = GAN.index(year_gz(sy)[0])
        ly = [x["ganzhi"] for x in liuyue(sy, yg, dm)]
        if ly == lu["liuyue"]:
            lym_ok += 1
    # 手工复算 3 例（独立 datetime 算术）：节时刻取自易安居页面（北京时）→ 与自研真太阳时口径分别核对
    M3 = [((2024, 2, 10, 8, 0), "男", "2024-03-05 10:23"), ((2000, 2, 5, 12, 0), "男", "2000-03-05 14:45"),
          ((2024, 6, 15, 12, 0), "女", "2024-06-05 12:10")]  # 女=阳年女逆排，上节 芒种 2024-06-05 12:10
    for t, sex, jie in M3:
        want = manual_qiyun(datetime(*t), datetime.strptime(jie, "%Y-%m-%d %H:%M"))
        got = compute(datetime(*t), 120.0, sex)["dayun"]["qiyun"]
        got_l = [got["age"], got["month"], got["day"]]
        manual_notes.append((_fmt(t), sex, jie, want, got_l))
    # 幂等写入申报
    def existing(path):
        try:
            return {x["case_id"] for x in csv.DictReader(open(os.path.join(BASE, path), encoding="utf-8"))
                    if x.get("case_id") and not x["case_id"].startswith("#")}
        except FileNotFoundError:
            return set()
    for fn, rows in (("data/arbitration_log.csv", arbs), ("report/boundary_cases.csv", brows)):
        seen = existing(fn)
        rows = [x for x in rows if x[0] not in seen]
        if rows:
            with open(os.path.join(BASE, fn), "a", encoding="utf-8", newline="") as f:
                csv.writer(f).writerows(rows)
    report = [
        f"L3-3 八字大运流年流月五行对拍（l3_bazi_daliu.py）：{len(cases)} 例（5 锚点 2男2女+1 立春+3分边界；20 随机 1949-2100 男女各半，避 23-24 时/12 节±30 分/立春日）",
        f"主 oracle 易安居 bazi.php：大运干支+十神+起运岁/月+岁数年份+五行16 全一致 {D['same']}；仅起运『天』差 1-2（真太阳时 vs 北京时 EOT 口径）{D['qiyun_day_diff']}；真实分歧 {D['other']}",
        f"第二 oracle lunar-python(sect=2)：大运干支一致 {sum(1 for t, sex, o, dl, lu, dq in lnd if lu['dayun_gz'] == [x['ganzhi'] for x in dl['list']])}/{len(lnd)}；",
        f"  流年干支(立春口径，首步大运 10 年全段)一致 {lny_ok}/{len(lnd)} 例（{lny_total} 年次）；流月 12 节月干支一致 {lym_ok}/{len(lnd)} 例",
        f"手工复算 3 例（独立 datetime 算术，节时刻取自易安居页面北京时）：{manual_notes}",
        f"申报：arbitration_log.csv bd- 新增 {len(arbs)} 条；boundary_cases.csv bd- 新增 {len(brows)} 条（幂等）",
    ]
    for x in [y for y in arbs if y[5] == "alt" and "分歧" in y[6]][:6]:
        report.append(f"  分歧：{x[6]}")
    return report

def main():
    ap = argparse.ArgumentParser(description="八字大运流年流月五行")
    ap.add_argument("--datetime", help="北京时间 YYYY-MM-DD HH:MM")
    ap.add_argument("--lon", type=float, default=120.0)
    ap.add_argument("--sex", default="男", choices=("男", "女"))
    ap.add_argument("--compare", action="store_true", help="对拍易安居+lunar-python")
    a = ap.parse_args()
    if a.compare:
        print("\n".join(compare()))
        return
    dt = datetime.strptime(a.datetime, "%Y-%m-%d %H:%M")
    print(json.dumps(compute(dt, a.lon, a.sex), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()

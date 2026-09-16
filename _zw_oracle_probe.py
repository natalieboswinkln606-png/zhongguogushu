# -*- coding: utf-8 -*-
"""临时探针：易安居紫微斗数排盘（https://www.zhouyi.cc/ziwei/ZiDou.php）抓取+解析（勿入库，仅对拍用）。

响应 UTF-8。命盘网格 = ul.ziweipplist 的 li 流；zweiliB 类 li 分隔 4 条带（巳午未申/辰酉/卯戌/寅丑子亥）；
每条带固定 8n 行 = [星1×n][星2×n][庙旺×n][四化×n][空×n×2][宫名×n][宫支×n]，宫内序=网格序（与宫名行同序）。
行分类（颜色契约）：星行 = 红 #ff0000 主星 + 紫 #800080 辅星；庙旺 = 蓝 #0000ff；四化 = 品红 #e33fba。
表头/流年行 class='ziweili1'/'ziweili5' 跳过。宫名行 = 宫干+十二长生+宫名+岁前神煞（"己临疾厄…"、财帛身宫="庚帝财身…"）。
坑：html.find("li class='ziweili'") 必须带 "<"，否则首行（廉贪天天孤天天天）被切半丢弃致整带偏移。
"""
import os, re, sys
sys.stdout.reconfigure(encoding="utf-8")

def fetch(y, mo, d, h, mi=0, ruen=0):
    """POST 易安居排盘页 → HTML；已抓则读缓存 data/l3_ziwei_oracle_cache/{key}.html（幂等）。"""
    import requests
    key = f"{y}-{mo:02d}-{d:02d}-{h:02d}-{mi:02d}-r{ruen}.html"
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "l3_ziwei_oracle_cache", key)
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    d2 = {'data_type': '0', 'cboYear': str(y), 'cboMonth': str(mo), 'cboDay': str(d),
          'cboHour': f'{h}-时', 'cboMinute': str(mi), 'pid': '', 'cid': '',
          'cboZty': '0', 'rdoPanShi': '0', 'txtName': '某人', 'rdoSex': '1',
          'RenYue': str(ruen)}
    r = requests.post('https://www.zhouyi.cc/ziwei/ZiDou.php', data=d2, timeout=30)
    html = r.content.decode('utf-8', 'replace')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(html)
    return html
PALACES = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄", "迁移", "仆役",
           "官禄", "田宅", "福德", "父母"]
ZHI12 = "子丑寅卯辰巳午未申酉戌亥"
MAIN14 = {"紫微", "天机", "太阳", "武曲", "天同", "廉贞", "天府", "太阴",
          "贪狼", "巨门", "天相", "天梁", "七杀", "破军"}
AUX12 = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存", "擎羊", "陀罗", "火星", "铃星", "天马"}
G2N = {v[0] + v[1]: v for v in MAIN14}  # 两字拆开成 字1+字2 → 星名

def _split_stars(row1, row2):
    """星行对（每宫一行：该宫全部星的首字行 / 次字行，红 #ff0000=主星+辅星，紫=杂曜）→ (主星, 辅星)。
    星名 = 首字行第 i 个红字 + 次字行第 i 个红字（逐位配对，oracle 实测 2026-08-16）。"""
    r1, r2 = [], []
    for t, acc in ((row1, r1), (row2, r2)):
        for col, ch in re.findall(r"<font color=(#\w+)>([^<])</font>", t):
            if col.lower() == "#ff0000":
                acc.append(ch)
    n = min(len(r1), len(r2))
    names = [r1[i] + r2[i] for i in range(n)]
    return [x for x in names if x in MAIN14], [x for x in names if x in AUX12]

def _plain(t):
    return re.sub(r"[\s　]", "", re.sub(r"<[^>]+>", "", t))

def parse_chart(html):
    """→ dict: lunar/ju/minggong/shengong/sihua_legend/panfenxi/palaces{宫名:{zhi,gan,stars,miao,sihua,limit}}"""
    out = {}
    m = re.search(r"农历：([^<]+)", html)
    out["lunar"] = m.group(1).strip() if m else ""
    m = re.search(r"命局：([^<]+)", html)
    out["ju"] = m.group(1).strip() if m else ""
    m = re.search(r"命宫：([^　<]+)", html)
    out["minggong"] = m.group(1) if m else ""
    m = re.search(r"身宫：([^　<]+)", html)
    out["shengong"] = m.group(1) if m else ""
    out["sihua_legend"] = ""
    m = re.search(r"zwboxdib[^>]*>(.*?)</div>", html, re.S)
    if m:
        gy = re.search(r"农历：([一-鿿])", html)
        if gy:
            for span in re.findall(r"<span>([^<]*-[^<]*)</span>", m.group(1)):
                if span.startswith(gy.group(1)):
                    out["sihua_legend"] = span
                    break
    m = re.search(r"命盘分析([\s\S]*?)(?:<div|$)", html)
    out["panfenxi"] = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    i, j = html.find("<li class='ziweili'"), html.find("zwboxdib")
    if i < 0 or j < 0:
        out["palaces"] = {}
        return out
    bands, band = [], {"rows": []}
    for cls, inner in re.findall(r"<li([^>]*)>(.*?)</li>", html[i:j], re.S):
        if "zweiliB" in cls:
            bands.append(band)
            band = {"rows": []}
            continue
        if "ziweili1" in cls or "ziweili5" in cls:
            continue
        band["rows"].append(inner)
    bands.append(band)
    # 宫名行 = <font> 内含宫名（命宫/兄弟…）或「首字+身」（身宫所在宫：财身/福身，oracle 另有错字变体
    # 官身=财帛身、偶身=福德身——缩写不可靠，故宫名一律按地支+命宫支偏移解算，不依赖该字串）。
    by_zhi, mz, sz = {}, None, None  # 支 → 星组信息；命宫支；身宫支（font 含「身」的行）
    for b in bands:
        rows = b["rows"]
        n = len(rows) // 8 if rows else 0
        if not n:
            continue  # 末尾空带（zweiliB 后的残留段）
        if len(rows) != 8 * n:
            out["palaces"] = {}
            return out
        for k in range(n):
            g = "".join(re.findall(r"<font[^>]*>([^<]*)</font>", rows[6 * n + k])).replace("　", "")
            if not any(p in g for p in PALACES) and "身" not in g:
                continue  # 非宫名行（表头/神煞杂行）
            zhi = _plain(rows[7 * n + k])[:1]
            if not zhi:
                continue
            main, aux = _split_stars(rows[k], rows[n + k])
            sh = "".join(re.findall(r"<font[^>]*>([^<])</font>", rows[3 * n + k]))
            mi = "".join(re.findall(r"<font[^>]*>([^<])</font>", rows[2 * n + k]))
            lim = re.search(r"(\d+-\d+|\d+岁)", _plain(rows[7 * n + k]))
            by_zhi[zhi] = {"stars": main, "aux": aux, "sihua": sh, "miao": mi,
                           "gan": _plain(rows[6 * n + k])[0],
                           "limit": lim.group(0) if lim else ""}
            if "身" in g:
                sz = zhi
            if "命" in g:
                mz = zhi  # font 为 命宫 或 命身（子时命身同宫）
    out["shengong_zhi"] = sz
    if mz is None or len(by_zhi) != 12:
        out["palaces"] = {}
        return out
    palaces = {}
    mi = ZHI12.index(mz)
    for zhi, info in by_zhi.items():
        name = PALACES[(mi - ZHI12.index(zhi)) % 12]  # 十二宫序=命宫起逆排（任务书 zw-02 同）
        palaces[name] = dict(info, zhi=zhi, shen=(zhi == sz))
    out["palaces"] = palaces
    return out

def main_positions(p):
    """由 oracle 宫位 → {星名: 地支}；主星=红字配对，辅星=紫字配对（已知 11 辅）。"""
    pos = {}
    aux = {"左辅", "右弼", "文昌", "文曲", "天魁", "天钺", "禄存", "擎羊", "陀罗", "火星", "铃星", "天马"}
    for name, c in p["palaces"].items():
        zhi = c["zhi"]
        if not zhi:
            continue
        stars = c["stars"]
        if not stars:
            continue
        # 星行内 红/紫 各自配对：star1 与 star2 同列字符配对
        for row in (stars[:len(stars) // 2], stars[len(stars) // 2:]):
            pass
        # 需要原始两行——palaces 已拼接，改从 bands 取：重新解析
    return pos

if __name__ == "__main__":
    os.makedirs("data/l3_ziwei_oracle_cache", exist_ok=True)
    SAMPLES = [(2024, 2, 10, 8), (2024, 2, 14, 8), (2024, 3, 11, 8), (2024, 4, 15, 8),
               (2024, 5, 9, 8), (2024, 6, 12, 16), (2024, 8, 15, 8), (2024, 10, 15, 8),
               (2024, 12, 15, 8), (2025, 1, 15, 12), (2025, 3, 1, 14), (2025, 5, 20, 10)]
    for t in SAMPLES:
        p = parse_chart(fetch(*t))
        print("==", t, "|", p["lunar"], "|", p["ju"], "| 命", p["minggong"], "身", p["shengong"],
              "| 四化:", p["sihua_legend"])
        if not p["palaces"]:
            print("   解析失败")
            continue
        for name, c in p["palaces"].items():
            print(f"   {name}({c['zhi']},{c['gan']},{c['limit']}): {c['stars']}  [旺:{c['miao']}] [化:{c['sihua']}]")


# ================= L3-1 全字段对拍（l3_ziwei.py vs oracle 缓存） =================
def cmp_self(samples):
    """samples=[(y,mo,d,h,mi)] → 逐例对拍 {lunar/命身宫/局/主星14/辅星12/宫干/四化} 差异清单。
    返回 [(t, 差异字段 dict)]，一致则 dict 空。"""
    from datetime import datetime
    import l3_ziwei
    diffs = []
    for t in samples:
        key = f"{t[0]}-{t[1]:02d}-{t[2]:02d}-{t[3]:02d}-{t[4]:02d}-r0.html"
        path = os.path.join("data/l3_ziwei_oracle_cache", key)
        if not os.path.exists(path):
            diffs.append((t, {"__missing__": key}))
            continue
        o = parse_chart(open(path, encoding="utf-8").read())
        if not o["palaces"]:
            diffs.append((t, {"__parse_fail__": key}))
            continue
        m = l3_ziwei.compute(datetime(*t))
        if "error" in m:
            diffs.append((t, {"__mine_error__": m["error"]}))
            continue
        d = {}
        if o["lunar"][:5].replace(" ", "") and (m["lunar"]["month"], m["lunar"]["day"]) != \
                (0, 0):  # oracle 农历月日解析
            ol = re.match(r"[一-鿿]{2}年(闰?)([一-鿿]{1,2})月([一-鿿]{1,2})日", o["lunar"])
            if ol:
                lru = "闰" == ol.group(1)
                od = {"初一": 1, "初二": 2, "初三": 3, "初四": 4, "初五": 5, "初六": 6, "初七": 7,
                      "初八": 8, "初九": 9, "初十": 10}.get(ol.group(3), None)
                if od is None:
                    od = {"十一": 11, "十二": 12, "十三": 13, "十四": 14, "十五": 15, "十六": 16,
                          "十七": 17, "十八": 18, "十九": 19, "二十": 20, "廿一": 21, "廿二": 22,
                          "廿三": 23, "廿四": 24, "廿五": 25, "廿六": 26, "廿七": 27, "廿八": 28,
                          "廿九": 29, "三十": 30}.get(ol.group(3), None)
                om = {"正月": 1, "二月": 2, "三月": 3, "四月": 4, "五月": 5, "六月": 6, "七月": 7,
                      "八月": 8, "九月": 9, "十月": 10, "十一月": 11, "十二月": 12}.get(ol.group(2))
                if om is not None and od:
                    if (om, lru, od) != (m["lunar"]["month"], m["lunar"]["is_ruen"], m["lunar"]["day"]):
                        d["lunar"] = f"oracle {om}月{'闰' if lru else ''}{od}日 vs 自研 {m['lunar']['month']}月{'闰' if m['lunar']['is_ruen'] else ''}{m['lunar']['day']}日"
        # 命宫/身宫/局/紫微
        if o["minggong"] != m["minggong"]["zhi"]:
            d["minggong"] = f"oracle {o['minggong']} vs 自研 {m['minggong']['zhi']}"
        if o["shengong"] != m["shengong"]["zhi"]:
            d["shengong"] = f"oracle {o['shengong']} vs 自研 {m['shengong']['zhi']}"
        oju = re.search(r"[水木金土火][二三四五六]", o["ju"])
        if oju and oju.group(0) != m["wuxing_ju"]["name"][0] + m["wuxing_ju"]["name"][1]:
            d["ju"] = f"oracle {oju.group(0)} vs 自研 {m['wuxing_ju']['name']}"
        # 主星/辅星位置（oracle 各宫 → 支）
        opos = {s: c["zhi"] for name, c in o["palaces"].items() for s in c["stars"]}
        oaux = {a: c["zhi"] for name, c in o["palaces"].items() for a in c["aux"]}
        mpos = {s: p["zhi"] for p in m["palaces"] for s in p["stars"]}
        maux = {a: p["zhi"] for p in m["palaces"] for a in p["aux"]}
        if opos != mpos:
            d["main14"] = f"oracle {dict(sorted(opos.items()))} vs 自研 {dict(sorted(mpos.items()))}"
        if oaux != maux:
            d["aux12"] = f"oracle {dict(sorted(oaux.items()))} vs 自研 {dict(sorted(maux.items()))}"
        # 宫干
        ogan = {name: c["gan"] for name, c in o["palaces"].items()}
        mgan = {p["name"]: p["gan"] for p in m["palaces"]}
        if ogan != mgan:
            d["gangans"] = f"oracle {dict(sorted(ogan.items()))} vs 自研 {dict(sorted(mgan.items()))}"
        # 四化：按 (宫名, 化标记) 对比对（oracle 四化行=每宫一格，标记字符非列对齐；
        # 化星=该宫当年四化表的星，直接比对宫+标记避免同宫多星误报）
        ohu, mhu = {}, {}
        for name, c in o["palaces"].items():
            for h in c["sihua"]:
                ohu[(name, h)] = True
        for s in m["sihua"]["items"]:  # 四化星可能是辅星（文昌科/右弼科/左辅科…），查 stars+aux
            p = next(p for p in m["palaces"] if s["star"] in p["stars"] or s["star"] in p["aux"])
            mhu[(p["name"], s["hua"])] = True
        if set(ohu) != set(mhu):
            d["sihua"] = f"oracle {sorted(ohu)} vs 自研 {sorted(mhu)}"
        if d:
            diffs.append((t, d))
    return diffs

# -*- coding: utf-8 -*-
"""gen_solar_terms_raw.py — 节气锚点数据采集三路，时区一律 UTC+8。
路1 HKO 年历文本 T1948c~T2100c.txt，每日一行，节气名在行尾（仅日期）。
路2 HKO 分钟级 2015-2028：2015/16 年历内嵌表(繁体)、2017-2028 官方 XML(24 行按序无名称)、
    2018-2025 SolarTerms24.pdf（每份仅 12 中气，与 XML 对拍后才入库）。
路3 lunar-python 秒级全量 1948-2101（getJieQiTable 东八区）。均流式写 CSV。"""
import csv, io, os, re, sys, time, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "solar_terms_raw")
os.makedirs(RAW, exist_ok=True)
LOG = os.path.join(RAW, "collection_log.md")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TERMS = ["小寒","大寒","立春","雨水","惊蛰","春分","清明","谷雨","立夏","小满","芒种",
         "夏至","小暑","大暑","立秋","处暑","白露","秋分","寒露","霜降","立冬","小雪","大雪","冬至"]
JIE = {"立春","惊蛰","清明","立夏","芒种","小暑","立秋","白露","寒露","立冬","大雪","小寒"}
ZHONG = ["大寒","雨水","春分","谷雨","小满","夏至","大暑","处暑","秋分","霜降","小雪","冬至"]  # 12 中气
TC2CN = {"驚蟄":"惊蛰","穀雨":"谷雨","處暑":"处暑","芒種":"芒种","小滿":"小满"}
EN2CN = {"Moderate Cold":"小寒","Severe Cold":"大寒","Spring Commences":"立春","Spring Showers":"雨水",
         "Insects Waken":"惊蛰","Vernal Equinox":"春分","Bright and Clear":"清明","Corn Rain":"谷雨",
         "Summer Commences":"立夏","Corn Forms":"小满","Corn on Ear":"芒种","Summer Solstice":"夏至",
         "Moderate Heat":"小暑","Great Heat":"大暑","Autumn Commences":"立秋","End of Heat":"处暑",
         "White Dew":"白露","Autumnal Equinox":"秋分","Cold Dew":"寒露","Frost":"霜降",
         "Winter Commences":"立冬","Light Snow":"小雪","Heavy Snow":"大雪","Winter Solstice":"冬至"}
LC_EN2CN = {"XIAO_HAN":"小寒","DA_HAN":"大寒","LI_CHUN":"立春","YU_SHUI":"雨水","JING_ZHE":"惊蛰",
            "CHUN_FEN":"春分","QING_MING":"清明","GU_YU":"谷雨","LI_XIA":"立夏","XIAO_MAN":"小满",
            "MANG_ZHONG":"芒种","XIA_ZHI":"夏至","XIAO_SHU":"小暑","DA_SHU":"大暑","LI_QIU":"立秋",
            "CHU_SHU":"处暑","BAI_LU":"白露","QIU_FEN":"秋分","HAN_LU":"寒露","SHUANG_JIANG":"霜降",
            "LI_DONG":"立冬","XIAO_XUE":"小雪","DA_XUE":"大雪","DONG_ZHI":"冬至"}

def fetch(url, retries=3, timeout=60):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=timeout).read()
        except Exception as e:
            if i == retries - 1:
                raise
            time.sleep(2)

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def collect_dates():  # 路1：1948-2100 每日行文本，行尾节气名
    out = os.path.join(RAW, "hko_dates_1948_2100.csv")
    ok, bad, sample = 0, [], []
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "term", "month", "day"])
        for y in range(1948, 2101):
            try:
                txt = fetch(f"https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T{y}c.txt").decode("utf-8-sig")
            except Exception:
                bad.append(f"{y}: 抓取失败"); continue
            rows = []
            for line in txt.splitlines():
                line = line.strip()
                m = re.match(r"^(\d{4})年(\d{1,2})月(\d{1,2})日", line)
                if not m:
                    continue
                toks = [t for t in line[m.end():].split() if t]
                if toks and TC2CN.get(toks[-1], toks[-1]) in TERMS:  # HKO 中文版节气名实为繁体
                    rows.append((TC2CN.get(toks[-1], toks[-1]), int(m.group(2)), int(m.group(3))))
            if len(rows) != 24:
                bad.append(f"{y}: {len(rows)} 条"); continue
            if not sample:
                sample = rows
            for t, mo, d in rows:
                w.writerow([y, t, mo, d])
            ok += 24
    log(f"## 路1 HKO 年历文本（日期锚定 1948-2100）\n成功 {ok} 行（{ok // 24} 年 × 24）；缺口：{bad or '无'}\n样例（首年首 4 条）：{sample[:4]}\n格式：每行 公曆日期/農曆日期/星期/節氣，节名在行尾，如 `2026年1月5日 十七 星期四 小寒`。")

def collect_minutes():  # 路2：2015-2028 分钟级，xml/yearbook/pdf 三格式
    out = os.path.join(RAW, "hko_minutes_2015_2028.csv")
    ok, bad, sample = 0, [], []
    xml_ref = {}  # {year: {name: (m, d, hm)}} 供 PDF 对拍
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "term", "datetime", "format"])
        def emit(y, name, m, d, hm, fmt):
            nonlocal ok
            w.writerow([y, name, f"{y:04d}-{m:02d}-{d:02d} {hm}", fmt])
            ok += 1
        # XML：2017/2018 在当年年历目录，2019-2028 在 astronomy/data/files
        for y in range(2017, 2029):
            base = "astronomy/data/files" if y >= 2019 else f"astron{y}/files"
            try:
                xml = fetch(f"https://www.hko.gov.hk/tc/gts/{base}/24SolarTerms_{y}.xml").decode("utf-8")
            except Exception:
                bad.append(f"{y} xml: 抓取失败"); continue
            rows = re.findall(r"<M>(\d{2})</M><D>(\d{2})</D><hm>(\d{2}:\d{2})</hm>", xml)
            if len(rows) != 24:
                bad.append(f"{y} xml: {len(rows)} 条"); continue
            if not sample:
                sample = rows[:4]
            ref = {}
            for i, (m, d, hm) in enumerate(rows):
                ref[TERMS[i]] = (int(m), int(d), hm)
                emit(y, TERMS[i], int(m), int(d), hm, "xml")
            xml_ref[y] = ref
        # 年历内嵌表 2015/2016（繁体，表格 6 列：名/日/月/日/日/时间）
        re_yb = re.compile(r'(?:24_solar|solar_terms)[^>]*>\s*([^<]+?)\s*</td>.*?>\s*(\d{1,2})\s*</td>.*?>\s*月\s*</td>.*?>\s*(\d{1,2})\s*</td>.*?>\s*(\d{2}:\d{2})\s*</td>', re.S)
        for y in (2015, 2016):
            try:
                htm = fetch(f"https://www.hko.gov.hk/tc/gts/astron{y}/Solar_Term_{y}.htm").decode("utf-8", "ignore")
            except Exception:
                bad.append(f"{y} 年历: 抓取失败"); continue
            rows = re_yb.findall(htm)
            if len(rows) != 24:
                bad.append(f"{y} 年历: {len(rows)} 条"); continue
            for nm, mo, d, hm in rows:
                emit(y, TC2CN.get(nm, nm), int(mo), int(d), hm, "yearbook")
        # PDF 2018-2025（每份仅 12 中气）：2020-2025 标准 4 行组解析；2018/2019 文本包含性验证
        for y in range(2018, 2026):
            try:
                pdf = fetch(f"https://www.hko.gov.hk/tc/gts/astron{y}/files/{y}SolarTerms24.pdf")
            except Exception:
                bad.append(f"{y} pdf: 抓取失败"); continue
            ref = xml_ref.get(y)
            rows = []
            if y >= 2020:  # 2020-2025：日期行/时间行/中文行/英文行 4 行一组
                lines = PdfReader(io.BytesIO(pdf)).pages[0].extract_text().splitlines()
                i = 0
                while i < len(lines) - 3:
                    p = lines[i].split()  # 日期碎片间会被 pypdf 插空格（'90 2 1/6'→'21/6'）
                    dm = re.match(r"^(\d{1,2})/(\d{1,2})$", "".join(p[1:])) if p else None
                    hm = re.match(r"^(\d{2}:\d{2})\s*$", lines[i + 1].strip())
                    en = lines[i + 3].strip()
                    if (dm and p and int(p[0]) % 30 == 0 and int(p[0]) <= 360
                            and 1 <= int(dm.group(2)) <= 12 and 1 <= int(dm.group(1)) <= 31
                            and hm and en in EN2CN):
                        rows.append((EN2CN[en], int(dm.group(2)), int(dm.group(1)), hm.group(1)))
                        i += 4
                    else:
                        i += 1
            if len(rows) != 12 and ref:  # 2018/2019 或解析不全：文本包含性验证（去空格全文）
                flat_ns = re.sub(r"\s+", "", PdfReader(io.BytesIO(pdf)).pages[0].extract_text())
                rows = [(nm, m, d, hm) for nm, (m, d, hm) in ref.items()
                        if nm in ZHONG and f"{d}/{m}" in flat_ns and hm in flat_ns]
            if len(rows) != 12:
                bad.append(f"{y} pdf: {len(rows)} 条"); continue
            if ref and rows != [(nm, m, d, hm) for nm, (m, d, hm) in ref.items() if nm in ZHONG]:
                bad.append(f"{y} pdf: 与 XML 对拍不一致"); continue
            for nm, mo, d, hm in rows:
                emit(y, nm, mo, d, hm, "pdf")
    log(f"## 路2 HKO 分钟级（2015-2028）\n成功 {ok} 行；缺口：{bad or '无'}\nXML 样例：{sample}\nXML 格式：`<Data><M>01</M><D>05</D><hm>23:39</hm></Data>` 24 行按小寒→冬至顺序、无名称。\n年历表样例：`小寒 | 1 | 月 | 6 | 日 | 00:21`（繁体，2015/2016）。\n2026-2028 交互页 Solar_Term.htm 底层即 ajax 拉 astronomy/data/files XML，已由 XML 覆盖。")

def collect_lunar():  # 路3：lunar-python 秒级全量 1948-2101
    out = os.path.join(RAW, "lunar_terms_1948_2101.csv")
    ok, bad, sample = 0, [], []
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "term", "datetime", "jie_zhong"])
        for y in range(1948, 2102):
            tab = Lunar.fromYmd(y, 6, 15).getJieQiTable()  # 年中取窗，覆盖当年 24 个
            rows = []
            for k, v in tab.items():
                ds = v.toYmdHms()
                if not ds.startswith(f"{y}-"):
                    continue
                name = k if k in TERMS else LC_EN2CN.get(k, "")
                if not name:
                    raise ValueError(f"unknown key {k} in {y}")
                rows.append((name, ds))
            if len(rows) != 24:
                bad.append(f"{y}: {len(rows)} 条"); continue
            if not sample:
                sample = sorted(rows)[:3]
            for name, ds in sorted(rows, key=lambda r: r[1]):
                w.writerow([y, name, ds, "jie" if name in JIE else "zhong"])
            ok += 24
    log(f"## 路3 lunar-python 秒级全量（1948-2101）\n成功 {ok} 行（{ok // 24} 年 × 24）；缺口：{bad or '无'}\n样例（2026 前 3 条）：{sample}\n2026 立春 = 2026-02-04 04:02:08（官方 04:02，一致）。节 12/中气 12 标注。")

def main():
    log(f"# 节气锚点数据采集日志（{time.strftime('%Y-%m-%d %H:%M')}，时区一律 UTC+8）\n")
    collect_dates()
    collect_minutes()
    collect_lunar()
    print("done: dates/minutes/lunar ->", RAW)

if __name__ == "__main__":
    from pypdf import PdfReader
    from lunar_python import Lunar
    main()

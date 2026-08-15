# -*- coding: utf-8 -*-
"""gen_shuowang_raw.py — 朔日锚点数据采集两路，时区一律 UTC+8。
路1 HKO 年历文本 T1948c~T2100c.txt（公历农历对照，先例 gen_solar_terms_raw.py 同源）：
    农历月首行写月名（正月/二月/…/閏二月），其余日子写初X/十X/廿X/三十 → 月名行即朔日。
路2 易安居排盘页反查（5 代表年）：POST Bazi.php，响应「出生农历：二○二四年 正月 初一日 午时」；
    以 lunar-python 朔日预测为中心，d-1/d/d+1 三日内找「初一日」日（月名须匹配，含閏），即为第三方朔日。
均流式写 CSV 到 data/shuowang_raw/，日志 collection_log.md。"""
import csv, os, re, sys, time, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "shuowang_raw")
os.makedirs(RAW, exist_ok=True)
LOG = os.path.join(RAW, "collection_log.md")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MONTH_CN = ["正月", "二月", "三月", "四月", "五月", "六月", "七月", "八月", "九月", "十月", "十一月", "十二月"]
RE_MONTH = re.compile(r"^[閏闰]?(正月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月)$")

def fetch(url, retries=3, timeout=60):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=timeout).read()
        except Exception:
            if i == retries - 1:
                raise
            time.sleep(2)

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def parse_month_name(word):  # 「閏二月」→(2, True)；「正月」→(1, False)
    m = RE_MONTH.match(word)
    if not m:
        return None
    return MONTH_CN.index(m.group(1)) + 1, word[0] in "閏闰"

def collect_hko():  # 路1：1948-2100 年历文本，月名行=朔日（HKO 官方日期锚点）
    out = os.path.join(RAW, "hko_shuo_1948_2100.csv")
    ok, bad, sample = 0, [], []
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "month", "is_ruen", "date"])
        for y in range(1948, 2101):
            try:
                txt = fetch(f"https://www.hko.gov.hk/tc/gts/time/calendar/text/files/T{y}c.txt").decode("utf-8-sig")
            except Exception:
                bad.append(f"{y}: 抓取失败")
                continue
            rows = []
            for line in txt.splitlines():
                m = re.match(r"^(\d{4})年(\d{1,2})月(\d{1,2})日\s+(\S+)", line)
                if not m:
                    continue
                pm = parse_month_name(m.group(4))
                if pm:
                    rows.append((pm[0], pm[1], int(m.group(2)), int(m.group(3))))
            if len(rows) < 12 or len(rows) > 14:
                bad.append(f"{y}: {len(rows)} 条")
                continue
            if not sample:
                sample = rows[:3]
            for mo, leap, md, dd in rows:
                w.writerow([y, mo, 1 if leap else 0, f"{y:04d}-{md:02d}-{dd:02d}"])
            ok += len(rows)
    log(f"## 路1 HKO 年历文本（朔日日期锚点 1948-2100）\n成功 {ok} 行；缺口：{bad or '无'}\n样例（首年首 3 条）：{sample}\n格式：每行 `公曆日期 農曆日 星期 [節氣]`，月首写月名（閏月带閏字），如 `2024年2月10日 正月 星期六`。")

def collect_zhouyi():  # 路2：易安居排盘反查 5 代表年（第三方，尽力而为）
    sys.path.insert(0, BASE)
    import requests
    from lunar_python import LunarMonth, LunarYear
    from datetime import datetime, timedelta

    out = os.path.join(RAW, "zhouyi_shuo_5y.csv")
    YEARS = [1950, 1976, 2000, 2024, 2088]
    CN = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    RE_LN = re.compile(r"出生农历</span>[〇○一二三四五六七八九]{4}年\s*([閏闰]?[正一二三四五六七八九十]+月)(?:&nbsp;|\s+)(初[一二三四五六七八九十]|十[一二三四五六七八九]|廿[一二三四五六七八九]|二十|三十)日")
    URL = "https://www.zhouyi.cc/bazi/pp/Bazi.php"

    def cn_day(s):  # 初一日/初十日/二十日/三十日 → 1..30
        t = s[1:] if s.startswith("初") else s
        if t == "十":
            return 10
        if len(t) == 1:
            return CN[t]
        if t.startswith("廿"):
            return 20 + CN[t[1]]
        if t.startswith("二十"):
            return 20 + (CN[t[2]] if len(t) > 2 else 0)
        if t.startswith("三十"):
            return 30 + (CN[t[2]] if len(t) > 2 else 0)
        return 10 + CN[t[1]]

    def query(y, mo, d):  # 3 次重试，失败返回 None
        form = {"data_type": "0", "cboYear": str(y), "cboMonth": str(mo), "cboDay": str(d),
                "cboHour": "12-午", "cboMinute": "0", "pid": "", "cid": "", "zty": "0",
                "txtName": "某人", "rdoSex": "1"}
        for i in range(3):
            try:
                html = requests.post(URL, data=form, timeout=30).content.decode("utf-8")
                m = RE_LN.search(html)
                if m:
                    return parse_month_name(m.group(1)), cn_day(m.group(2))
                return None
            except Exception:
                if i == 2:
                    return None
                time.sleep(2)
        return None

    def shuo_pred(y):  # lunar 预测公历年内全部朔日（(公历日期, 农历月序, 闰)）
        out_l = []
        for ly in range(y - 1, y + 2):
            for lm in LunarYear.fromYear(ly).getMonths():
                if lm.getYear() != ly:
                    continue
                d = (datetime(2000, 1, 1, 12, 0) + timedelta(days=lm.getFirstJulianDay() - 2451545)).date()
                if y <= d.year <= y and d.year == y:
                    out_l.append((d, lm.getMonth() if lm.getMonth() > 0 else -lm.getMonth(), lm.isLeap()))
        return out_l

    ok, bad, sample = 0, [], []
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "month", "is_ruen", "date"])
        for y in YEARS:
            for d0, mo, leap in shuo_pred(y):
                found = None
                for dd in [d0, d0 - timedelta(days=1), d0 + timedelta(days=1)]:
                    r = query(dd.year, dd.month, dd.day)
                    time.sleep(0.5)  # 节流防反爬
                    if r and r[0] == (mo, leap) and r[1] == 1:
                        found = dd
                        break
                if found is None:
                    bad.append(f"{y}-农历{mo}月{'闰' if leap else ''}: 反查失败（预测朔日 {d0}）")
                    continue
                w.writerow([y, mo, 1 if leap else 0, found.isoformat()])
                if not sample:
                    sample = [y, mo, leap, str(found)]
                ok += 1
    log(f"## 路2 易安居排盘反查（5 代表年 {YEARS}）\n成功 {ok} 行；失败：{bad or '无'}\n样例：{sample}\n方法：POST Bazi.php 取「出生农历」字段，lunar 预测朔日±1 日找「初一日」且月名匹配。")

def main():
    log(f"# 朔日锚点数据采集日志（{time.strftime('%Y-%m-%d %H:%M')}，时区一律 UTC+8）\n")
    collect_hko()
    collect_zhouyi()
    print("done: hko/zhouyi ->", RAW)

if __name__ == "__main__":
    main()

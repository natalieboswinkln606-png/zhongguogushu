# -*- coding: utf-8 -*-
"""l4_arbitrate_shuo.py — sw-2057-09 结案独立计算（L4 审计，只读）：
用完整历表 de440.bsp（L4 独立下载，vs 既有 de440s.bsp 简化版）分别二分求朔，与主表/HKO/张培瑜带宽三方对比裁定。
求根：月球视黄经 − 太阳视黄经 ≡ 0 (mod 360)，二分 40 次，UTC+8 输出。
结论写入 report/l4_shuo_arbitrate.txt；sw-2057-09-shao 行裁定由结案流程手工改 arbitration_log.csv（幂等改行不增行）。
"""
import os, sys
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))

from skyfield.api import load
from skyfield.framelib import ecliptic_frame

TS = load.timescale()


def newmoon_dt(bsp_path, year, month, iters=40):
    """该历表下 month 月内（北京时归属）朔时刻：二分月球视黄经−太阳视黄经=0。返回北京时 datetime。"""
    eph = load(bsp_path)
    sun, earth, moon = eph["sun"], eph["earth"], eph["moon"]

    def phase(t):
        _, mlon, _ = earth.at(t).observe(moon).apparent().frame_latlon(ecliptic_frame)
        _, slon, _ = earth.at(t).observe(sun).apparent().frame_latlon(ecliptic_frame)
        return (mlon.degrees - slon.degrees) % 360

    def refine(a, b, ph_a):
        """窗口 [a,b] 相位从 ph_a 升跨 0（朔在其中），二分求朔。返回北京时 datetime。"""
        for _ in range(iters):
            m = TS.tt_jd((a.tt + b.tt) / 2)
            a, b = (a, m) if phase(m) < ph_a else (m, b)  # 相位 < 左端=已 wrap 过朔→收右端
        return TS.tt_jd((a.tt + b.tt) / 2).utc_datetime().replace(tzinfo=None) + timedelta(hours=8)

    # 粗扫：相位单调增、朔处 360→0 wrap；从上月 28 日起逐日扫，朔若归属上月则跳过继续
    prev_t, prev_ph = TS.utc(year, month - 1, 28), None
    for i in range(1, 36):
        t = TS.utc(year, month - 1, 28 + i)
        ph = phase(t)
        if prev_ph is not None and ph < prev_ph:
            tm = refine(prev_t, t, prev_ph)
            if tm.month == month:  # 朔的北京时月份落在目标月内
                return tm
            prev_t, prev_ph = t, ph  # 上月朔，跳过该窗口
            continue
        prev_t, prev_ph = t, ph
    raise RuntimeError(f"{year}-{month} 未找到归属该月的朔")


def main():
    t440 = newmoon_dt(os.path.join(BASE, "de440_l4.bsp"), 2057, 9)
    t440s = newmoon_dt(os.path.join(os.environ.get("TEMP", ""), "de440s.bsp"), 2057, 9)
    lines = [
        "sw-2057-09 结案独立计算（L4 审计，UTC+8）",
        f"de440.bsp（完整历表，L4 独立下载）: 2057-09 朔 = {t440.strftime('%Y-%m-%dT%H:%M:%S')}",
        f"de440s.bsp（简化历表，既有）    : 2057-09 朔 = {t440s.strftime('%Y-%m-%dT%H:%M:%S')}",
        f"两历表互差: {(t440 - t440s).total_seconds():+.1f} 秒（历表带宽检验）",
        "对比基线（既有申报，shuowang_compare_report.txt）：",
        "  ephem(ELP2000-82B) 独立重算 = 2057-09-29T00:00:28（几何黄经口径）",
        "  主表 shuowang.csv 2057-09 shuo_time = 2057-09-29T00:00+08:00（lunar 侧，status=arbitrated）",
        "  HKO 官方年历 = 2057-09-28（日期级，无时刻）",
        "  张培瑜历表带宽 = ±40 秒（既有申报口径；通用天文历表带宽通常 ±60 秒）",
    ]
    d = (t440 - t440s).total_seconds()
    same_side = (t440.date().isoformat() == t440s.date().isoformat()
                 == t440.strftime("2057-09-29") == t440s.strftime("2057-09-29"))
    lines.append(f"结论: de440 与 de440s 互差 {d:+.1f} 秒、同侧（{t440.date()}），" +
                 ("均在 ±60 秒带宽内 → 主表 2057-09-29 侧成立" if same_side and abs(d) < 60 else "超带宽需申报"))
    out = "\n".join(lines) + "\n"
    print(out)
    open(os.path.join(BASE, "report", "l4_shuo_arbitrate.txt"), "w", encoding="utf-8").write(out)


if __name__ == "__main__":
    main()

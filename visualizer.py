# -*- coding: utf-8 -*-
"""visualizer.py — 中国传统术数现代可视化渲染器与离线 HTML 生成器

功能特性：
1. CLI 工具：python visualizer.py --datetime "2006-06-25 00:30" --gender 女 --out temp/chart.html
2. 八字四柱：传统四列竖排，五行颜色标记（木绿、火红、土褐、金金、水蓝），十神与藏干清晰。
3. 紫微斗数：传统 4x4 回字形 12 宫盘面（中央为命盘元信息，四周顺逆排 12 宫，主星/辅星/煞星列表、四化标签各具特色）。
4. 奇门遁甲：传统九宫格（3x3 洛书排布），显示天盘、地盘、九星、八门、八神。
5. 六爻卦象：本卦变卦对比，六爻纳甲、六亲、六神、世应、动爻全景展现。
6. 零外部依赖：纯内联 CSS + 原生 JS，支持完全离线查看与交互（三方四正高亮、标签页平滑切换）。
"""
import argparse
from datetime import datetime
import json
import os
import sys
from typing import Any, Dict, Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

import api_server
from shushu_schema import (
    BaziChartSchema, ZiweiChartSchema, QimenChartSchema, LiuyaoChartSchema
)

# ==============================================================================
# 五行色彩常量系统
# ==============================================================================

WX_COLOR_MAP = {
    "木": {"text": "#16a34a", "bg": "#f0fdf4", "border": "#86efac", "badge": "#22c55e", "dark": "#4ade80"},
    "火": {"text": "#dc2626", "bg": "#fef2f2", "border": "#fca5a5", "badge": "#ef4444", "dark": "#f87171"},
    "土": {"text": "#b45309", "bg": "#fffbeb", "border": "#fcd34d", "badge": "#d97706", "dark": "#fbbf24"},
    "金": {"text": "#ca8a04", "bg": "#fefce8", "border": "#fde047", "badge": "#eab308", "dark": "#facc15"},
    "水": {"text": "#2563eb", "bg": "#eff6ff", "border": "#93c5fd", "badge": "#3b82f6", "dark": "#60a5fa"},
}

SIHUA_COLOR_MAP = {
    "禄": {"bg": "#16a34a", "text": "#ffffff", "border": "#15803d"},
    "权": {"bg": "#9333ea", "text": "#ffffff", "border": "#7e22ce"},
    "科": {"bg": "#0284c7", "text": "#ffffff", "border": "#0369a1"},
    "忌": {"bg": "#ea580c", "text": "#ffffff", "border": "#c2410c"},
}

# 紫微 4x4 回字形地支环固定坐标 (row, col)
# 4x4 网格：四周 12 宫，中间 (1,1)-(2,2) 留给命盘元信息
ZIWEI_GRID_COORDS = {
    "巳": (0, 0), "午": (0, 1), "未": (0, 2), "申": (0, 3),
    "辰": (1, 0),                               "酉": (1, 3),
    "卯": (2, 0),                               "戌": (2, 3),
    "寅": (3, 0), "丑": (3, 1), "子": (3, 2), "亥": (3, 3),
}

# 奇门 3x3 洛书九宫坐标 (row, col)
# 4 巽 (东南) | 9 离 (正南) | 2 坤 (西南)
# 3 震 (正东) | 5 中 (中央) | 7 兑 (正西)
# 8 艮 (东北) | 1 坎 (正北) | 6 乾 (西北)
QIMEN_GRID_COORDS = {
    4: (0, 0), 9: (0, 1), 2: (0, 2),
    3: (1, 0), 5: (1, 1), 7: (1, 2),
    8: (2, 0), 1: (2, 1), 6: (2, 2),
}


# ==============================================================================
# HTML 模板片段生成器
# ==============================================================================

def render_bazi_html(bazi: BaziChartSchema) -> str:
    """生成八字四柱与大运、旺衰可视化卡片"""
    pillars = bazi.pillars
    keys = ["year", "month", "day", "hour"]
    titles = ["年柱", "月柱", "日柱", "时柱"]

    cards_html = []
    for k, title in zip(keys, titles):
        p = pillars[k]
        wx_g = p.wx_gan
        wx_z = p.wx_zhi
        col_g = WX_COLOR_MAP.get(wx_g, WX_COLOR_MAP["金"])
        col_z = WX_COLOR_MAP.get(wx_z, WX_COLOR_MAP["土"])

        # 藏干 HTML
        cg_html = []
        for cg in p.hidden_stems:
            cg_col = WX_COLOR_MAP.get(cg.wx, WX_COLOR_MAP["金"])
            cg_html.append(f"""
            <div class="cg-item">
                <span class="cg-gan" style="color:{cg_col['badge']}">{cg.gan}</span>
                <span class="cg-god">{cg.god}</span>
                <span class="cg-wx" style="background:{cg_col['bg']}; color:{cg_col['text']}">{cg.wx}</span>
            </div>
            """)

        cards_html.append(f"""
        <div class="pillar-card">
            <div class="pillar-badge">{title}</div>
            <div class="stem-god-tag">{p.stem_god or ""}</div>
            <div class="char-box gan-box" style="border-color:{col_g['border']}; background:linear-gradient(180deg, {col_g['bg']} 0%, #ffffff 100%);">
                <span class="char-text" style="color:{col_g['text']}">{p.gan}</span>
                <span class="wx-subtag" style="background:{col_g['badge']}">{wx_g}</span>
            </div>
            <div class="char-box zhi-box" style="border-color:{col_z['border']}; background:linear-gradient(180deg, {col_z['bg']} 0%, #ffffff 100%);">
                <span class="char-text" style="color:{col_z['text']}">{p.zhi}</span>
                <span class="wx-subtag" style="background:{col_z['badge']}">{wx_z}</span>
            </div>
            <div class="nayin-box">
                <span class="nayin-label">纳音</span>
                <span class="nayin-val">{p.nayin}</span>
            </div>
            <div class="canggan-list">
                <div class="cg-header">藏干十神</div>
                {''.join(cg_html)}
            </div>
        </div>
        """)

    # 大运步骤
    dy = bazi.dayun
    dy_steps_html = []
    for s in dy.steps:
        gan_col = WX_COLOR_MAP.get(api_server.rules.wx_of_gan(s.gan), WX_COLOR_MAP["金"])
        dy_steps_html.append(f"""
        <div class="dayun-step-card">
            <div class="dy-step-idx">第 {s.index} 步</div>
            <div class="dy-ganzhi" style="color:{gan_col['text']}">{s.ganzhi}</div>
            <div class="dy-god">{s.god}</div>
            <div class="dy-years">{s.start_year} - {s.end_year}</div>
            <div class="dy-age">{s.age_start}岁 ~ {s.age_end}岁</div>
        </div>
        """)

    # 旺衰仪表
    ws = bazi.wangshuai
    level_color = {
        "极旺": "#dc2626", "偏旺": "#ea580c", "中和": "#16a34a",
        "偏弱": "#2563eb", "极弱": "#7c3aed"
    }.get(ws.level, "#16a34a")

    return f"""
    <section class="section-container" id="section-bazi">
        <div class="section-header">
            <h2 class="section-title">八字命盘与大运流转</h2>
            <div class="section-meta">日主：<strong>{bazi.day_master} ({api_server.rules.wx_of_gan(bazi.day_master)})</strong> | 综合评级：<span class="ws-tag" style="background:{level_color}">{ws.level} ({ws.score}分)</span></div>
        </div>
        
        <div class="bazi-pillars-grid">
            {''.join(cards_html)}
        </div>

        <div class="bazi-analysis-grid">
            <div class="analysis-card wangshuai-panel">
                <div class="panel-header">
                    <span class="panel-icon">⚖️</span>
                    <h3>日主旺衰判定（三得分析）</h3>
                </div>
                <div class="ws-score-hero">
                    <div class="ws-score-number" style="color:{level_color}">{ws.score}</div>
                    <div class="ws-score-details">
                        <div class="ws-level-badge" style="background:{level_color}">{ws.level}</div>
                        <div class="ws-advice-text">{ws.advice}</div>
                    </div>
                </div>
                <div class="ws-bars-container">
                    <div class="ws-bar-item">
                        <div class="bar-title">得令 (权重 40%): <span>月支 {ws.de_ling.month_zhi} ({ws.de_ling.status}) — {ws.de_ling.score}分</span></div>
                        <div class="bar-track"><div class="bar-fill" style="width:{ws.de_ling.score}%; background:#16a34a"></div></div>
                    </div>
                    <div class="ws-bar-item">
                        <div class="bar-title">得地 (权重 35%): <span>分值 {ws.de_di.score}/{ws.de_di.max_score} ({ws.de_di.score_pct}%)</span></div>
                        <div class="bar-track"><div class="bar-fill" style="width:{ws.de_di.score_pct}%; background:#2563eb"></div></div>
                    </div>
                    <div class="ws-bar-item">
                        <div class="bar-title">得势 (权重 25%): <span>分值 {ws.de_shi.score}/{ws.de_shi.max_score} ({ws.de_shi.score_pct}%)</span></div>
                        <div class="bar-track"><div class="bar-fill" style="width:{ws.de_shi.score_pct}%; background:#ea580c"></div></div>
                    </div>
                </div>
            </div>

            <div class="analysis-card dayun-panel">
                <div class="panel-header">
                    <span class="panel-icon">🔄</span>
                    <h3>大运走势 ({dy.direction}排 · {dy.qiyun.text})</h3>
                    <span class="panel-subinfo">交运时间：{dy.qiyun.jiao_time}</span>
                </div>
                <div class="dayun-steps-scroll">
                    {''.join(dy_steps_html)}
                </div>
            </div>
        </div>
    </section>
    """


def render_ziwei_html(ziwei: ZiweiChartSchema) -> str:
    """生成紫微斗数传统 4x4 回字形 12 宫盘面"""
    palaces_by_zhi = {p.zhi: p for p in ziwei.palaces}

    # 构造 4x4 回字形 DOM
    cells_html = []
    for zhi, (r, c) in ZIWEI_GRID_COORDS.items():
        p = palaces_by_zhi.get(zhi)
        if not p:
            continue

        # 主星
        stars_html = []
        for star in p.stars:
            # 检查是否有四化落于该星
            sh_badge = ""
            for it in ziwei.sihua:
                if it.star == star:
                    col = SIHUA_COLOR_MAP.get(it.hua, {"bg": "#dc2626", "text": "#fff"})
                    sh_badge = f'<span class="sihua-badge" style="background:{col["bg"]}; color:{col["text"]}">{it.hua}</span>'
            stars_html.append(f'<span class="zw-main-star">{star}{sh_badge}</span>')

        # 吉星
        ji_html = [f'<span class="zw-ji-star">{s}</span>' for s in p.ji_stars]
        # 煞星
        sha_html = [f'<span class="zw-sha-star">{s}</span>' for s in p.sha_stars]

        # 宫位三方四正属性
        sanfang_data = ",".join(p.sanfang_sizheng)
        sanfang_zhi_data = ",".join(p.sanfang_sizheng_zhi)

        shen_badge = '<span class="zw-shen-tag">身宫</span>' if p.shen else ""
        is_ming = (p.name == "命宫")
        ming_class = "zw-minggong-cell" if is_ming else ""

        cells_html.append(f"""
        <div class="zw-cell {ming_class}" data-zhi="{zhi}" data-name="{p.name}" data-sanfang="{sanfang_data}" data-sanfang-zhi="{sanfang_zhi_data}" style="grid-row: {r + 1}; grid-column: {c + 1};">
            <div class="zw-cell-header">
                <div class="zw-palace-title">
                    <span class="zw-pname">{p.name}</span>
                    {shen_badge}
                </div>
                <div class="zw-ganzhi-badge">{p.gan}{p.zhi}</div>
            </div>
            <div class="zw-stars-container">
                <div class="zw-main-stars-group">
                    {''.join(stars_html) if stars_html else '<span class="zw-empty-star">无主星</span>'}
                </div>
                <div class="zw-aux-stars-group">
                    <div class="zw-ji-list">{' '.join(ji_html)}</div>
                    <div class="zw-sha-list">{' '.join(sha_html)}</div>
                </div>
            </div>
            <div class="zw-cell-footer">
                <span class="zw-sanfang-tip" title="三方四正：{', '.join(p.sanfang_sizheng)}">四正: {p.sanfang_sizheng[3]}</span>
            </div>
        </div>
        """)

    # 中心命盘元信息
    sihua_summary = " ".join([f"<span class='sihua-tag-pill' style='background:{SIHUA_COLOR_MAP[it.hua]['bg']}'>{it.star}·{it.hua}</span>" for it in ziwei.sihua])

    center_html = f"""
    <div class="zw-center-panel" style="grid-row: 2 / span 2; grid-column: 2 / span 2;">
        <div class="zw-center-title">紫微斗数命盘</div>
        <div class="zw-center-meta-list">
            <div class="center-meta-row"><span>公历日期：</span><strong>{ziwei.input.datetime}</strong></div>
            <div class="center-meta-row"><span>农历干支：</span><strong>{ziwei.lunar.year}年 {ziwei.lunar.month_name}{ziwei.lunar.day}日 ({ziwei.shichen_zhi}时)</strong></div>
            <div class="center-meta-row"><span>五行局局：</span><strong style="color:#d97706">{ziwei.wuxing_ju['name']}</strong></div>
            <div class="center-meta-row"><span>命宫地支：</span><strong>{ziwei.minggong['gan']}{ziwei.minggong['zhi']}</strong> | <span>身宫：</span><strong>{ziwei.shengong['zhi']}</strong></div>
            <div class="center-meta-row"><span>紫微星位：</span><strong>{ziwei.ziwei_star['zhi']}宫</strong></div>
            <div class="center-sihua-box">
                <div class="sihua-box-title">生年四化</div>
                <div class="sihua-pills-row">{sihua_summary}</div>
            </div>
        </div>
        <div class="zw-interactive-tip">💡 悬停或点击任意宫位，即可动态高亮其「三方四正」</div>
    </div>
    """

    return f"""
    <section class="section-container" id="section-ziwei">
        <div class="section-header">
            <h2 class="section-title">紫微斗数 4x4 回字形天盘</h2>
            <div class="section-meta">命宫：{ziwei.minggong['gan']}{ziwei.minggong['zhi']} | 五行局：{ziwei.wuxing_ju['name']} | 身宫：{ziwei.shengong['zhi']}</div>
        </div>
        <div class="zw-board-wrapper">
            <div class="zw-grid-board">
                {center_html}
                {''.join(cells_html)}
            </div>
        </div>
    </section>
    """


def render_qimen_html(qimen: QimenChartSchema) -> str:
    """生成奇门遁甲传统 3x3 洛书九宫格"""
    cells_html = []
    for p_num, (r, c) in QIMEN_GRID_COORDS.items():
        cell = qimen.pan.get(str(p_num))
        if not cell:
            continue

        star_name = cell.star or "—"
        door_name = cell.door or "—"
        shen_name = cell.shen or "—"

        is_zf = (qimen.zhifu_zhishi.zhifu_palace == p_num)
        is_zs = (qimen.zhifu_zhishi.zhishi_palace == p_num)
        role_badges = []
        if is_zf:
            role_badges.append("<span class='qm-role-badge zf-badge'>值符</span>")
        if is_zs:
            role_badges.append("<span class='qm-role-badge zs-badge'>值使</span>")

        # 门吉凶样式
        door_class = "qm-jimen" if door_name in ("开门", "休门", "生门") else ("qm-xiongmen" if door_name in ("死门", "伤门", "惊门") else "qm-zhongmen")

        cells_html.append(f"""
        <div class="qm-cell {'qm-zf-cell' if is_zf else ''}" style="grid-row: {r + 1}; grid-column: {c + 1};">
            <div class="qm-cell-header">
                <span class="qm-palace-num">{cell.palace} {cell.gua}</span>
                <span class="qm-direction">{cell.direction}</span>
                <div class="qm-badges-wrap">{' '.join(role_badges)}</div>
            </div>
            <div class="qm-god-row">
                <span class="qm-shen-tag">神：{shen_name}</span>
                <span class="qm-star-tag">星：{star_name}</span>
            </div>
            <div class="qm-gan-center">
                <div class="qm-tian-gan" title="天盘干">天 <span>{cell.tianpan_gan}</span></div>
                <div class="qm-di-gan" title="地盘干">地 <span>{cell.dipan_gan}</span></div>
            </div>
            <div class="qm-door-row">
                <span class="qm-door-tag {door_class}">{door_name}</span>
            </div>
        </div>
        """)

    # 格局清单
    geju_html = []
    for g in qimen.geju:
        g_col = "#16a34a" if g.type == "吉" else "#dc2626"
        geju_html.append(f"""
        <div class="qm-geju-card" style="border-left: 4px solid {g_col}">
            <div class="geju-title">
                <span class="geju-name">{g.name}</span>
                <span class="geju-type-pill" style="background:{g_col}">{g.type}</span>
                <span class="geju-palace">{g.palace} 宫</span>
            </div>
            <div class="geju-basis">{g.basis}</div>
        </div>
        """)

    dj = qimen.dingju
    zz = qimen.zhifu_zhishi

    return f"""
    <section class="section-container" id="section-qimen">
        <div class="section-header">
            <h2 class="section-title">时家奇门 3x3 洛书九宫盘</h2>
            <div class="section-meta">节气：<strong>{dj.term}</strong> | 遁元：<strong>{dj.dun}{dj.ju}局 ({dj.yuan})</strong> | 旬首：<strong>{zz.xunshou} ({zz.yiyi})</strong></div>
        </div>

        <div class="qimen-layout-grid">
            <div class="qm-board-panel">
                <div class="qm-grid-board">
                    {''.join(cells_html)}
                </div>
            </div>

            <div class="qm-geju-panel">
                <div class="panel-header">
                    <span class="panel-icon">🚩</span>
                    <h3>命中吉凶格局 ({len(qimen.geju)} 项)</h3>
                </div>
                <div class="qm-geju-scroll">
                    {''.join(geju_html) if geju_html else '<div class="no-geju">本局无显著特殊格局</div>'}
                </div>
            </div>
        </div>
    </section>
    """


def render_liuyao_html(liuyao: LiuyaoChartSchema) -> str:
    """生成六爻排盘本卦与变卦对比视图"""
    lines_html = []
    for line in reversed(liuyao.lines):
        is_yang = (line.yao == "九")
        is_bian_yang = (line.bian_yao == "九")
        dong_class = "ly-dong-line" if line.dong else ""
        dong_marker = "<span class='ly-dong-marker'>● 动</span>" if line.dong else ""

        # 本卦爻图
        if is_yang:
            bar_ben = "<div class='yao-bar yang-bar'></div>"
        else:
            bar_ben = "<div class='yao-bar yin-bar'><span class='yin-l'></span><span class='yin-r'></span></div>"

        # 变卦爻图
        if is_bian_yang:
            bar_bian = "<div class='yao-bar yang-bar'></div>"
        else:
            bar_bian = "<div class='yao-bar yin-bar'><span class='yin-l'></span><span class='yin-r'></span></div>"

        lines_html.append(f"""
        <tr class="ly-line-row {dong_class}">
            <td class="ly-shen-cell">{line.shen}</td>
            <td class="ly-qin-cell">{line.qin}</td>
            <td class="ly-ganzhi-cell">{line.gan}{line.zhi} ({line.wx})</td>
            <td class="ly-shiying-cell"><span class="sy-badge">{line.shi_ying}</span></td>
            <td class="ly-bar-cell">{bar_ben}</td>
            <td class="ly-pos-cell">{line.pos}爻 {dong_marker}</td>
            <td class="ly-bar-cell">{bar_bian}</td>
            <td class="ly-shiying-cell"><span class="sy-badge">{line.bian_shi_ying}</span></td>
            <td class="ly-ganzhi-cell">{line.bian_gan}{line.bian_zhi} ({line.bian_wx})</td>
            <td class="ly-qin-cell">{line.bian_qin}</td>
        </tr>
        """)

    bg = liuyao.ben_gua
    vg = liuyao.bian_gua

    return f"""
    <section class="section-container" id="section-liuyao">
        <div class="section-header">
            <h2 class="section-title">周易六爻排盘</h2>
            <div class="section-meta">起卦：<strong>{liuyao.method.get('label', '')}</strong> | 月建：<strong>{liuyao.yue_jian.get('ganzhi', '')}</strong> | 日辰：<strong>{liuyao.ri_chen.get('ganzhi', '')}</strong></div>
        </div>

        <div class="ly-dual-gua-card">
            <div class="ly-gua-header-row">
                <div class="ly-header-side">
                    <h3>本卦：【{bg.name}】</h3>
                    <span class="ly-palace-tag">{bg.palace}宫{bg.order}世 ({bg.up}上{bg.down}下)</span>
                    <p class="ly-guaci">{bg.guaci}</p>
                </div>
                <div class="ly-header-middle">
                    <span class="ly-arrow">➔ 变 ➔</span>
                </div>
                <div class="ly-header-side">
                    <h3>变卦：【{vg.name}】</h3>
                    <span class="ly-palace-tag">{vg.palace}宫{vg.order}世 ({vg.up}上{vg.down}下)</span>
                    <p class="ly-guaci">{vg.guaci}</p>
                </div>
            </div>

            <table class="ly-table">
                <thead>
                    <tr>
                        <th>六神</th>
                        <th>本卦六亲</th>
                        <th>纳甲干支</th>
                        <th>世应</th>
                        <th>本卦爻象</th>
                        <th>爻位</th>
                        <th>变卦爻象</th>
                        <th>世应</th>
                        <th>变卦干支</th>
                        <th>变卦六亲</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(lines_html)}
                </tbody>
            </table>
        </div>
    </section>
    """


# ==============================================================================
# CSS 样式定义（现代化响应式、优雅暗金/素雅设计）
# ==============================================================================

CSS_STYLES = """
:root {
    --bg-main: #f8fafc;
    --bg-card: #ffffff;
    --text-primary: #0f172a;
    --text-secondary: #475569;
    --border-color: #e2e8f0;
    --primary-color: #1e293b;
    --gold-accent: #d97706;
    --card-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05);
    --hover-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.08), 0 4px 6px -4px rgb(0 0 0 / 0.05);
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background-color: var(--bg-main);
    color: var(--text-primary);
    line-height: 1.5;
    padding-bottom: 60px;
}

/* 顶部导航与英雄头 */
.hero-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: #f8fafc;
    padding: 32px 24px;
    border-bottom: 2px solid #d97706;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.hero-container {
    max-width: 1280px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}
.hero-title-wrap h1 {
    font-size: 26px;
    font-weight: 700;
    color: #fbbf24;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}
.hero-subtitle {
    font-size: 13px;
    color: #94a3b8;
}
.hero-meta-bar {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    background: rgba(255,255,255,0.06);
    padding: 10px 18px;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.1);
    font-size: 13px;
}
.hero-meta-bar span strong { color: #fef08a; }

/* 主体容器与导航标签 */
.main-content {
    max-width: 1280px;
    margin: 24px auto;
    padding: 0 20px;
}
.nav-tab-bar {
    display: flex;
    gap: 8px;
    margin-bottom: 24px;
    border-bottom: 2px solid var(--border-color);
    padding-bottom: 8px;
    overflow-x: auto;
}
.nav-tab-btn {
    background: #ffffff;
    border: 1px solid var(--border-color);
    padding: 8px 20px;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 600;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
}
.nav-tab-btn:hover {
    color: var(--gold-accent);
    border-color: var(--gold-accent);
}
.nav-tab-btn.active {
    background: #0f172a;
    color: #fbbf24;
    border-color: #0f172a;
}

/* 区块通用结构 */
.section-container {
    background: var(--bg-card);
    border-radius: 12px;
    box-shadow: var(--card-shadow);
    padding: 24px;
    margin-bottom: 32px;
    border: 1px solid var(--border-color);
}
.section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 14px;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 10px;
}
.section-title {
    font-size: 20px;
    font-weight: 700;
    color: #0f172a;
    border-left: 4px solid var(--gold-accent);
    padding-left: 10px;
}
.section-meta {
    font-size: 13px;
    color: var(--text-secondary);
}

/* ================== 八字四柱与大运 ================== */
.bazi-pillars-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 24px;
}
@media (max-width: 768px) {
    .bazi-pillars-grid { grid-template-columns: repeat(2, 1fr); }
}
.pillar-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    transition: transform 0.2s ease;
}
.pillar-card:hover {
    transform: translateY(-2px);
    border-color: #cbd5e1;
}
.pillar-badge {
    display: inline-block;
    font-size: 12px;
    font-weight: 700;
    color: #475569;
    background: #e2e8f0;
    padding: 2px 10px;
    border-radius: 12px;
    margin-bottom: 6px;
}
.stem-god-tag {
    font-size: 14px;
    font-weight: 600;
    color: #0f172a;
    min-height: 22px;
    margin-bottom: 6px;
}
.char-box {
    border: 2px solid;
    border-radius: 8px;
    padding: 10px 4px;
    margin-bottom: 8px;
    position: relative;
}
.char-text {
    font-size: 32px;
    font-weight: 800;
    line-height: 1;
    display: block;
}
.wx-subtag {
    position: absolute;
    bottom: 4px;
    right: 6px;
    color: #ffffff;
    font-size: 10px;
    padding: 1px 5px;
    border-radius: 4px;
    font-weight: bold;
}
.nayin-box {
    background: #ffffff;
    border: 1px dashed #cbd5e1;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
}
.nayin-label { color: #64748b; }
.nayin-val { font-weight: 600; color: #1e293b; }
.canggan-list {
    background: #ffffff;
    border: 1px solid #f1f5f9;
    border-radius: 6px;
    padding: 6px;
    font-size: 11px;
}
.cg-header {
    color: #94a3b8;
    font-size: 10px;
    margin-bottom: 4px;
    text-align: left;
}
.cg-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 2px 4px;
    border-bottom: 1px solid #f8fafc;
}
.cg-item:last-child { border-bottom: none; }
.cg-gan { font-weight: 700; }
.cg-god { color: #334155; }
.cg-wx { padding: 1px 4px; border-radius: 3px; font-size: 10px; }

/* 旺衰与大运分析面板 */
.bazi-analysis-grid {
    display: grid;
    grid-template-columns: 1fr 1.4fr;
    gap: 20px;
}
@media (max-width: 900px) {
    .bazi-analysis-grid { grid-template-columns: 1fr; }
}
.analysis-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px;
}
.panel-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 14px;
}
.panel-header h3 {
    font-size: 15px;
    font-weight: 700;
    color: #1e293b;
}
.panel-subinfo {
    font-size: 12px;
    color: #64748b;
    margin-left: auto;
}
.ws-score-hero {
    display: flex;
    align-items: center;
    gap: 16px;
    background: #ffffff;
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
    margin-bottom: 14px;
}
.ws-score-number {
    font-size: 40px;
    font-weight: 800;
    line-height: 1;
}
.ws-level-badge {
    display: inline-block;
    color: #ffffff;
    font-size: 12px;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 12px;
    margin-bottom: 4px;
}
.ws-advice-text {
    font-size: 12px;
    color: #475569;
}
.ws-bars-container { display: flex; flex-direction: column; gap: 10px; }
.ws-bar-item .bar-title {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #334155;
    margin-bottom: 4px;
}
.bar-track {
    background: #e2e8f0;
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
}
.bar-fill { height: 100%; border-radius: 4px; }

.dayun-steps-scroll {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
}
@media (max-width: 600px) {
    .dayun-steps-scroll { grid-template-columns: repeat(2, 1fr); }
}
.dayun-step-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 10px 8px;
    text-align: center;
    transition: all 0.2s ease;
}
.dayun-step-card:hover {
    border-color: #d97706;
    box-shadow: 0 2px 6px rgba(217, 119, 6, 0.15);
}
.dy-step-idx { font-size: 11px; color: #94a3b8; margin-bottom: 2px; }
.dy-ganzhi { font-size: 18px; font-weight: 800; margin-bottom: 2px; }
.dy-god { font-size: 12px; font-weight: 600; color: #334155; }
.dy-years { font-size: 11px; color: #64748b; margin-top: 4px; }
.dy-age { font-size: 10px; color: #94a3b8; }

/* ================== 紫微斗数 4x4 回字盘 ================== */
.zw-board-wrapper {
    overflow-x: auto;
    padding: 6px 0;
}
.zw-grid-board {
    display: grid;
    grid-template-columns: repeat(4, minmax(220px, 1fr));
    grid-template-rows: repeat(4, minmax(170px, auto));
    gap: 8px;
    background: #e2e8f0;
    padding: 8px;
    border-radius: 12px;
}
.zw-cell {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.2s ease;
    position: relative;
    cursor: pointer;
}
.zw-cell:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    border-color: #0284c7;
    z-index: 10;
}
.zw-cell.highlight-sanfang {
    background: #f0f9ff !important;
    border: 2px solid #0284c7 !important;
    box-shadow: 0 0 12px rgba(2, 132, 199, 0.3) !important;
}
.zw-cell.active-focus {
    background: #fefce8 !important;
    border: 2px solid #eab308 !important;
}
.zw-minggong-cell {
    border-color: #d97706;
}
.zw-minggong-cell .zw-pname {
    color: #b45309;
    font-weight: 800;
}
.zw-cell-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 6px;
    margin-bottom: 6px;
}
.zw-palace-title {
    display: flex;
    align-items: center;
    gap: 6px;
}
.zw-pname {
    font-size: 15px;
    font-weight: 700;
    color: #1e293b;
}
.zw-shen-tag {
    background: #dc2626;
    color: #ffffff;
    font-size: 10px;
    padding: 1px 5px;
    border-radius: 4px;
    font-weight: bold;
}
.zw-ganzhi-badge {
    font-size: 13px;
    font-weight: 700;
    color: #64748b;
    background: #f1f5f9;
    padding: 1px 6px;
    border-radius: 4px;
}
.zw-stars-container {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 6px;
}
.zw-main-stars-group {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}
.zw-main-star {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    font-size: 15px;
    font-weight: 800;
    color: #0f172a;
    background: #f8fafc;
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid #e2e8f0;
}
.zw-empty-star { font-size: 12px; color: #94a3b8; font-style: italic; }
.sihua-badge {
    font-size: 10px;
    font-weight: 700;
    padding: 1px 4px;
    border-radius: 3px;
}
.zw-aux-stars-group {
    display: flex;
    flex-direction: column;
    gap: 3px;
    font-size: 12px;
}
.zw-ji-list { color: #16a34a; font-weight: 600; }
.zw-sha-list { color: #dc2626; font-weight: 600; }
.zw-cell-footer {
    border-top: 1px solid #f1f5f9;
    padding-top: 4px;
    margin-top: 6px;
    font-size: 10px;
    color: #94a3b8;
    text-align: right;
}

/* 紫微中心天盘 */
.zw-center-panel {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: #f8fafc;
    border-radius: 10px;
    padding: 24px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    border: 2px solid #d97706;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.3);
}
.zw-center-title {
    font-size: 22px;
    font-weight: 800;
    color: #fbbf24;
    text-align: center;
    margin-bottom: 16px;
    letter-spacing: 1px;
}
.zw-center-meta-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    font-size: 13px;
}
.center-meta-row {
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    padding-bottom: 4px;
}
.center-meta-row span { color: #94a3b8; }
.center-meta-row strong { color: #f1f5f9; }
.center-sihua-box {
    margin-top: 10px;
    background: rgba(255,255,255,0.05);
    padding: 10px;
    border-radius: 6px;
}
.sihua-box-title { font-size: 11px; color: #cbd5e1; margin-bottom: 6px; }
.sihua-pills-row { display: flex; gap: 6px; flex-wrap: wrap; }
.sihua-tag-pill {
    color: #ffffff;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
}
.zw-interactive-tip {
    margin-top: 14px;
    font-size: 11px;
    color: #fbbf24;
    text-align: center;
    background: rgba(251, 191, 36, 0.1);
    padding: 4px 8px;
    border-radius: 4px;
}

/* ================== 奇门遁甲九宫 ================== */
.qimen-layout-grid {
    display: grid;
    grid-template-columns: 1.4fr 1fr;
    gap: 20px;
}
@media (max-width: 900px) {
    .qimen-layout-grid { grid-template-columns: 1fr; }
}
.qm-board-panel {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 12px;
}
.qm-grid-board {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(3, 1fr);
    gap: 8px;
}
.qm-cell {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 10px;
    min-height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: all 0.2s ease;
}
.qm-cell:hover {
    border-color: #d97706;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.qm-zf-cell {
    border: 2px solid #d97706;
    background: #fffdf5;
}
.qm-cell-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    font-weight: 700;
    color: #1e293b;
    border-bottom: 1px solid #f1f5f9;
    padding-bottom: 4px;
}
.qm-direction { font-size: 10px; color: #64748b; }
.qm-badges-wrap { display: flex; gap: 2px; }
.qm-role-badge {
    color: #ffffff;
    font-size: 10px;
    padding: 1px 4px;
    border-radius: 3px;
    font-weight: bold;
}
.zf-badge { background: #d97706; }
.zs-badge { background: #2563eb; }
.qm-god-row {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    font-weight: 600;
}
.qm-shen-tag { color: #9333ea; }
.qm-star-tag { color: #0284c7; }
.qm-gan-center {
    display: flex;
    justify-content: space-around;
    align-items: center;
    margin: 8px 0;
}
.qm-tian-gan, .qm-di-gan {
    font-size: 12px;
    color: #64748b;
}
.qm-tian-gan span, .qm-di-gan span {
    font-size: 20px;
    font-weight: 800;
    color: #0f172a;
    display: inline-block;
    margin-left: 2px;
}
.qm-door-row {
    text-align: center;
    border-top: 1px solid #f1f5f9;
    padding-top: 4px;
}
.qm-door-tag {
    display: inline-block;
    font-size: 13px;
    font-weight: 700;
    padding: 1px 12px;
    border-radius: 4px;
}
.qm-jimen { background: #f0fdf4; color: #16a34a; border: 1px solid #86efac; }
.qm-xiongmen { background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }
.qm-zhongmen { background: #f8fafc; color: #475569; border: 1px solid #cbd5e1; }

.qm-geju-panel {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 16px;
    display: flex;
    flex-direction: column;
}
.qm-geju-scroll {
    max-height: 480px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding-right: 4px;
}
.qm-geju-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 10px 12px;
}
.geju-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
}
.geju-name { font-size: 14px; font-weight: 700; color: #1e293b; }
.geju-type-pill {
    color: #ffffff;
    font-size: 10px;
    font-weight: bold;
    padding: 1px 6px;
    border-radius: 3px;
}
.geju-palace { font-size: 11px; color: #64748b; margin-left: auto; }
.geju-basis { font-size: 12px; color: #475569; line-height: 1.4; }

/* ================== 六爻排盘 ================== */
.ly-dual-gua-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 20px;
}
.ly-gua-header-row {
    display: flex;
    justify-content: space-around;
    align-items: center;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 16px;
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 16px;
}
.ly-header-side { text-align: center; max-width: 420px; }
.ly-header-side h3 { font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 4px; }
.ly-palace-tag { display: inline-block; font-size: 12px; background: #e2e8f0; padding: 2px 8px; border-radius: 4px; color: #475569; margin-bottom: 6px; }
.ly-guaci { font-size: 12px; color: #64748b; font-style: italic; }
.ly-arrow { font-size: 16px; font-weight: bold; color: #d97706; }

.ly-table {
    width: 100%;
    border-collapse: collapse;
    background: #ffffff;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.ly-table th {
    background: #0f172a;
    color: #f8fafc;
    font-size: 12px;
    font-weight: 600;
    padding: 10px 8px;
    text-align: center;
}
.ly-table td {
    padding: 10px 8px;
    text-align: center;
    font-size: 13px;
    border-bottom: 1px solid #f1f5f9;
}
.ly-line-row:hover { background: #f8fafc; }
.ly-dong-line { background: #fffdf5; }
.ly-dong-marker { color: #dc2626; font-size: 10px; font-weight: bold; }
.yao-bar {
    width: 80px;
    height: 12px;
    margin: 0 auto;
    border-radius: 2px;
}
.yang-bar { background: #1e293b; }
.yin-bar { display: flex; justify-content: space-between; }
.yin-bar span { width: 34px; height: 100%; background: #1e293b; border-radius: 2px; }
.ly-dong-line .yang-bar { background: #dc2626; }
.ly-dong-line .yin-bar span { background: #dc2626; }
.sy-badge { font-weight: bold; color: #d97706; }
"""

# ==============================================================================
# JavaScript 交互（离线纯内联）
# ==============================================================================

JS_SCRIPTS = """
document.addEventListener('DOMContentLoaded', () => {
    // 1. 导航标签页切换
    const tabBtns = document.querySelectorAll('.nav-tab-btn');
    const sections = {
        'bazi': document.getElementById('section-bazi'),
        'ziwei': document.getElementById('section-ziwei'),
        'qimen': document.getElementById('section-qimen'),
        'liuyao': document.getElementById('section-liuyao')
    };

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.getAttribute('data-target');
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            if (target === 'all') {
                Object.values(sections).forEach(sec => sec.style.display = 'block');
            } else {
                Object.keys(sections).forEach(k => {
                    sections[k].style.display = (k === target) ? 'block' : 'none';
                });
            }
        });
    });

    // 2. 紫微斗数 4x4 回字盘 三方四正动态高亮
    const zwCells = document.querySelectorAll('.zw-cell');
    zwCells.forEach(cell => {
        cell.addEventListener('mouseenter', () => {
            const sanfangStr = cell.getAttribute('data-sanfang') || '';
            const sanfangList = sanfangStr.split(',').map(s => s.trim());

            zwCells.forEach(c => {
                const cName = c.getAttribute('data-name');
                if (c === cell) {
                    c.classList.add('active-focus');
                } else if (sanfangList.includes(cName)) {
                    c.classList.add('highlight-sanfang');
                } else {
                    c.classList.remove('highlight-sanfang', 'active-focus');
                }
            });
        });

        cell.addEventListener('mouseleave', () => {
            zwCells.forEach(c => c.classList.remove('highlight-sanfang', 'active-focus'));
        });
    });
});
"""


# ==============================================================================
# 核心 HTML 页面生成函数
# ==============================================================================

def generate_chart_html(datetime_str: str, gender: str = "女", lon: float = 120.0) -> str:
    """给定时间、性别、经度，调用内核并生成完整精美的离线 HTML 页面"""
    dt = api_server.parse_datetime(datetime_str)

    # 1. 调用四大盘面
    bazi_chart = api_server.build_bazi_chart(dt, gender, lon)
    ziwei_chart = api_server.build_ziwei_chart(dt, lon, gender)
    qimen_chart = api_server.build_qimen_chart(dt, lon)
    liuyao_chart = api_server.build_liuyao_chart(dt, lon, mode="lunar")

    # 2. 渲染各模块 HTML
    bazi_section = render_bazi_html(bazi_chart)
    ziwei_section = render_ziwei_html(ziwei_chart)
    qimen_section = render_qimen_html(qimen_chart)
    liuyao_section = render_liuyao_html(liuyao_chart)

    # 3. 组装全局单文件 HTML
    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>中国传统术数全景排盘系统 — {datetime_str} ({gender})</title>
    <style>
{CSS_STYLES}
    </style>
</head>
<body>
    <header class="hero-header">
        <div class="hero-container">
            <div class="hero-title-wrap">
                <h1>中国传统术数工程化全景排盘</h1>
                <div class="hero-subtitle">四柱八字 · 紫微斗数 · 时家奇门 · 周易六爻</div>
            </div>
            <div class="hero-meta-bar">
                <span>出生时间：<strong>{datetime_str}</strong></span>
                <span>性别：<strong>{gender}</strong></span>
                <span>东经经度：<strong>{lon}°</strong></span>
                <span>真太阳时：<strong>{bazi_chart.input.true_solar_time or ''}</strong></span>
            </div>
        </div>
    </header>

    <main class="main-content">
        <nav class="nav-tab-bar">
            <button class="nav-tab-btn active" data-target="all">全景总览 (全部)</button>
            <button class="nav-tab-btn" data-target="bazi">八字四柱与大运</button>
            <button class="nav-tab-btn" data-target="ziwei">紫微斗数 4x4 回字盘</button>
            <button class="nav-tab-btn" data-target="qimen">时家奇门 3x3 洛书盘</button>
            <button class="nav-tab-btn" data-target="liuyao">周易六爻排卦</button>
        </nav>

        {bazi_section}
        {ziwei_section}
        {qimen_section}
        {liuyao_section}
    </main>

    <script>
{JS_SCRIPTS}
    </script>
</body>
</html>
"""
    return full_html


# ==============================================================================
# CLI 主入口
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="中国传统术数全景排盘可视化生成器")
    parser.add_argument("--datetime", required=True, help="出生北京时间，格式 'YYYY-MM-DD HH:MM'")
    parser.add_argument("--gender", default="女", choices=["男", "女"], help="性别：'男' 或 '女'（默认 女）")
    parser.add_argument("--lon", type=float, default=120.0, help="东经经度（默认 120.0）")
    parser.add_argument("--out", default="temp/chart.html", help="输出 HTML 文件路径（默认 temp/chart.html）")
    args = parser.parse_args()

    out_path = os.path.abspath(args.out)
    out_dir = os.path.dirname(out_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    html_content = generate_chart_html(args.datetime, args.gender, args.lon)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    file_size = os.path.getsize(out_path)
    print(f"[OK] 成功生成可视化排盘 HTML: {out_path} ({file_size} 字节)")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""rules.py — 唯一算法文件：干支序/阴阳/五行关系。其余数据一律落 CSV。"""
GAN = "甲乙丙丁戊己庚辛壬癸"          # 天干序：甲=0…癸=9
ZHI = "子丑寅卯辰巳午未申酉戌亥"      # 地支序：子=0…亥=11
WX = ("木", "火", "土", "金", "水")   # 相生环序（i+1 生、i+2 克）
GAN_WX = {g: WX[i // 2] for i, g in enumerate(GAN)}  # 甲乙木…壬癸水
ZHI_WX = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
          "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
YANG_GAN, YANG_ZHI = set("甲丙戊庚壬"), set("子寅辰午申戌")

def gan_idx(g): return GAN.index(g)
def zhi_idx(z): return ZHI.index(z)
def wx_of_gan(g): return GAN_WX[g]
def wx_of_zhi(z): return ZHI_WX[z]
def sheng(a, b): return WX[(WX.index(a) + 1) % 5] == b   # 木生火…
def ke(a, b): return WX[(WX.index(a) + 2) % 5] == b      # 木克土…

def rel(a, b):
    """五行 a 对 b：比和/生/泄/克/耗。乘=克之太过、侮=反克，属动态，不列静态项。"""
    if a == b: return "比和"
    if sheng(a, b): return "生"
    if sheng(b, a): return "泄"
    if ke(a, b): return "克"
    return "耗"

def five_rels():
    """全量 25 项五行关系：5 比和 + 5 生 + 5 泄 + 5 克 + 5 耗（生/克有序对各 10）。"""
    return [(a, b, rel(a, b)) for a in WX for b in WX]

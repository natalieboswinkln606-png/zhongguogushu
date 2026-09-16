# -*- coding: utf-8 -*-
"""shushu_schema.py — 中国传统术数标准化 Pydantic 数据模型与 JSON Schema

定义四大术数核心排盘数据模型：
1. BaziChartSchema: 四柱、十神、纳音、藏干十神、大运起运岁数与年份序列、旺衰分值
2. ZiweiChartSchema: 12 宫网格定义（宫位名、地支、天干、主星列表、吉星列表、煞星列表、四化标注、三方四正关联宫位）
3. QimenChartSchema: 9 宫九星八门八神天盘地盘干支、值符值使、吉凶格局
4. LiuyaoChartSchema: 本卦变卦六爻、纳甲干支、六亲、世应、动爻

以及 API 请求/响应标准模型与 JSON Schema 生成工具。
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# ==============================================================================
# 通用元数据与辅助定义
# ==============================================================================

class InputMetaSchema(BaseModel):
    """输入排盘的基础信息"""
    datetime: str = Field(..., description="公历北京时间 YYYY-MM-DD HH:MM")
    gender: Optional[str] = Field("女", description="性别：'男' 或 '女'")
    lon: Optional[float] = Field(120.0, description="东经经度，默认 120.0")
    true_solar_time: Optional[str] = Field(None, description="真太阳时 ISO 字符串")
    tz: Optional[str] = Field("UTC+8 北京时间", description="时区描述")


# ==============================================================================
# 1. 八字 (Bazi) 数据模型
# ==============================================================================

class HiddenStemGodSchema(BaseModel):
    """地支藏干及其十神"""
    gan: str = Field(..., description="藏干天干")
    wx: str = Field(..., description="藏干五行")
    god: str = Field(..., description="对日主的十神名称")
    relation: Optional[str] = Field(None, description="五行动态关系（比和/生/泄/克/耗）")


class PillarSchema(BaseModel):
    """单柱定义（年柱/月柱/日柱/时柱）"""
    name: str = Field(..., description="柱名（年柱/月柱/日柱/时柱）")
    gan: str = Field(..., description="天干")
    zhi: str = Field(..., description="地支")
    ganzhi: str = Field(..., description="干支组合（两字）")
    wx_gan: str = Field(..., description="天干五行")
    wx_zhi: str = Field(..., description="地支五行")
    nayin: str = Field(..., description="纳音五行名（如：海中金、炉中火）")
    nayin_wx: str = Field(..., description="纳音正五行（金/木/水/火/土）")
    stem_god: Optional[str] = Field(None, description="天干对日主的十神（日柱通常为日元/日主）")
    hidden_stems: List[HiddenStemGodSchema] = Field(default_factory=list, description="地支藏干及十神列表")
    rule_id: Optional[str] = Field(None, description="计算规则 ID")
    source: Optional[str] = Field(None, description="规则出处来源")


class QiyunAgeSchema(BaseModel):
    """起运岁数折算详情"""
    years: int = Field(..., description="起运岁数（整岁）")
    months: int = Field(..., description="起运月数")
    days: int = Field(..., description="起运天数")
    hours: int = Field(..., description="起运小时数")
    text: str = Field(..., description="人类可读起运时间文本描述（如：5岁8个月24天起运）")
    jie_time: Optional[str] = Field(None, description="节气基准时间")
    jiao_time: Optional[str] = Field(None, description="首次交运时刻")


class DayunStepSchema(BaseModel):
    """大运单步详情"""
    index: int = Field(..., description="大运步数序号（1-8）")
    ganzhi: str = Field(..., description="大运干支")
    gan: str = Field(..., description="大运天干")
    zhi: str = Field(..., description="大运地支")
    god: str = Field(..., description="大运干对日主的十神")
    start_year: int = Field(..., description="起运公历年份")
    end_year: int = Field(..., description="止运公历年份")
    age_start: Optional[int] = Field(None, description="起始虚岁/实岁")
    age_end: Optional[int] = Field(None, description="结束虚岁/实岁")


class DayunSchema(BaseModel):
    """大运完整排布"""
    direction: str = Field(..., description="顺行或逆行（'顺' / '逆'）")
    qiyun: QiyunAgeSchema = Field(..., description="起运岁数与时刻详情")
    steps: List[DayunStepSchema] = Field(default_factory=list, description="8 步大运序列")


class WangshuaiDeLingSchema(BaseModel):
    """旺衰 得令 分析"""
    month_zhi: str = Field(..., description="月令地支")
    ben_qi: str = Field(..., description="月令本气天干")
    ben_qi_wx: str = Field(..., description="月令五行")
    status: str = Field(..., description="得令状态（旺/相/休/囚/死）")
    score: float = Field(..., description="得令分值（0-100）")


class WangshuaiDeDiItemSchema(BaseModel):
    """得地 单柱长生位分析"""
    pillar: str = Field(..., description="柱名（年支/月支/日支/时支）")
    zhi: str = Field(..., description="地支")
    stage: str = Field(..., description="十二长生位（长生/临官/帝旺/墓...）")
    root: bool = Field(..., description="是否有同五行藏干通根")
    points: int = Field(..., description="长生位计分")
    weight: int = Field(..., description="权重")


class WangshuaiDeDiSchema(BaseModel):
    """旺衰 得地 分析"""
    score: int = Field(..., description="得地实际得分")
    max_score: int = Field(..., description="得地满分上限")
    score_pct: float = Field(..., description="得地百分比（0-100）")
    items: List[WangshuaiDeDiItemSchema] = Field(default_factory=list, description="四支长生分档项")


class WangshuaiDeShiSchema(BaseModel):
    """旺衰 得势 分析"""
    score: int = Field(..., description="得势实际得分")
    max_score: int = Field(..., description="得势满分上限")
    score_pct: float = Field(..., description="得势百分比（0-100）")


class WangshuaiZongheSchema(BaseModel):
    """旺衰 综合判定结果"""
    score: float = Field(..., description="综合旺衰加权得分（0-100）")
    level: str = Field(..., description="旺衰评级（极旺/偏旺/中和/偏弱/极弱）")
    advice: str = Field(..., description="扶抑用神建议与平衡策略")
    weights: Dict[str, float] = Field(default_factory=dict, description="令/地/势各权重比例")
    thresholds: Dict[str, str] = Field(default_factory=dict, description="五档评级阈值表")


class WangshuaiSchema(BaseModel):
    """日主旺衰全指标体系"""
    day_master: str = Field(..., description="日主天干")
    score: float = Field(..., description="综合得分")
    level: str = Field(..., description="评级（极旺/偏旺/中和/偏弱/极弱）")
    advice: str = Field(..., description="扶抑建议")
    de_ling: WangshuaiDeLingSchema = Field(..., description="得令分析")
    de_di: WangshuaiDeDiSchema = Field(..., description="得地分析")
    de_shi: WangshuaiDeShiSchema = Field(..., description="得势分析")
    zonghe: WangshuaiZongheSchema = Field(..., description="综合评定")


class BaziChartSchema(BaseModel):
    """八字排盘标准 Schema（四柱、十神、纳音、藏干十神、大运起运岁数与年份序列、旺衰分值）"""
    input: InputMetaSchema = Field(..., description="排盘输入参数")
    pillars: Dict[str, PillarSchema] = Field(..., description="四柱定义（year, month, day, hour）")
    day_master: str = Field(..., description="日主天干")
    ten_gods: Dict[str, Any] = Field(..., description="十神映射字典（干、支藏干十神全景）")
    nayin: Dict[str, str] = Field(..., description="四柱纳音五行对照表")
    canggan_gods: Dict[str, List[HiddenStemGodSchema]] = Field(..., description="四柱地支藏干十神全览")
    dayun: DayunSchema = Field(..., description="大运起运岁数与年份序列")
    wangshuai: WangshuaiSchema = Field(..., description="日主旺衰分值与评级")


# ==============================================================================
# 2. 紫微斗数 (Ziwei) 数据模型
# ==============================================================================

class ZiweiPalaceSchema(BaseModel):
    """紫微斗数 12 宫单宫网格定义"""
    name: str = Field(..., description="宫位名（命宫/兄弟/夫妻/子女/财帛/疾厄/迁移/仆役/官禄/田宅/福德/父母）")
    zhi: str = Field(..., description="地支（子/丑/寅/卯/辰/巳/午/未/申/酉/戌/亥）")
    gan: str = Field(..., description="天干（甲/乙/丙/丁/戊/己/庚/辛/壬/癸）")
    stars: List[str] = Field(default_factory=list, description="十四主星列表（紫微/天府/天梁/天相...）")
    ji_stars: List[str] = Field(default_factory=list, description="吉辅星列表（左辅/右弼/文昌/文曲/天魁/天钺/禄存/天马）")
    sha_stars: List[str] = Field(default_factory=list, description="煞星列表（擎羊/陀罗/火星/铃星/地空/地劫）")
    sihua: List[str] = Field(default_factory=list, description="生年四化标注（禄/权/科/忌）")
    sanfang_sizheng: List[str] = Field(default_factory=list, description="三方四正关联宫位名称列表（本宫、三合方两宫、对冲方一宫）")
    sanfang_sizheng_zhi: List[str] = Field(default_factory=list, description="三方四正关联地支列表")
    shen: bool = Field(False, description="是否为身宫所在")


class ZiweiLunarSchema(BaseModel):
    """紫微排盘农历参数"""
    year: str = Field(..., description="农历年干支")
    month: int = Field(..., description="农历月份数字")
    month_name: str = Field(..., description="农历月名称（如：正月、闰二月）")
    day: int = Field(..., description="农历日（1-30）")
    is_ruen: bool = Field(False, description="是否闰月")


class ZiweiSihuaItemSchema(BaseModel):
    """生年四化项目"""
    star: str = Field(..., description="化曜星名")
    hua: str = Field(..., description="四化类型（禄/权/科/忌）")


class ZiweiChartSchema(BaseModel):
    """紫微斗数排盘标准 Schema（12 宫网格定义、主星/吉星/煞星、四化标注、三方四正关联）"""
    input: InputMetaSchema = Field(..., description="输入参数")
    lunar: ZiweiLunarSchema = Field(..., description="农历日月信息")
    shichen_zhi: str = Field(..., description="生时地支")
    minggong: Dict[str, str] = Field(..., description="命宫位置（zhi, gan）")
    shengong: Dict[str, str] = Field(..., description="身宫位置（zhi）")
    wuxing_ju: Dict[str, str] = Field(..., description="五行局名（水二局/木三局/金四局/土五局/火六局）")
    ziwei_star: Dict[str, str] = Field(..., description="紫微星所在宫位地支")
    sihua: List[ZiweiSihuaItemSchema] = Field(default_factory=list, description="生年四化全局列表")
    palaces: List[ZiweiPalaceSchema] = Field(..., description="12 宫网格排布（依命宫逆排顺序或地支固定环）")


# ==============================================================================
# 3. 奇门遁甲 (Qimen) 数据模型
# ==============================================================================

class QimenPalaceSchema(BaseModel):
    """奇门九宫单宫网格定义"""
    palace: int = Field(..., description="洛书九宫序号（1-9）")
    gua: str = Field(..., description="八卦九宫名（坎宫/坤宫/震宫/巽宫/中宫/乾宫/兑宫/艮宫/离宫）")
    direction: str = Field(..., description="物理方位（正北/西南/正东/东南/中央/西北/正西/东北/正南）")
    dipan_gan: str = Field(..., description="地盘奇仪干（戊己庚辛壬癸丁丙乙）")
    tianpan_gan: str = Field(..., description="天盘奇仪干（转盘带干，中宫寄坤可能双干）")
    star: Optional[str] = Field(None, description="九星（天蓬/天芮/天冲/天辅/天禽/天心/天柱/天任/天英）")
    door: Optional[str] = Field(None, description="八门（休门/生门/伤门/杜门/景门/死门/惊门/开门）")
    shen: Optional[str] = Field(None, description="八神（值符/腾蛇/太阴/六合/白虎/玄武/九地/九天）")


class QimenGejuSchema(BaseModel):
    """奇门格局判定项"""
    id: str = Field(..., description="格局规则编号（如：qd-g-01, qd-x-05）")
    name: str = Field(..., description="格局名称（如：青龙返首、飞鸟跌穴、六仪击刑、三奇入墓）")
    type: str = Field(..., description="吉凶性质（'吉' 或 '凶'）")
    palace: str = Field(..., description="格局落宫序号（'1'~'9'）")
    basis: str = Field(..., description="判定依据说明")
    source: Optional[str] = Field(None, description="底本出处")


class QimenDingjuSchema(BaseModel):
    """奇门定局信息"""
    term: str = Field(..., description="所属节气")
    dun: str = Field(..., description="阴阳遁（'阳遁' 或 '阴遁'）")
    yuan: str = Field(..., description="三元（'上元' / '中元' / '下元'）")
    ju: int = Field(..., description="局数（1-9）")


class QimenZhifuZhishiSchema(BaseModel):
    """奇门值符值使"""
    xunshou: str = Field(..., description="旬首六甲干支（如：甲子、甲戌）")
    yiyi: str = Field(..., description="旬首隐仪（戊己庚辛壬癸）")
    zhifu_star: str = Field(..., description="值符九星名")
    zhifu_palace: int = Field(..., description="值符落宫序号")
    zhishi_door: str = Field(..., description="值使八门名")
    zhishi_palace: int = Field(..., description="值使落宫序号")


class QimenChubuSchema(BaseModel):
    """奇门吉凶初步评估"""
    verdict: str = Field(..., description="综合倾向（'好' / '平' / '差'）")
    level: int = Field(..., description="倾向级别（1好、2平、3差）")
    ji_count: int = Field(..., description="命中吉格数")
    xiong_count: int = Field(..., description="命中凶格数")
    xiong_palaces: List[str] = Field(default_factory=list, description="凶格重灾宫位列表")


class QimenChartSchema(BaseModel):
    """奇门遁甲排盘标准 Schema（9 宫九星八门八神天盘地盘干支、值符值使、吉凶格局）"""
    input: InputMetaSchema = Field(..., description="输入参数")
    pillars: Dict[str, str] = Field(..., description="排盘四柱干支")
    dingju: QimenDingjuSchema = Field(..., description="定局元会信息")
    zhifu_zhishi: QimenZhifuZhishiSchema = Field(..., description="值符值使信息")
    month_jiang: Optional[str] = Field(None, description="月将地支")
    pan: Dict[str, QimenPalaceSchema] = Field(..., description="九宫网格字典（'1'~'9' 宫详细配置）")
    geju: List[QimenGejuSchema] = Field(default_factory=list, description="命中吉凶格局清单")
    chubu: Optional[QimenChubuSchema] = Field(None, description="初步吉凶研判")


# ==============================================================================
# 4. 六爻 (Liuyao) 数据模型
# ==============================================================================

class LiuyaoGuaInfoSchema(BaseModel):
    """六爻单卦基本卦象信息"""
    name: str = Field(..., description="六十四卦名（如：火天大有、乾为天）")
    palace: str = Field(..., description="所属八宫（乾/兑/离/震/巽/坎/艮/坤）")
    order: int = Field(..., description="八宫卦序（1-8，第7为游魂，第8为归魂）")
    guaci: str = Field(..., description="周易通行本卦辞原文")
    up: str = Field(..., description="上卦经卦名")
    down: str = Field(..., description="下卦经卦名")
    lines: str = Field(..., description="六爻阴阳序列（自下而上初至上，如：'阳阳阳阳阳阳'）")


class LiuyaoLineSchema(BaseModel):
    """六爻单爻网格定义"""
    pos: str = Field(..., description="爻位名（'初'、'二'、'三'、'四'、'五'、'上'）")
    yao: str = Field(..., description="本卦爻象称谓（'九' 为阳爻、'六' 为阴爻）")
    shen: str = Field(..., description="日干起六神（青龙/朱雀/勾陈/螣蛇/白虎/玄武）")
    qin: str = Field(..., description="本卦六亲（兄弟/父母/子孙/官鬼/妻财）")
    gan: str = Field(..., description="本卦纳甲天干")
    zhi: str = Field(..., description="本卦纳甲地支")
    wx: str = Field(..., description="本卦爻支五行")
    shi_ying: str = Field("", description="世应标记（'世' / '应' / 空）")
    dong: bool = Field(False, description="是否为动爻")
    bian_yao: str = Field(..., description="变卦爻象称谓（'九' 或 '六'）")
    bian_qin: str = Field(..., description="变卦六亲（仍依本卦八宫五行取）")
    bian_gan: str = Field(..., description="变卦纳甲天干")
    bian_zhi: str = Field(..., description="变卦纳甲地支")
    bian_wx: str = Field(..., description="变卦爻支五行")
    bian_shi_ying: str = Field("", description="变卦世应标记（'世' / '应' / 空）")


class LiuyaoChartSchema(BaseModel):
    """六爻排盘标准 Schema（本卦变卦六爻、纳甲干支、六亲、世应、动爻）"""
    input: Dict[str, Any] = Field(..., description="排盘时间与起卦参数")
    method: Dict[str, Any] = Field(..., description="起卦法与起卦数")
    yue_jian: Dict[str, Any] = Field(..., description="月建（月支与月令干支）")
    ri_chen: Dict[str, Any] = Field(..., description="日辰（日柱干支）")
    ben_gua: LiuyaoGuaInfoSchema = Field(..., description="本卦详情")
    bian_gua: LiuyaoGuaInfoSchema = Field(..., description="变卦详情")
    lines: List[LiuyaoLineSchema] = Field(..., description="自初爻至上爻六爻全息信息")
    dong_yao: List[int] = Field(default_factory=list, description="动爻爻位序号列表（1-6）")


# ==============================================================================
# 5. API 请求与响应标准化模型
# ==============================================================================

class BaziRequest(BaseModel):
    datetime: str = Field(..., description="北京时间 YYYY-MM-DD HH:MM")
    gender: str = Field("女", description="性别（男/女）")
    lon: float = Field(120.0, description="东经经度")


class ZiweiRequest(BaseModel):
    datetime: str = Field(..., description="北京时间 YYYY-MM-DD HH:MM")
    lon: float = Field(120.0, description="东经经度")
    gender: Optional[str] = Field("女", description="性别（男/女）")
    target_year: Optional[int] = Field(None, description="流年大限目标年")


class QimenRequest(BaseModel):
    datetime: str = Field(..., description="北京时间 YYYY-MM-DD HH:MM")
    lon: float = Field(120.0, description="东经经度")


class LiuyaoRequest(BaseModel):
    datetime: str = Field(..., description="北京时间 YYYY-MM-DD HH:MM")
    lon: float = Field(120.0, description="东经经度")
    mode: str = Field("lunar", description="起卦模式：'lunar'（农历时间）或 'gongli'（公历时间）")
    n1: Optional[int] = Field(None, description="数字起卦数1（可选）")
    n2: Optional[int] = Field(None, description="数字起卦数2（可选）")


class SnapshotRequest(BaseModel):
    datetime: str = Field(..., description="北京时间 YYYY-MM-DD HH:MM")
    gender: str = Field("女", description="性别（男/女）")
    lon: float = Field(120.0, description="东经经度")
    ziwei_target_year: Optional[int] = Field(None, description="紫微流年目标年份")


class ReconcileRequest(BaseModel):
    text: str = Field(..., description="待测算结论结论草稿文本")
    snapshot: Optional[Dict[str, Any]] = Field(None, description="已落盘全量快照 dict；若未提供则根据 datetime/gender 即时生成")
    datetime: Optional[str] = Field(None, description="若无 snapshot，提供日期时间即时生成快照进行对账")
    gender: Optional[str] = Field("女", description="性别")
    lon: Optional[float] = Field(120.0, description="经度")


class ReconcileResponse(BaseModel):
    matched: List[Any] = Field(default_factory=list, description="成功在快照中溯源的项")
    unverified: List[Any] = Field(default_factory=list, description="未能机械溯源的项（宁多报不漏报）")
    conflicts: List[Any] = Field(default_factory=list, description="严重冲突项（大运错位、双源不一致、旺衰分值漂移等）")


class HealthResponse(BaseModel):
    status: str = Field("ok", description="服务健康状态")
    version: str = Field("1.0.0", description="API 引擎版本")
    timestamp: str = Field(..., description="服务器响应时间戳")
    modules_ready: List[str] = Field(default_factory=list, description="已就绪的术数内核模块")


# ==============================================================================
# 6. JSON Schema 导出工具函数
# ==============================================================================

def export_all_schemas() -> Dict[str, Any]:
    """导出四大术数盘面的标准化 JSON Schema 字典"""
    return {
        "BaziChartSchema": BaziChartSchema.model_json_schema(),
        "ZiweiChartSchema": ZiweiChartSchema.model_json_schema(),
        "QimenChartSchema": QimenChartSchema.model_json_schema(),
        "LiuyaoChartSchema": LiuyaoChartSchema.model_json_schema(),
        "BaziRequest": BaziRequest.model_json_schema(),
        "ZiweiRequest": ZiweiRequest.model_json_schema(),
        "QimenRequest": QimenRequest.model_json_schema(),
        "LiuyaoRequest": LiuyaoRequest.model_json_schema(),
        "SnapshotRequest": SnapshotRequest.model_json_schema(),
        "ReconcileRequest": ReconcileRequest.model_json_schema(),
        "ReconcileResponse": ReconcileResponse.model_json_schema(),
        "HealthResponse": HealthResponse.model_json_schema(),
    }


if __name__ == "__main__":
    import json
    schemas = export_all_schemas()
    print(f"成功导出 {len(schemas)} 个标准 JSON Schema 模型")
    print("Schema keys:", list(schemas.keys()))

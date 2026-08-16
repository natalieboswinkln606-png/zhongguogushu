# 中国传统文化术数研究系统（shushu）

**定位**：纯开源的术数数据基座与研究工具集——数据落 CSV、算法仅一处（rules.py）、一切可复现、可对拍、可仲裁。

**承诺：差异无处藏身**——任何数据都带 source_ref 可溯源；对拍差异按四类分类（转录错/底本错/算法分歧/范围外）；争议走 arbitration_log 仲裁；异文进 whitelist 白名单。

## 三段锚点声明

| 锚点段 | 定义源 | 精度 |
| --- | --- | --- |
| 当代（1900-2100） | 官方年历定义源（紫台/香港天文台） | 分钟级 |
| 古代（1900 前） | 张培瑜《三千五百年历日天象》 | 时辰级 |
| 库（实现源） | lunar-python（MIT）等，仅作对拍 oracle | — |

详见 docs/preregister.md（容差、校核、约定语义、三角色、剔除三态）。

## 架构分层

| 层 | 内容 | 冻结状态 |
| --- | --- | --- |
| L0 历法基座 | 节气（solar_terms.csv，紫台/张培瑜双锚点对拍）、朔望（shuowang.csv，skyfield 星历仲裁）、干支表（ganzhi_days.csv，1900-2100 全区间 lunar-python 对拍） | 完成 |
| L1 四柱内核 | m1.py（冻结）：年/月/日/时四柱、节气分界、真太阳时、十神 | 冻结 |
| L2 十神/大运流年/旺衰/神煞 | l3_bazi_daliu.py（顺逆/起运/流年）、l3_wangshuai.py（月令旺衰）、l3_shensha.py（神煞） | 冻结 |
| L3 术种层 | 12 术种模块（下表），每输出项带 Rule-ID/底本出处/异文标注 | 冻结 |
| L4 审计层 | l4_audit.py 端到端抽查（160 断言）+ Rule-ID 注册表双向校验（rule_registry.csv 174 条）+ SHA256SUMS.txt 快照重签；sw-2057-09 已结案 | 完成 |

## L3 术种层 12 模块

| 术种 | 模块 | 底本 |
| --- | --- | --- |
| 紫微斗数 | l3_ziwei.py / l3_ziwei_liunian.py | 安星法（命身宫/十二宫/四化/辅星/大限小限流年），oracle 缓存独立解析复验 |
| 六爻 | l3_liuyao.py | 《梅花易数》时间起卦、《周易》通行本卦辞、najia.csv 纳甲、bagong.csv 八宫（京房六亲） |
| 六壬 | l3_liuren.py | 《六壬大全》卷一起例（日干寄宫/贼克/比用/涉害/遥克/昴星/别责/八专/伏吟/返吟九宗门） |
| 奇门排盘 | l3_qimen.py | 《奇门遁甲统宗》转盘法 72 局 + 张志春《神奇之门》拆补定局，易安居实测逐宫校准 |
| 奇门断局 | l3_qimen_duanju.py | 《统宗》《烟波钓叟歌》（用神/格局/吉凶初步） |
| 黄历 | l3_huangli.py | 《协纪辨方书》为主（建除/黄黑道/宜忌/择日），辅《玉匣记》 |
| 人际合盘 | l3_hepan.py | 结构互动/十神互定位/夫妻宫/四场景/流年合盘/六爻测事接线/代占直断（四底本），易安居为 oracle |
| 河洛理数 | l3_heluolishu.py | 网传太玄数起卦派（与古籍洛书数派分歧已如实申报 arbitration_log） |
| 梅花易数 | l3_meihua.py | 《梅花易数》邵雍原著（先天八卦数/起卦三法/体用生克五态），辅《增广校正梅花易数》 |
| 小六壬 | l3_xiaoliuren.py | 马前课/李淳风六壬时课/六兀轮经体系 |
| 称骨 | l3_chenggu.py | 《称骨歌》（托名袁天罡，版本异文在输出 notes 声明） |
| 五运六气 | l3_wuyunliuqi.py | 《黄帝内经·素问》运气七篇 |

## 当前状态

**全量完成（v1.0 冻结）**：L0→L1（m1.py）→L2→L3（12 术种）→L4 审计全链路收官。Rule-ID 注册表 174 条、端到端 160 断言、全量断言 **PASS 787 / FAIL 0**；所有对拍差异与异文已申报 data/arbitration_log.csv（121 行）与 report/boundary_cases.csv（169 行）；SHA256SUMS.txt 最终重签完成。

## 运行方式

全量断言（推荐顺序）：

```bash
# 基座（M0）：生成/对拍/校验/断言
python gen_ganzhi.py && python compare.py && python validate.py && python assert_tables.py
# L2/L3 各层（Windows 需 UTF-8 输出）
PYTHONIOENCODING=utf-8 python assert_l3_bazi_daliu.py      # 大运流年
PYTHONIOENCODING=utf-8 python assert_l3_wangshuai.py       # 旺衰
PYTHONIOENCODING=utf-8 python assert_l3_shensha.py         # 神煞
PYTHONIOENCODING=utf-8 python assert_l3_ziwei.py           # 紫微斗数
PYTHONIOENCODING=utf-8 python assert_l3_ziwei_liunian.py   # 紫微流年
PYTHONIOENCODING=utf-8 python assert_l3_liuyao.py          # 六爻（带网络对拍，缓存命中幂等）
PYTHONIOENCODING=utf-8 python assert_l3_liuren.py          # 六壬
PYTHONIOENCODING=utf-8 python assert_l3_qimen.py           # 奇门排盘
PYTHONIOENCODING=utf-8 python assert_l3_qimen_duanju.py    # 奇门断局
PYTHONIOENCODING=utf-8 python assert_l3_huangli.py         # 黄历
PYTHONIOENCODING=utf-8 python assert_l3_hepan.py           # 人际合盘
PYTHONIOENCODING=utf-8 python assert_l3_heluolishu.py      # 河洛理数
PYTHONIOENCODING=utf-8 python assert_l3_meihua.py          # 梅花易数
PYTHONIOENCODING=utf-8 python assert_l3_xiaoliuren.py      # 小六壬
PYTHONIOENCODING=utf-8 python assert_l3_chenggu.py         # 称骨
PYTHONIOENCODING=utf-8 python assert_l3_wuyunliuqi.py      # 五运六气
# L4 审计层：端到端抽查 + 注册表校验（只读）；--resign 重签 SHA256SUMS.txt（唯一写操作）；--verify 只读校验快照
python l4_audit.py
python l4_audit.py --resign
python l4_audit.py --verify
```

> 重跑任何断言/对拍脚本会改写报告时间戳导致快照失配——重跑后执行 `python l4_audit.py --resign` 重新冻结，或 `python l4_audit.py --verify` 校验当前快照。

## 目录

- `data/` — CSV 数据（UTF-8）：基座 8 表（nayin/canggan/bagong/najia/changsheng/ganzhi_days + solar_terms/shuowang 空模板）+ 节气/朔望实际数据 + l3_qimen_duanju_yongshen.csv + rule_registry.csv（Rule-ID 注册表 174 条）+ arbitration_log.csv（争议仲裁 121 行）+ shushu.db（validate.py 生成）
- `rules.py` — 唯一算法文件（干支序/阴阳/五行关系）
- `m1.py` — L1 四柱内核（冻结）
- `l3_*.py` — L2/L3 术种模块（冻结）
- `l4_audit.py` — L4 审计层（端到端抽查/注册表校验/重签）
- `assert_*.py` — 各层独立断言脚本
- `gen_*.py` / `compare.py` / `*_compare.py` — 生成/对拍/校验
- `report/` — 全部报告：compare_report.txt、assert_report.txt、m1_compare_report.txt、shuowang_compare_report.txt、solar_terms_compare_report.txt、skyfield_arbitrate_report.txt、l2_compare_report.txt、l3_*_report.txt（12 术种）、l4_audit_report.txt、final_assert_report.txt（全量断言汇总）、boundary_cases.csv（边界用例 169 行）
- `docs/` — preregister.md（预注册契约）、whitelist.csv、sampling.md

## 许可

MIT License（见 LICENSE）。

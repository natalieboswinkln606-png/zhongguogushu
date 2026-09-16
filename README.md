# 中国古术 (zhongguogushu)
### 中国传统文化术数高精度计算、对账与全谱推演系统
*Precision Chinese Metaphysics Computation & Cross-Verification Engine*

简体中文 | [English](README_EN.md)

**定位**：纯开源、可复现、零漂移的中国传统术数精密数据基座与全谱引擎。数据落静态表与 CSV、算法单一真相源、支持 16 个标准化 MCP (Model Context Protocol) 工具接口，100% 自动化断言回归闭环。

**核心承诺：差异无处藏身**——所有推演均带 `source_ref` 经典古籍溯源；跨流派分歧按四类严格分类（转录错/底本错/算法分歧/范围外）；争议统一归入 `arbitration_log.csv` 仲裁；古籍异文录入白名单与防御拦截。

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
| L2 十神/大运流年/旺衰/神煞/流日 | l3_bazi_daliu.py（顺逆/起运/流年）、l3_wangshuai.py（月令旺衰）、l3_shensha.py（神煞）、l3_bazi_liuri.py（流日，v1.1 增补） | 冻结 |
| L3 术种层 | 12 术种模块 + 铁板条文层（下表），每输出项带 Rule-ID/底本出处/异文标注 | 冻结 |
| L4 审计层 | l4_audit.py 端到端抽查（198 断言）+ Rule-ID 注册表双向校验（rule_registry.csv 181 条）+ SHA256SUMS.txt 快照重签；sw-2057-09 已结案 | 完成 |

## L3 术种层（12 术种 + 流日/铁板条文层）

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
| 流日（非经典层级） | l3_bazi_liuri.py | 随件声明：古典主干止于流年，颗粒度越细可附会空间越大；序列=m1 正午反解 + ganzhi_days；关系层复用 l3_hepan（hp-01 三字俱全口径）；黄历层引用 l3_huangli；只出数据层+关系层，不作吉凶断语 |
| 铁板条文层 | l3_tieban.py | 考刻-验证交互回路（tb-01..04：太玄数键/刻框架/条文键匹配/计分排序）；考刻=用已知事实拟合刻数（拟合≠预测验证）；引擎不自造传本编号，条文库 data/tieban_tiaowen.csv 由使用者自备 |

## 当前状态

**全量完成（v1.0 冻结 + v1.1 增补）**：L0→L1（m1.py）→L2→L3（12 术种 + 流日 + 铁板条文层）→L4 审计全链路收官。Rule-ID 注册表 181 条、端到端 198 断言、全量断言 **PASS 853 / FAIL 0**；所有对拍差异与异文已申报 data/arbitration_log.csv（记录 123 条，125 行含表头/注释）与 report/boundary_cases.csv（记录 170 条，172 行含表头/注释）；SHA256SUMS.txt 重签完成（文本按 LF 归一取哈希，与 .gitattributes eol=lf 对称，防 CRLF 检出伪失配）。（v1.0 结案数：788 / 174 / 161。）

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
PYTHONIOENCODING=utf-8 python assert_l3_bazi_liuri.py      # 流日（非经典层级）
PYTHONIOENCODING=utf-8 python assert_l3_tieban.py          # 铁板条文层（考刻-验证回路）
# L4 审计层：端到端抽查 + 注册表校验（只读）；--resign 重签 SHA256SUMS.txt（唯一写操作）；--verify 只读校验快照
python l4_audit.py
python l4_audit.py --resign
python l4_audit.py --verify
```

> 重跑任何断言/对拍脚本会改写报告时间戳导致快照失配——重跑后执行 `python l4_audit.py --resign` 重新冻结，或 `python l4_audit.py --verify` 校验当前快照。

## 目录

- `data/` — CSV 数据（UTF-8）：基座 8 表（nayin/canggan/bagong/najia/changsheng/ganzhi_days + solar_terms/shuowang 空模板）+ 节气/朔望实际数据 + l3_qimen_duanju_yongshen.csv + tieban_tiaowen.csv（铁板条文库，空模板由使用者自备内容）+ rule_registry.csv（Rule-ID 注册表 181 条）+ arbitration_log.csv（争议仲裁 120 条，122 行含表头/注释）+ shushu.db（validate.py 生成）
- `rules.py` — 唯一算法文件（干支序/阴阳/五行关系）
- `m1.py` — L1 四柱内核（冻结）
- `l3_*.py` — L2/L3 术种模块（冻结）
- `l4_audit.py` — L4 审计层（端到端抽查/注册表校验/重签）
- `assert_*.py` — 各层独立断言脚本
- `gen_*.py` / `compare.py` / `*_compare.py` — 生成/对拍/校验
- `report/` — 全部报告：compare_report.txt、assert_report.txt、m1_compare_report.txt、shuowang_compare_report.txt、solar_terms_compare_report.txt、skyfield_arbitrate_report.txt、l2_compare_report.txt、l3_*_report.txt（各术种，含 v1.1 流日对拍报告）、l4_audit_report.txt、final_assert_report.txt（全量断言汇总）、boundary_cases.csv（边界用例 170 条，172 行含表头/注释）
- `docs/` — preregister.md（预注册契约）、whitelist.csv、sampling.md

## v1.1 增补（2026-09-15）

在 v1.0 冻结版之上**只新增、不修改**冻结文件（m1.py、既有 l3_*.py 零改动）：

- **`l3_bazi_liuri.py`（lr-01..03，流日）**：非经典层级，随件声明（古典主干止于流年；颗粒度越细，断语一致性与可复核性越差、事后附会空间越大）。只出数据层+关系层，不作吉凶断语。日柱=ganzhi_days 表（正午真太阳时反解，跨经度鲁棒）；关系层复用 l3_hepan 表（hp-01 三字俱全口径）；黄历层引用 l3_huangli。oracle 对拍 68 样本 198 检查项差异 0（report/l3_bazi_liuri_report.txt），断言 13/13（含同支口径：自刑四支、同支半合归局，与 hp-01 一致）。
- **`l3_tieban.py`（tb-01..04，铁板条文层）**：定位声明——考刻是方法内核（用已知事实反推刻数，拟合≠预测验证），"纯查表"只描述考刻后的下半程。四层：tb-01 太玄数键（import l3_heluolishu 同源表+固定值断言锁）、tb-02 刻框架（一时八刻 96 刻制 / 古百刻制 alt；每刻窗起点+1 分钟取样；子时跨午夜按真太阳时子正分裂日柱）、tb-03 条文键匹配（**引擎不自造传本编号与条文**，id/正文直引外部库 data/tieban_tiaowen.csv，空=通配）、tb-04 考刻-验证交互回路（候选刻→检索→claim+facts 自动判定或人工 verdicts→计分排序）。断言 10/10（含子时跨午夜分裂、百刻制、合成语料计分排序、warnings 外显与 positioning 声明）。
- **集成**：rule_registry.csv 174→181；l4_audit.py 端到端 161→198（新增流日/铁板跨模块断言：流日原局=m1、流日日柱=ganzhi_days、黄历层双源同值、铁板四柱=m1、八刻候选日柱=ganzhi_days、太玄数键 8 数和，另加 CSV 表结构锁防未转义逗号列漂移）；l5_defense_check.py 头注释"7项"陈旧计数修正为实际 9 项，脚本纳入版本控制；final_assert_report.txt 同步更新（全量 788→848）。
- **冻结纪律**：新文件已 `git add`；`python l4_audit.py --resign` 重签、`--verify` 校验（113 文件一致；LF 归一口径已通过"规范化检出"验收）。2026-09-15 修复轮：撤销 2026-08-30 误入工作区的 l3_hepan.py 戌戌自刑增列（恢复 v1.0 自刑四支口径，申报 data/arbitration_log.csv hp-x03），冻结文件与 v1.0 逐字节归零。
- **2026-09-15 P 命造验收段 2 术理打回修复轮**（走完整流程：修复→回归断言→重签→双路复验）：① r3/r4 节气判界时制统一——`m1.py` `year_pillar`/`month_pillar` 判界两侧同用北京时域（solar_terms.csv=UTC+8 同域），原实现把真太阳时与节气表直接比较，乌鲁木齐等西经度地在大时差窗口误判年/月柱（1974-02-04 14:30 @87.6 误癸丑/乙丑→正甲寅/丙寅）；② hp-03 生肖链补三刑环（`l3_hepan.py`，与 hp-01/ri_zhi 三字俱全口径一致，修复前子卯生肖落"无特殊"漏报）。回归断言新增 m01/m02（assert_l3_bazi_daliu.py）与 sheng_xiao 三刑环（assert_l3_hepan.py）；重签 114 文件、verify 113/113 一致、全量断言 0 FAIL。
- **2026-09-15 qiyun 起运时制修复轮**（段 2 打回链延伸，修复→对拍实证→申报裁决→回归→重签闭环）：`l3_bazi_daliu.py` `qiyun()` 起运间隔改按**出生到节气绝对时长、两侧统一北京时域相减**（与 solar_terms.csv 同域，判界口径同 F1）；原单边真太阳时口径把 (lon−120)×4 分经度修正与均时差（乌鲁木齐合计 ≈ −134 分 ≈ 11 天）伪差计入间隔。对拍复跑 25 例：15 例全一致 / 10 例仅起运『天』差 1 / **0 真实分歧**；第二 oracle lunar-python 25/25（岁/月/天对拍字段口径）一致、第三 oracle skyfield DE440s（太阳视黄经二分求根）抽查 13 例本表节时刻 ≤2 分；10 例天差经四阶段实证为易安居页自带节表远期年偏离天文真值 ±5~14 分 × 12 分/天边界敏感（申报 bd-q02，裁决 **arbitrated**：第三 oracle 局限、非本引擎缺陷）。原 bd-a05（判界时制）/bd-q01（EOT 口径差 17 例）追加**结案(修复消解)**行（hp-x03 先例：新增申报行说明、不删旧行）；boundary_cases.csv 全 arbitrated、无 pending 残留。**影响面收敛验证**：P 全谱数据重跑（t1 八字/t1 紫微/t4 全术种/t5 深测/快照）仅起运派生字段变化——起运 9岁9月20天→9岁10月1天、交运 1984-04-26 12:13→1984-05-07 16:13，紫微/六爻/六壬/奇门/合盘/流日/铁板/称骨/快照不变量与其余字段**零变化**；report/l3_bazi_daliu_report.txt 按新事实全面重写。final_assert_report.txt 同步（全量 848→853：daliu 35→37、hepan 48→51，分节 二 89→91、三 467→470）；重签 114 文件、verify 113/113 一致。**双路第三方复验（数据抄写+术理）均放行**、8 条低危 findings 全部修正（bd-q02 文字 overclaim 订正并两表同步、偏差基线注明、M3 页口径说明、k01 描述、生肖链三字俱全专项断言 +2、errata 建档 report/errata/2026-09-15-qiyun-fix.md、preregister 判界时域/起运同域口径成文）。

## v2.0 升级（2026-09-16 全谱工程体系与 16 MCP 工具）

在保持 v1.0/v1.1 全部数据底座与密码学防线的前提下，完成向全功能现代术数引擎的架构跃迁：

1. **静态化零 I/O 内存底座（`data_static_tables.py`）**：
   - 154 年（1948-2101）高精朔望（1905 条）、节气（3696 条）、藏干、纳音完整预编译为 Python 内存只读数据结构。
   - 实现 0 磁盘 I/O，平均单次查询性能达 **1.7 微秒**。
2. **强类型领域模型（`shushu_context.py` & `shushu_schema.py`）**：
   - 构建 `ShushuContext` 与 `StandardPillars`，确立不可变时空基准与六十甲子唯一真值源。
   - 彻底阻断任何跨模块调用时的“时空漂移”与干支不一致。
3. **标准化 16 个 MCP (Model Context Protocol) 工具集（`mcp_server.py`）**：
   - `shushu_bazi` / `shushu_bazi_geju` / `shushu_ziwei` / `shushu_ziwei_yunxian`
   - `shushu_liuyao` / `shushu_liuren` / `shushu_jinkoujue` / `shushu_qimen`
   - `shushu_qizheng` / `shushu_huangli` / `shushu_hepan` / `shushu_heluo`
   - `shushu_meihua` / `shushu_xiaoliuren` / `shushu_shensha_ext` / `shushu_tieban_ext`
4. **扩充古典精密术种**：
   - **八字格局判别**（`l3_bazi_geju.py`）：《子平真诠》正统十神定格、建禄月劫格、阳刃格、专旺格、从格、化气格，透干权重严格按月令本气/中气/余气裁决。
   - **大六壬金口诀**（`l3_jinkoujue.py`）：地分、将神、贵神、人元四位，五动、三动、旺相休囚死及合破刑冲。
   - **果老星宗七政四余**（`l3_qizheng.py`）：J2000 天体几何真经度、11 曜赤道/黄道换算、罗计严格 180° 对冲、明初二十八宿不等度宿度划分。
   - **紫微运限流曜**（`l3_ziwei_yunxian.py`）：流年斗君排布、九大流曜（流禄/流羊/流陀/流魁/流钺/流昌/流曲/流化）、流年四化。
   - **扩展神煞库**（`l3_shensha_ext.py`）：三奇贵人（天上/地下/人中）、天赦、天医、太极、十恶大败、阴阳差错、孤鸾等 50+ 古典神煞。
   - **邵子铁板八刻滚盘**（`l3_tieban_ext.py`）：考刻滚盘算法与千条条文检索验证回路。
5. **全库回归验证**：
   - 35 套自动化测试套件 **100% PASS**（累计 >1,300 项断言）。

## 许可

MIT License（见 LICENSE）。

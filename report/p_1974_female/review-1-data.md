# P 女命报告 · 数据抄写维度第三方对抗审查（完整版）

- 审查员：数据抄写维度对抗审查（独立复算 + 溯源比对）
- 审查对象：`temp/_p_final_report.md`（476 行，2026-09-15 22:17）
- 数据底座：`temp/_probe_snap.json`（生成 2026-09-15T22:16:16）
- 复算环境：工作目录 D:\shushu，`PYTHONIOENCODING=utf-8 python`，引擎为磁盘现行文件（16 文件 sha256 与快照 meta.provenance **16/16 全匹配**，确认快照确由该批冻结引擎生成）
- 复算临时脚本（项目外）：`C:\Users\tanzr\AppData\Local\Temp\recompute_p.py`（结果 JSON 同目录 recompute_p.json）

---

## 一、独立复算结论：14 个模块关键值全部与报告一致（放行证据）

| 模块 | 复算命令（节选） | 复算关键值 vs 报告 |
|---|---|---|
| 四柱 | `m1.compute(datetime(1974,7,5,22,13),87.6)` | 甲寅/庚午/丁未/庚戌；真太阳时 1974-07-05T19:59:12 ✓ |
| 大运 | `l3_bazi_daliu.dayun(dt,87.6,"女")` | 逆排；己巳1984-1993…壬戌2054-2063 八步；起运{9,10,1,18}；节1974-06-06 09:52；交运1984-05-07 16:13 ✓ |
| 旺衰 | `l3_wangshuai.compute(dt,87.6)` | de_ling{旺,100,ws-01}；de_di items=4(ws-02)；zonghe{68.6,偏旺,ws-04,权重0.4/0.35/0.25} ✓ |
| 神煞 | `l3_shensha.compute(dt,87.6)` | 年上亡神(ss-16)/国印(ss-14)、月上将星(ss-07)/禄神(ss-08)、日上天喜(ss-11)、时上华盖(ss-05)/天罗(ss-18)，hit_total=7 ✓ |
| 称骨 | `l3_chenggu.compute(dt,87.6,"女")` | 甲寅1两2钱/五月5钱/16日8钱/戌时6钱，合计3两1钱(cg-01/cg-02)，歌诀文本 ✓ |
| 紫微 | `l3_ziwei.compute(dt.replace(hour=22,minute=0),87.6)` | 命宫壬申、身宫辰、金四局(zw-03)；十二宫三栏与四化（禄权→父母癸酉、科→仆役丁丑、忌→迁移丙寅）✓ |
| 紫微流年 | `l3_ziwei_liunian.compute(dt,87.6,"女",2026)` | 起限4岁/逆行、12 限干支宫位限四化、2026 丙午/命宫庚午(夫妻)/天同禄天机权文昌科廉贞忌 ✓ |
| 奇门 | `l3_qimen.compute(dt,87.6)` | 夏至·下元·阴遁6局(qm-01)；旬首甲辰隐仪壬、值符天芮落4宫；值使死门 zhishi_palace=5；八门盘坤2死门 ✓ |
| 五运六气 | `l3_wuyunliuqi.compute(dt)` | 甲寅土运太过·敦阜之纪(wylq-01)；司天少阳相火/在泉厥阴风木；三之气 1974-05-21 18:36 → 1974-07-23 13:30；三之气客主同气 ✓ |
| 梅花 | `l3_meihua.compute_time(dt,87.6)` | 太玄数3/5/16/11；地火明夷→互雷水解→变水火既济、动5；体离火旺/用坤土相/耗泄；mh-06 文本一致 ✓ |
| 六爻 | `l3_liuyao.compute(dt,87.6)` | 明夷世4应1；既济世3应6；初爻=子孙·己卯木·应·朱雀 ✓ |
| 六壬 | `l3_liuren.compute(dt,87.6)` | 月将未/贵人酉(夜)；四课 卯丁空、亥卯雀、卯未空、亥卯雀；元首课 初卯空父母/中亥雀官鬼/末未阴子孙；时柱辛亥(北京时口径) ✓ |
| 小六壬 | `l3_xiaoliuren.compute(dt,87.6)` | 月数5→小吉、日数16→留连、时支序12→大安；断辞「身未动时…」 ✓ |
| 黄历 | `l3_huangli.daily(date(1974,7,5))` | 丁未/五月十六/除日吉(hl-01)/勾陈黑道(hl-02)/建除黄道(hl-02b)/红艳(hl-03-07)/宜忌表 ✓ |
| 河洛 | `l3_heluolishu.compute(dt,"女",87.6)` | 天30/地30；坎为水(6,6)；风水涣元堂六上；大运卦六上/九五/六四前三步；卦辞 ✓ |

**机器批量比对（脚本内 re 抽取全文表格，与快照逐格比对）：**
- 流年表 34 行（§6 17 行 + B.5 17 行）vs `snap.liunian` → **0 不一致**
- 大运表 16 行（§1.4 8 行 + B.4 8 行，两种列序分别解析）vs `snap.dayun.steps` → **0 不一致**
- 紫微宫位表 24 行（§3 + Z.2）vs `snap.ziwei_hours[22].palaces`（主星/辅煞并集/四化分别比对）→ **0 不一致**
- 神煞 §7/B.6 vs `snap.shensha.groups` → 名称与 rule_id 全等
- 正文全部数字 token 逐一清点（含 09:52、19:59:12、68.6、100、0.4/0.35/0.25、1979/1980/1988/1989、3两1钱 等）→ 均有出处，无裸数据
- 已跑 reconcile（temp/_p_rec.json）：`conflicts=0`，unverified=5（己卯 / 1979 / 1980 / 1988 / 1989，均为工具覆盖面限制；人工已定位：`snap.liuyao.lines[0]`、`snap.heluolishu.hlyl04.dayun.items` — 非数据错误）

## 二、Findings

### F1（高）紫微延伸数据引用的 `snap.ziwei_hours[hour=22]` 无承载字段（快照无法复核，违反「先落盘后引用」）

- 报告位置与原文：
  - L78「命宫：壬申；身宫：辰宫；**五行局：金四局**（数据底座：snap.ziwei_hours[hour=22]）」
  - L103「起限 4 岁，逆行，共 12 限（**数据底座：snap.ziwei_hours[hour=22]**）」+ L105-118 十二限表（含限四化）
  - L120「2026 流年：干支丙午；流年命宫落庚午（夫妻宫）；流年四化…（**数据底座：snap.ziwei_hours[hour=22]**）」
  - L95「生年四化落宫：廉贞禄→父母（癸酉）…（数据底座：snap.ziwei_hours[hour=22]）」
- 快照实际：`ziwei_hours[hour=22]` 条目键**仅** {hour, lunar, minggong, palaces}（l4_audit_output.py 生成逻辑：zr 仅存 minggong.zhi/gan + palaces 五字段，不存 wuxing_ju/shengong/daxian/liunian）；快照**全文**关键词计数=0：「金四」「大限」「起限」「daxian」「wuxing_ju」「身宫」「限四化」「廉贞禄」等星-化绑定均不出现（「流年」仅 10 处，均属 heluolishu/hepan 注记）。
- 复现：
  ```bash
  cd D:\shushu
  python -c "import json;d=json.load(open('temp/_probe_snap.json',encoding='utf-8'));print(list([x for x in d['ziwei_hours'] if x['hour']==22][0].keys()))"
  # → ['hour','lunar','minggong','palaces']
  python -c "raw=open('temp/_probe_snap.json',encoding='utf-8').read();[print(t,raw.count(t)) for t in ['金四','大限','起限','daxian','wuxing_ju','身宫','限四化']]"
  # → 全部 0
  ```
- 值本身经独立复算**全部正确**（l3_ziwei.compute 金四局/身宫辰；l3_ziwei_liunian.compute 12 限与 2026 四化逐行一致），且与 harvest 产物 `temp/_p_t1_ziwei.json` 的 `liunian_module` 全等——问题在**引用路径承载不了这批数据**：快照既无字段也无法机械复核，出口后审计链断。
- 修正建议（二选一）：① 这 4 处改标 harvest 产物来源并注明 l3_ziwei_liunian 直出链路；② 扩展 snapshot 生成器，将 `wuxing_ju`、`shengong`、`daxian`、`liunian(2026)` 落盘进快照后重出报告。

### F2（中）旺衰明细（ws-01 score=100、权重表）引用 `snap.wangshuai.zonghe`，该路径仅含 score/level

- 报告位置：L38「得令：…status=旺、score=100（rule=ws-01；数据底座：**snap.wangshuai.zonghe**，明细见附录 B.3）」；L40「…权重 得令 0.4 / 得地 0.35 / 得势 0.25；数据底座：snap.wangshuai.zonghe」
- 快照实际：`wangshuai` = `{"zonghe":{"score":68.6,"level":"偏旺"}}`——生成器源码明确只注入 zonghe 两字段；快照无 de_ling/de_di/de_shi/weights。
- 复现：
  ```bash
  python -c "import json;print(json.load(open('temp/_probe_snap.json',encoding='utf-8'))['wangshuai'])"
  # → {'zonghe': {'score': 68.6, 'level': '偏旺'}}
  ```
- 值经独立复算正确：`l3_wangshuai.compute` → de_ling.score=100、status=旺、rule_id=ws-01；zonghe.weights={'de_ling':0.4,'de_di':0.35,'de_shi':0.25}；de_di.items 长度 4。数值无误，引用路径无承载（68.6/偏旺两值在快照内 ✓，明细不在）。
- 修正建议：得令/权重行改标附录 B.3 或引擎直出；或将 wangshuai 三栏明细补入快照。

### F3（低）两处「泛指型」引用：附录来源文件名与实际文件不符；snap.meta 无口径字段

- 附录头（L279/L283）声明「source: t1_bazi.json / t1_ziwei.json / t4_b_all.json」，实际文件为 `temp/_p_t1_bazi.json`、`temp/_p_t1_ziwei.json`、`temp/_p_t4_all.json`（均存在、内容与附录一致）；字面文件名在盘上不存在。
- §15 L250/L251「判界时域…（数据底座：snap.meta）」「起运间隔…（数据底座：snap.meta）」：`snap.meta` 仅 {tool, generated_at, note, provenance}，无判界/起运口径字段。口径原文在 `docs/preregister.md` 确有背书（已核原文：「判界时域（2026-09-15 裁决）…一律北京时域」「起运间隔（2026-09-15 裁决）…两侧同域相减」，I-7 契约亦在）。
- 修正建议：文件名补 `_p_` 前缀；L250/251 引用改标 docs/preregister.md。

## 三、观察（非 finding，供仲裁参考）

1. 附录区与 `temp/_p_harvest.txt` 逐行 diff：仅 8 个标题追加「 (snapshot)」标签 + 末尾 1 行，**数据内容零改动**（附录头自述「禁止修改本文件」属流程注记，不影响数据一致性）。
2. §5「值使死门（zhishi_palace=5，中宫）」与「八门盘坤二宫死门」并存：两者均为快照原值（引擎口径=值使数至中宫、门盘寄坤2；中宫 star/door/shen 实测全 null，与 B 案事故形态不同），报告如实搬运，无自相矛盾。
3. §11 六壬时柱辛亥（北京时钟表时口径）与主链庚戌（真太阳时口径）：报告在 §11/§15 两处显式声明并列口径、互不顶替，快照 liuren.notes 同文——属申报口径而非双源不一致。
4. §4 大限「行限戊辰(44-53)」用于 2026 年（52 岁）：与引擎 daxian.items[4].liunian_years 含「2026(午)」一致 ✓。

## 四、总评

独立复算 14 模块、16 文件哈希、5 类结构化机器比对全部通过；**未发现任何数值造假、错抄或双源不一致**。三项 findings 均为「引用路径承载/表述」问题（F1 高、F2 中、F3 低），不涉及数据值错误；其中 F1 建议在出口前修正或补落盘，以保证快照可审计链完整。

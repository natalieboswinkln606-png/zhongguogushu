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

## 当前状态

**M0 数据基座已完成（v0.2），docs 为预注册契约**：8 张表（nayin/canggan/bagong/najia/changsheng/ganzhi_days + 节气/朔望空模板）；日干支已与 lunar-python 全区间对拍；属性断言 25 项全过；快照/勘误/白名单增补/转录协议见 docs/preregister.md。运行：`python gen_ganzhi.py && python compare.py && python validate.py && python assert_tables.py`。

## 目录

- `data/` — CSV 数据（UTF-8）+ shushu.db（validate.py 生成）
- `rules.py` — 唯一算法文件（干支序/阴阳/五行关系）
- `gen_ganzhi.py` / `compare.py` / `validate.py` / `assert_tables.py` — 生成/对拍/校验/断言
- `report/` — compare_report.txt、assert_report.txt
- `docs/` — preregister.md、whitelist.csv、sampling.md

## 许可

MIT License（见 LICENSE）。

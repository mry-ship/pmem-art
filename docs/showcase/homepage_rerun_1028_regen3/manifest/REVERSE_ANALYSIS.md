# regen3 反向分析与已修项（2026-10-30）

## 已修
1. **展陈路由**：`_SHOWCASE` 认「全部重跑/再跑一遍」；探针补克隆/变体/锁风格/提示词；未点名单支时默认同范围全清单（`_SHOWCASE_DEFAULT_FULL`）。测试：`tests/test_showcase_route.py`。
2. **status 措辞**：未满 4 轮且 <9.5 时预览不再说「已挑选最高分终稿」，改为「还不能当终稿，须继续」。
3. **finish 路径**：`docs/showcase/` 下成图不再被 `winner.image` 覆盖成 `assets/...`；assets 副本写入 `asset_image`。
4. **变体合同**：表情差分硬验收（半眯中线等可量测部位）；风格维勿崩到 6。已 `skills --install`。

## 仍属模型/内容短板（技能已收紧，需下趟重跑验证）
- 困倦半眯最高 8.94（好于 regen2 ~8.0，仍未兑现中线）
- c01 四档 / UI 概念满轮未过 9.5
- c04 recompose 机位难立住（本趟最终可到 9.43）
- Mode C 非关键枚仍允许同套一次出（展陈写「未记分」过 gate）
- 本机无 rembg（Mode C 靠生成端透明底）

## 验收
- `python3 -m unittest tests.test_showcase_route tests.test_showcase_gate -q`
- `python3 pmem_art.py showcase-gate --html docs/showcase/homepage_rerun_1028_regen3/index.html`
- `python3 pmem_art.py route --text "全部重跑 homepage_rerun_1028" --canonical "整页展陈同范围重跑"`

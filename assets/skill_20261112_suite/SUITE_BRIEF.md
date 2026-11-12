# 2026-11-12 全技能并发清点 · Suite Brief

## Banner
【按 全技能清点 / skill_suite 走了】`execute_ok=true`（无 agent canonical 冲突）

## 本趟默认
- 输出根：`assets/skill_20261112_suite/out/<route_id>/`
- 统一题材轴：**海港休闲 merge 咖啡馆新 IP「Brimwave Café」**（新开，不复用旧 seafood/drink 关系稿）
- 垫图：按技能类型对位 GH（禁止非 merge 一律套货柜表面；UI/图标跟各自参考表面）
- 生图：Cursor `GenerateImage`；隔离底默认纯黑（合成梯整表用浅奶油卡）
- 闭环：≥9.5 到线即停，最多 4 轮；交件标明是否过线
- 并发：各支独立 session，禁止共用 `latest`

## 垫图表
| route | 垫图 | 锁什么 | 不锁 |
| :--- | :--- | :--- | :--- |
| ui.kit | `refs/ref_ui.png` + `refs/ref_ui_dl.jpg` | 休闲 merge HUD 版式/组件气质 | 禁止像素抄 GH 构图 |
| icon.a | `refs/ref_appicon_dl.jpg` | App Icon 完成度/圆角安全区气质 | 禁止抄绿发角色肖像 |
| icon.b | 无（stroke 预设） | 线性一致 SVG 套 | — |
| icon.c | `refs/ref_merge_strip.png` | 道具格隔离底可读 | 禁止整表合成梯 |
| merge.ladder | `refs/ref_merge.png` + strip | 真机货面画风 + 格子版式 | 勿抄 HUD/手指 |
| draw.lens | `refs/ref_life.jpg` | 只出机位句，点选前不生图 | — |
| draw.clone | `refs/ref_merge.png` 锁画风 | 换新题材：港湾面包合成静物 | 禁止贴样张构图 |
| draw.variant | `refs/ref_story.jpg` 作身份 | 同一角色换惊讶表情 | 机位已在图上 |
| draw.multi | identity=`ref_life.jpg` structure=`ref_ui_renovate_dl.jpg` | 关态装修半成品→开态完工 | 身份机位作废跟结构 |
| draw.key | `refs/ref_life.jpg` 风格参考 | Key Art 主视觉 | 不抄像素 |
| style.lock | `refs/ref_merge.png` | 色板/光影/禁用词入库 | 本步不生图 |
| critique.review | 用本趟某张终稿 | 六维审 | 不生图 |
| atlas.file | 扫 suite out | 归位+刷新 atlas | 不生图 |
| coach.report | — | 进步/短板报告 | 知识卡不写入 |
| prompt.write | — | 扩写 Brimwave Café merge 提示词 2–4 套 | 不生图 |
| draw.ordinary | `refs/ref_life.jpg` | 单张港湾午后静物 | 不升 UI/图标/合成梯 |

## CLI 骨架（每支改 session / route-id / refs）
```bash
pyw -3 -u pmem_art.py route --text "<点名句>" --canonical "<标准句>"
pyw -3 -u pmem_art.py converge start --session suite_<id> --module brand.WorldStyle --route-id <rid> --goal "..." --reference-image-paths <pads> --aspect-ratio <ar>
pyw -3 -u pmem_art.py contract set --id suite_<id> --defaults "默认：…" --locks "…" --unlocks "…" --vibe "…"
pyw -3 -u pmem_art.py converge discuss --id suite_<id> --text "…"
pyw -3 -u pmem_art.py reasonableness review --id suite_<id> --skill <rid> --draft "…" --revised "…"
# GenerateImage → 落到 out/<rid>/rN.png
pyw -3 -u pmem_art.py converge generate --session suite_<id> --round N --image <path>
pyw -3 -u pmem_art.py converge judge --session suite_<id> --round N --image <path> ...
# ≥9.5 或满4 → finish
pyw -3 -u pmem_art.py converge finish --id suite_<id>
```

## 结算要求（每支回报父级）
1. banner / route_id
2. 终稿路径（或文字交付路径）
3. 各轮六维+总分+是否过线
4. 用的垫图路径
5. 底类型：opaque_isolation / true_alpha / n/a
6. 一句话成败与主要翻车点

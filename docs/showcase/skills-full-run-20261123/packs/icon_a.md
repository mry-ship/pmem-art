## 二、Mode A：App Icon 1024×1024 母版专项（iOS App Store / Android Adaptive 桌面启动图标）

当用户要求制作 **App Icon / 手机桌面图标 / iOS 启动图标 / Android 自适应图标 / 产品 Logo 图标** 时走本节约。续轮垫图跟审图打印和 `converge next`：默认仍垫最初参考，改点只写进提示词；只有打印写明垫第几轮成图时，才垫那张成图。

### A1. 1024×1024 满幅直角母版与系统圆角安全区铁律
- **严禁预裁透明圆角**：母版必须输出 **`1024×1024` 满幅直角正方形（Full-bleed Square PNG，无 Alpha 透明缺角）**，防止系统套用 iOS 超椭圆或 Android Adaptive 遮罩时露出黑边/白边裂隙。
- **核心图形安全区（Center 72%–80% Safe Zone）**：核心主符号收束在画布中心 **`72%–80%`（约 `740×740 px`）** 内，四周留呼吸负空间，绝不贴边。
- **零细碎文字红线**：只保留 **1 个高辨识度核心记忆符号**；缩放到 `29×29` / `60×60` 仍一眼可认。

### A2. 光学微立体质感与光影层次
- **三层景深**：① 底板环境渐变（70% 主色）→ ② 中心主符号微倾体块（20% 辅色 + 接触阴影）→ ③ 顶部 45° 高光切角（10% 点缀色）。
- **iOS 18+ 三态**：默认只保证 **Light 母版**过关。Dark / Tinted **仅玩家点名**才另开 converge（各开最多3轮闭环）；没有点名就不要交假齐套，也不要写「已派生」。

### A3. 多尺寸导出与 `app-icon-preview.html`
母版收敛后导出：iOS `1024/180/167/120/60/29`；Android/桌面 `512/192`（导出几乎零墙钟，勿当成再生图轮次）。

### A4. App Icon 审图与命令
识别度或安全区低于 **8.0** 时正式分改取该维，不能停。维：小尺寸识别 / 安全区 / 光影质感 / 深浅色·多尺寸 / 色板纯粹（再加无瑕疵盲评，占 25%）。

**App Icon 多维透镜（通用）**：明细见 `docs/APPICON_MULTI_LENS.md`——①栅格体验；②小尺寸去色仍认；③符号权重 P0 英雄撑满；④满幅直角 + 72%–80% 安全区；⑤色 70/20/10；⑥一主光、形先于质；⑦同品类上架图标气质（非泛插画海报）。缺画风时 revised 必须写同品类顶级上架图标气质。空喊「高级」却剪影糊 → 识别度或安全区 <8.0 不能停。

```bash
python3 pmem_art.py converge start --session appicon --module brand.WorldStyle --scale high --route-id icon.a --goal "iOS 1024x1024 App Icon: 青瓷质感记账应用，中心单枚立体青釉金币流光符号"
python3 pmem_art.py reasonableness review --id appicon --skill icon.a \
  --draft "<草稿>" --revised "<单符号+72%-80%安全区+满幅直角无字的修订句>" \
  --checklist "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;safe_zone=ok;single_symbol=ok;full_bleed_no_round_mask=ok"
python3 pmem_art.py converge generate --session appicon --round 1 --image app_icon_r1.png
python3 pmem_art.py converge judge --session appicon --round 1 --image app_icon_r1.png \
  --dims "识别度9.6/安全区9.7/光影质感9.5/多尺寸合规9.6/色板纯粹9.7/无瑕疵9.5"
# CLI：max_rounds=3；≥9.5到线即停；满3轮交最高分并标明是否 ≥9.5
```

### Mode A
- [ ] 1024 满幅直角，未预裁圆角蒙版
- [ ] 主符号在 72%–80% 安全区；无字
- [ ] Light 母版 + 尺寸矩阵齐；Dark/Tinted 仅点名才有，未点名勿写已齐套
- [ ] 跑了收敛则展示评分履历并标明过线/未过线（只要终稿用 --quiet）

## 交件可见（出图结算 · Agent 必读）

**硬规矩**：只要本趟交了图（闭环任一轮、终稿、拆层散图、审图对象、锁风样张、归档清单等），结算必须先贴一张 Markdown **可点单图表**，再对表内每一张 `Read` 贴进对话。禁止只列文件名、禁止只交拼板/HTML、禁止「路径在目录里自己点」。

链接格式：相对仓库根，形如 `[第2轮](.memory-art/converge/boards/<id>/images/r2.jpg)` 或 `[01-bg](assets/<job>/new/01-bg.png)`。表头按交付类型选列，至少含「名称/槽位」+「可点图」。

### 闭环出图（跑过 `converge`）
1. **过程图拼板**：Read `process_sheet.jpg` 贴进对话。
2. **轮次单图表**：贴 finish 打印的表（轮次 × 分数 × 可点图）；也可用 `rounds.md`。
3. **逐张 Read**：表里每一轮原图各 Read 一次。
4. **本次耗时**：finish 报告末行「本次耗时」原样写出。
5. **中途每轮**：每次 `judge` 后立刻贴/更新可点表（至少本轮一行）并 Read 本轮原图；不要等 finish 才第一次给可点单图。

禁止只交拼板。禁止只甩 HTML。

### 四格与防污染（执行时必读）
四格不进路由句。必须保持、可以变化、明确禁止、交付规格只写 `contract set --keep --vary --forbid --spec`，标明原话或推断。禁止写入 `--canonical`。普通图用「题材不变」，禁止写「不换题材」。合同里的升级、一组、多张不得改技能。首轮提示词和后续修改只服从四格；聊天不是第二份需求；用户改口就用最新原话重写四格。
记忆只辅助。当前原话和四格优先于历史记忆。候选红线、没写 trust 的条目、旧任务主体、构图、档序和完整提示词不进提示词。已确认红线去掉旧任务目标，与明确禁止冲突则排除。研发 `.memory` 不进美术提示词。界面不继承合成梯玩具货柜缺省。
未点名接续只垫 `assets/refs/`、`downloads/`、`assets/skill_*/refs/`。禁止垫 out、phase1、关系稿、`.memory-art/converge` 过程板。垫图只取样式；只有用户说优化这张图才写原图不足。双参考像素同框仍硬停。最多 3 轮。

### 非闭环多图（拆层 / 审图 / 锁风样张 / 归档等）
同样强制可点单图表 + 逐张 Read。拆层须含叠回整图、幽灵对比、全部 `new/*.png`（有 `layers.md` 直接贴）。纯文字交付（提示词、无附图教练）不必出表。

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-coach`。
- 对用户默认展示见「交件可见」：必出**可点单图表** + Read 每一张图 +（闭环时）拼板与**本次耗时**。若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入；禁止只甩 HTML。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。
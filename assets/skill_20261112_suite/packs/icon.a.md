## 二、Mode A：App Icon 1024×1024 母版专项（iOS App Store / Android Adaptive 桌面启动图标）

当用户要求制作 **App Icon / 手机桌面图标 / iOS 启动图标 / Android 自适应图标 / 产品 Logo 图标** 时走本节约。

### A1. 1024×1024 满幅直角母版与系统圆角安全区铁律
- **严禁预裁透明圆角**：母版必须输出 **`1024×1024` 满幅直角正方形（Full-bleed Square PNG，无 Alpha 透明缺角）**，防止系统套用 iOS 超椭圆或 Android Adaptive 遮罩时露出黑边/白边裂隙。
- **核心图形安全区（Center 72%–80% Safe Zone）**：核心主符号收束在画布中心 **`72%–80%`（约 `740×740 px`）** 内，四周留呼吸负空间，绝不贴边。
- **零细碎文字红线**：只保留 **1 个高辨识度核心记忆符号**；缩放到 `29×29` / `60×60` 仍一眼可认。

### A2. 光学微立体质感与光影层次
- **三层景深**：① 底板环境渐变（70% 主色）→ ② 中心主符号微倾体块（20% 辅色 + 接触阴影）→ ③ 顶部 45° 高光切角（10% 点缀色）。
- **iOS 18+ 三态**：默认只保证 **Light 母版**过关。Dark / Tinted **仅玩家点名**才另开 converge（各开最多4轮闭环）；没有点名就不要交假齐套，也不要写「已派生」。

### A3. 多尺寸导出与 `app-icon-preview.html`
母版收敛后导出：iOS `1024/180/167/120/60/29`；Android/桌面 `512/192`（导出几乎零墙钟，勿当成再生图轮次）。

### A4. App Icon 审图与命令
识别度或安全区低于 **8.0** 时正式分改取该维，不能停。维：小尺寸识别 / 安全区 / 光影质感 / 深浅色·多尺寸 / 色板纯粹（再加无瑕疵盲评，占 25%）。

**App Icon 多维透镜（通用）**：明细见 `docs/APPICON_MULTI_LENS.md`——①栅格体验；②小尺寸去色仍认；③符号权重 P0 英雄撑满；④满幅直角 + 72%–80% 安全区；⑤色 70/20/10；⑥一主光、形先于质；⑦同品类上架图标气质（非泛插画海报）。缺画风时 revised 必须写同品类顶级上架图标气质。空喊「高级」却剪影糊 → 识别度或安全区 <8.0 不能停。

```bash
pyw -3 -u pmem_art.py converge start --session appicon --module brand.WorldStyle --scale high --route-id icon.a --goal "iOS 1024x1024 App Icon: 青瓷质感记账应用，中心单枚立体青釉金币流光符号"
pyw -3 -u pmem_art.py reasonableness review --id appicon --skill icon.a \
  --draft "<草稿>" --revised "<单符号+72%-80%安全区+满幅直角无字的修订句>" \
  --checklist "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;safe_zone=ok;single_symbol=ok;full_bleed_no_round_mask=ok"
pyw -3 -u pmem_art.py converge generate --session appicon --round 1 --image app_icon_r1.png
pyw -3 -u pmem_art.py converge judge --session appicon --round 1 --image app_icon_r1.png \
  --dims "识别度9.6/安全区9.7/光影质感9.5/多尺寸合规9.6/色板纯粹9.7/无瑕疵9.5"
# CLI：max_rounds=4；≥9.5到线即停；满4轮交最高分并标明是否 ≥9.5
```

### Mode A
- [ ] 1024 满幅直角，未预裁圆角蒙版
- [ ] 主符号在 72%–80% 安全区；无字
- [ ] Light 母版 + 尺寸矩阵齐；Dark/Tinted 仅点名才有，未点名勿写已齐套
- [ ] 跑了收敛则展示评分履历并标明过线/未过线（只要终稿用 --quiet）

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-coach`。
- 对用户默认展示：**每轮六维分 + 不足 + 改点 + 胜出图 + 全轮履历**；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。
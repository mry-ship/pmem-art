# EXEC PACK icon.c

banner heading: ## 四、Mode C：游戏道具隔离底栅格图标（64/128/256px PNG，非 SVG）
skill: pmem-icon
file: .cursor/skills/pmem-icon/SKILL.md

## 四、Mode C：游戏道具隔离底栅格图标（64/128/256px PNG，非 SVG）

先锁「线宽/圆角/色板/投影」style-spec，再**批量**生成隔离底 PNG 做 preview。  
**关键枚 converge 默认禁止**：仅玩家点名某枚不对、或一致性审查不过时才开；开则最多4轮、≥9.5到线即停（CLI `max_rounds=4`，标明是否 ≥9.5）。**禁止**默认对背包每一格开闭环。
```bash
python3 pmem_art.py converge start --session <icon_c_id> --goal "道具格：<name>" --module brand.WorldStyle --route-id icon.c
python3 pmem_art.py reasonableness review --id <icon_c_id> --skill icon.c \
  --draft "<草稿>" --revised "<厚剪影+透明底+棚拍光+无字的修订句>" \
  --checklist "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;silhouette_read=ok;transparent_friendly=ok"
# 然后：converge generate → judge → finish（均带 --session <icon_c_id>）
```

正式分：剪影识别 30%（门槛）/ 描边色板 20% / 棚拍光 20% / 透明底 15%（门槛）/ 无字 15%（门槛）；无瑕疵盲评同库（展示六维时须带上）。judge 示例：`--dims "剪影识别8.6/描边色板8.4/棚拍光8.5/透明底9.0/无字9.2/无瑕疵8.8"`。Cursor：不透明隔离底（禁止后抠）；透明引擎：须真 alpha；白底/品红底不算合格隔离。门槛 <8.0 → 正式分改取该维。

**同店气质对齐（缺风格时强制）**：未点名画风且无风格参考时，写同品类顶级道具格气质（先认品类；禁止非休闲硬套软塑胶 merge）。同任务已有合成梯/`surface` 必须复用同一句。禁止垫竞品像素抄脸。

**图标 C 短透镜**：①厚剪影 64px 可认；②底隔离（Cursor实色/透明引擎真alpha）；③品类主光+接触影；④描边/色板/投影锁死；⑤无字无场景；⑥形先于质；⑦优先复用同店 surface。

### Mode C
- [ ] 底隔离合格；厚剪影 64px 可认
- [ ] 套件描边/色板/投影一致；无字
- [ ] 品类主光 + 接触影；无场景插画
- [ ] 关键枚若收敛：评分履历可见

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-coach`。
- 对用户默认展示：**每轮六维分 + 不足 + 改点 + 胜出图 + 全轮履历**；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。
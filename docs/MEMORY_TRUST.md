# 美术记忆可信度（Candidate → Verified → Canonical）

> 一次 AI 出图 ≥9.5 **不等于**一种配方长期有效。  
> 自动写入只进 **candidate**；**只有人工确认**（或既有盲评流水线）后才升级。  
> Warm-Start **只把已确认的红线/拍板写进提示词**；缺 `trust` 与 candidate 一律不进提示词。

## 等级

| `trust` | 含义 | 谁写入 | Warm-Start |
| :--- | :--- | :--- | :--- |
| **candidate** | 候选：单次收敛/反馈自动沉淀 | `converge finish`、高信号 feedback | **不**进提示词；recipe **不**计入定稿置信 |
| **verified** | 已复核：主美/人工确认，或盲评流水线 | `memory promote --to verified`；B2 盲评等人工闸 | 红线/拍板可注入；recipe 可计置信（摘要仍不进 prompt） |
| **canonical** | 主美确认的长期规范 | `memory promote --to canonical`（须人工） | 最高优先；冲突时胜出 |

`status` 仍管生死：`active` / `provisional` / `revoked` / `superseded` / `archived` …  
`trust` 管「有多信」。

**缺 `trust` 字段**：一律按 **candidate** 处理（不再有「祖父条款」把旧条目当成 verified）。  
这类条目 **不会**进提示词，也不会抬 recipe 置信；`doctor` 会单独统计「缺 trust」并提示迁移。

## 命令

```bash
# 升为已验证 / 主美定稿
pyw -3 -u pmem_art.py memory promote --id <ENTRY_ID> --to verified
pyw -3 -u pmem_art.py memory promote --id <ENTRY_ID> --to canonical --by "主美名"

# 审计：哪些 live 条目缺 trust / 仍是 candidate（默认含 recipe+红线+拍板）
pyw -3 -u pmem_art.py memory audit
# 只看可注入种类（与 promote-missing / doctor 软信号一致）
pyw -3 -u pmem_art.py memory audit --kind style_redline,art_decision

# 升级迁移（默认只预览；加 --apply 才写入）
# 默认只处理「缺 trust」的 style_redline / art_decision（recipe 不进 prompt，勿指望靠它清 recipe）
pyw -3 -u pmem_art.py memory promote-missing --to verified --by "migration-0.16.16"
pyw -3 -u pmem_art.py memory promote-missing --to verified --by "migration-0.16.16" --apply
pyw -3 -u pmem_art.py memory promote-missing --to verified --module character.Astra --kind style_redline --apply

# 否定撤销（不再进召回）
pyw -3 -u pmem_art.py memory revoke --id <ENTRY_ID> --reason "画师否定：头身比合同已改"

# 冲突：保留赢家，输家标记 superseded
pyw -3 -u pmem_art.py memory resolve --keep <WIN_ID> --drop <LOSE_ID> --reason "新头身比取代旧红线"
```

## 自动写入边界

- `finish --apply` 写入的 recipe / style_redline：**trust=candidate**（达标 recipe 的 `status` 仍可为 `active`，未达标为 `provisional`）。
- **不会**因同模块多次 ≥9.5 自动升 verified。`maybe_auto_verify_on_repeat_pass` 保留签名但恒返回空；verified 只来自 `memory promote`（或人工确认过的盲评路径）。
- 知识卡仍须玩家明确「收下」才写入（既有 `/pmem-coach` 合同不变）。
- 被 `revoke` 的条目 `status=revoked`，Warm-Start / search 默认排除。
- 个人 `taste`（keep_phrases / banned_habits）走口味通道，不经本表 trust 闸；仍会与当前四格 `forbid` 做冲突过滤。

## 与四格合同

开跑后用 `contract set --keep/--vary/--forbid/--spec` 写四格。四格**不进**标准路由句。  
Warm-Start 注入时：已确认红线/拍板若与四格 `forbid` **肯定句**冲突则排除；写着「避免/禁止…」的红线本身不算冲突。

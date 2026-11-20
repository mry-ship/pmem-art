# 美术记忆可信度（Candidate → Verified → Canonical）

> 一次 AI 出图 ≥9.5 **不等于**一种配方长期有效。  
> 自动写入只进 **candidate**；重复验证或主美确认后才升级。

## 等级

| `trust` | 含义 | 谁写入 | Warm-Start |
| :--- | :--- | :--- | :--- |
| **candidate** | 候选：单次收敛/反馈自动沉淀 | `converge finish`、高信号 feedback | recipe **不**计入定稿置信加成；红线仍可注入（标候选） |
| **verified** | 已复核：重复过线或独立盲评确认 | `memory promote --to verified`；同模块第 2 次 ≥9.5 `finish` 自动升；B2 盲评流水线 | recipe 可计置信 |
| **canonical** | 主美确认的长期规范 | `memory promote --to canonical`（须人工） | 最高优先；冲突时胜出 |

`status` 仍管生死：`active` / `provisional` / `revoked` / `superseded` / `archived` …  
`trust` 管「有多信」。无 `trust` 的旧条目：`provisional`→按 candidate；其余 live →按 **verified**（祖父条款，避免一夜清空置信）。

## 命令

```bash
# 升为已验证 / 主美定稿
pyw -3 -u pmem_art.py memory promote --id <ENTRY_ID> --to verified
pyw -3 -u pmem_art.py memory promote --id <ENTRY_ID> --to canonical --by "主美名"

# 否定撤销（不再进召回）
pyw -3 -u pmem_art.py memory revoke --id <ENTRY_ID> --reason "画师否定：头身比合同已改"

# 冲突：保留赢家，输家标记 superseded
pyw -3 -u pmem_art.py memory resolve --keep <WIN_ID> --drop <LOSE_ID> --reason "新头身比取代旧红线"
```

## 自动写入边界

- `finish --apply` 写入的 recipe / style_redline：**trust=candidate**（达标 recipe 的 `status` 仍可为 `active`，未达标为 `provisional`）。
- **二次过线自动升 verified**：同一模块磁盘上已有 ≥2 条达标（≥9.5）live recipe 时，把其中仍为 candidate 的升为 verified（`by=auto:repeat_pass`）。**不会**自动升 canonical。
- 知识卡仍须玩家明确「收下」才写入（既有 `/pmem-coach` 合同不变）。
- 被 `revoke` 的条目 `status=revoked`，Warm-Start / search 默认排除。

# Merge 交付管线（项目 canonical）

## 触发
- **`/pmem-merge-ladder`、`/art-ladder`、`/art-merge` 是同一条技能。** 全项目合成梯只走此管线。
- **16:9 同框** 只作体量预览，**不替代**文字八行定稿，也不是交付物。

## 顺序（禁止跳关）
1. **Step 0** — `BIBLES.md` + `ref-read`（B/C）→ 写 `surface` 句。
2. **第一段讨论** — 固定 3 稿。定清八件升级链和画风。六条说不通，或画风没写成一句，就不出图。不再拉到 8 稿。
3. **机读审关系** — 讨论定稿后 `python pmem_art.py merge relation-judge --file <副本.yaml> --track <域名>` → **exit 0 才算数字过关**。数字过了、合成说不通，仍然不算定稿。
4. **关系核对出图** — **默认每一档单独出一张 1:1 正方形**（画面里只有这一件）。整梯 16:9 八等列只作体量预览；`split-sheet` 若切进邻件或身份错位，**整套作废**，改回逐格重出。**禁止**垫 `val_heart` / `market` 风格 ref 文件。
5. **像素审计** — `python pmem_art.py merge audit --dir … --phase1 … --track …`。
6. **体量归一化（仅 audit 未过）** — `merge normalize` 按 YAML `scale_pct` 拉齐框高并 **再次 audit**。只把前景铺到平涂底上，不把原图矩形贴上去。通过则接受，仍不过则 **整梯重出**（normalize 是保险，不是主路径）。`audit` 会拦住内嵌方框。
7. **第二段** — `converge start --scale medium` → generate/judge **每轮后必跑 merge audit**；≥9.6 且关系仍在才 finish。

## 禁止
- 未定稿 `relation-judge` 通过就上 showcase。
- L02–L08 全部垫 L01 锁占格。
- 从 16:9 sheet **抠图 pad** 代替等分切格（见 `place_squares` 旧路径，仅作对照）。

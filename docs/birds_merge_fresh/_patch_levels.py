from pathlib import Path

START = "- **默认 8**（L1–L8）。merge 没给数量就按 8，不必再问。"
START2 = "- **默认起点 8**（L1–L8）。merge 没给数量先按 8 起草，但**对标后以合理为准**：竞品生物/建造段只有 6 档说得通 → 改为 `levels: 6`（常见 2×3），允许集 `6|8|9|12|15`。"
NEW = """- **默认起点 8**（L1–L8）。merge 没给数量先按 8 起草，但**对标后以合理为准**：竞品生物/建造段只有 6 档说得通 → 改为 `levels: 6`（常见 2×3），允许集 `6|8|9|12|15`。
- 玩家点名固定数量 → 跟点名（仍须过商业合理；点名 8 却说不通时要写明取舍，不能默默灌假档）。
- 有整表格子参考：`levels` **跟格数**。禁止无视参考硬做成 8。
- **禁止为凑满默认 8**自创金铠/火焰冠/无过渡堆群；玩家拒绝竞品某末段（如群）时，优先缩短档数或改用竞品确有的单件 denser 犒赏，详见 `MERGE_MULTI_LENS` §9。
"""

END_MARKERS = ["\n### C. `delivery`", "\n### C. delivery"]

files = [
    Path("skills_kit/skill_specs.py"),
    Path(".cursor/commands/pmem-merge-ladder.md"),
    Path(".agents/commands/pmem-merge-ladder.md"),
    Path(".claude/commands/pmem-merge-ladder.md"),
]

for f in files:
    t = f.read_text(encoding="utf-8")
    if START2.split("。")[0] in t and "禁止为凑满默认 8" in t:
        print("already", f)
        continue
    start = t.find(START)
    if start < 0:
        start = t.find("- **默认起点 8**")
    if start < 0:
        print("MISS start", f)
        continue
    end = -1
    for m in END_MARKERS:
        end = t.find(m, start)
        if end >= 0:
            break
    if end < 0:
        print("MISS end", f)
        continue
    t2 = t[:start] + NEW + t[end:]
    f.write_text(t2, encoding="utf-8")
    print("patched", f)

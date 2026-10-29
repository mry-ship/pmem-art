---
id: 01M642X1MVWSVPT5XPG1MBFHPQ
module: infra.Judge
entity: OfficialScore
kind: conclusion
status: seed
supersedes: []
anchors:
- skills_kit/scoring.py#weighted_harmonic
- vlm_judge.py#build_judge_system_prompt
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 官方停机分是六维加权调和平均，解析失败不能手填
verify: tests 与 scoring.weighted_harmonic；文档不再写五维均值当官方分
aliases:
- 六维
- 调和平均
- 官方分
---
依据提交 c791df8（六维打分）和 30ea756（文档对齐六维调和）。官方停机分是构图/光影/透视/质感/风格/无瑕疵的加权调和平均，不是更早的五维均值。解析失败要 fail-closed，不能手填总分交差。

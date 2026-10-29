---
id: 01M642X0RZZCHSHNJ16ZVJ1PKS
module: infra.Judge
entity: PixelJudge
kind: exclusion
status: seed
supersedes: []
anchors:
- vlm_judge.py#build_judge_system_prompt
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: VLM只按像素打六维，禁止把提示词当作成图证据
verify: build_judge_system_prompt 含禁止因 Prompt 写了某效果就默认画出来
applies: 独立 VLM 裁判开启时
aliases:
- 看图打分
- Prompt泄漏
---
依据 vlm_judge.py 的系统提示和 2026-10-29 六维打分提交。
排除：独立 VLM 裁判按图像像素打六个分，禁止因为 Prompt 写了某效果就默认画出来了。
无瑕疵是看图盲评，不要套一份瑕疵清单。
没配 API key 时不能假装打过分。

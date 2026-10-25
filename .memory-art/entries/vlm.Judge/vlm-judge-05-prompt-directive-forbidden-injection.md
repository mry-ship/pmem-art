---
id: vlm-judge-05
module: vlm.Judge
kind: pipeline_constraint
status: active
note_date: '2026-10-25'
verified: '2026-10-25'
author: pmem-art
summary: 生成 prompt 前置当前档位指令，并清掉上一档指令；next_fix 不带红线锁死标签
---
`compose_style_first_prompt` 把本档 `prompt_directive` 放在 prompt 最前，并去掉更早的收敛强度段，避免两套风格头叠在一起。`[红线锁死: ...]` 会从生成词和 next_fix 里剥掉。high 档只写「禁止搬入原图没有的物件」，生成词里不点名耳机、背包、孔明灯、花瓶。

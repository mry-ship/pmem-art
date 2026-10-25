---
id: vlm-judge-04
module: vlm.Judge
kind: pipeline_constraint
status: active
note_date: '2026-10-25'
verified: '2026-10-25'
author: pmem-art
summary: low 档只在缺陷写明动作或姿态已改变时压到 8.50，保持原姿态的描述不误杀
---
low 档 `allow_action_pose_change` 为 false。缺陷里出现「动作改变」「姿态不符」「pose changed」这类漂移说法时，校准分压到 8.50 以下。只写「保持托腮」或「未改动作」不会触发。

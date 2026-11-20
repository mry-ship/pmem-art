---
id: 01M7VWGCVAJ2F0BDRNVH5TJ88W
module: infra.Scripts
entity: ApiTransit
kind: decision
status: active
supersedes: []
anchors: []
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 生图/对话中转切到 APIKing；密钥只走 APIKING_API_KEY 环境变量
verify: image_gen.py --list 显示 apiking；--balance 返回余额且 config.key 为空
applies: 本机 Cursor skills 生图/对话中转配置时
source:
  conversation: bf7d8e5f-c2a9-4e6a-893b-c08ebb46f00e
---
apikey-image / openai / kimi / typesafe / gemini 的 base_url 改为 https://apiking.ai/v1（gemini 根为 https://apiking.ai）。
密钥禁止写进 config.json：key 留空，key_env=APIKING_API_KEY；若误把 sk- 填进 key_env 会当环境变量名导致泄漏到 --list，已防呆并迁到用户环境变量。
生图：默认同步 /images/generations|/edits + Idempotency-Key；
可选 --async-task 轮询 /images/tasks；
--balance/--models-remote/--dry-run 不扣生图费。
qwen-image-layered 仍是 WaveSpeed，未改。

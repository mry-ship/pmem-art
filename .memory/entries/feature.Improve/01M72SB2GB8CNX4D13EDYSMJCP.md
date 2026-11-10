---
id: 01M72SB2GB8CNX4D13EDYSMJCP
module: feature.Improve
entity: WarmStartGuardrails
kind: exclusion
status: active
supersedes: []
anchors:
- improve/warm_start.py
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 不做 archive 旧 merge summary，改注入过滤
source:
  conversation: 47f6bbb9-8756-4463-9252-553fb8630b97
---
排除：给 14 条旧 merge recipe/redline 的 frontmatter 打 status:superseded。
理由：治标不治本，以后还会冒出新的旧话术；
改个人记忆文件面大、回退差。
改为只在 build_warm_start_pack 按 summary 短语过滤 merge.* 条目。

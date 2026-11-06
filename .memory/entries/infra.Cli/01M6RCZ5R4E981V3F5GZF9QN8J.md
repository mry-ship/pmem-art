---
id: 01M6RCZ5R4E981V3F5GZF9QN8J
module: infra.Cli
entity: AtlasRevealApi
kind: risk
status: active
supersedes: []
anchors:
- atlas_reveal.py#promote_final
- atlas_reveal.py#_cors
- atlas_reveal.py#_serve_static
- skills_kit/converge.py#_session_file
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 工作台本机接口无令牌，会话 id 带 .. 能改写目录外 JSON
verify: 临时目录调 atlas_reveal.promote_final(root, source_path=一张png, session_id='../../secret')，目录外
  json 被改写
applies: pmem_art atlas 守护进程在跑、浏览器能访问 127.0.0.1 时
aliases:
- 本机接口
- CORS
- 路径穿越
- promote_final
- session_id
source:
  conversation: 2fb9d6ff-529d-4817-aa0f-d09fd39d062b
---
atlas_reveal 绑 127.0.0.1，但 CORS 是 * 且回 Access-Control-Allow-Private-Network。
浏览器打开恶意网页时，可以读项目里除 .git / .env / node_modules 以外的文件（静态托管没有后缀白名单，.py 也按 octet-stream 返回），并且 POST /api/delete 把图扔进垃圾、POST /api/promote 覆盖图。
promote_final 和 converge._session_file 都是直接拼 f"{session_id}.json"，不拒绝 ..。
临时目录实测：session_id=../../secret 时，promote_final 返回 ok，并把目录外的 secret.json 从 {"keep": true} 改成带 winner_image 的会话 JSON。
本机工具，不是远程未授权；风险在工作台开着时被网页读仓库、丢图、改写 JSON。

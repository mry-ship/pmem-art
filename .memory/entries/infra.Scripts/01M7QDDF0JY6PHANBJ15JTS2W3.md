---
id: 01M7QDDF0JY6PHANBJ15JTS2W3
module: infra.Scripts
entity: Packaging
kind: feature
status: active
supersedes: []
anchors:
- README.md
- USER_MANUAL.md
- docs/route_pipeline.html
- docs/showcase/skills-homepage/index.html
revision: git:a0e50b0
author: 1002378395@qq.com
note_date: '2026-11-18'
summary: 发版后须同步 README/手册/认路图/展陈页的版本与新合同说明
verify: rg "0.16.13|局部改" README.md USER_MANUAL.md docs/route_pipeline.html docs/showcase/skills-homepage/index.html
applies: 发用户包后更新对外文档
aliases:
- 主页手册
- 发版文档
- README同步
source:
  conversation: 1c3c3fc0-ee1e-4b91-82b0-59a517862363
---
需求来源：发用户包后主页与手册若只改版本号、不写新合同，画师仍按旧说法用。
必须保持：升版后同步 README、USER_MANUAL、docs/route_pipeline.html、docs/showcase/skills-homepage、docs/skills/flows.html；
版本链到最新 Release；
新合同（如局部改 draw.touchup）写进技能表、30秒选型、认路对照表。
适用条件：每次打用户包 / GitHub Release 之后。
入口：改完推 main；用户包 zip 不含这些改动时下次重打，或仅文档提交即可上 GitHub 主页。

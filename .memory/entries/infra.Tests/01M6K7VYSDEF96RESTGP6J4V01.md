---
id: 01M6K7VYSDEF96RESTGP6J4V01
module: infra.Tests
entity: CoachLearn
kind: conclusion
status: active
supersedes: []
anchors:
- tests/test_coach_learn_drills.py
revision: git:8d36bd0
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: coach 测例子进程须 UTF-8 且用唯一临时目录
verify: python -m pytest tests/test_coach_learn_drills.py -q
applies: Windows 跑 tests/test_coach_learn_drills.py 时
---
固定 /tmp 路径在全量套件下会抢目录；
subprocess text 默认 GBK 会在读中文 stdout 时 UnicodeDecodeError。
改为 tempfile.mkdtemp + encoding=utf-8 errors=replace。

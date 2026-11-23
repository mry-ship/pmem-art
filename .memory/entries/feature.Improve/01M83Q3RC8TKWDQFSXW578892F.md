---
id: 01M83Q3RC8TKWDQFSXW578892F
module: feature.Improve
entity: TasteWriteLock
kind: correction
status: active
supersedes: []
anchors:
- improve/taste_profile.py#save_taste
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: taste 写入用 memory_write_lock+原子replace，sync放锁外
verify: tests.test_hard_pits_gates.TestTasteLock
applies: save_taste / finish 后静默写口味
source:
  kind: conversation
---
并行 finish/coach 写 taste 时 Windows 复制 lock 文件自锁。
更正：save_taste 锁内 tmp+os.replace；
sync_active_project_to_library 放锁外；
OSError/Timeout 重试。

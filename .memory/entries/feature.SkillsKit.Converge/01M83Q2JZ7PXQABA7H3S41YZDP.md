---
id: 01M83Q2JZ7PXQABA7H3S41YZDP
module: feature.SkillsKit.Converge
entity: HardPitAspectRegister
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/converge.py#_assert_output_matches_session_aspect
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 有垫图须显式aspect；登记成图必须对上会话画幅并记sha1
verify: unittest tests.test_hard_pits_gates -q
applies: converge start/generate/judge 出图闭环
verified: '2026-11-23'
verified_at: '2026-11-23T16:38:52.743+08:00'
source:
  kind: conversation
---
展陈 multi 会话自称16:9却登720×1280。更正：
  1) start 有垫图时强制 --aspect-ratio，禁止从垫图像素静默继承；
  2) generate 登记时无论是否有垫图都用 _aspect_relation 硬校输出；
  3) 登记写 image_sha1，judge 时对账防换文件挂分。

---
id: 01M83RYN1ZY4KZZC9J6BGG19VS
module: feature.SkillsKit.Converge
entity: PlateBind
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/scoring.py#cap_reported_dims
- skills_kit/converge.py#_foreign_plate_owner
- skills_kit/converge.py#_finish_plate_replaced
- skills_kit/judge_auto.py#auto_vlm_judge_image
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 硬顶压分后六维不得高于正式分；换图或串图不能挂原分
verify: pyw -3 -m unittest tests.test_hard_pits_gates.TestImageSha1 tests.test_param_validation.TestGateFixes
applies: converge generate/judge/finish；旧轮次没有 image_sha1 时不拦 finish
aliases:
- 串图
- 换图挂分
- 六维封顶
- sha1
source:
  kind: test
---
正式分被硬顶压到加权均值以下时，报出去的六维也必须压到不超过这个正式分；
加权均值没有被压低时，允许单轴高于均值。
重写后的维度串必须能被 parse_5d_dims 原样读回，读不回就不改显示串，避免加和尺被写成界面尺。
generate 拒绝把已登记在其他轮次或其他会话的同一份字节再登记；
同一会话同一轮重试放行，会话文件名与内部 session_id 不一致时仍按文件名认作本会话。
judge 把当时文件的 sha1 写入轮次。
finish 时赢家带 sha1 则重算，字节变了或文件没了就拒绝结算，不标 finished，showcase_ready 记回 false。
没有 image_sha1 的旧轮次仍可结算。
不改 8.90/7.90/8.50/8.85 顶和 9.5 过线，也不改对向画幅只锁画风。

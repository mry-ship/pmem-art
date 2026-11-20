---
id: 01M7WSA8066ZBHQWHW8KJ2KJFP
module: feature.SkillsKit.Converge
entity: FinishSettleTrust
kind: correction
status: active
supersedes: []
anchors:
- feedback.py#_write_memory_entry_unlocked
- skills_kit/converge.py#_apply_finish_memory_and_atlas
revision: git:55fd2ca
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: finish同资产覆盖不得降级已promote的trust
verify: pytest tests/test_auto_verify_write_path.py::TestAutoVerifyWritePath::test_replace_same_asset_does_not_demote_canonical
  -q
applies: converge finish --apply 写 recipe 且 replace_same_asset 时
---
Bugbot：write_memory_entry(replace_same_asset) 无条件写 trust=candidate，converge finish 过线替换同资产 recipe 时会把主美已 promote 的 verified/canonical 打回 candidate；
auto_verify 也回不到 canonical。
更正：覆盖时按 TRUST_RANK 取高不取低，并保留 trust_by/trust_at。
验证见 test_replace_same_asset_does_not_demote_canonical。

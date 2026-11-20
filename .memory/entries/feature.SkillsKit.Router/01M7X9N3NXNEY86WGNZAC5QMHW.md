---
id: 01M7X9N3NXNEY86WGNZAC5QMHW
module: feature.SkillsKit.Router
entity: GridNotInCanonical
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/route_normalize.py#validate_canonical
revision: git:ea22106
author: yanghu
note_date: '2026-11-21'
summary: 四格写进标准路由句则判冲突
verify: pytest tests/test_skill_hardening.py::CanonicalWarnTests tests/test_route_false_fire.py::RouteFalseFireTests::test_same_style_chest_is_not_merge
  -q
applies: pmem_art.py route 的 --canonical 与 advise_route
---
需求来源：四格合同是生成依据，不能为了让路由更完整而改已验证的短模板。
必须保持：标准路由句继续用短模板。
canonical 里出现必须保持、可以变化、明确禁止、交付规格或 --keep/--vary/--forbid/--spec 时，validate_canonical 报 grid_in_canonical，advise 降为冲突且 execute_ok 为假。
普通图模板仍是「题材不变」，禁止「不换题材」。
认路折叠继续 append_extras=False，「变成」不得带出「别画原来」。
同风格蓝色宝箱不因合同里的升级或一组送进合成梯。
适用条件：Agent 填写 --canonical 或本地启发式标准句做二次 plan 时。
入口：python3 pmem_art.py route --text --canonical。

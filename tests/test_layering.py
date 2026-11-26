"""分层守卫：用 AST 检查产品模块的导入方向（含函数内的延迟导入）。

规则（层级从低到高 core < domain < engine < entry）：
  R1 低层不得导入高层（含 core 只能导入 core）。
  R2 domain 层的四个域（memory / judge / routing / atlas）互不导入。
  R3 任何产品模块不得导入 entry 层（pmem_art、art_shell_hook、skills_kit 包 __init__ 等）。
  R4 scripts.pmem_layer_split 是独立技能包，不得导入产品模块。
现有违规冻结在 tests/layering_baseline.json，只允许减少，不允许新增。
重新生成基线：py -3 -I tests/test_layering.py --write-baseline
"""
from __future__ import annotations

import ast
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(__file__).with_name("layering_baseline.json")

LAYERS = {"core": 0, "domain": 1, "engine": 2, "entry": 3}
CORE = {
    "art_cli", "skills_kit._time", "improve._time", "skills_kit.platform_cli",
    "skills_kit.session_lock", "skills_kit.local_locks", "skills_kit.gate_skip",
    "skills_kit.alpha_policy", "skills_kit.icon_geometry", "skills_kit.subject_lexicon",
    "skills_kit.medium_family", "skills_kit.must_fix", "skills_kit.final_prompt_gate",
    "skills_kit.colloquial_lexicon", "skills_kit.benchmark_catalog",
    "skills_kit.agent_route_cases", "skills_kit.prior_reuse_gate",
}
DOMAINS = {
    "memory": {"lifecycle", "feedback", "classify", "improve"},  # improve.* 按前缀归入
    "judge": {
        "vlm_judge", "skills_kit.scoring", "skills_kit.judge_auto",
        "skills_kit.converge_judge_bridge", "skills_kit.absolute_5d_agent_rubric",
        "skills_kit.image_gates", "skills_kit.scale_profile", "skills_kit.judge_rules",
    },
    "routing": {
        "skills_kit.agent_router", "skills_kit.route_bank",
        "skills_kit.route_gate", "skills_kit.route_ask", "skills_kit.route_normalize",
        "skills_kit.skill_registry", "skills_kit.skill_specs",
    },
    "atlas": {"atlas_index", "atlas_reveal", "build_atlas", "skills_kit.process_board"},
}
ENGINE = {
    "skills_kit.converge", "skills_kit.converge_loop", "skills_kit.converge_policy",
    "skills_kit.prompt_scale", "skills_kit.delivery_gates", "skills_kit.reasonableness_gate",
    "skills_kit.understanding_contract", "skills_kit.showcase_gate",
    "skills_kit.validate_params", "skills_kit.parallel_slots", "skills_kit.merge_relation",
    "skills_kit.skill_image_gen", "skills_kit.export_mode_c_icon",
}
ENTRY = {
    "pmem_art", "art_shell_hook", "benchmark_evolution", "skills_kit",
    "skills_kit.install", "skills_kit.skills_verify",
}
SKILL_PKG = "scripts.pmem_layer_split"


def classify(mod: str) -> tuple[str, str] | None:
    """返回 (层, 域)；不属于产品模块返回 None。

    core.* 全部是 core 层。connectors.* 是跨域连接器，与入口同层：只有入口和连接器自己能
    导入它们，业务模块经 core.hooks 按名字调用，守卫里看不到这条边（这是设计）。
    """
    if mod == "core" or mod.startswith("core."):
        return "core", "core"
    if mod == "connectors" or mod.startswith("connectors."):
        return "entry", "connector"
    if mod in CORE:
        return "core", "core"
    for dom, names in DOMAINS.items():
        if mod in names or (dom == "memory" and mod.startswith("improve.")):
            return "domain", dom
    if mod in ENGINE:
        return "engine", "engine"
    if mod in ENTRY:
        return "entry", "entry"
    return None


def _product_files() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for p in sorted(ROOT.glob("*.py")):
        out[p.stem] = p
    for pkg in ("skills_kit", "improve", "core", "connectors"):
        for p in sorted((ROOT / pkg).glob("*.py")):
            out[pkg if p.stem == "__init__" else f"{pkg}.{p.stem}"] = p
    for p in sorted((ROOT / "scripts" / "pmem_layer_split").glob("*.py")):
        name = SKILL_PKG if p.stem == "__init__" else f"{SKILL_PKG}.{p.stem}"
        out[name] = p
    return out


def _resolve(cur: str, is_pkg: bool, node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [a.name for a in node.names]
    assert isinstance(node, ast.ImportFrom)
    base = node.module or ""
    if node.level:
        pkg = cur.split(".") if is_pkg else cur.split(".")[:-1]
        pkg = pkg[: len(pkg) - (node.level - 1)]
        base = ".".join(pkg + ([base] if base else []))
    return [base] + [f"{base}.{a.name}" for a in node.names]


def _dynamic_targets(node: ast.AST) -> list[str]:
    """__import__("x") / importlib.import_module("x") 里的字符串常量。变量名无法静态解析，不计。"""
    if not isinstance(node, ast.Call) or not node.args:
        return []
    fn = node.func
    name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else ""
    arg = node.args[0]
    if name in ("__import__", "import_module") and isinstance(arg, ast.Constant) and isinstance(arg.value, str):
        return [arg.value]
    return []


def collect_violations() -> tuple[set[str], list[str]]:
    files = _product_files()
    violations: set[str] = set()
    unclassified: list[str] = []
    for mod, path in files.items():
        in_skill = mod.startswith(SKILL_PKG)
        src = classify(mod)
        if src is None and not in_skill:
            unclassified.append(mod)
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                targets = _resolve(mod, path.name == "__init__.py", node)
            else:
                targets = _dynamic_targets(node)
            for target in targets:
                # 取最长匹配的产品模块名
                hit = max((m for m in files if target == m or target.startswith(m + ".")),
                          key=len, default=None)
                if hit is None or hit == mod:
                    continue
                if in_skill:
                    if not hit.startswith(SKILL_PKG):
                        violations.add(f"{mod} -> {hit} [R4 skill_isolated]")
                    continue
                dst = classify(hit)
                if dst is None:
                    continue
                if dst[0] == "entry" and src[0] != "entry":
                    violations.add(f"{mod} -> {hit} [R3 import_entry]")
                elif LAYERS[dst[0]] > LAYERS[src[0]]:
                    violations.add(f"{mod} -> {hit} [R1 upward {src[0]}->{dst[0]}]")
                elif src[0] == dst[0] == "domain" and src[1] != dst[1]:
                    violations.add(f"{mod} -> {hit} [R2 cross_domain {src[1]}->{dst[1]}]")
    return violations, unclassified


class LayeringTests(unittest.TestCase):
    def test_every_product_module_is_classified(self) -> None:
        _, unclassified = collect_violations()
        self.assertEqual(unclassified, [], "新模块要在 tests/test_layering.py 里归层：" + ", ".join(unclassified))

    def test_no_new_layer_violations(self) -> None:
        current, _ = collect_violations()
        frozen = set(json.loads(BASELINE.read_text(encoding="utf-8"))["violations"])
        new = sorted(current - frozen)
        self.assertEqual(new, [], "出现新的分层违规（不允许新增）：\n  " + "\n  ".join(new))

    def test_baseline_has_no_stale_entries(self) -> None:
        current, _ = collect_violations()
        frozen = set(json.loads(BASELINE.read_text(encoding="utf-8"))["violations"])
        fixed = sorted(frozen - current)
        self.assertEqual(fixed, [], "这些违规已消除，请重新生成基线让它只减不增：\n  " + "\n  ".join(fixed))


if __name__ == "__main__":
    if "--write-baseline" in sys.argv:
        cur, unc = collect_violations()
        BASELINE.write_text(json.dumps({"violations": sorted(cur)}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"baseline written: {len(cur)} violations; unclassified={unc}")
    else:
        unittest.main()

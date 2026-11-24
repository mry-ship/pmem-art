from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills_kit.reasonableness_gate import cmd_reasonableness_at_root

draft = "红伞白点蘑菇托盘上放瑞士芝士、蓝果橙果绿叶，黑底休闲3D"
revised = (
    "红伞白点蘑菇托盘上放瑞士芝士、蓝果橙果绿叶，黑底休闲3D。"
    "红伞帽白点蘑菇柄造型食物托盘（装饰道具）：托盘上稳放一块带圆孔瑞士芝士、一颗蓝果、一颗橙果、两三片卡通绿叶；"
    "纯黑隔离底#000；略俯视前侧单主光柔阴影；1:1；"
    "休闲手游3D软立体圆润厚实暖饱和无硬描边；无文字水印无界面。"
    "一眼失败：变野生菌生态图、丢蓝果橙果绿叶、白底或加UI字。"
)
checklist = "subject_action=ok;contact_scale=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok"
code = cmd_reasonableness_at_root(
    ROOT,
    action="review",
    session_id="showcase-ordinary-20261123",
    skill="ordinary",
    draft=draft,
    revised=revised,
    checklist=checklist,
    notes="keep_draft_anchors",
    force=False,
)
raise SystemExit(code)

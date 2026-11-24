from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills_kit.reasonableness_gate import cmd_reasonableness_at_root

draft = "休闲三消主菜单HUD概念图，竖屏9:16，对标Royal Match级三消装修主页"
revised = (
    "休闲三消主菜单HUD概念图，竖屏9:16 concept-only。对标品类=Royal Match级三消/装修休闲主页。"
    "不使用任何参考图生图；控件仅按下列八项文字规格生成。"
    "八项："
    "1渲染=玩具软立体塑料chrome+暖场景底，不成写实摄影/赛博霓虹/扁平线稿；"
    "2镜头=轻微俯视房间全屏，切天花上沿，地板留底栏高；"
    "3分区=顶栏单行头像|金币|体力|星星|右上设置；中景花园房间角色情绪锚；中下主任务Level+Area双钮；底栏五Tab且Home居中；"
    "4色面积=场景暖绿米约70%、chrome金白20%、主CTA珊瑚橙10%，锚色#F4A261/#FFE8A3/#2E8B57；"
    "5材质=按钮厚塑料描边顶高光、顶栏胶囊金属描边、植被软绒、地面木纹；"
    "6疏密=主任务最大，次入口远小于主任务，禁右侧四squircles万能骨架，设置角落可点不抢戏；"
    "7控件工艺=顶栏与主按钮写清：圆角胶囊/厚圆角矩形、暖金描边、上下深浅体积、顶高光条、柔投影、主钮Bold字重/顶栏Semibold，控件不重叠不切边；"
    "8文案=允许Level/Play/Home与资源数字，禁止海报大标题与乱码假字。"
    "一眼失败：分区错成空心九宫格或关卡棋盘、主CTA遮脸、chrome做成海报。"
    "主CTA不遮脸不压主角五官；chrome来自UI规格。"
)
checklist = (
    "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;"
    "layout_zones=ok;no_content_clutter=ok;chrome_not_illustration=ok;"
    "cta_clear_of_faces=ok;control_craft=ok"
)
code = cmd_reasonableness_at_root(
    ROOT,
    action="review",
    session_id="showcase-ui-kit-20261123",
    skill="ui",
    draft=draft,
    revised=revised,
    checklist=checklist,
    notes="text_only_no_ref",
    force=False,
)
raise SystemExit(code)

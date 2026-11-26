"""口语留出集：没写触发词的自然说法也要走对技能；反例防止词表补宽后误伤。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skills_kit.agent_router import plan_route  # noqa: E402

IMG = ["ref/a.png"]
TWO = ["ref/a.png", "ref/b.png"]
ROLES2 = ["identity", "structure"]

# (句子, 附图, 角色, 期望 route_ids)
POSITIVE = [
    ("画一张原画 森林里的小屋", [], [], ["draw.key"]),
    ("来张原画，一个骑士", [], [], ["draw.key"]),
    ("我想看不同镜头的方案再决定", [], [], ["draw.lens"]),
    ("几种机位给我看看", [], [], ["draw.lens"]),
    ("把背景里那个小瑕疵去掉", IMG, [], ["draw.touchup"]),
    ("按这张图的画风画一只猫", IMG, [], ["draw.clone"]),
    ("参考这张，画一只新的狐狸", IMG, [], ["draw.clone"]),
    ("照这个色调画一家书店", IMG, [], ["draw.clone"]),
    ("这张图换成冬天版本，其他不动", IMG, [], ["draw.variant"]),
    ("同一个女孩，身份和机位不动，换成冬天的衣服", IMG, [], ["draw.variant"]),
    ("同一个宝箱出开箱前后三个状态", [], [], ["draw.multi"]),
    ("三张图同一机位，分别是白天、黄昏、夜晚", [], [], ["draw.multi"]),
    ("把这张场景拆成可叠回的图层", IMG, [], ["layer.split"]),
    ("帮我写个提示词，要冷调雨夜", [], [], ["prompt.write"]),
    ("锁一下这张样张的风格", IMG, [], ["style.lock"]),
]

# 不能被补宽的词表带偏
NEGATIVE = [
    ("水彩头像，看着舒服就行", [], [], ["draw.ordinary"]),
    ("画一张冷调的窗边女孩", [], [], ["draw.ordinary"]),
    ("镜头感强一点的半身像，只要一张", [], [], ["draw.ordinary"]),
    ("两张附图都留着，画一张窗边女孩，没说哪张管什么", TWO, [], ["draw.ordinary"]),
    ("以后都按这张的画风画，先锁风格", IMG, [], ["style.lock"]),
    ("先写提示词，先不出图", [], [], ["prompt.write"]),
    ("同一个女孩，身份和机位不动，再来一张生气的表情", IMG, [], ["draw.variant"]),
    ("第一张是脸，第二张是坐姿，两张各管一件事", TWO, ROLES2, ["draw.multi"]),
    ("按这个提示词画一张窗边女孩", [], [], ["draw.ordinary"]),
]


class RouteColloquialVocabTests(unittest.TestCase):
    def _run(self, rows):
        bad = []
        for text, imgs, roles, want in rows:
            got = list(plan_route(text, images=imgs, image_roles=roles).route_ids)
            if got != want:
                bad.append(f"{text!r}: want {want} got {got}")
        self.assertEqual(bad, [], "\n" + "\n".join(bad))

    def test_positive_phrasings(self) -> None:
        self._run(POSITIVE)

    def test_negative_no_false_fire(self) -> None:
        self._run(NEGATIVE)


if __name__ == "__main__":
    unittest.main()

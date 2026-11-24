"""本轮正文压过相反的口味和档位句。"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from improve.taste_profile import TEMP_HINTS, _extract_hints
from improve.warm_start import merge_warm_start_prompt
from skills_kit.prompt_scale import compose_style_first_prompt, drop_opposed_injections


_MEDIUM = {
    "scale": "medium",
    "prompt_directive": "题材画风优先：保画风与机位，柔化光影，只抛光已经有的材质和光，不另起一种光",
    "forbidden_changes": [
        "viewpoint_angle (不改机位与镜头视角)",
        "element_count (不增删主体元素清单)",
    ],
}


class TastePolarityTests(unittest.TestCase):
    def test_high_saturation_is_not_stored_as_avoid(self) -> None:
        self.assertNotIn("避免过饱和", _extract_hints("上架图标要高饱和", TEMP_HINTS))

    def test_oversaturation_is_still_avoid(self) -> None:
        self.assertIn("避免过饱和", _extract_hints("这张过饱和了", TEMP_HINTS))


class BriefBeatsInjectionTests(unittest.TestCase):
    def test_icon_brief_drops_opposed_taste_and_scale_lines(self) -> None:
        memory = (
            "【Warm-Start 注入包 — 第 1 轮 Prompt 必须吸收】\n"
            "- 个人口味: 光影=柔光 / 顶光 / 暖光；色温=避免过饱和 / 暖色调"
        )
        brief = (
            "题材画风优先：保画风与机位，柔化光影，只抛光已经有的材质和光，不另起一种光 | "
            "一个大符号撑满、高饱和。左右约占画面 76%，落在 72%–80% 安全区。"
            "不要漂在空地上的投影。 | "
            "约束：不改机位与镜头视角；不增删主体元素清单"
        )
        out = drop_opposed_injections(f"{memory}\n{brief}", memory_block=memory)
        self.assertNotIn("避免过饱和", out)
        self.assertNotIn("柔光", out)
        self.assertNotIn("柔化光影", out)
        self.assertNotIn("只抛光已经有的", out)
        self.assertNotIn("不改机位", out)
        self.assertNotIn("与机位", out)
        self.assertIn("顶光", out)
        self.assertIn("暖光", out)
        self.assertIn("暖色调", out)
        self.assertIn("高饱和", out)
        self.assertIn("76%", out)
        self.assertIn("不要漂在空地上的投影", out)
        self.assertIn("不增删主体元素清单", out)
        self.assertIn("保画风", out)

    def test_plain_polish_keeps_camera_and_taste(self) -> None:
        text = (
            "题材画风优先：保画风与机位，柔化光影，只抛光已经有的材质和光，不另起一种光 | "
            "半身肖像，暖色。 | "
            "约束：不改机位与镜头视角；不增删主体元素清单\n"
            "- 个人口味: 光影=柔光 / 顶光；色温=避免过饱和 / 暖色调"
        )
        out = drop_opposed_injections(text)
        self.assertIn("不改机位与镜头视角", out)
        self.assertIn("保画风与机位", out)
        self.assertIn("柔光", out)
        self.assertIn("避免过饱和", out)
        self.assertIn("柔化光影", out)

    def test_memory_mention_of_high_sat_does_not_erase_taste(self) -> None:
        memory = "【Warm-Start 注入包】\n- 红线: 旧案高饱和\n- 个人口味: 色温=避免过饱和 / 暖色调"
        brief = "半身肖像，低饱和。"
        out = drop_opposed_injections(f"{memory}\n{brief}", memory_block=memory)
        self.assertIn("避免过饱和", out)

    def test_negated_fill_does_not_drop_camera_lock(self) -> None:
        text = "不要撑满。 | 约束：不改机位与镜头视角；不增删主体"
        out = drop_opposed_injections(text)
        self.assertIn("不改机位与镜头视角", out)

    def test_medium_compose_omits_camera_and_soften_when_brief_asks(self) -> None:
        out = compose_style_first_prompt(
            "一个大符号撑满、高饱和。左右约占画面 76%。不要漂在空地上的投影。",
            _MEDIUM,
        )
        self.assertNotIn("不改机位", out)
        self.assertNotIn("柔化光影", out)
        self.assertNotIn("与机位", out)
        self.assertNotIn("只抛光已经有的", out)
        self.assertIn("不增删主体元素清单", out)
        self.assertIn("高饱和", out)
        self.assertIn("保画风", out)

    def test_medium_compose_keeps_camera_for_plain_polish(self) -> None:
        out = compose_style_first_prompt("半身肖像，暖色。", _MEDIUM)
        self.assertIn("不改机位与镜头视角", out)
        self.assertIn("保画风与机位", out)
        self.assertIn("柔化光影", out)

    def test_warm_start_omits_opposed_taste(self) -> None:
        pack = {
            "prompt_block": (
                "【Warm-Start 注入包 — 第 1 轮 Prompt 必须吸收】\n"
                "- 个人口味: 光影=柔光 / 顶光；色温=避免过饱和 / 暖色调"
            )
        }
        out = merge_warm_start_prompt(
            "高饱和。左右约占画面 76%。不要漂在空地上的投影。",
            pack,
        )
        self.assertNotIn("避免过饱和", out)
        self.assertNotIn("柔光", out)
        self.assertIn("顶光", out)
        self.assertIn("暖色调", out)
        self.assertIn("高饱和", out)

    def test_block_highlight_drops_soft_light(self) -> None:
        pack = {
            "prompt_block": (
                "【Warm-Start 注入包 — 第 1 轮 Prompt 必须吸收】\n"
                "- 个人口味: 光影=柔光 / 顶光；色温=暖色调"
            )
        }
        out = merge_warm_start_prompt(
            "中间图示按同品类已上架图标的完成度来画：一块材料铺满整个符号，高光成块。",
            pack,
        )
        self.assertNotIn("柔光", out)
        self.assertIn("顶光", out)

    def test_warm_start_keeps_taste_for_plain_polish(self) -> None:
        pack = {
            "prompt_block": (
                "【Warm-Start 注入包 — 第 1 轮 Prompt 必须吸收】\n"
                "- 个人口味: 光影=柔光 / 顶光；色温=避免过饱和 / 暖色调"
            )
        }
        out = merge_warm_start_prompt("半身肖像，暖色。", pack)
        self.assertIn("避免过饱和", out)
        self.assertIn("柔光", out)

    def test_reject_reference_person_drops_identity_lock(self) -> None:
        tail = (
            "约束：不增删主体元素清单；保持原图画风笔触与色板；"
            "保持原图性别、物种、年龄段与核心外观"
        )
        out = drop_opposed_injections(tail, brief="不要画国王、皇冠、胡子和人脸。")
        self.assertNotIn("性别", out)
        self.assertIn("保持原图画风", out)
        self.assertIn("不增删主体元素清单", out)

    def test_juicy_icon_brief_drops_mute_and_recompose_ban(self) -> None:
        text = (
            "约束：不改机位与镜头视角；不做整体 recompose / 换景别故事；不增删主体元素清单\n"
            "- 个人口味: 光影=顶光 / 暖光；色温=避免过饱和 / 暖色调"
        )
        brief = "软卡通厚体积，与英雄冷暖相反，外轮廓被四边裁开，底色只留在四角，可读核心落在 72%–80% 安全区。"
        out = drop_opposed_injections(f"{text}\n{brief}")
        self.assertNotIn("避免过饱和", out)
        self.assertNotIn("recompose", out)
        self.assertNotIn("不改机位", out)
        self.assertIn("不增删主体元素清单", out)
        self.assertIn("顶光", out)
        self.assertIn("暖色调", out)

    def test_glaze_request_drops_oily_highlight_ban(self) -> None:
        text = "- 个人禁用习惯: 廉价塑料感/油腻高光；过曝高光"
        out = drop_opposed_injections(text, brief="高光改成厚糖釉")
        self.assertNotIn("油腻高光", out)
        self.assertIn("廉价塑料感", out)
        self.assertIn("过曝高光", out)

    def test_plain_volume_keeps_oily_highlight_ban(self) -> None:
        text = "- 个人禁用习惯: 廉价塑料感/油腻高光；过曝高光"
        out = drop_opposed_injections(text, brief="软卡通厚体积，外轮廓被四边裁开")
        self.assertIn("油腻高光", out)

    def test_stage_margin_flags_a_centered_box_inside_the_band(self) -> None:
        from PIL import Image

        from skills_kit.prompt_scale import icon_stage_margins, icon_subject_span

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "stage.png"
            im = Image.new("RGB", (200, 200), (20, 40, 90))
            im.paste(Image.new("RGB", (160, 150), (220, 40, 40)), (20, 25))
            im.save(path)
            bw, bh = icon_subject_span(path)
            left, right, top, bottom = icon_stage_margins(path)
        self.assertGreaterEqual(min(bw, bh), 0.72)
        self.assertGreater(max(left, right, top, bottom), 0.06)

    def test_stage_margin_quiet_when_silhouette_reaches_edges(self) -> None:
        from PIL import Image

        from skills_kit.prompt_scale import icon_stage_margins

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bleed.png"
            im = Image.new("RGB", (200, 200), (20, 40, 90))
            im.paste(Image.new("RGB", (196, 196), (220, 40, 40)), (2, 2))
            im.save(path)
            left, right, top, bottom = icon_stage_margins(path)
        self.assertLessEqual(max(left, right, top, bottom), 0.06)

    def test_icon_continuation_releases_the_stage(self) -> None:
        from skills_kit.prompt_scale import compose_continuation_prompt, get_converge_scale_profile

        text = compose_continuation_prompt(
            "外轮廓被四边裁开",
            get_converge_scale_profile("medium"),
            pad_image="r1.jpg",
            release_margin=True,
        )
        self.assertIn("四周留白不算要保持的内容", text)
        self.assertNotIn("没点名的地方保持垫图", text)

    def test_plain_polish_keeps_recompose_ban(self) -> None:
        text = "半身肖像，暖色。 | 约束：不做整体 recompose / 换景别故事；不改机位与镜头视角"
        out = drop_opposed_injections(text)
        self.assertIn("不做整体 recompose", out)
        self.assertIn("不改机位与镜头视角", out)

    def test_subject_span_flags_a_floating_mark(self) -> None:
        from PIL import Image

        from skills_kit.prompt_scale import icon_subject_span

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "icon.png"
            im = Image.new("RGB", (200, 200), (20, 40, 90))
            mark = Image.new("RGB", (80, 70), (220, 40, 40))
            im.paste(mark, (60, 65))
            im.save(path)
            bw, bh = icon_subject_span(path)
        self.assertLess(bw, 0.72)
        self.assertLess(bh, 0.72)

    def test_subject_span_ignores_a_corner_gradient(self) -> None:
        from PIL import Image

        from skills_kit.prompt_scale import icon_subject_span

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "grad.png"
            im = Image.new("RGB", (200, 200))
            pix = im.load()
            for y in range(200):
                for x in range(200):
                    pix[x, y] = (20 + x // 4, 40 + y // 5, 120)
            im.paste(Image.new("RGB", (70, 60), (220, 30, 40)), (65, 70))
            im.save(path)
            bw, bh = icon_subject_span(path)
        self.assertLess(bw, 0.72)
        self.assertLess(bh, 0.72)
        self.assertGreater(bw, 0.2)

    def test_directive_removed_on_purpose_is_not_missing(self) -> None:
        from skills_kit.prompt_scale import directive_survives_in_prompt

        directive = "题材画风优先：保画风与机位，柔化光影"
        prompt = "题材画风优先：保画风 | 外轮廓被画面裁到，约占 76%，不要投影"
        self.assertFalse(directive in prompt)
        self.assertTrue(directive_survives_in_prompt(directive, prompt))

    def test_plain_brief_keeps_identity_lock(self) -> None:
        tail = "约束：保持原图性别、物种、年龄段与核心外观"
        out = drop_opposed_injections(tail, brief="把茶盏再画稳一点")
        self.assertIn("性别、物种、年龄段与核心外观", out)


if __name__ == "__main__":
    unittest.main()

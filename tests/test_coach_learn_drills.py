#!/usr/bin/env python3
"""Regression: coach / learn suggest must import DRILLS; coach syncs into project library."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class CoachLearnDrillsTests(unittest.TestCase):
    def _run(self, proj: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(ROOT / "pmem_art.py"), "--root", str(proj), *args],
            capture_output=True,
            text=True,
            env=env,
        )

    def test_coach_and_learn_suggest_do_not_crash_on_drills(self) -> None:
        tmp = Path("/tmp/pmem_coach_learn_drills_test")
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        shared = tmp / "shared"
        proj = tmp / "proj"
        env = dict(os.environ)
        env["PMEM_ART_SHARED_DIR"] = str(shared)

        init = self._run(proj, "init", "--name", "CoachLearn", env=env)
        self.assertEqual(init.returncode, 0, init.stderr or init.stdout)

        mem = proj / ".memory-art" / "_reflections"
        mem.mkdir(parents=True, exist_ok=True)
        (mem / "seed.json").write_text(
            json.dumps(
                {
                    "what_still_weak": "构图中轴对称太死板，光影暗部糊化",
                    "taste_deltas": {"from_defects": ["透视消失点偏中", "质感边缘毛边"]},
                    "what_fixed": [],
                    "lessons": [{"category": "composition", "note": "三分法"}],
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        coach = self._run(proj, "coach", env=env)
        self.assertEqual(coach.returncode, 0, coach.stderr or coach.stdout)
        self.assertNotIn("NameError", coach.stderr or "")
        out = coach.stdout or ""
        self.assertTrue("教练" in out or "短板" in out, out[:500])

        surface = proj / ".memory-art" / "_profile" / "coach_plan.json"
        self.assertTrue(surface.is_file(), "coach_plan missing on surface profile")
        plan = json.loads(surface.read_text(encoding="utf-8"))
        self.assertTrue(plan.get("weak_spots"), plan)
        self.assertTrue(any(w.get("drills") for w in plan["weak_spots"]), plan)

        # atlas_commands includes coach → load_project syncs into projects/<id>/
        proj_plans = list((proj / ".memory-art" / "projects").glob("*/_profile/coach_plan.json"))
        self.assertTrue(proj_plans, "coach_plan not synced into project library layer")

        learn = self._run(proj, "learn", "suggest", env=env)
        self.assertEqual(learn.returncode, 0, learn.stderr or learn.stdout)
        self.assertNotIn("NameError", learn.stderr or "")


if __name__ == "__main__":
    unittest.main()

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
out = Path(__file__).with_name("_reason_out.txt")

draft = (
    "Same pink-dress blonde fairy with fruit basket, sleepy expression, black background."
)
revised = (
    "Same identity and locked camera as the reference: medium close-up waist-up blonde fairy on solid black, "
    "slight three-quarter facing camera, cartoon 3D soft-plastic render. "
    "KEEP LOCKED: bright blonde thick side-swept bangs and twin braids with pink bands; pointed elf ears with pink inner tone; "
    "emerald green irises; pink puffed-sleeve dress with white collar and vertical pearl buttons; pearl necklace with one turquoise circular pendant; "
    "four translucent light-blue veined fairy wings; right hand (viewer left) holding woven fruit basket with red apple, green grapes, yellow fruit; "
    "left hand raised near chest; same head tilt and silhouette; no new accessories, no purple bracelet. "
    "ONLY CHANGE expression to sleepy/yawning: BOTH upper eyelids must press down past the horizontal midline of each green iris, "
    "leaving only a thin green iris slit plus catchlight; soft sleepy half-open mouth as a light yawn (not a smirk, not a wide grin). "
    "Keep soft plastic highlights, clean edges, commercial casual cute character finish. Solid black background."
)
checklist = (
    "subject_action=ok;contact_scale=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;only_named_delta=ok"
)

cmd = [
    sys.executable,
    "-u",
    str(root / "pmem_art.py"),
    "reasonableness",
    "review",
    "--id",
    "battery1105-variant",
    "--skill",
    "variant",
    "--draft",
    draft,
    "--revised",
    revised,
    "--checklist",
    checklist,
]
proc = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace")
out.write_text(
    f"exit={proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}\n",
    encoding="utf-8",
)
print(proc.stdout)
print(proc.stderr, file=sys.stderr)
Path(__file__).with_name("_revised_prompt.txt").write_text(revised, encoding="utf-8")
sys.exit(proc.returncode)

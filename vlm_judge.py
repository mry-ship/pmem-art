#!/usr/bin/env python3
"""Independent vision-model art judge (optional).

When an API key is configured (config / env / local secrets), `converge judge`
asks a real vision model for 5D scores. When no key is set, the pipeline keeps
the default agent-as-judge path (CLI `--dims` / `--defects`).
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_ANTHROPIC_BASE = "https://api.anthropic.com"
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

ENV_KEY_CANDIDATES = (
    "PMEM_VLM_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
)


def default_vlm_judge_config() -> dict[str, Any]:
    return {
        "enabled": "auto",  # auto | always | never
        "provider": "openai",  # openai | openai_compatible | anthropic
        "api_key": "",
        "api_key_env": "PMEM_VLM_API_KEY",
        "base_url": "",
        "model": "",
        "timeout_sec": 90,
        "on_error": "fallback",  # fallback | fail
        "max_image_side_px": 1536,
        "write_sidecar": True,
    }


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in (overlay or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_vlm_judge_config(root: Path | None, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Merge defaults ← project config.yaml ← optional local secrets file."""
    cfg = default_vlm_judge_config()
    project_cfg = ((data or {}).get("config") or {}).get("vlm_judge")
    if isinstance(project_cfg, dict):
        cfg = _deep_merge(cfg, project_cfg)
    if root is not None:
        local = Path(root) / ".memory-art" / "vlm_judge.local.yaml"
        if local.is_file():
            try:
                from pmem_art import load_yaml
                local_data = load_yaml(local.read_text(encoding="utf-8"))
                if isinstance(local_data, dict):
                    # Allow either top-level keys or nested under vlm_judge:
                    blob = local_data.get("vlm_judge") if isinstance(local_data.get("vlm_judge"), dict) else local_data
                    if isinstance(blob, dict):
                        cfg = _deep_merge(cfg, blob)
            except Exception:
                pass
    return cfg


_PLACEHOLDER_KEYS = {
    "",
    "YOUR_KEY_HERE",
    "<api-key>",
    "sk-xxx",
    "sk-x",
    "sk-test",
    "sk-test-123",
    "changeme",
    "todo",
}


def _looks_like_real_key(value: str) -> bool:
    v = (value or "").strip()
    if not v or v in _PLACEHOLDER_KEYS:
        return False
    if len(v) < 16:
        return False
    return True


def resolve_api_key(cfg: dict[str, Any]) -> str:
    """Resolve API key without logging it. Prefer explicit config, then named env, then fallbacks."""
    inline = str(cfg.get("api_key") or "").strip()
    if _looks_like_real_key(inline):
        return inline
    named = str(cfg.get("api_key_env") or "PMEM_VLM_API_KEY").strip()
    if named and _looks_like_real_key(os.environ.get(named, "")):
        return os.environ[named].strip()
    provider = str(cfg.get("provider") or "openai").strip().lower()
    ordered = list(ENV_KEY_CANDIDATES)
    if provider == "anthropic":
        ordered = ("ANTHROPIC_API_KEY", "PMEM_VLM_API_KEY", "OPENAI_API_KEY")
    elif provider in ("openai", "openai_compatible"):
        ordered = ("PMEM_VLM_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY")
    for env_name in ordered:
        val = os.environ.get(env_name, "").strip()
        if _looks_like_real_key(val):
            return val
    return ""


def is_vlm_judge_configured(cfg: dict[str, Any] | None = None, *, root: Path | None = None, data: dict[str, Any] | None = None) -> bool:
    cfg = cfg or load_vlm_judge_config(root, data)
    mode = str(cfg.get("enabled") or "auto").strip().lower()
    if mode in ("never", "off", "false", "0"):
        return False
    key = resolve_api_key(cfg)
    if mode == "always":
        return bool(key)
    # auto
    return bool(key)


def vlm_judge_status(root: Path | None = None, data: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = load_vlm_judge_config(root, data)
    key = resolve_api_key(cfg)
    active = is_vlm_judge_configured(cfg)
    provider = str(cfg.get("provider") or "openai")
    model = str(cfg.get("model") or "").strip() or (
        DEFAULT_ANTHROPIC_MODEL if provider == "anthropic" else DEFAULT_OPENAI_MODEL
    )
    mode = str(cfg.get("enabled") or "auto").strip().lower()
    if active:
        source = "independent_vlm"
    elif mode in ("never", "off", "false", "0"):
        source = "disabled"
    elif mode == "always" and not key:
        source = "always_but_no_key"
    else:
        source = "agent_self_judge"
    return {
        "enabled_mode": cfg.get("enabled", "auto"),
        "active": active,
        "provider": provider,
        "model": model,
        "base_url": cfg.get("base_url") or (
            DEFAULT_ANTHROPIC_BASE if provider == "anthropic" else DEFAULT_OPENAI_BASE
        ),
        "api_key_present": bool(key),
        "api_key_env": cfg.get("api_key_env") or "PMEM_VLM_API_KEY",
        "on_error": cfg.get("on_error") or "fallback",
        "source": source,
    }


def _mime_for(path: Path) -> str:
    suf = path.suffix.lower()
    if suf in (".jpg", ".jpeg"):
        return "image/jpeg"
    if suf == ".webp":
        return "image/webp"
    if suf == ".gif":
        return "image/gif"
    return "image/png"


def _encode_image_b64(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    return base64.standard_b64encode(raw).decode("ascii"), _mime_for(path)


def build_judge_system_prompt(scale_prof: dict[str, Any] | None = None) -> str:
    weights = (scale_prof or {}).get("dim_weights") or {
        "composition": 0.20,
        "lighting_color": 0.25,
        "perspective_anatomy": 0.20,
        "texture_detail": 0.20,
        "spec_style": 0.15,
    }
    scale = str((scale_prof or {}).get("scale") or "medium")
    return (
        "你是独立美术主美裁判，只根据图像像素做五维打分，禁止因 Prompt 写了某效果就默认画出来了。"
        "分数 0~10，一位小数。严苛：平光/呆板居中/假纸纹/数字化噪点不得虚高到 9.0+。"
        f"当前收敛档位={scale}。五维权重提示（你仍须给单项分，总分由系统加权）："
        f"构图{weights.get('composition', 0.2):.0%}、光影{weights.get('lighting_color', 0.25):.0%}、"
        f"透视解剖{weights.get('perspective_anatomy', 0.2):.0%}、质感{weights.get('texture_detail', 0.2):.0%}、"
        f"风格规格{weights.get('spec_style', 0.15):.0%}。"
        "只输出一个 JSON 对象，不要 Markdown 围栏，字段："
        '{"composition":0,"lighting_color":0,"perspective_anatomy":0,"texture_detail":0,"spec_style":0,'
        '"strengths":"...","defects":"...","next_fix":"..."}'
    )


def build_judge_user_text(
    *,
    goal: str = "",
    module: str = "",
    scale: str = "",
    round_num: int = 1,
) -> str:
    parts = [
        f"请审阅第 {round_num} 轮候选图。",
        f"档位: {scale or 'medium'}。",
    ]
    if module:
        parts.append(f"模块: {module}。")
    if goal:
        parts.append(f"任务简述（仅供上下文，勿把未画出的词当已实现）: {goal[:400]}")
    parts.append("按系统要求输出 JSON。")
    return " ".join(parts)


def _extract_json_object(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        raw = fence.group(1)
    else:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            raw = raw[start : end + 1]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def observations_from_vlm_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize model JSON into dims string + defects/strengths/next_fix."""
    aliases = {
        "composition": ("composition", "构图", "comp"),
        "lighting_color": ("lighting_color", "lighting", "光影", "色彩", "light"),
        "perspective_anatomy": ("perspective_anatomy", "perspective", "anatomy", "透视", "解剖", "结构"),
        "texture_detail": ("texture_detail", "texture", "质感", "肌理", "细节"),
        "spec_style": ("spec_style", "style", "spec", "风格", "规格"),
    }
    scores: dict[str, float] = {}
    for dest, keys in aliases.items():
        for k in keys:
            if k in payload and payload[k] is not None:
                try:
                    scores[dest] = float(payload[k])
                    break
                except (TypeError, ValueError):
                    continue
    dims = ""
    if len(scores) == 5:
        dims = (
            f"构图{scores['composition']:.1f}/光影{scores['lighting_color']:.1f}/"
            f"透视{scores['perspective_anatomy']:.1f}/质感{scores['texture_detail']:.1f}/"
            f"风格{scores['spec_style']:.1f}"
        )
    return {
        "dims": dims,
        "dims_scores": scores,
        "strengths": str(payload.get("strengths") or payload.get("亮点") or "").strip(),
        "defects": str(payload.get("defects") or payload.get("缺陷") or payload.get("不合理") or "").strip(),
        "next_fix": str(payload.get("next_fix") or payload.get("修正") or "").strip(),
        "raw_payload": payload,
    }


def _http_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise RuntimeError("VLM response is not a JSON object")
    return data


def _call_openai_compatible(
    *,
    api_key: str,
    base_url: str,
    model: str,
    system: str,
    user_text: str,
    image_b64: str,
    mime: str,
    timeout: float,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{image_b64}"},
                    },
                ],
            },
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = _http_json(url, payload, headers, timeout)
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"OpenAI-compatible response missing choices: {data!r}"[:300])
    msg = (choices[0] or {}).get("message") or {}
    content = msg.get("content")
    if isinstance(content, list):
        texts = [str(p.get("text") or "") for p in content if isinstance(p, dict)]
        return "\n".join(texts)
    return str(content or "")


def _call_anthropic(
    *,
    api_key: str,
    base_url: str,
    model: str,
    system: str,
    user_text: str,
    image_b64: str,
    mime: str,
    timeout: float,
) -> str:
    url = base_url.rstrip("/") + "/v1/messages"
    payload = {
        "model": model,
        "max_tokens": 1200,
        "temperature": 0.2,
        "system": system,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime,
                            "data": image_b64,
                        },
                    },
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    data = _http_json(url, payload, headers, timeout)
    blocks = data.get("content") or []
    texts = [str(b.get("text") or "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
    if not texts:
        raise RuntimeError(f"Anthropic response missing text: {data!r}"[:300])
    return "\n".join(texts)


def call_vision_judge(
    image_path: Path,
    *,
    cfg: dict[str, Any],
    scale_prof: dict[str, Any] | None = None,
    goal: str = "",
    module: str = "",
    round_num: int = 1,
) -> dict[str, Any]:
    """Call the configured vision API. Raises on transport/parse failure."""
    api_key = resolve_api_key(cfg)
    if not api_key:
        raise RuntimeError("VLM API key not configured")
    if not image_path.is_file():
        raise FileNotFoundError(f"image not found: {image_path}")

    provider = str(cfg.get("provider") or "openai").strip().lower()
    timeout = float(cfg.get("timeout_sec") or 90)
    b64, mime = _encode_image_b64(image_path)
    system = build_judge_system_prompt(scale_prof)
    user_text = build_judge_user_text(
        goal=goal,
        module=module,
        scale=str((scale_prof or {}).get("scale") or ""),
        round_num=round_num,
    )

    if provider == "anthropic":
        base = str(cfg.get("base_url") or DEFAULT_ANTHROPIC_BASE).rstrip("/")
        model = str(cfg.get("model") or DEFAULT_ANTHROPIC_MODEL)
        text = _call_anthropic(
            api_key=api_key,
            base_url=base,
            model=model,
            system=system,
            user_text=user_text,
            image_b64=b64,
            mime=mime,
            timeout=timeout,
        )
    else:
        base = str(cfg.get("base_url") or DEFAULT_OPENAI_BASE).rstrip("/")
        model = str(cfg.get("model") or DEFAULT_OPENAI_MODEL)
        text = _call_openai_compatible(
            api_key=api_key,
            base_url=base,
            model=model,
            system=system,
            user_text=user_text,
            image_b64=b64,
            mime=mime,
            timeout=timeout,
        )

    payload = _extract_json_object(text)
    if not payload:
        raise RuntimeError(f"VLM returned non-JSON content: {text[:240]}")
    obs = observations_from_vlm_payload(payload)
    if not obs.get("dims"):
        raise RuntimeError(f"VLM JSON missing 5D scores: {payload!r}"[:300])
    obs["provider"] = provider
    obs["model"] = model if provider != "anthropic" else str(cfg.get("model") or DEFAULT_ANTHROPIC_MODEL)
    obs["raw_text"] = text
    return obs


def maybe_run_independent_vlm_judge(
    image_path: str,
    *,
    root: Path | None = None,
    data: dict[str, Any] | None = None,
    scale_prof: dict[str, Any] | None = None,
    goal: str = "",
    module: str = "",
    round_num: int = 1,
    cli_dims: str = "",
    cli_defects: str = "",
    cli_strengths: str = "",
    cli_next_fix: str = "",
) -> dict[str, Any]:
    """
    Try independent VLM judge. Returns a result dict always:

    - source = "independent_vlm" | "agent_self_judge" | "vlm_error_fallback"
    - dims / defects / strengths / next_fix filled for downstream audit
    """
    cfg = load_vlm_judge_config(root, data)
    status = vlm_judge_status(root, data)
    out: dict[str, Any] = {
        "source": "agent_self_judge",
        "active": False,
        "status": status,
        "dims": cli_dims or "",
        "defects": cli_defects or "",
        "strengths": cli_strengths or "",
        "next_fix": cli_next_fix or "",
        "error": "",
        "provider": "",
        "model": "",
    }
    if not is_vlm_judge_configured(cfg):
        return out

    p = Path(image_path) if image_path else Path()
    if image_path and not p.is_file() and root is not None:
        cand = Path(root) / image_path
        if cand.is_file():
            p = cand
    if not p.is_file():
        out["error"] = f"image missing for VLM judge: {image_path}"
        if str(cfg.get("on_error") or "fallback") == "fail":
            out["source"] = "vlm_error"
            out["active"] = True
        else:
            out["source"] = "vlm_error_fallback"
        return out

    try:
        obs = call_vision_judge(
            p,
            cfg=cfg,
            scale_prof=scale_prof,
            goal=goal,
            module=module,
            round_num=round_num,
        )
        out.update(
            {
                "source": "independent_vlm",
                "active": True,
                "dims": obs["dims"],
                "defects": obs.get("defects") or "",
                "strengths": obs.get("strengths") or "",
                "next_fix": obs.get("next_fix") or "",
                "provider": obs.get("provider") or "",
                "model": obs.get("model") or "",
                "raw_payload": obs.get("raw_payload"),
            }
        )
        if cfg.get("write_sidecar", True):
            sidecar = p.with_suffix(p.suffix + ".vlm.json")
            try:
                sidecar.write_text(
                    json.dumps(
                        {
                            "dims": out["dims"],
                            "defects": out["defects"],
                            "strengths": out["strengths"],
                            "next_fix": out["next_fix"],
                            "provider": out["provider"],
                            "model": out["model"],
                            "source": "independent_vlm",
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
            except OSError:
                pass
        return out
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, RuntimeError, ValueError) as exc:
        out["error"] = str(exc)
        if str(cfg.get("on_error") or "fallback") == "fail":
            out["source"] = "vlm_error"
            out["active"] = True
            out["dims"] = ""
            out["defects"] = f"独立视觉裁判失败: {exc}"
        else:
            out["source"] = "vlm_error_fallback"
            out["dims"] = cli_dims or ""
            out["defects"] = cli_defects or ""
        return out


def cmd_vlm_judge(
    root: Path,
    data: dict[str, Any],
    action: str = "status",
    *,
    image: str = "",
    scale: str = "medium",
    goal: str = "",
    module: str = "",
) -> int:
    """CLI helper: status | probe."""
    action = (action or "status").strip().lower()
    if action in ("status", "config", "show"):
        st = vlm_judge_status(root, data)
        print("🔭 独立视觉裁判 (vlm_judge)")
        print(f"   · 模式 enabled={st['enabled_mode']} → {'已激活' if st['active'] else '未激活（走 Agent 自评）'}")
        print(f"   · provider={st['provider']}  model={st['model']}")
        print(f"   · base_url={st['base_url']}")
        print(f"   · api_key={'已配置' if st['api_key_present'] else '未配置'}  (env 优先: {st['api_key_env']} / OPENAI_API_KEY / ANTHROPIC_API_KEY)")
        print(f"   · on_error={st['on_error']}  source={st['source']}")
        print("   · 本地密钥文件（可选，勿提交）: .memory-art/vlm_judge.local.yaml")
        print("   · 项目配置: .memory-art/config.yaml → vlm_judge:")
        return 0

    if action in ("probe", "test", "run"):
        if not image:
            print("❌ probe 需要 --image <path>")
            return 1
        from skills_kit import get_converge_scale_profile

        prof = get_converge_scale_profile(scale or "medium", goal=goal, module=module)
        res = maybe_run_independent_vlm_judge(
            image,
            root=root,
            data=data,
            scale_prof=prof,
            goal=goal,
            module=module,
            round_num=1,
        )
        print(json.dumps({k: v for k, v in res.items() if k != "raw_payload"}, ensure_ascii=False, indent=2))
        if res["source"] == "independent_vlm":
            return 0
        if res["source"] == "agent_self_judge":
            print("ℹ️ 未配置 API key，未发起视觉请求。")
            return 0
        return 1

    print(f"未知 action: {action}（可用 status | probe）")
    return 1

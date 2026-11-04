#!/usr/bin/env python3
"""
build_atlas.py: 将 .memory-art/ 记忆库、模块色板、管线规格与项目图片索引编译为
零外部依赖、双击即用的美术记忆图谱与看图工作台 (art-atlas.html)。

默认用相对路径懒加载图片（不嵌 data_uri）；可选 embed 离线导出。
「所有图归总」可见索引含 assets / .cursor/generated / generated / converge；散图归「其他」，不正式 ingest。
"""
from __future__ import annotations

import html
import json
import os
from pathlib import Path
from typing import Any

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>__PROJECT_NAME__ · pmem-art 美术记忆图谱与视觉工作台</title>
<style>
  :root {
    --bg-app: #090d16;
    --bg-panel: #111827;
    --bg-card: #172033;
    --bg-card-hover: #1e293b;
    --border: rgba(148, 163, 184, 0.16);
    --border-strong: rgba(45, 212, 191, 0.45);
    --text-main: #f1f5f9;
    --text-muted: #94a3b8;
    --text-dim: #64748b;
    --teal: #2dd4bf;
    --teal-bg: rgba(45, 212, 191, 0.12);
    --gold: #f59e0b;
    --gold-bg: rgba(245, 158, 11, 0.14);
    --danger: #f43f5e;
    --danger-bg: rgba(244, 63, 94, 0.14);
    --purple: #a855f7;
    --purple-bg: rgba(168, 85, 247, 0.14);
    --success: #10b981;
    --success-bg: rgba(16, 185, 129, 0.14);
    --thumb-size: 180px;
    --thumb-gap: 12px;
    --card-body-h: 36px;
    --gallery-cols: 4;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; height: 100%;
    font: 13.5px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: var(--bg-app); color: var(--text-main);
    overflow: hidden;
  }
  /* Checkerboard & Stage Backgrounds for Artists */
  .stage-checker {
    background-color: #1e2430;
    background-image:
      linear-gradient(45deg, #2a3242 25%, transparent 25%),
      linear-gradient(-45deg, #2a3242 25%, transparent 25%),
      linear-gradient(45deg, transparent 75%, #2a3242 75%),
      linear-gradient(-45deg, transparent 75%, #2a3242 75%);
    background-size: 20px 20px;
    background-position: 0 0, 0 10px, 10px -10px, -10px 0;
  }
  .stage-dark { background: #0b0f19 !important; background-image: none !important; }
  .stage-light { background: #f1f5f9 !important; background-image: none !important; }
  .stage-game {
    background: radial-gradient(circle at 30% 25%, #1e3a4b 0%, #0f172a 70%, #070b14 100%) !important;
  }

  /* Layout */
  .app-shell { display: flex; flex-direction: column; height: 100vh; }
  header.topbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 18px; background: #0d1322; border-bottom: 1px solid var(--border);
    gap: 16px; flex-shrink: 0;
  }
  .brand-area { display: flex; align-items: center; gap: 12px; }
  .brand-logo {
    width: 34px; height: 34px; border-radius: 9px;
    background: linear-gradient(135deg, #0f172a 0%, #1e3a4b 50%, #2dd4bf 100%);
    border: 1.5px solid var(--gold);
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; color: var(--gold); font-size: 15px;
    box-shadow: 0 0 16px rgba(45, 212, 191, 0.22);
  }
  .brand-title h1 { margin: 0; font-size: 15.5px; font-weight: 700; letter-spacing: 0.2px; }
  .brand-title p { margin: 0; font-size: 11.5px; color: var(--text-muted); }

  /* KPI 顶栏已去掉：与下方 Tab 重复，改为「⋯ 更多」里的概况行 */

  .toolbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 18px; background: var(--bg-panel); border-bottom: 1px solid var(--border);
    gap: 12px; flex-wrap: wrap; flex-shrink: 0;
  }
  .nav-tabs { display: flex; gap: 6px; flex-wrap: wrap; }
  .tab-btn {
    background: transparent; color: var(--text-muted);
    border: 1px solid transparent; padding: 6px 13px; border-radius: 7px;
    cursor: pointer; font-size: 13px; font-weight: 600;
    display: flex; align-items: center; gap: 6px; transition: all 0.15s;
  }
  .tab-btn:hover { color: var(--text-main); background: rgba(255,255,255,0.04); }
  .tab-btn.active {
    background: var(--teal-bg); color: var(--teal);
    border-color: var(--border-strong);
  }
  .tab-btn .count-badge {
    font-size: 11px; padding: 1px 6px; border-radius: 99px;
    background: rgba(255,255,255,0.08); color: var(--text-main);
  }

  .stage-controls { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
  .search-box {
    background: #090d16; border: 1px solid var(--border); color: var(--text-main);
    padding: 5px 11px; border-radius: 6px; width: 210px; font-size: 12.5px;
  }
  .search-box:focus { outline: none; border-color: var(--teal); }
  .ctrl-group {
    display: flex; align-items: center; gap: 4px;
    background: #090d16; padding: 3px; border-radius: 7px; border: 1px solid var(--border);
  }
  .ctrl-btn {
    background: transparent; border: none; color: var(--text-muted);
    padding: 4px 8px; border-radius: 5px; font-size: 11.5px; cursor: pointer;
  }
  .ctrl-btn.active { background: var(--bg-card-hover); color: var(--teal); font-weight: 600; }

  /* Workspace 3-Column Body */
  .workspace { display: flex; flex: 1; min-height: 0; overflow: hidden; }
  aside.sidebar {
    width: 270px; background: var(--bg-panel); border-right: 1px solid var(--border);
    display: flex; flex-direction: column; overflow-y: auto; flex-shrink: 0;
    padding: 12px 10px;
  }
  .side-section-title {
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px;
    color: var(--text-dim); padding: 8px 8px 4px;
  }
  .mod-item {
    padding: 8px 10px; border-radius: 8px; cursor: pointer;
    display: flex; flex-direction: column; gap: 3px; margin-bottom: 3px;
    border: 1px solid transparent; transition: all 0.14s;
  }
  .mod-item:hover { background: rgba(255,255,255,0.03); }
  .mod-item.active {
    background: var(--bg-card); border-color: var(--border-strong);
  }
  .mod-item.child { margin-left: 16px; border-left: 2px solid rgba(45, 212, 191, 0.25); padding-left: 10px; }
  .mod-row1 { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
  .mod-id { font-weight: 600; font-size: 12.5px; color: var(--text-main); font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
  .mod-badges { display: flex; gap: 4px; align-items: center; }
  .mini-pill { font-size: 10.5px; padding: 1px 6px; border-radius: 99px; background: rgba(255,255,255,0.07); color: var(--text-muted); }
  .mini-pill.redline { background: var(--danger-bg); color: #fda4af; }
  .mini-pill.warn { background: var(--gold-bg); color: #fcd34d; }
  .mod-title { font-size: 11.5px; color: var(--text-muted); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

  /* Center Main Stage */
  main.main-stage {
    flex: 1; overflow-y: auto; padding: 18px 22px; min-width: 0;
    overflow-anchor: none; /* 禁止浏览器在虚拟列表换片时自动抢滚动 */
    overscroll-behavior: contain;
  }

  /* Module Header Banner */
  .mod-banner {
    background: linear-gradient(135deg, rgba(23, 32, 51, 0.95), rgba(15, 23, 42, 0.95));
    border: 1px solid var(--border); border-radius: 12px; padding: 16px 20px;
    margin-bottom: 18px; display: flex; flex-direction: column; gap: 12px;
  }
  .mod-banner-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; flex-wrap: wrap; }
  .mod-banner h2 { margin: 0 0 4px; font-size: 18px; display: flex; align-items: center; gap: 10px; }
  .mod-banner p { margin: 0; color: var(--text-muted); font-size: 13px; max-width: 820px; }
  .palette-bar { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
  .swatch-chip {
    display: flex; align-items: center; gap: 7px;
    background: #090d16; border: 1px solid var(--border);
    padding: 4px 10px 4px 5px; border-radius: 7px; cursor: pointer;
    transition: transform 0.12s, border-color 0.12s;
  }
  .swatch-chip:hover { transform: translateY(-1px); border-color: var(--gold); }
  .swatch-box { width: 20px; height: 20px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.22); }
  .swatch-hex { font-family: ui-monospace, monospace; font-size: 11.5px; font-weight: 700; color: var(--text-main); }
  .swatch-name { font-size: 11px; color: var(--text-muted); }

  /* Gallery Grid — virtual window keeps DOM light */
  .gallery-virt { position: relative; overflow-anchor: none; }
  .gallery-spacer { width: 100%; pointer-events: none; flex-shrink: 0; overflow-anchor: none; }
  .gallery-grid {
    display: grid;
    /* 列数由 JS 与虚拟滚动共用，禁止 auto-fill 另算一列导致滚轮乱跳 */
    grid-template-columns: repeat(var(--gallery-cols), minmax(0, 1fr));
    gap: var(--thumb-gap);
    overflow-anchor: none;
  }
  .asset-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 11px; overflow: hidden; display: flex; flex-direction: column;
    /* 锁死高度，与 galleryMetrics.rowH 对齐，避免滚动时垫片估算漂移 */
    height: calc(var(--thumb-size) * 0.78 + var(--card-body-h));
    max-height: calc(var(--thumb-size) * 0.78 + var(--card-body-h));
    overflow-anchor: none;
  }
  .asset-card:hover {
    border-color: var(--border-strong);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.28);
  }
  .asset-card.role-rejected { border-color: rgba(244, 63, 94, 0.45); }
  .asset-card.qa-fail { border-color: var(--gold); }
  body.compact-thumbs .asset-name { display: none; }
  body.compact-thumbs .gallery-grid { gap: 8px; }
  .thumb-zoom-group {
    display: flex; align-items: center; gap: 6px;
    background: #090d16; border: 1px solid var(--border); border-radius: 8px;
    padding: 3px 8px;
  }
  .thumb-zoom-group input[type=range] { width: 110px; accent-color: var(--teal); }
  .thumb-zoom-group .zoom-btn {
    background: transparent; border: 1px solid var(--border); color: var(--text-muted);
    width: 24px; height: 24px; border-radius: 6px; cursor: pointer; font-size: 14px; line-height: 1;
  }
  .thumb-zoom-group .zoom-btn:hover { color: var(--teal); border-color: var(--border-strong); }
  .thumb-zoom-label { font-size: 11px; color: var(--text-muted); min-width: 42px; text-align: center; font-variant-numeric: tabular-nums; }
  .thumb-wrap {
    position: relative; height: calc(var(--thumb-size) * 0.78);
    flex: 0 0 calc(var(--thumb-size) * 0.78);
    display: flex; align-items: center; justify-content: center;
    overflow: hidden; cursor: zoom-in; padding: 8px;
    background: #0b101d;
  }
  .thumb-wrap img {
    max-width: 100%; max-height: 100%; object-fit: contain;
  }

  /* 9-Slice & Safe Margin SVG Overlay on Thumbnails & Lightbox */
  .overlay-9slice {
    position: absolute; inset: 10px; pointer-events: none;
    border: 1px dashed rgba(45, 212, 191, 0.75);
    display: none;
  }
  .show-guides .overlay-9slice { display: block; }
  .slice-line { position: absolute; background: rgba(244, 63, 94, 0.75); }
  .slice-line.v1 { top: 0; bottom: 0; left: 12%; width: 1px; border-left: 1px dashed #f43f5e; background: none; }
  .slice-line.v2 { top: 0; bottom: 0; right: 12%; width: 1px; border-right: 1px dashed #f43f5e; background: none; }
  .slice-line.h1 { left: 0; right: 0; top: 12%; height: 1px; border-top: 1px dashed #f43f5e; background: none; }
  .slice-line.h2 { left: 0; right: 0; bottom: 12%; height: 1px; border-bottom: 1px dashed #f43f5e; background: none; }

  .role-tag {
    position: absolute; top: 8px; left: 8px;
    padding: 2px 8px; border-radius: 5px; font-size: 11px; font-weight: 700;
  }
  .role-tag.anchor, .role-tag.approved { background: #10b981; color: #fff; }
  .role-tag.rejected { background: #f43f5e; color: #fff; }
  .role-tag.draft_violation { background: #f59e0b; color: #090d16; }

  .spec-tag {
    position: absolute; bottom: 8px; right: 8px;
    background: rgba(9, 13, 22, 0.82); border: 1px solid var(--border);
    padding: 2px 7px; border-radius: 4px; font-size: 10.5px; font-family: ui-monospace, monospace;
    color: var(--text-muted);
  }
  .asset-body {
    height: var(--card-body-h); min-height: var(--card-body-h); max-height: var(--card-body-h);
    padding: 6px 8px; box-sizing: border-box;
    display: flex; flex-direction: column; gap: 0; overflow: hidden; flex-shrink: 0;
  }
  .asset-chips {
    display: flex; align-items: center; gap: 6px; min-width: 0;
  }
  .role-chip {
    flex-shrink: 0; padding: 1px 7px; border-radius: 4px;
    font-size: 10px; font-weight: 700; line-height: 1.5; color: #fff;
    background: #10b981;
  }
  .role-chip.rejected { background: #f43f5e; }
  .role-chip.draft_violation { background: #f59e0b; color: #090d16; }
  .role-chip.draft { background: #475569; color: #e2e8f0; }
  .cat-chip {
    flex-shrink: 0; padding: 1px 6px; border-radius: 4px;
    font-size: 10px; font-weight: 600;
    background: rgba(255,255,255,0.08); color: var(--text-muted);
  }
  .asset-name {
    flex: 1; min-width: 0; font-size: 11px; color: var(--text-dim);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .btn-folder {
    flex-shrink: 0; width: 26px; height: 22px; padding: 0;
    background: transparent; border: 1px solid var(--border); color: var(--text-muted);
    border-radius: 6px; cursor: pointer; font-size: 12px; line-height: 1;
  }
  .btn-folder:hover { color: var(--teal); border-color: var(--border-strong); }
  .asset-path { font-family: ui-monospace, monospace; font-size: 11.5px; color: var(--teal); word-break: break-all; }
  .asset-caption { font-size: 12.5px; color: var(--text-main); line-height: 1.45; }
  .asset-meta-row {
    margin-top: auto; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.06);
    display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: var(--text-dim);
  }

  /* Redline Do vs Don't Compare Cards */
  .compare-card {
    background: var(--bg-card); border: 1px solid rgba(244, 63, 94, 0.35);
    border-radius: 12px; padding: 18px; margin-bottom: 18px;
  }
  .compare-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 12px; }
  .compare-title { font-size: 15px; font-weight: 700; color: #fda4af; display: flex; align-items: center; gap: 8px; }
  .compare-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 12px; }
  @media (max-width: 900px) { .compare-grid { grid-template-columns: 1fr; } }
  .compare-box {
    border-radius: 9px; overflow: hidden; border: 1px solid var(--border);
    background: #0b101d; display: flex; flex-direction: column;
  }
  .compare-box.do-box { border-color: rgba(16, 185, 129, 0.5); }
  .compare-box.dont-box { border-color: rgba(244, 63, 94, 0.55); }
  .compare-box-head {
    padding: 7px 12px; font-weight: 700; font-size: 12px;
    display: flex; justify-content: space-between;
  }
  .do-box .compare-box-head { background: var(--success-bg); color: #6ee7b7; }
  .dont-box .compare-box-head { background: var(--danger-bg); color: #fda4af; }
  .compare-img-wrap {
    height: 270px; display: flex; align-items: center; justify-content: center;
    padding: 12px; cursor: zoom-in; position: relative;
  }
  .compare-img-wrap img { max-width: 100%; max-height: 100%; object-fit: contain; }
  .compare-caption { padding: 9px 12px; font-size: 12px; color: var(--text-muted); border-top: 1px solid var(--border); }

  /* Interactive A/B Slider Widget */
  .ab-slider-container {
    position: relative; width: 100%; height: 320px; overflow: hidden;
    border-radius: 9px; border: 1px solid var(--border); user-select: none;
    margin-top: 12px;
  }
  .ab-layer {
    position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  }
  .ab-layer img { max-width: 92%; max-height: 92%; object-fit: contain; pointer-events: none; }
  .ab-before { clip-path: inset(0 50% 0 0); }
  .ab-handle {
    position: absolute; top: 0; bottom: 0; left: 50%; width: 3px;
    background: var(--gold); cursor: ew-resize; z-index: 5;
  }
  .ab-handle::after {
    content: "⇄ 拖动对比";
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
    background: var(--gold); color: #090d16; font-weight: 800; font-size: 11px;
    padding: 3px 8px; border-radius: 99px; white-space: nowrap;
    box-shadow: 0 2px 10px rgba(0,0,0,0.5);
  }

  /* AI Recipe & Prompt Studio */
  .recipe-card {
    background: var(--bg-card); border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: 12px; padding: 18px; margin-bottom: 16px;
  }
  .code-block {
    background: #080c14; border: 1px solid var(--border); border-radius: 8px;
    padding: 10px 12px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 12px; color: #e2e8f0; white-space: pre-wrap; word-break: break-word;
    margin: 6px 0 12px; position: relative;
  }
  .btn-copy {
    background: var(--teal-bg); color: var(--teal); border: 1px solid var(--border-strong);
    padding: 4px 10px; border-radius: 6px; font-size: 11.5px; font-weight: 600;
    cursor: pointer; transition: all 0.15s;
  }
  .btn-copy:hover { background: var(--teal); color: #090d16; }

  /* Memory Entries & Evolution Graph */
  .entry-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 10px; padding: 14px 16px; margin-bottom: 12px;
  }
  .entry-card.stale { border-color: var(--gold); background: linear-gradient(90deg, rgba(245, 158, 11, 0.08), var(--bg-card)); }
  .badge {
    display: inline-block; padding: 2px 8px; border-radius: 5px; font-size: 11px; font-weight: 700;
  }
  .badge.danger { background: var(--danger-bg); color: #fda4af; border: 1px solid rgba(244,63,94,0.35); }
  .badge.warning { background: var(--gold-bg); color: #fcd34d; border: 1px solid rgba(245,158,11,0.35); }
  .badge.purple { background: var(--purple-bg); color: #d8b4fe; border: 1px solid rgba(168,85,247,0.35); }
  .badge.teal { background: var(--teal-bg); color: var(--teal); border: 1px solid var(--border-strong); }
  .badge.gold { background: var(--gold-bg); color: var(--gold); border: 1px solid rgba(245,158,11,0.45); }
  .badge.success { background: var(--success-bg); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.35); }
  .badge.info { background: rgba(56, 189, 248, 0.15); color: #7dd3fc; border: 1px solid rgba(56,189,248,0.35); }

  /* 半透明叠层预览：点图放大，点空白关闭（不跳二级页） */
  .img-viewer {
    display: none; position: fixed; inset: 0; z-index: 580; /* 高于教学 520 / 详情 570，详情里点放大仍能盖住 */
    background: rgba(0, 0, 0, 0.72); backdrop-filter: blur(8px);
    align-items: center; justify-content: center; cursor: zoom-out;
    padding: 16px 56px;
  }
  .img-viewer.open { display: flex; }
  .img-viewer-card {
    position: relative; max-width: min(94vw, 1480px); max-height: 94vh;
    display: flex; flex-direction: column; align-items: center; gap: 10px;
    cursor: default;
  }
  .iv-stage {
    display: flex; gap: 12px; align-items: stretch; justify-content: center;
    max-width: 94vw; max-height: calc(94vh - 120px);
  }
  .iv-pane {
    position: relative; display: flex; flex-direction: column; align-items: center; gap: 6px;
    min-width: 0;
  }
  .iv-pane img {
    max-width: min(46vw, 720px); max-height: calc(94vh - 160px);
    object-fit: contain; border-radius: 10px;
    box-shadow: 0 24px 64px rgba(0,0,0,0.55);
    background: #0b101d;
  }
  .img-viewer:not(.compare-on) .iv-pane.main img {
    max-width: min(92vw, 1200px);
  }
  .img-viewer:not(.compare-on) .iv-pane.ref { display: none; }
  .iv-pane-label {
    font-size: 11px; color: var(--text-muted); letter-spacing: 0.04em;
  }
  .iv-nav {
    position: absolute; top: 50%; transform: translateY(-50%);
    width: 44px; height: 72px; border-radius: 12px; border: 1px solid var(--border);
    background: rgba(17,24,39,0.88); color: var(--text-main); font-size: 28px;
    cursor: pointer; z-index: 5; display: flex; align-items: center; justify-content: center;
  }
  .iv-nav:hover { border-color: var(--teal); color: var(--teal); }
  .iv-nav.prev { left: 10px; }
  .iv-nav.next { right: 10px; }
  .iv-nav:disabled { opacity: 0.25; cursor: default; }
  .img-viewer-bar {
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    background: rgba(17, 24, 39, 0.92); border: 1px solid var(--border);
    border-radius: 999px; padding: 6px 10px; max-width: 94vw;
  }
  .img-viewer-bar .iv-path {
    font-family: ui-monospace, monospace; font-size: 11.5px; color: var(--teal);
    max-width: 28vw; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .img-viewer-bar .btn-copy:disabled,
  .img-viewer-bar .btn-copy.disabled {
    opacity: 0.35; cursor: not-allowed; filter: grayscale(0.4);
  }
  .iv-evolve {
    display: none; width: min(94vw, 1480px); max-height: 42vh; overflow: auto;
    background: rgba(9,13,22,0.94); border: 1px solid var(--border); border-radius: 12px;
    padding: 12px; text-align: left;
  }
  .img-viewer.evolve-on .iv-evolve { display: block; }
  .img-viewer.evolve-on .iv-stage { max-height: calc(52vh - 40px); }
  .img-viewer.evolve-on .iv-pane img { max-height: calc(52vh - 80px); }
  .img-viewer.meta-on .iv-stage { max-height: calc(94vh - 280px); }
  .img-viewer.meta-on:not(.evolve-on) .iv-pane img { max-height: calc(94vh - 300px); }
  .img-viewer.meta-on.evolve-on .iv-stage { max-height: calc(42vh - 20px); }
  .img-viewer.meta-on.evolve-on .iv-pane img { max-height: calc(42vh - 60px); }
  .iv-meta {
    display: none; width: min(94vw, 720px); max-height: 18vh; overflow: auto;
    text-align: left; background: rgba(9,13,22,0.94);
    border: 1px solid var(--border); border-radius: 12px; padding: 8px 12px;
  }
  .img-viewer.meta-on .iv-meta { display: block; }
  .iv-meta-head {
    display: flex; flex-wrap: wrap; gap: 8px; align-items: baseline;
    margin-bottom: 4px; color: var(--text-muted); font-size: 12px;
  }
  .iv-meta-score {
    font-size: 14px; color: var(--gold); font-family: ui-monospace, monospace; font-weight: 700;
  }
  .iv-meta-dims { display: flex; flex-wrap: wrap; gap: 4px; margin: 4px 0 2px; }
  .iv-meta-dim {
    font-size: 10.5px; padding: 1px 6px; border-radius: 4px;
    background: rgba(255,255,255,0.06); color: #cbd5e1;
    font-family: ui-monospace, monospace;
  }
  .iv-meta-navhint { margin-top: 6px; font-size: 11px; color: var(--text-dim); }
  .evolve-head {
    display: flex; justify-content: space-between; gap: 8px; align-items: center;
    margin-bottom: 10px; color: var(--text-muted); font-size: 12px;
  }
  .evolve-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px;
  }
  .evolve-card {
    background: #111827; border: 1px solid var(--border); border-radius: 10px; padding: 8px;
  }
  .evolve-card.current { border-color: var(--border-strong); }
  .evolve-card img {
    width: 100%; height: 140px; object-fit: contain; border-radius: 8px;
    background: #0b101d; cursor: zoom-in;
  }
  .evolve-meta { font-size: 11.5px; color: var(--text-muted); margin-top: 6px; line-height: 1.45; }
  .evolve-prompt {
    margin-top: 6px; max-height: 72px; overflow: auto; white-space: pre-wrap; word-break: break-word;
    font: 11px/1.4 ui-monospace, monospace; color: #cbd5e1;
    background: rgba(0,0,0,0.35); border-radius: 6px; padding: 6px; border: 1px dashed var(--border);
  }
  .evolve-actions { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }

  /* Lightbox 详情（可选，从预览条进） */
  .lightbox {
    position: fixed; inset: 0; background: rgba(5, 8, 15, 0.88);
    backdrop-filter: blur(8px); z-index: 450; display: none;
    align-items: stretch; justify-content: space-between;
  }
  .lightbox.open { display: flex; }
  .lb-stage {
    flex: 1; display: flex; flex-direction: column; position: relative; overflow: hidden;
  }
  .lb-toolbar {
    padding: 10px 18px; background: rgba(17, 24, 39, 0.9); border-bottom: 1px solid var(--border);
    display: flex; justify-content: space-between; align-items: center; z-index: 2;
  }
  .lb-canvas {
    flex: 1; display: flex; align-items: center; justify-content: center;
    overflow: auto; position: relative; padding: 24px;
  }
  .lb-img-box { position: relative; display: inline-block; transition: transform 0.15s ease; }
  .lb-img-box img { max-width: 82vw; max-height: 80vh; display: block; }
  .lb-aside {
    width: 400px; background: var(--bg-panel); border-left: 1px solid var(--border);
    padding: 18px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px;
  }
  .toast {
    position: fixed; bottom: 20px; right: 20px; background: var(--teal); color: #090d16;
    font-weight: 700; padding: 8px 16px; border-radius: 8px; z-index: 200;
    box-shadow: 0 6px 20px rgba(0,0,0,0.4); display: none;
  }

  /* === v0.13 Auto-Refresh Bar, Category Filter Cards & Self-Improve Tab === */
  .live-refresh-bar { display: flex; align-items: center; gap: 8px; background: rgba(15,23,42,0.92); border: 1px solid rgba(45,212,191,0.45); padding: 4px 10px; border-radius: 999px; }
  .live-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--success); box-shadow: 0 0 8px var(--success); animation: livePulse 1.8s infinite ease-in-out; }
  .live-dot.paused { background: var(--gold); box-shadow: none; animation: none; }
  @keyframes livePulse { 0%, 100% { transform: scale(1); opacity: 1; } 50% { transform: scale(1.35); opacity: 0.55; } }
  .live-btn { background: rgba(16,185,129,0.16); border: 1px solid rgba(45,212,191,0.5); color: #6ee7b7; padding: 3px 10px; border-radius: 999px; font-size: 11.5px; font-weight: 700; cursor: pointer; transition: 0.15s; }
  .live-btn.paused { background: rgba(245,158,11,0.16); border-color: rgba(245,158,11,0.5); color: #fcd34d; }
  .live-btn:hover { filter: brightness(1.15); }
  .live-sync-time { font-size: 11px; color: var(--text-muted); font-family: ui-monospace, monospace; }

  .cat-filter-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 8px; }
  .cat-pill-card { background: rgba(9,13,22,0.82); border: 1px solid var(--border); border-radius: 10px; padding: 9px 12px; cursor: pointer; transition: all 0.15s; display: flex; flex-direction: column; gap: 4px; }
  .cat-pill-card:hover { border-color: var(--gold); transform: translateY(-1px); }
  .cat-pill-card.active { border-color: var(--teal); background: rgba(45,212,191,0.13); box-shadow: 0 0 0 1px rgba(45,212,191,0.35); }
  .cat-pill-top { display: flex; align-items: center; justify-content: space-between; font-size: 12.5px; font-weight: 700; color: var(--text-main); }
  .cat-pill-sub { font-size: 11px; color: var(--text-muted); display: flex; gap: 8px; align-items: center; }

  .autopilot-strip { margin-top: 6px; background: linear-gradient(90deg, rgba(45,212,191,0.12), rgba(245,158,11,0.10), rgba(168,85,247,0.12)); border: 1px solid rgba(45,212,191,0.4); border-radius: 10px; padding: 10px 14px; display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
  .autopilot-tags { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; font-size: 12px; }
  .autopilot-chip { background: rgba(9,13,22,0.85); border: 1px solid var(--border); padding: 3px 9px; border-radius: 999px; font-size: 11px; color: var(--text-main); }

  .asset-desc-box { margin-top: 4px; padding: 7px 9px; background: rgba(9,13,22,0.75); border-left: 3px solid var(--teal); border-radius: 6px; font-size: 12px; color: var(--text-main); line-height: 1.5; }
  .asset-desc-box.rejected { border-left-color: var(--danger); background: rgba(244,63,94,0.09); }
  .asset-prompt-line { margin-top: 4px; font-size: 11px; color: var(--text-muted); font-family: ui-monospace, monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; background: rgba(9,13,22,0.78); padding: 4px 8px; border-radius: 5px; border: 1px dashed var(--border); cursor: pointer; }
  .asset-prompt-line:hover { border-color: var(--teal); color: var(--teal); }
  .cat-top-badge { position: absolute; top: 8px; right: 8px; padding: 2px 8px; border-radius: 5px; font-size: 11px; font-weight: 700; background: rgba(9,13,22,0.86); color: var(--teal); border: 1px solid rgba(45,212,191,0.4); backdrop-filter: blur(6px); }

  .improve-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; margin-bottom: 18px; }
  .improve-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 16px; }
  .improve-card h3 { margin: 0 0 10px; font-size: 14.5px; font-weight: 700; display: flex; align-items: center; justify-content: space-between; color: var(--gold); }
  .taste-pill-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 5px; }
  .taste-pill { padding: 3px 9px; border-radius: 999px; font-size: 11.5px; background: var(--teal-bg); border: 1px solid var(--border-strong); color: var(--teal); }
  .taste-pill.ban { background: var(--danger-bg); border-color: rgba(244,63,94,0.4); color: #fda4af; }
  .score-step-row { display: flex; align-items: center; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
  .score-step { padding: 4px 10px; border-radius: 7px; font-size: 11.5px; font-family: ui-monospace, monospace; background: #090d16; border: 1px solid var(--border); }
  .score-step.pass { border-color: var(--success); background: var(--success-bg); color: #6ee7b7; font-weight: 700; }
  .kcard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; margin-top: 10px; }
  .kcard { background: #090d16; border: 1px solid var(--border); border-radius: 10px; padding: 12px; }
  .kcard-title { font-size: 13px; font-weight: 700; color: var(--teal); margin-bottom: 4px; display: flex; justify-content: space-between; gap: 6px; }
  .more-wrap { position: relative; }
  .more-menu {
    display: none; position: absolute; top: calc(100% + 6px); left: 0; z-index: 40;
    min-width: 220px; background: #0d1322; border: 1px solid var(--border);
    border-radius: 10px; padding: 6px; box-shadow: 0 12px 32px rgba(0,0,0,0.45);
  }
  .more-wrap.open .more-menu { display: block; }
  .more-menu button {
    width: 100%; text-align: left; background: transparent; border: 0; color: var(--text-muted);
    padding: 8px 10px; border-radius: 7px; cursor: pointer; font-size: 12.5px; font-weight: 600;
  }
  .more-menu button:hover, .more-menu button.active { background: var(--teal-bg); color: var(--teal); }
  .more-menu .more-meta {
    margin: 6px 4px 2px; padding: 8px 10px; border-radius: 8px;
    background: rgba(9,13,22,0.85); border: 1px solid var(--border);
    font-size: 11px; color: var(--text-muted); line-height: 1.55;
  }
  .more-menu .more-meta b { color: var(--text-main); }
  .side-nav-item {
    padding: 8px 12px; border-radius: 8px; cursor: pointer; margin: 2px 8px;
    color: var(--text-muted); font-size: 12.5px; font-weight: 600;
  }
  .side-nav-item:hover { background: rgba(255,255,255,0.04); color: var(--text-main); }
  .side-nav-item.active { background: var(--teal-bg); color: var(--teal); border: 1px solid var(--border-strong); }
  .side-nav-item .count { float: right; opacity: 0.75; font-size: 11px; }
  .side-sub {
    margin: 0 8px 4px 18px; padding: 6px 10px; border-radius: 7px; cursor: pointer;
    font-size: 12px; color: var(--text-dim);
  }
  .side-sub:hover { color: var(--text-main); background: rgba(255,255,255,0.03); }
  .side-sub.active { color: var(--teal); background: rgba(45,212,191,0.08); }
  .empty-today {
    padding: 28px 18px; text-align: center; color: var(--text-muted);
    border: 1px dashed var(--border); border-radius: 12px; background: #0b101d;
  }
  .asset-card .thumb-wrap img {
    background: #0b101d;
    width: 100%; height: 100%;
  }
  .lb-path-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
  .src-badge {
    position: absolute; left: 8px; bottom: 8px; z-index: 2;
    font-size: 10px; padding: 2px 6px; border-radius: 99px;
    background: rgba(0,0,0,0.55); color: #e2e8f0; border: 1px solid rgba(255,255,255,0.12);
  }
  .img-ctx-menu {
    display: none; position: fixed; z-index: 9999; min-width: 200px;
    background: #0d1322; border: 1px solid var(--border); border-radius: 10px;
    padding: 6px; box-shadow: 0 16px 40px rgba(0,0,0,0.55);
  }
  .img-ctx-menu.open { display: block; }
  .img-ctx-menu button {
    width: 100%; text-align: left; background: transparent; border: 0;
    color: var(--text-main); padding: 8px 12px; border-radius: 7px;
    cursor: pointer; font-size: 12.5px; font-weight: 600;
  }
  .img-ctx-menu button:hover { background: var(--teal-bg); color: var(--teal); }
  .img-ctx-menu .ctx-sep { height: 1px; background: var(--border); margin: 4px 6px; }
  .img-ctx-menu button.danger { color: #fda4af; }
  .img-ctx-menu button.danger:hover { background: var(--danger-bg); color: #fecdd3; }

  .reveal-banner {
    display: none; align-items: center; gap: 10px; flex-wrap: wrap;
    margin: 0 16px 8px; padding: 8px 12px; border-radius: 10px;
    background: var(--gold-bg); border: 1px solid rgba(245,158,11,0.35); color: #fde68a; font-size: 12px;
  }
  .reveal-banner.show { display: flex; }
  .reveal-banner code { font-size: 11px; color: #fef3c7; }

  .batch-bar {
    display: none; position: sticky; top: 0; z-index: 40;
    align-items: center; gap: 8px; flex-wrap: wrap;
    margin: 0 0 10px; padding: 8px 10px; border-radius: 10px;
    background: rgba(15, 23, 42, 0.96); border: 1px solid var(--border-strong);
    backdrop-filter: blur(8px);
  }
  body.batch-mode .batch-bar { display: flex; }
  .batch-bar .batch-count { color: var(--teal); font-weight: 700; min-width: 72px; }
  .batch-bar .btn-danger {
    background: var(--danger-bg); color: #fda4af; border: 1px solid rgba(244,63,94,0.45);
  }
  .batch-bar .btn-danger:hover { filter: brightness(1.12); }

  .asset-card { position: relative; }
  .asset-check {
    display: none; position: absolute; top: 8px; left: 8px; z-index: 5;
    width: 22px; height: 22px; border-radius: 6px; align-items: center; justify-content: center;
    background: rgba(9,13,22,0.82); border: 1.5px solid rgba(148,163,184,0.55);
    color: transparent; font-size: 13px; font-weight: 800; pointer-events: none;
  }
  body.batch-mode .asset-check { display: flex; }
  .asset-card.selected .asset-check {
    background: var(--teal); border-color: var(--teal); color: #042f2e;
  }
  body.batch-mode .asset-card.selected {
    outline: 2px solid var(--teal); outline-offset: 1px;
  }
  body.batch-mode .asset-card:hover {
    box-shadow: 0 0 0 1px rgba(45,212,191,0.35);
  }
  .ctrl-btn.batch-on { background: var(--danger-bg); color: #fda4af; border-color: rgba(244,63,94,0.45); }

  .prompt-trace { display: flex; flex-direction: column; gap: 10px; }
  .prompt-trace-head {
    font-size: 12px; color: var(--text-muted); display: flex; flex-direction: column; gap: 4px;
  }
  .round-card {
    background: #090d16; border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px;
  }
  .round-card.current { border-color: var(--border-strong); box-shadow: inset 0 0 0 1px rgba(45,212,191,0.2); }
  .round-card .round-top {
    display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;
    margin-bottom: 6px;
  }
  .round-card .round-title { font-weight: 700; color: var(--teal); font-size: 13px; }
  .round-card .round-score { font-family: ui-monospace, monospace; font-size: 12px; color: var(--gold); }
  .round-card .round-meta { font-size: 11.5px; color: var(--text-muted); margin: 4px 0; }
  .round-card .round-prompt {
    margin-top: 6px; max-height: 140px; overflow: auto; white-space: pre-wrap; word-break: break-word;
    font: 11.5px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    background: rgba(15,23,42,0.85); border: 1px dashed var(--border); border-radius: 8px; padding: 8px;
    color: #cbd5e1;
  }
  .round-card .round-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }

  .teach-modal {
    display: none; position: fixed; inset: 0; z-index: 520;
    background: rgba(5,8,15,0.88); backdrop-filter: blur(8px);
    align-items: stretch; justify-content: center; padding: 18px;
  }
  .teach-modal.open { display: flex; }
  .teach-shell {
    width: min(1180px, 98vw); max-height: 94vh; display: flex; flex-direction: column;
    background: #0f172a; border: 1px solid var(--border); border-radius: 14px; overflow: hidden;
    box-shadow: 0 24px 80px rgba(0,0,0,0.45);
  }
  .teach-top {
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
    padding: 12px 16px; border-bottom: 1px solid var(--border); background: #111827;
  }
  .teach-top-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
  .teach-tip {
    margin: 0 16px; padding: 8px 12px; border-radius: 8px;
    background: rgba(45,212,191,0.08); border: 1px solid rgba(45,212,191,0.28);
    color: #99f6e4; font-size: 12px; line-height: 1.5;
  }
  .teach-body { display: flex; flex: 1; min-height: 0; }
  .teach-nav {
    width: 240px; overflow: auto; border-right: 1px solid var(--border); padding: 8px;
    background: #0b1220; flex-shrink: 0;
  }
  .teach-nav-group {
    font-size: 10.5px; letter-spacing: 0.04em; text-transform: uppercase;
    color: var(--text-dim); padding: 10px 10px 4px; font-weight: 700;
  }
  .teach-nav button {
    width: 100%; text-align: left; border: 0; background: transparent; color: var(--text-muted);
    padding: 9px 10px; border-radius: 8px; cursor: pointer; font-size: 12.5px; font-weight: 600;
  }
  .teach-nav button:hover { background: rgba(255,255,255,0.04); color: var(--text-main); }
  .teach-nav button.active { background: var(--teal-bg); color: var(--teal); }
  .teach-nav button .teach-nav-skill {
    font-size: 10.5px; opacity: .75; font-weight: 500; margin-top: 2px;
    font-family: ui-monospace, monospace;
  }
  .teach-main { flex: 1; overflow: auto; padding: 16px 18px 22px; }
  .teach-skill-row {
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 4px;
  }
  .teach-skill { font-family: ui-monospace, monospace; color: var(--teal); font-size: 12.5px; }
  .teach-when { color: var(--text-muted); font-size: 12.5px; margin: 6px 0 12px; }
  .teach-how { margin: 0 0 14px 18px; color: #cbd5e1; }
  .teach-how li { margin: 5px 0; line-height: 1.45; }
  .teach-pipeline {
    display: flex; flex-wrap: wrap; align-items: stretch; gap: 8px; margin-top: 4px;
  }
  .teach-ex {
    background: #090d16; border: 1px solid var(--border); border-radius: 10px; padding: 8px;
    width: min(300px, 100%); flex: 1 1 240px; max-width: 340px;
  }
  .teach-pipeline { align-items: flex-start; }
  .teach-ex.role-ref { border-color: rgba(96,165,250,0.45); }
  .teach-ex.role-process { border-color: rgba(251,191,36,0.4); }
  .teach-ex.role-final { border-color: rgba(52,211,153,0.5); }
  .teach-ex img {
    width: 100%; height: 180px; object-fit: contain; border-radius: 8px; background:
      linear-gradient(45deg,#1a2233 25%,transparent 25%),
      linear-gradient(-45deg,#1a2233 25%,transparent 25%),
      linear-gradient(45deg,transparent 75%,#1a2233 75%),
      linear-gradient(-45deg,transparent 75%,#1a2233 75%);
    background-size: 16px 16px; background-position: 0 0,0 8px,8px -8px,-8px 0;
    background-color: #0b101d;
    cursor: zoom-in;
  }
  .teach-ex .cap {
    font-size: 11.5px; color: var(--text-muted); margin-top: 6px;
    display: flex; align-items: center; gap: 6px; flex-wrap: wrap;
  }
  .teach-ex .teach-score-line {
    margin-top: 6px; font-size: 12px; color: var(--gold);
    font-family: ui-monospace, monospace; font-weight: 700;
  }
  .teach-dims {
    display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px;
  }
  .teach-dim {
    font-size: 10.5px; padding: 1px 6px; border-radius: 4px;
    background: rgba(255,255,255,0.06); color: #cbd5e1;
    font-family: ui-monospace, monospace;
  }
  .teach-ex .teach-prompt {
    margin-top: 6px; max-height: 88px; overflow: auto; white-space: pre-wrap; word-break: break-word;
    font: 11px/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    background: rgba(15,23,42,0.85); border: 1px dashed var(--border); border-radius: 6px; padding: 6px 8px;
    color: #cbd5e1;
  }
  .teach-ex .teach-note { font-size: 11.5px; color: var(--text-muted); margin-top: 4px; line-height: 1.4; }
  .teach-ex .teach-actions { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }

  /* 工作台「详情」：教学同款三级对照（原图→过程→终稿） */
  .detail-modal {
    display: none; position: fixed; inset: 0; z-index: 570;
    background: rgba(5,8,15,0.9); backdrop-filter: blur(8px);
    align-items: stretch; justify-content: center; padding: 18px;
  }
  .detail-modal.open { display: flex; }
  .detail-shell {
    width: min(1240px, 98vw); max-height: 94vh; display: flex; flex-direction: column;
    background: #0f172a; border: 1px solid var(--border); border-radius: 14px; overflow: hidden;
    box-shadow: 0 24px 80px rgba(0,0,0,0.5);
  }
  .detail-top {
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
    padding: 12px 16px; border-bottom: 1px solid var(--border); background: #111827; flex-shrink: 0;
  }
  .detail-top-actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
  .detail-tip {
    margin: 0 16px; padding: 8px 12px; border-radius: 8px; flex-shrink: 0;
    background: rgba(45,212,191,0.08); border: 1px solid rgba(45,212,191,0.28);
    color: #99f6e4; font-size: 12px; line-height: 1.5;
  }
  .detail-main {
    flex: 1; overflow: auto; padding: 16px 18px 22px; min-height: 0;
  }
  .detail-meta-bar {
    display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: baseline;
    margin-bottom: 12px; font-size: 12.5px; color: var(--text-muted);
  }
  .detail-meta-bar code { color: var(--teal); font-size: 12px; }
  .detail-empty {
    color: var(--text-dim); font-size: 13px; padding: 18px;
    border: 1px dashed var(--border); border-radius: 10px;
  }

  .evolve-dims {
    display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px;
  }
  .evolve-dim {
    font-size: 10.5px; padding: 1px 6px; border-radius: 4px;
    background: rgba(255,255,255,0.06); color: #cbd5e1;
    font-family: ui-monospace, monospace;
  }
  .evolve-score-line {
    margin-top: 4px; font-size: 12px; color: var(--gold);
    font-family: ui-monospace, monospace; font-weight: 700;
  }
  .teach-role {
    display: inline-flex; align-items: center; padding: 1px 7px; border-radius: 999px;
    font-size: 10.5px; font-weight: 700; letter-spacing: 0.02em;
  }
  .teach-role.ref, .teach-role.original { background: rgba(59,130,246,0.18); color: #93c5fd; }
  .teach-role.process { background: rgba(245,158,11,0.16); color: #fcd34d; }
  .teach-role.final { background: rgba(16,185,129,0.16); color: #6ee7b7; }
  .teach-ex.role-original { border-color: rgba(96,165,250,0.45); }
  .teach-rounds { display: flex; flex-direction: column; gap: 10px; margin-top: 8px; }
  .teach-round {
    background: #090d16; border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px;
  }
  .teach-round.passed { border-color: rgba(52,211,153,0.45); }
  .teach-round-top {
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: space-between;
    margin-bottom: 6px;
  }
  .teach-round-title { font-weight: 700; color: var(--teal); font-size: 13px; }
  .teach-round-score { font-family: ui-monospace, monospace; color: var(--gold); font-size: 12px; }
  .teach-round-meta { font-size: 12px; color: var(--text-muted); margin: 3px 0; line-height: 1.45; }
  .teach-round-prompt {
    margin-top: 6px; max-height: 120px; overflow: auto; white-space: pre-wrap; word-break: break-word;
    font: 11.5px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    background: rgba(15,23,42,0.85); border: 1px dashed var(--border); border-radius: 8px; padding: 8px;
    color: #cbd5e1;
  }
  .teach-samples { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; margin-top: 8px; }
  .teach-sample {
    background: #090d16; border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px;
  }
  .teach-sample h4 { margin: 0 0 6px; font-size: 12.5px; color: var(--teal); }
  .teach-sample .body {
    font-size: 12px; color: #cbd5e1; white-space: pre-wrap; word-break: break-word; line-height: 1.45;
  }
  .teach-arrow {
    align-self: center; color: var(--text-dim); font-size: 18px; font-weight: 700;
    padding: 0 2px; user-select: none;
  }
  .teach-foot {
    display: flex; flex-wrap: wrap; gap: 8px; align-items: center;
    margin-top: 16px; padding-top: 12px; border-top: 1px dashed var(--border);
  }
  .teach-locked {
    flex: 1 1 280px; font-size: 11.5px; color: var(--gold);
    background: var(--gold-bg); border: 1px solid rgba(245,158,11,0.35);
    border-radius: 8px; padding: 8px 10px;
  }
  .teach-nav-btns { display: flex; gap: 6px; flex-wrap: wrap; }
  @media (max-width: 820px) {
    .teach-body { flex-direction: column; }
    .teach-nav { width: 100%; max-height: 140px; border-right: 0; border-bottom: 1px solid var(--border); }
    .teach-ex { max-width: none; }
    .teach-arrow { display: none; }
  }
</style>
<meta name="pmem-build-id" content="__BUILD_ID__">
</head>
<body>
<div class="app-shell">
  <header class="topbar">
    <div class="brand-area">
      <div class="brand-logo">ART</div>
      <div class="brand-title">
        <h1 id="projName">pmem-art 美术记忆图谱与视觉工作台</h1>
        <p id="projStyle">面向人类美术师与 AI 美术 Agent 的模块视觉锚点、防翻车红线、九宫格/Alpha 质检与生图配方库</p>
      </div>
    </div>
    <div class="live-refresh-bar" id="liveRefreshBar">
      <span class="live-dot" id="liveDot"></span>
      <button class="live-btn" id="btnToggleAutoRefresh" onclick="toggleAutoRefresh()" title="默认开启；每 10 秒检测新图并无感刷新">🔄 自动刷新: 开启 (10s)</button>
      <button class="btn-copy" style="padding:3px 9px;font-size:11px;" onclick="manualRefreshNow()" title="立即重新加载最新数据">⚡ 立即刷新</button>
      <span class="live-sync-time" id="liveSyncTime"></span>
    </div>
  </header>

  <div class="toolbar">
    <div class="nav-tabs" id="navTabs">
      <button class="tab-btn active" data-tab="gallery" title="看项目里今天出的图">🖼️ 所有图归总 <span class="count-badge" id="cntGallery">0</span></button>
      <div class="more-wrap" id="moreWrap">
        <button class="tab-btn" type="button" id="btnMoreTabs" onclick="toggleMoreMenu(event)">⋯ 更多</button>
        <div class="more-menu" id="moreMenu">
          <div class="more-meta" id="moreMeta">概况加载中…</div>
          <button type="button" data-tab="improve">🧠 自我迭代与知识图鉴 <span id="cntImprove">0</span></button>
          <button type="button" data-tab="redlines">🚫 正反例红线 <span id="cntRedlines">0</span></button>
          <button type="button" data-tab="recipes">🧪 生图配方 <span id="cntRecipes">0</span></button>
          <button type="button" data-tab="memories">🧭 视觉记忆 <span id="cntMemories">0</span></button>
          <button type="button" data-tab="qa">🛡️ 管线质检 <span id="cntQa">0</span></button>
        </div>
      </div>
    </div>

    <div class="stage-controls">
      <input type="search" id="searchInput" class="search-box" placeholder="🔍 搜文件名、路径、模块、Prompt…" />
      <div class="more-wrap" id="bgWrap">
        <button class="ctrl-btn" type="button" id="btnBgMenu" onclick="toggleBgMenu(event)" title="画布底色">🏁 底色</button>
        <div class="more-menu" id="bgMenu">
          <button type="button" data-bg="stage-checker" class="active">🏁 棋盘</button>
          <button type="button" data-bg="stage-dark">🌑 深底</button>
          <button type="button" data-bg="stage-light">🌕 浅底</button>
        </div>
      </div>
      <button class="ctrl-btn" id="toggleGuidesBtn" title="九宫格/安全线">📐 辅助线</button>
      <div class="thumb-zoom-group" title="缩略图大小：越小一屏越多（96–360）">
        <button type="button" class="zoom-btn" id="thumbZoomOut" aria-label="缩小">−</button>
        <input type="range" id="thumbSlider" min="96" max="360" value="180" step="4" />
        <button type="button" class="zoom-btn" id="thumbZoomIn" aria-label="放大">＋</button>
        <span class="thumb-zoom-label" id="thumbZoomLabel">180</span>
      </div>
      <button class="ctrl-btn" type="button" id="btnTeach" title="技能介绍与示例图（参考/过程/终稿）">📖 教学</button>
      <button class="ctrl-btn" type="button" id="btnOpenTrash" title="打开工作台垃圾桶（删除的图可找回）">♻️ 垃圾桶</button>
      <button class="ctrl-btn" type="button" id="btnBatchMode" title="进入批量删除：勾选 / Ctrl+A / Shift 片选">🗑️ 批量删除</button>
    </div>
  </div>

  <div class="reveal-banner" id="revealBanner">
    <span>📁 本地服务未连通：删除/文件夹定位会失败。浏览器不能从 file:// 直接启动 Python——请点「重试连通」下载启动脚本并双击运行，或双击项目里的「打开工作台」脚本。</span>
    <code>python pmem_art.py atlas</code>
    <button type="button" class="btn-copy" id="btnRevealRetry" style="padding:3px 9px;font-size:11px;">重试连通</button>
    <button type="button" class="btn-copy" id="btnOpenHttpWorkbench" style="padding:3px 9px;font-size:11px;">用 http 打开</button>
  </div>

  <div class="workspace">
    <aside class="sidebar" id="moduleSidebar"></aside>
    <main class="main-stage" id="mainStage"></main>
  </div>
</div>

<!-- 半透明叠层预览（点图默认进这里；点空白关闭） -->
<div class="img-viewer" id="imgViewer" title="点击空白处关闭">
  <button type="button" class="iv-nav prev" id="ivPrev" title="上一张 (←)">‹</button>
  <div class="img-viewer-card" id="imgViewerCard">
    <div class="iv-stage" id="ivStage">
      <div class="iv-pane main">
        <img id="ivImg" src="" alt="" />
        <div class="iv-pane-label" id="ivMainLabel">当前图</div>
      </div>
      <div class="iv-pane ref" id="ivRefPane">
        <img id="ivRefImg" src="" alt="" />
        <div class="iv-pane-label">参考原图</div>
      </div>
    </div>
    <div class="iv-meta" id="ivMetaPanel"></div>
    <div class="img-viewer-bar">
      <span class="iv-path" id="ivPath"></span>
      <button type="button" class="btn-copy" id="ivPrevBtn" title="上一张">←</button>
      <button type="button" class="btn-copy" id="ivNextBtn" title="下一张">→</button>
      <button type="button" class="btn-copy" id="ivCompare" title="与参考原图并列对比">并列参考图</button>
      <button type="button" class="btn-copy" id="ivReveal" title="在访达中显示并选中">📁 文件夹</button>
      <button type="button" class="btn-copy" id="ivCopy" title="复制绝对路径">📋 路径</button>
      <button type="button" class="btn-copy" id="ivSave" title="另存为">💾</button>
      <button type="button" class="btn-copy" id="ivDetail" title="教学同款：原图→过程→终稿（含提示词/六维/设终稿）" style="background:var(--teal-bg);color:var(--teal);border-color:rgba(45,212,191,0.45);">详情 · 进化对照</button>
      <button type="button" class="btn-copy" id="ivClose" style="background:var(--danger-bg);color:#fda4af;border-color:rgba(244,63,94,0.4);">✕</button>
    </div>
  </div>
  <button type="button" class="iv-nav next" id="ivNext" title="下一张 (→)">›</button>
</div>

<!-- Lightbox 详情（可选） -->
<div class="lightbox" id="lightbox">
  <div class="lb-stage">
    <div class="lb-toolbar">
      <div style="display:flex;align-items:center;gap:12px;">
        <strong id="lbTitle" style="font-family:monospace;color:var(--teal);"></strong>
        <span id="lbSpecBadge" class="badge teal"></span>
      </div>
      <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
        <button class="btn-copy" id="lbCopyPath" title="复制绝对路径">📋 路径</button>
        <button class="btn-copy" id="lbRevealFolder" title="在访达/资源管理器中显示并选中该图">📁 文件夹</button>
        <button class="btn-copy" id="lbOpenEditor" title="在 Cursor/编辑器打开">📂 编辑器</button>
        <button class="btn-copy" id="lbZoomIn">＋</button>
        <button class="btn-copy" id="lbZoomOut">－</button>
        <button class="btn-copy" id="lbZoomReset">1:1</button>
        <button class="btn-copy" style="background:var(--danger-bg);color:#fda4af;border-color:rgba(244,63,94,0.4);" id="lbClose">✕</button>
      </div>
    </div>
    <div class="lb-canvas stage-checker" id="lbCanvas">
      <div class="lb-img-box" id="lbImgBox">
        <img id="lbImg" src="" alt="" />
        <div class="overlay-9slice" id="lbOverlay9Slice" style="inset:0;">
          <div class="slice-line v1"></div><div class="slice-line v2"></div>
          <div class="slice-line h1"></div><div class="slice-line h2"></div>
        </div>
      </div>
    </div>
  </div>
  <aside class="lb-aside" id="lbAside"></aside>
</div>

<div class="toast" id="toast">已复制到剪贴板</div>

<!-- 工作台详情：教学同款三级对照（原图→过程→终稿） -->
<div class="detail-modal" id="detailModal" title="点击空白关闭">
  <div class="detail-shell" id="detailShell">
    <div class="detail-top">
      <div>
        <strong style="font-size:15px;">🧾 详情 · 进化对照</strong>
        <span style="margin-left:8px;color:var(--text-dim);font-size:12px;">原图 → 过程 → 终稿 · 每张图下挂 Prompt / 六维 / 不足</span>
      </div>
      <div class="detail-top-actions">
        <button type="button" class="btn-copy" id="detailTech" title="打开旧版技术侧栏（路径/记忆/色卡）">技术信息</button>
        <button type="button" class="btn-copy" id="detailClose">✕</button>
      </div>
    </div>
    <div class="detail-tip">放大只负责看大图；完整进化过程在这里看（与教学同一套版式）。过程图可「设置为最终交稿」。</div>
    <main class="detail-main" id="detailMain"></main>
  </div>
</div>

<!-- 教学：技能介绍 + 写死示例图（不可工作台删除） -->
<div class="teach-modal" id="teachModal" title="点击空白关闭">
  <div class="teach-shell" id="teachShell">
    <div class="teach-top">
      <div>
        <strong style="font-size:15px;">📖 技能教学</strong>
        <span style="margin-left:8px;color:var(--text-dim);font-size:12px;">给美术看的：什么时候用哪条技能 · 参考→过程→终稿</span>
      </div>
      <div class="teach-top-actions">
        <button type="button" class="btn-copy" id="teachOpenFolder" title="在资源管理器打开教学素材文件夹">📁 打开教学文件夹</button>
        <button type="button" class="btn-copy" id="teachClose">✕</button>
      </div>
    </div>
    <div class="teach-tip">对话框输入左侧技能名（如 <code>/pmem-draw</code>）就会走对应流程。主画廊默认只看定稿；点图放大后点「详情 · 进化对照」看完整过程。教学图不进画廊、也不能被工作台删掉。</div>
    <div class="teach-body">
      <aside class="teach-nav" id="teachNav"></aside>
      <main class="teach-main" id="teachMain"></main>
    </div>
  </div>
</div>

<!-- 图片右键菜单：复制 / 另存为 / 跳文件夹 / 编辑器 -->
<div class="img-ctx-menu" id="imgCtxMenu" role="menu">
  <button type="button" data-act="copy-abs">📋 复制绝对路径</button>
  <button type="button" data-act="copy-rel">📋 复制相对路径</button>
  <button type="button" data-act="copy-name">📋 复制文件名</button>
  <div class="ctx-sep"></div>
  <button type="button" data-act="save-as">💾 另存为…</button>
  <button type="button" data-act="reveal">📁 在文件夹中显示</button>
  <button type="button" data-act="copy-folder">📋 复制文件夹路径</button>
  <button type="button" data-act="editor">📂 在编辑器打开</button>
  <div class="ctx-sep"></div>
  <button type="button" data-act="viewer">🔍 放大查看</button>
  <button type="button" data-act="lightbox">🧾 详情 · 进化对照</button>
  <div class="ctx-sep"></div>
  <button type="button" class="danger" data-act="delete">🗑️ 删除此图</button>
  <button type="button" data-act="batch">☑️ 进入批量删除</button>
</div>

<script>
let DATA = __ATLAS_JSON__;

/** 垃圾桶清单里的原路径：刷新时从画廊索引剔除，避免「删了又回来」 */
function trashOriginalSet(manifest) {
  const out = new Set();
  const items = (manifest && Array.isArray(manifest.items)) ? manifest.items : [];
  items.forEach(it => {
    const p = String((it && it.original) || "").replace(/\\/g, "/").replace(/^\/+/, "");
    if (p) out.add(p);
  });
  return out;
}

function stripTrashedAssetsFromData(data, banned) {
  if (!data || !banned || !banned.size) return 0;
  let n = 0;
  const assets = data.assets || {};
  Object.keys(assets).forEach(k => {
    const kn = String(k).replace(/\\/g, "/");
    const pk = String((assets[k] && assets[k].path) || "").replace(/\\/g, "/");
    if (banned.has(kn) || banned.has(pk)) {
      delete assets[k];
      n += 1;
    }
  });
  if (Array.isArray(data.index_images)) {
    const before = data.index_images.length;
    data.index_images = data.index_images.filter(x => {
      const p = String((x && x.path) || "").replace(/\\/g, "/");
      return !banned.has(p);
    });
    n += Math.max(0, before - data.index_images.length);
  }
  return n;
}

async function syncTrashFilterIntoData(data) {
  try {
    const res = await fetch(".memory-art/_trash/manifest.json?_t=" + Date.now(), { cache: "no-store" });
    if (!res.ok) return 0;
    const man = await res.json().catch(() => null);
    return stripTrashedAssetsFromData(data, trashOriginalSet(man));
  } catch (e) {
    return 0;
  }
}

const THUMB_MIN = 96;
const THUMB_MAX = 360;
const THUMB_DEFAULT = 180;
const MAX_DECODE = 32;          // 视口内并发解码上限（过小会滑动后空白半晌）
const VIRT_ROW_BUFFER = 8;      // 上下多挂几行，滑动少重建
const AUTO_REFRESH_MS = 10000;
const ATLAS_STATE_KEY = "pmem_atlas_state_v18";

let state = {
  module: "ALL",
  tab: "gallery",
  categoryFilter: "ALL",
  dayFilter: "today",
  plateFilter: "final",
  sideMode: "all",
  selectedLibrary: "CURRENT",
  search: "",
  bgClass: "stage-checker",
  showGuides: false,
  autoRefresh: true,
  modulesOpen: false,
  lbScale: 1.0,
  lbPath: "",
  thumbSize: THUMB_DEFAULT,
  batchMode: false
};

let _galleryAssets = [];
let _virtScrollBound = false;
let _virtRaf = 0;
let _virtRangeKey = "";
let _imgIo = null;
let _decodeBusy = 0;
let _decodeQueue = [];
let _searchTimer = 0;
let _selectedPaths = new Set();
let _lastClickedIdx = -1;
let _hoveredPath = "";
let _revealOk = null;

function assetSrc(a) {
  if (!a) return "";
  if (a.data_uri) return a.data_uri;
  return String(a.path || "").replace(/\\/g, "/");
}

/** 画廊用小图（有 thumb 缓存就用）；点开放大仍走 assetSrc 原图 */
function thumbSrc(a) {
  if (!a) return "";
  if (a.thumb) return String(a.thumb).replace(/\\/g, "/");
  return assetSrc(a);
}

function absAssetPath(rel) {
  const root = String(DATA.root || "").replace(/\\/g, "/").replace(/\/$/, "");
  const p = String(rel || "").replace(/\\/g, "/").replace(/^\/+/, "");
  if (!root) return p;
  return root + "/" + p;
}

function sourceLabel(src) {
  return ({
    module: "定稿/模块",
    cursor_generated: "Cursor",
    generated: "generated",
    converge: "收敛",
    other: "散图"
  })[src] || "图";
}

function getActiveProjectMeta() {
  const ap = DATA.active_project || {};
  const fallbackName = DATA.config?.project?.name || "pmem-art";
  const pid = ap.project_id || "pmem-art";
  return {
    project_id: pid,
    project_name: ap.project_name || fallbackName,
    library_dir: ap.library_dir || (".memory-art/projects/" + pid),
    copied_from_project: ap.copied_from_project || ""
  };
}

function getProjectLibraries() {
  const ap = getActiveProjectMeta();
  if (Array.isArray(DATA.project_libraries) && DATA.project_libraries.length > 0) {
    return DATA.project_libraries;
  }
  return [{
    project_id: ap.project_id,
    project_name: ap.project_name,
    is_current: true,
    library_dir: ap.library_dir,
    entries_count: (DATA.entries || []).length,
    modules_count: Object.keys(DATA.modules || {}).length,
    entries: DATA.entries || [],
    knowledge_cards: DATA.profile?.private_knowledge_cards || [],
    taste: DATA.profile?.taste || {},
    reflections: DATA.profile?.reflections || []
  }];
}

function getSelectedLibraryObj() {
  const libs = getProjectLibraries();
  const cur = libs.find(l => l.is_current) || libs[0];
  if (!state.selectedLibrary || state.selectedLibrary === "CURRENT") return cur;
  return libs.find(l => l.project_id === state.selectedLibrary) || cur;
}

window.selectProjectLibrary = function(projectId) {
  const libs = getProjectLibraries();
  const target = libs.find(l => l.project_id === projectId);
  state.selectedLibrary = (target && !target.is_current) ? target.project_id : "CURRENT";
  saveAtlasState();
  renderStage();
};

function saveAtlasState() {
  try {
    const stage = document.getElementById("mainStage");
    sessionStorage.setItem(ATLAS_STATE_KEY, JSON.stringify({
      module: state.module,
      tab: state.tab,
      categoryFilter: state.categoryFilter,
      dayFilter: state.dayFilter,
      plateFilter: state.plateFilter,
      sideMode: state.sideMode,
      search: state.search,
      bgClass: state.bgClass,
      showGuides: state.showGuides,
      autoRefresh: !!state.autoRefresh,
      modulesOpen: !!state.modulesOpen,
      thumbSize: state.thumbSize,
      scrollTop: stage ? stage.scrollTop : 0
    }));
  } catch (e) {}
}

function restoreAtlasState() {
  try {
    // v16：丢掉旧版「顶栏 KPI + 全量 Tab」状态。
    // 自动刷新：无存档时默认开启；有存档则尊重用户暂停/开启（首次打开必为开）。
    const raw = sessionStorage.getItem(ATLAS_STATE_KEY);
    if (!raw) {
      state.autoRefresh = true;
      return;
    }
    const saved = JSON.parse(raw);
    if (saved && typeof saved === "object") {
      if (saved.module) state.module = saved.module;
      if (saved.tab) state.tab = saved.tab;
      if (saved.categoryFilter) state.categoryFilter = saved.categoryFilter;
      if (saved.dayFilter) state.dayFilter = saved.dayFilter;
      if (saved.plateFilter) state.plateFilter = saved.plateFilter;
      else state.plateFilter = "final";
      if (saved.sideMode) state.sideMode = saved.sideMode;
      if (typeof saved.search === "string") state.search = saved.search;
      if (saved.bgClass) state.bgClass = saved.bgClass;
      if (typeof saved.showGuides === "boolean") state.showGuides = saved.showGuides;
      if (typeof saved.modulesOpen === "boolean") state.modulesOpen = saved.modulesOpen;
      state.autoRefresh = (typeof saved.autoRefresh === "boolean") ? saved.autoRefresh : true;
      if (typeof saved.thumbSize === "number") {
        state.thumbSize = Math.max(THUMB_MIN, Math.min(THUMB_MAX, saved.thumbSize));
      }
      setTimeout(() => {
        const stage = document.getElementById("mainStage");
        if (stage && saved.scrollTop) stage.scrollTop = saved.scrollTop;
      }, 30);
    }
  } catch (e) {
    state.autoRefresh = true;
  }
}

function applyThumbSize(px, { persist = true, refreshVirt = true } = {}) {
  const n = Math.max(THUMB_MIN, Math.min(THUMB_MAX, Math.round(Number(px) || THUMB_DEFAULT)));
  state.thumbSize = n;
  const bodyH = n < 140 ? 32 : 36;
  const gap = n < 140 ? 8 : 12;
  document.documentElement.style.setProperty("--thumb-size", n + "px");
  document.documentElement.style.setProperty("--thumb-gap", gap + "px");
  document.documentElement.style.setProperty("--card-body-h", bodyH + "px");
  document.body.classList.toggle("compact-thumbs", n < 140);
  const slider = document.getElementById("thumbSlider");
  const label = document.getElementById("thumbZoomLabel");
  if (slider && Number(slider.value) !== n) slider.value = String(n);
  if (label) label.textContent = String(n);
  if (persist) saveAtlasState();
  if (refreshVirt && state.tab === "gallery") scheduleVirtualPaint(true);
}

window.toggleMoreMenu = function(ev) {
  if (ev) ev.stopPropagation();
  const bg = document.getElementById("bgWrap");
  if (bg) bg.classList.remove("open");
  document.getElementById("moreWrap").classList.toggle("open");
};
document.addEventListener("click", () => {
  const w = document.getElementById("moreWrap");
  if (w) w.classList.remove("open");
  const bg = document.getElementById("bgWrap");
  if (bg) bg.classList.remove("open");
});

function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.style.display = "block";
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => { t.style.display = "none"; }, 1800);
}

function copyText(text, label) {
  navigator.clipboard?.writeText(text);
  showToast("📋 已复制: " + (label || text.slice(0, 32)));
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s == null ? "" : String(s);
  return d.innerHTML;
}

function getFilteredModules() {
  if (state.module === "ALL") return Object.keys(DATA.modules);
  // Include selected module and its child modules
  return Object.keys(DATA.modules).filter(m => m === state.module || m.startsWith(state.module + "."));
}

function getFilteredEntries() {
  const mods = new Set(getFilteredModules());
  const q = state.search.trim().toLowerCase();
  const selLib = getSelectedLibraryObj();
  const sourceEntries = (selLib && !selLib.is_current) ? (selLib.entries || []) : (DATA.entries || []);
  return sourceEntries.filter(e => {
    const modMatch = state.module === "ALL" || mods.has(e.module) || (e.scope === "project" && state.tab === "memories") || (selLib && !selLib.is_current);
    if (!modMatch) return false;
    if (!q) return true;
    return JSON.stringify(e).toLowerCase().includes(q);
  });
}

function dayCounts() {
  const c = { today: 0, yesterday: 0, earlier: 0, ALL: 0 };
  for (const a of Object.values(DATA.assets || {})) {
    if (isWorkbenchHiddenAsset(a)) continue;
    if (state.plateFilter && state.plateFilter !== "ALL" && assetPlate(a) !== state.plateFilter) continue;
    const b = a.day_bucket || "earlier";
    if (c[b] != null) c[b] += 1;
    c.ALL += 1;
  }
  return c;
}

function assetPlate(a) {
  if (a && a.plate) return a.plate;
  const p = String((a && a.path) || "").replace(/\\/g, "/");
  const name = p.split("/").pop() || "";
  const src = (a && a.source) || "";
  const role = String((a && a.role) || (a && a.png_meta && a.png_meta.pmem_role) || "").toLowerCase();
  if (role === "rejected" || /reject/i.test(name)) return "rejected";
  if (role === "reference") return "reference";
  if (src === "converge" || src === "cursor_generated" || src === "generated" || src === "other") return "process";
  if (p.includes("/boards/") || p.includes("/.memory-art/converge/")) return "process";
  if (/(^|[_-])r\d{1,2}\./i.test(name) || /^r\d{1,2}\./i.test(name)) return "process";
  if (role === "draft" || role === "draft_violation" || /draft/i.test(name)) return "process";
  return "final";
}

function plateCounts() {
  const c = { final: 0, process: 0, rejected: 0, reference: 0, ALL: 0 };
  Object.values(DATA.assets || {}).forEach(a => {
    const k = assetPlate(a);
    c.ALL += 1;
    if (c[k] != null) c[k] += 1;
  });
  return c;
}

function isWorkbenchHiddenAsset(a) {
  if (!a) return true;
  if (a.workbench_hide) return true;
  // 磁盘已删 / 仅记忆残留：不进主画廊（进化对照里会标缺图）
  if (a.exists === false) return true;
  const role = String((a.role) || (a.png_meta && a.png_meta.pmem_role) || "").toLowerCase();
  if (role === "reference") return true;
  const plate = assetPlate(a);
  // 过程图 / 参考原图不单独进主画廊，避免刷屏；进化面板再看
  return plate === "process" || plate === "reference";
}

function getFilteredAssets() {
  const mods = new Set(getFilteredModules());
  const q = state.search.trim().toLowerCase();
  // 兼容旧状态：过程/参考筛选项已移除
  if (state.plateFilter === "process" || state.plateFilter === "reference" || state.plateFilter === "ALL") {
    state.plateFilter = "final";
  }
  let list = Object.values(DATA.assets || {}).filter(a => {
    if (isWorkbenchHiddenAsset(a)) return false;
    if (state.sideMode === "all" || state.module === "ALL") {
      if (state.plateFilter && state.plateFilter !== "ALL") {
        if (assetPlate(a) !== state.plateFilter) return false;
      }
      if (state.dayFilter && state.dayFilter !== "ALL") {
        if ((a.day_bucket || "earlier") !== state.dayFilter) return false;
      }
      if (state.categoryFilter && state.categoryFilter !== "ALL") {
        if ((a.category || "misc") !== state.categoryFilter) return false;
      }
    } else {
      const modMatch = mods.has(a.module);
      if (!modMatch) return false;
    }
    if (!q) return true;
    const blob = [a.path, a.module, a.description, a.prompt, a.source, a.category, assetPlate(a)].join(" ").toLowerCase();
    return blob.includes(q);
  });
  // 防旧数据里同一文件 / 与 \\ 两套键并排出现
  const seen = new Set();
  list = list.filter(a => {
    const n = String((a && a.path) || "").replace(/\\/g, "/");
    if (!n || seen.has(n)) return false;
    seen.add(n);
    return true;
  });
  list.sort((x, y) => (Number(y.mtime) || 0) - (Number(x.mtime) || 0));
  return list;
}

function renderHeaderAndSidebar() {
  const proj = DATA.config?.project || {};
  document.getElementById("projName").textContent = (proj.name || "pmem-art") + " · 美术记忆图谱与视觉工作台";
  document.getElementById("projStyle").textContent = (proj.art_style || "") + " | 引擎: " + (proj.engine || "Unity/UE") + " | 色彩空间: " + (proj.color_space || "sRGB");

  const totalAssets = Object.keys(DATA.assets).length;
  const totalMemories = DATA.entries.length;
  const redlineCount = DATA.entries.filter(e => e.kind === "style_redline").length;
  const qaWarnCount = DATA.qa_issues.length + DATA.stale_entries.length;

  const prof = DATA.profile || {};
  const kCount = (prof.knowledge_cards || []).length;
  const rCount = (prof.reflections || []).length;
  const activeProj = getActiveProjectMeta();
  const projLibs = getProjectLibraries();
  const moreMeta = document.getElementById("moreMeta");
  if (moreMeta) {
    moreMeta.innerHTML = `项目 <b>${esc(activeProj.project_id)}</b>（${projLibs.length} 库）· 图 <b>${totalAssets}</b> · 模块 <b>${Object.keys(DATA.modules).length}</b> · 记忆 <b>${totalMemories}</b> · 红线 <b>${redlineCount}</b> · 质检 <b>${qaWarnCount}</b> · 知识 <b>${kCount}</b>`;
  }
  const syncEl = document.getElementById("liveSyncTime");
  if (syncEl) {
    const bt = (DATA.built_at || "").replace(" UTC+8", "");
    syncEl.textContent = bt ? `同步: ${bt.slice(11)}` : "";
    syncEl.title = `最后构建: ${DATA.built_at || ""} · Build ID: ${DATA.build_id || ""}`;
  }
  updateAutoRefreshUI();

  // Update tab counts
  const fAssets = getFilteredAssets();
  const fEntries = getFilteredEntries();
  document.getElementById("cntGallery").textContent = fAssets.length;
  const cntImp = document.getElementById("cntImprove");
  if (cntImp) cntImp.textContent = kCount + rCount;
  document.getElementById("cntRedlines").textContent = fEntries.filter(e => e.kind === "style_redline" || e.kind === "visual_correction").length;
  document.getElementById("cntRecipes").textContent = fEntries.filter(e => e.kind === "recipe" || e.ai_params).length;
  document.getElementById("cntMemories").textContent = fEntries.length;
  document.getElementById("cntQa").textContent = DATA.qa_issues.length + DATA.stale_entries.length;

  // Render Sidebar — 所有图归总置顶（默认：定稿 + 今天）
  const sb = document.getElementById("moduleSidebar");
  const dc = dayCounts();
  const pc = plateCounts();
  const catSum = DATA.category_summary || {};
  let htmlStr = `
    <div class="side-section-title">看图</div>
    <div class="side-nav-item ${state.sideMode === 'all' ? 'active' : ''}" onclick="selectAllImagesNav()">
      🖼️ 所有图归总 <span class="count">${pc.final}</span>
    </div>
    <div class="side-section-title">状态</div>
    <div class="side-sub ${state.sideMode === 'all' && state.plateFilter === 'final' ? 'active' : ''}" onclick="selectPlateFilter('final')">✅ 定稿 <span class="count">${pc.final}</span></div>
    <div class="side-sub ${state.sideMode === 'all' && state.plateFilter === 'rejected' ? 'active' : ''}" onclick="selectPlateFilter('rejected')">❌ 废案 <span class="count">${pc.rejected}</span></div>
    <div class="side-hint" style="padding:4px 10px 8px;color:var(--text-dim);font-size:11px;line-height:1.4;">过程稿 ${pc.process} · 参考 ${pc.reference} 不单独占画廊；放大后点「详情 · 进化对照」看完整过程</div>
    <div class="side-section-title">时间</div>
    <div class="side-sub ${state.sideMode === 'all' && state.dayFilter === 'today' ? 'active' : ''}" onclick="selectDayFilter('today')">今天 <span class="count">${dc.today}</span></div>
    <div class="side-sub ${state.sideMode === 'all' && state.dayFilter === 'yesterday' ? 'active' : ''}" onclick="selectDayFilter('yesterday')">昨天 <span class="count">${dc.yesterday}</span></div>
    <div class="side-sub ${state.sideMode === 'all' && state.dayFilter === 'earlier' ? 'active' : ''}" onclick="selectDayFilter('earlier')">更早 <span class="count">${dc.earlier}</span></div>
    <div class="side-sub ${state.sideMode === 'all' && state.dayFilter === 'ALL' ? 'active' : ''}" onclick="selectDayFilter('ALL')">全部时间 <span class="count">${dc.ALL}</span></div>
    <div class="side-section-title">类型</div>
    <div class="side-sub ${state.sideMode === 'all' && state.categoryFilter === 'ALL' ? 'active' : ''}" onclick="selectCategoryFilter('ALL')">全部类型</div>
  `;
  const catKeys = Object.keys(catSum).length ? Object.keys(catSum) : Object.keys(DATA.categories || {});
  for (const catKey of catKeys) {
    const catCfg = (DATA.categories || {})[catKey] || catSum[catKey] || {};
    const n = (catSum[catKey] && catSum[catKey].total_assets != null)
      ? catSum[catKey].total_assets
      : Object.values(DATA.assets || {}).filter(a => (a.category || "misc") === catKey).length;
    if (!n && !["brand","character","scene","ui","misc"].includes(catKey)) continue;
    const icon = catCfg.icon || (catSum[catKey] && catSum[catKey].icon) || "📦";
    const short = catCfg.short || (catSum[catKey] && catSum[catKey].short) || catKey;
    htmlStr += `<div class="side-sub ${state.sideMode === 'all' && state.categoryFilter === catKey ? 'active' : ''}" onclick="selectCategoryFilter('${esc(catKey)}')">${icon} ${esc(short)} <span class="count">${n}</span></div>`;
  }

  const modCount = Object.keys(DATA.modules || {}).length;
  htmlStr += `
    <div class="side-section-title" style="cursor:pointer;" onclick="toggleModulesPanel()" title="模块列表不常用，默认收起">
      模块 <span class="count">${modCount}</span> ${state.modulesOpen ? "▾" : "▸"}
    </div>
  `;
  if (state.modulesOpen) {
    for (const [catKey, catCfg] of Object.entries(DATA.categories || {})) {
      const catMods = Object.entries(DATA.modules || {}).filter(([k, v]) => v.category === catKey);
      if (!catMods.length) continue;
      htmlStr += `<div class="side-section-title" style="opacity:0.7;margin-top:4px;">${esc(catCfg.icon || '')} ${esc(catCfg.short || catCfg.label || catKey)}</div>`;
      for (const [modId, modCfg] of catMods) {
        const isChild = modId.split(".").length > 2;
        const mAssets = Object.values(DATA.assets || {}).filter(a => a.module === modId);
        htmlStr += `
          <div class="mod-item ${isChild ? 'child' : ''} ${state.sideMode === 'module' && state.module === modId ? 'active' : ''}" onclick="selectModule('${esc(modId)}')">
            <div class="mod-row1">
              <span class="mod-id">${esc(modId)}</span>
              <span class="mini-pill">${mAssets.length}</span>
            </div>
            <div class="mod-title">${esc(modCfg.title || '')}</div>
          </div>
        `;
      }
    }
  }
  sb.innerHTML = htmlStr;
}

window.toggleModulesPanel = function() {
  state.modulesOpen = !state.modulesOpen;
  saveAtlasState();
  renderHeaderAndSidebar();
};

window.toggleBgMenu = function(ev) {
  if (ev) ev.stopPropagation();
  const wrap = document.getElementById("bgWrap");
  const more = document.getElementById("moreWrap");
  if (more) more.classList.remove("open");
  if (wrap) wrap.classList.toggle("open");
};

window.selectAllImagesNav = function() {
  state.sideMode = "all";
  state.module = "ALL";
  state.dayFilter = "today";
  state.plateFilter = "final";
  state.categoryFilter = "ALL";
  state.tab = "gallery";
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === "gallery"));
  saveAtlasState();
  renderStage();
};

window.selectPlateFilter = function(plateKey) {
  state.sideMode = "all";
  state.module = "ALL";
  state.plateFilter = plateKey;
  state.tab = "gallery";
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === "gallery"));
  saveAtlasState();
  renderStage();
};

window.selectDayFilter = function(dayKey) {
  state.sideMode = "all";
  state.module = "ALL";
  state.dayFilter = dayKey;
  state.tab = "gallery";
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === "gallery"));
  saveAtlasState();
  renderStage();
};

window.selectCategoryFilter = function(catKey) {
  state.sideMode = "all";
  state.module = "ALL";
  state.categoryFilter = catKey;
  if (state.tab !== "gallery") {
    state.tab = "gallery";
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === "gallery"));
  }
  saveAtlasState();
  renderStage();
};

function renderModuleBanner() {
  if (state.sideMode === "all" || state.module === "ALL") {
    const dc = dayCounts();
    const dayLabel = ({ today: "今天", yesterday: "昨天", earlier: "更早", ALL: "全部时间" })[state.dayFilter] || state.dayFilter;
    const plateLabel = ({ final: "定稿", process: "过程稿", reference: "参考", rejected: "废案", ALL: "全部状态" })[state.plateFilter] || state.plateFilter;
    const catLabel = state.categoryFilter === "ALL" ? "全部类型" : (DATA.categories?.[state.categoryFilter]?.short || state.categoryFilter);
    const pc = plateCounts();
    return `
      <div class="mod-banner">
        <div class="mod-banner-top">
          <div>
            <h2>🖼️ 所有图归总 · ${esc(plateLabel)} · ${esc(dayLabel)} · ${esc(catLabel)}
              <span class="badge teal" style="font-size:11px;">默认定稿 · 按时间倒序</span>
            </h2>
            <p>默认只看定稿；过程稿 / 参考图请进放大预览的「显示进化过程 / 并列参考图」。散图归「其他」，只工作台可见，不写 recipe。定稿 ${pc.final} · 过程 ${pc.process} · 今天 ${dc.today}</p>
          </div>
        </div>
      </div>
    `;
  }
  const m = DATA.modules[state.module] || {};
  const specs = m.specs || {};
  const palette = m.palette || [];
  return `
    <div class="mod-banner">
      <div class="mod-banner-top">
        <div>
          <h2>
            <span>${esc(m.title || state.module)}</span>
            <span class="badge teal" style="font-family:monospace;">${esc(state.module)}</span>
            ${m.parent ? `<span class="badge info">继承自 ${esc(m.parent)}</span>` : ''}
          </h2>
          <p>${esc(m.description || '')}</p>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button class="btn-copy" onclick="copyAgentContext('${esc(state.module)}')">🤖 一键复制该模块 AI 记忆上下文</button>
        </div>
      </div>
      <div style="display:flex;gap:10px;flex-wrap:wrap;font-size:12px;color:var(--text-muted);">
        <span>📐 标准分辨率: <b style="color:var(--text-main)">${esc(specs.resolution || '未限')}</b></span>
        <span>🔲 透明通道: <b style="color:var(--text-main)">${specs.alpha_required ? '必须 RGBA (预乘 Alpha)' : '无需透明'}</b></span>
        ${specs.nine_slice ? `<span>💠 九宫格切线: <b style="color:var(--gold)">[${specs.nine_slice.join(', ')}] px</b></span>` : ''}
        ${specs.safe_margin_px ? `<span>🛡️ 边缘安全区: <b style="color:var(--teal)">${specs.safe_margin_px} px</b></span>` : ''}
      </div>
      ${palette.length ? `
        <div class="palette-bar">
          <span style="font-size:11.5px;color:var(--text-muted);margin-right:4px;">模块锁定色卡 (点击复制 HEX):</span>
          ${palette.map(p => `
            <div class="swatch-chip" onclick="copyText('${esc(p.hex)}', '${esc(p.name)} ${esc(p.hex)}')">
              <span class="swatch-box" style="background:${esc(p.hex)}"></span>
              <span class="swatch-hex">${esc(p.hex)}</span>
              <span class="swatch-name">${esc(p.name)}</span>
            </div>
          `).join("")}
        </div>
      ` : ''}
    </div>
  `;
}

function renderGalleryTab() {
  const assets = getFilteredAssets();
  const dc = dayCounts();
  _galleryAssets = assets;
  if (!assets.length) {
    if (state.sideMode === "all" && state.plateFilter === "final" && state.dayFilter === "today") {
      return `<div class="empty-today">
        <div style="font-size:16px;font-weight:700;color:var(--text-main);margin-bottom:6px;">今天还没有定稿</div>
        <div style="margin-bottom:14px;">过程稿与参考原图不单独占画廊；有定稿后放大可看进化过程。也可放宽时间。</div>
        <button class="btn-copy" onclick="selectDayFilter('ALL')">定稿·全部时间</button>
        <button class="btn-copy" onclick="selectPlateFilter('rejected')">看废案</button>
      </div>`;
    }
    return `<div class="entry-card">当前筛选下没有定稿。试试「全部时间」或清掉搜索。过程/参考请在放大后打开进化过程。</div>`;
  }
  return `<div class="gallery-virt" id="galleryVirt" data-count="${assets.length}">
    <div class="batch-bar" id="batchBar">
      <span class="batch-count" id="batchCount">已选 0</span>
      <button type="button" class="btn-copy" id="btnBatchSelectAll">全选当前筛选</button>
      <button type="button" class="btn-copy" id="btnBatchClear">清空勾选</button>
      <button type="button" class="btn-copy btn-danger" id="btnBatchDelete">批量移入垃圾桶</button>
      <button type="button" class="btn-copy" id="btnBatchOpenTrash">打开垃圾桶</button>
      <button type="button" class="btn-copy" id="btnBatchCancel">取消</button>
      <span style="color:var(--text-dim);font-size:11px;">Ctrl+A 全选 · Shift+点击片选 · Delete 移入垃圾桶（可找回）</span>
    </div>
    <div style="font-size:11.5px;color:var(--text-dim);margin:0 0 8px;">共 ${assets.length} 张 · 视口按需渲染 · 缩略图 ${state.thumbSize}px</div>
    <div class="gallery-spacer" id="gallerySpacerTop"></div>
    <div class="gallery-grid" id="galleryGrid"></div>
    <div class="gallery-spacer" id="gallerySpacerBot"></div>
  </div>`;
}

function PathName(p) {
  const s = String(p || "").replace(/\\/g, "/");
  const i = s.lastIndexOf("/");
  return i >= 0 ? s.slice(i + 1) : s;
}

function cardHtml(a) {
  const role = a.role || a.png_meta?.pmem_role || (a.formal ? "approved" : "draft");
  const roleLabels = {
    anchor: "定稿",
    approved: "定稿",
    rejected: "废案",
    draft_violation: "待修",
    draft: "草稿"
  };
  const catShort = a.category_short || a.module || "散图";
  const src = thumbSrc(a);
  const name = PathName(a.path);
  const pathAttr = esc(a.path);
  const selected = _selectedPaths.has(a.path) ? " selected" : "";
  const roundHint = a.converge_round ? ` · R${a.converge_round}` : "";
  return `
    <div class="asset-card role-${esc(role)} ${a.qa_passed === false ? 'qa-fail' : ''}${selected}" data-path="${pathAttr}" title="${pathAttr}${roundHint}">
      <div class="asset-check" aria-hidden="true">✓</div>
      <div class="thumb-wrap ${state.bgClass} ${state.showGuides ? 'show-guides' : ''}">
        <img src="${esc(src)}" alt="" loading="eager" decoding="async" />
        ${state.showGuides ? `<div class="overlay-9slice">
          <div class="slice-line v1"></div><div class="slice-line v2"></div>
          <div class="slice-line h1"></div><div class="slice-line h2"></div>
        </div>` : ""}
      </div>
      <div class="asset-body">
        <div class="asset-chips">
          <span class="role-chip ${esc(role)}">${roleLabels[role] || esc(role)}</span>
          <span class="cat-chip">${esc(catShort)}</span>
          <span class="asset-name" title="${pathAttr}">${esc(name)}</span>
          <button type="button" class="btn-folder" data-act="reveal" title="在文件夹中显示并选中">📁</button>
        </div>
      </div>
    </div>
  `;
}

function galleryMetrics() {
  const stage = document.getElementById("mainStage");
  // 固定用舞台宽度算列（不要用空 grid 的 clientWidth，否则首帧 cols 漂移会扯滚动）
  const width = Math.max(200, stage ? (stage.clientWidth - 44) : 800);
  const gap = state.thumbSize < 140 ? 8 : 12;
  const bodyH = state.thumbSize < 140 ? 32 : 36;
  const cols = Math.max(1, Math.floor((width + gap) / (state.thumbSize + gap)));
  // 必须与 CSS：height = thumb*0.78 + bodyH；行距 = card + gap
  const cardH = Math.round(state.thumbSize * 0.78) + bodyH;
  const rowH = cardH + gap;
  const rows = Math.max(1, Math.ceil((_galleryAssets.length || 0) / cols));
  return { cols, rowH, rows, gap, cardH, bodyH, totalH: rows * rowH };
}

function pumpDecodeQueue() {
  while (_decodeBusy < MAX_DECODE && _decodeQueue.length) {
    const img = _decodeQueue.shift();
    if (!img || !img.isConnected) continue;
    const s = img.getAttribute("data-src");
    if (!s || img.getAttribute("data-loaded") === "1") continue;
    _decodeBusy += 1;
    img.setAttribute("data-loaded", "1");
    const done = () => {
      _decodeBusy = Math.max(0, _decodeBusy - 1);
      pumpDecodeQueue();
    };
    img.onload = done;
    img.onerror = done;
    img.src = s;
  }
}

function enqueueDecode(img) {
  if (!img || img.getAttribute("data-loaded") === "1") return;
  if (_decodeQueue.indexOf(img) >= 0) return;
  _decodeQueue.push(img);
  pumpDecodeQueue();
}

function paintVirtualGallery(force) {
  const stage = document.getElementById("mainStage");
  const grid = document.getElementById("galleryGrid");
  const topSp = document.getElementById("gallerySpacerTop");
  const botSp = document.getElementById("gallerySpacerBot");
  if (!stage || !grid || !topSp || !botSp) return;
  const pinnedScroll = stage.scrollTop;
  const assets = _galleryAssets;
  if (!assets.length) {
    grid.innerHTML = "";
    topSp.style.height = "0px";
    botSp.style.height = "0px";
    _virtRangeKey = "";
    return;
  }
  const { cols, rowH, rows, totalH } = galleryMetrics();
  document.documentElement.style.setProperty("--gallery-cols", String(cols));
  const scrollTop = pinnedScroll;
  const virt = document.getElementById("galleryVirt");
  const virtTop = virt ? Math.max(0, virt.offsetTop) : 0;
  const localScroll = Math.max(0, scrollTop - virtTop);
  const viewH = stage.clientHeight;
  let startRow = Math.max(0, Math.floor(localScroll / rowH) - VIRT_ROW_BUFFER);
  let endRow = Math.min(rows, Math.ceil((localScroll + viewH) / rowH) + VIRT_ROW_BUFFER);
  if (endRow <= startRow) endRow = Math.min(rows, startRow + 1);
  const startIdx = startRow * cols;
  const endIdx = Math.min(assets.length, endRow * cols);
  const selSig = state.batchMode ? _selectedPaths.size + ":" + (_lastClickedIdx | 0) : "0";
  const rangeKey = [startIdx, endIdx, cols, state.thumbSize, assets.length, state.showGuides ? 1 : 0, state.batchMode ? 1 : 0, selSig].join(":");
  const topH = startRow * rowH;
  const botH = Math.max(0, totalH - endRow * rowH);
  // 同一窗口：只同步垫片，不重建 DOM（重建会让滚轮感觉「自己在上下晃」）
  if (!force && rangeKey === _virtRangeKey && grid.children.length) {
    if (topSp.style.height !== topH + "px") topSp.style.height = topH + "px";
    if (botSp.style.height !== botH + "px") botSp.style.height = botH + "px";
    return;
  }
  _virtRangeKey = rangeKey;
  topSp.style.height = topH + "px";
  botSp.style.height = botH + "px";
  const slice = assets.slice(startIdx, endIdx);
  grid.style.gridTemplateColumns = `repeat(${cols}, minmax(0, 1fr))`;
  grid.innerHTML = slice.map(cardHtml).join("");
  if (_imgIo) { try { _imgIo.disconnect(); } catch (e) {} _imgIo = null; }
  _decodeQueue = [];
  _decodeBusy = 0;
  updateBatchCount();
  // 换片后若浏览器锚定把滚动拽走，立刻钉回
  if (Math.abs(stage.scrollTop - pinnedScroll) > 0.5) {
    stage.scrollTop = pinnedScroll;
  }
}

let _scrollPaintTimer = 0;
function scheduleVirtualPaint(force) {
  if (force) {
    if (_virtRaf) cancelAnimationFrame(_virtRaf);
    _virtRaf = 0;
    clearTimeout(_scrollPaintTimer);
    _scrollPaintTimer = 0;
    paintVirtualGallery(true);
    return;
  }
  // 滑动：rAF 合并一帧内多次 scroll；略延后合并突发滚动，减少重建次数
  if (_virtRaf) return;
  _virtRaf = requestAnimationFrame(() => {
    _virtRaf = 0;
    paintVirtualGallery(false);
  });
}

function cardPathFromEvent(el) {
  const card = el && el.closest ? el.closest("[data-path]") : null;
  return card ? card.getAttribute("data-path") : "";
}

function bindGalleryActions() {
  const stage = document.getElementById("mainStage");
  if (!stage || stage.dataset.galleryBound === "1") return;
  stage.dataset.galleryBound = "1";
  stage.addEventListener("click", (ev) => {
    const folderBtn = ev.target.closest(".btn-folder, [data-act='reveal']");
    if (folderBtn) {
      ev.preventDefault();
      ev.stopPropagation();
      const p = cardPathFromEvent(folderBtn);
      if (p) revealInFolder(p);
      return;
    }
    if (ev.target.closest("#btnBatchSelectAll")) {
      selectAllFiltered();
      return;
    }
    if (ev.target.closest("#btnBatchClear")) {
      clearSelection();
      return;
    }
    if (ev.target.closest("#btnBatchDelete")) {
      deleteSelectedAssets();
      return;
    }
    if (ev.target.closest("#btnBatchOpenTrash")) {
      openTrashFolder();
      return;
    }
    if (ev.target.closest("#btnBatchCancel")) {
      setBatchMode(false);
      return;
    }
    const card = ev.target.closest(".asset-card[data-path]");
    if (card && state.batchMode) {
      ev.preventDefault();
      ev.stopPropagation();
      const p = card.getAttribute("data-path");
      const idx = _galleryAssets.findIndex(a => a.path === p);
      toggleSelectPath(p, { shiftKey: ev.shiftKey, idx });
      return;
    }
    const thumb = ev.target.closest(".asset-card .thumb-wrap");
    if (thumb) {
      ev.preventDefault();
      ev.stopPropagation();
      const p = cardPathFromEvent(thumb);
      if (p) openViewer(p);
    }
  });
  stage.addEventListener("mouseover", (ev) => {
    const card = ev.target.closest(".asset-card[data-path]");
    if (card) _hoveredPath = card.getAttribute("data-path") || "";
  });
  stage.addEventListener("mouseout", (ev) => {
    const card = ev.target.closest(".asset-card[data-path]");
    if (!card) return;
    const to = ev.relatedTarget && ev.relatedTarget.closest ? ev.relatedTarget.closest(".asset-card[data-path]") : null;
    if (!to) _hoveredPath = "";
  });
  stage.addEventListener("contextmenu", (ev) => {
    const card = ev.target.closest(".asset-card[data-path]");
    if (!card) return;
    showImgCtxMenu(ev, card.getAttribute("data-path"));
  });
}

function bindVirtualScroll() {
  const stage = document.getElementById("mainStage");
  if (!stage || _virtScrollBound) return;
  _virtScrollBound = true;
  bindGalleryActions();
  stage.addEventListener("scroll", () => {
    if (state.tab !== "gallery") return;
    scheduleVirtualPaint(false);
  }, { passive: true });
  window.addEventListener("resize", () => {
    if (state.tab !== "gallery") return;
    scheduleVirtualPaint(false);
  }, { passive: true });
}

function renderImproveTab() {
  const prof = DATA.profile || {};
  const selLib = getSelectedLibraryObj();
  const isHist = selLib && !selLib.is_current;
  const taste = isHist ? (selLib.taste || {}) : (prof.taste || {});
  const privCardsForView = isHist ? (selLib.knowledge_cards || []) : (prof.private_knowledge_cards || []);
  const sharedCardsForView = prof.shared_knowledge_cards || [];
  const privIdsForView = new Set(privCardsForView.map(c => c.id));
  const kCards = privCardsForView.concat(sharedCardsForView.filter(c => !privIdsForView.has(c.id)));
  const refls = isHist ? (selLib.reflections || []) : (prof.reflections || []);
  const sig = taste.signal_counts || {};
  const projLibs = getProjectLibraries();
  const activeProj = getActiveProjectMeta();

  const lightingPills = (taste.preferred_lighting || []).map(x => `<span class="taste-pill">☀️ ${esc(x)}</span>`).join("") || `<span style="color:var(--text-muted)">暂未捕获</span>`;
  const compPills = (taste.preferred_composition || []).map(x => `<span class="taste-pill">📐 ${esc(x)}</span>`).join("") || `<span style="color:var(--text-muted)">暂未捕获</span>`;
  const tempPills = (taste.preferred_color_temperature || []).map(x => `<span class="taste-pill">🎨 ${esc(x)}</span>`).join("") || `<span style="color:var(--text-muted)">暂未捕获</span>`;
  const linePills = (taste.preferred_line_weight || []).map(x => `<span class="taste-pill">✒️ ${esc(x)}</span>`).join("") || `<span style="color:var(--text-muted)">暂未捕获</span>`;
  const banPills = (taste.banned_habits || []).map(x => `<span class="taste-pill ban">🚫 ${esc(x)}</span>`).join("") || `<span style="color:var(--text-muted)">暂无</span>`;

  const reflHtml = refls.map(r => {
    const scoresHtml = (r.scores || []).map(s => `
      <span class="score-step ${s.passed ? 'pass' : ''}">第${s.round}轮: ${Number(s.score).toFixed(1)}分 ${s.passed ? '🏆 达标' : '→'}</span>
    `).join("");
    const fixesHtml = (r.what_fixed || []).map(f => `<li style="margin-left:16px;margin-top:3px;font-size:12px;color:var(--text-main);">${esc(f)}</li>`).join("");
    return `
      <div class="kcard" style="margin-bottom:10px;">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;">
          <strong style="color:var(--gold);font-size:13.5px;">🎯 ${esc(r.goal || r.session_id)}</strong>
          <span class="badge success">${esc(r.outcome || "")}</span>
        </div>
        <div style="font-size:11.5px;color:var(--text-muted);margin-top:4px;font-family:ui-monospace,monospace;">
          模块: ${esc(r.module)} · 模式: ${esc(r.converge_mode)} · 合格线: ≥${r.threshold}分 (最多${r.max_rounds}轮) · 胜出图: ${esc(r.winner_image || "")}
        </div>
        <div class="score-step-row">${scoresHtml}</div>
        ${r.strengths ? `<div style="margin-top:8px;font-size:12px;color:#6ee7b7;">✨ <b>保留亮点：</b>${esc(r.strengths)}</div>` : ""}
        ${fixesHtml ? `<div style="margin-top:6px;font-size:12px;color:#93c5fd;">🔧 <b>自动修正轨迹：</b><ul style="margin:4px 0 0;padding:0;">${fixesHtml}</ul></div>` : ""}
      </div>
    `;
  }).join("") || `<div class="entry-card">暂无收敛复盘记录。</div>`;

  const privCount = privCardsForView.length;
  const sharedCount = sharedCardsForView.length;
  const kCardsHtml = kCards.map(c => {
    const isShared = c.layer_scope === "shared";
    const ownerLabel = isShared
      ? "🌐 全局共享通用库 (~/.pmem-art/shared/)"
      : `🏷️ 所属专项库: ${c.project_name || selLib.project_name} (${c.project_id || selLib.project_id})`;
    const layerBadge = isShared
      ? `<span class="badge info" style="font-size:10px;">🌐 跨项目共享层 (Shared)</span>`
      : `<span class="badge teal" style="font-size:10px;">🔒 项目私有层 (${esc(c.project_id || selLib.project_id)})${c.promoted_to_shared ? ' · 已同步全局' : ''}</span>`;
    return `
    <div class="kcard" style="border-color:${isShared ? 'rgba(56,189,248,0.28)' : 'rgba(45,212,191,0.35)'};">
      <div class="kcard-title">
        <span>📘 ${esc(c.title)}</span>
        ${layerBadge}
      </div>
      <div style="font-size:12px;color:var(--text-main);line-height:1.55;margin-top:4px;">${esc(c.body)}</div>
      <div style="font-size:10.5px;color:var(--text-dim);margin-top:6px;font-family:ui-monospace,monospace;">${esc(ownerLabel)} · ID: ${esc(c.id)} · 标签: ${esc((c.tags || []).join(" · "))}</div>
    </div>
    `;
  }).join("");

  const switcherHtml = `
    <div class="improve-card" style="border-color:rgba(168,85,247,0.4);">
      <h3>
        <span>🗂️ 专项记忆库项目切换器 & 历史项目演进看板 (Specialized Project Library Switcher)</span>
        <span style="font-size:11px;color:#d8b4fe;font-family:ui-monospace,monospace;">.memory-art/projects/ (${projLibs.length} 个项目专项库) + ~/.pmem-art/shared/</span>
      </h3>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">
        每个项目拥有明确项目名标识的专属记忆库 <code>.memory-art/projects/&lt;project-id&gt;/</code>。当你把旧项目的 <code>.memory-art</code> 文件夹直接拷贝到新项目时，系统会自动把旧项目封存为<b>历史项目专项库（只读溯源、严禁串味）</b>，并为新项目自动创建干净的专属记忆库，同时挂载全局共享通用库 <code>~/.pmem-art/shared/</code>：
      </div>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px;">
        ${projLibs.map(lib => {
          const isSel = (state.selectedLibrary === "CURRENT" && lib.is_current) || (state.selectedLibrary === lib.project_id);
          return `
            <div class="kcard" style="cursor:pointer;border-color:${isSel ? 'var(--teal)' : (lib.is_current ? 'rgba(16,185,129,0.4)' : 'rgba(245,158,11,0.35)')};background:${isSel ? 'rgba(45,212,191,0.08)' : '#090d16'};" onclick="selectProjectLibrary('${esc(lib.project_id)}')">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:6px;flex-wrap:wrap;">
                <strong style="color:${lib.is_current ? '#6ee7b7' : '#fcd34d'};font-size:13px;">🏷️ ${esc(lib.project_name)}</strong>
                <span class="badge ${lib.is_current ? 'success' : 'warning'}" style="font-size:10px;">${lib.is_current ? '🟢 当前项目专项库' : '🕓 历史项目专项库（拷贝保留·严禁串味）'}</span>
              </div>
              <div style="font-size:11px;color:var(--text-muted);font-family:ui-monospace,monospace;margin-top:4px;">
                项目ID: <b>${esc(lib.project_id)}</b> · 路径: <code>${esc(lib.library_dir)}/</code>
              </div>
              <div style="display:flex;gap:10px;flex-wrap:wrap;font-size:11.5px;color:var(--text-main);margin-top:6px;">
                <span>🧭 专项记忆: <b>${lib.entries_count || 0} 条</b></span>
                <span>📘 私有知识卡: <b>${(lib.knowledge_cards || []).length} 张</b></span>
                <span>🏆 收敛复盘: <b>${(lib.reflections || []).length} 场</b></span>
              </div>
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;

  return `
    ${switcherHtml}
    <div class="improve-grid">
      <div class="improve-card" style="margin-bottom:0;">
        <h3><span>🎨 个人审美口味档案 (Personal Taste Profile)</span><span style="font-size:11px;color:var(--text-muted);font-family:ui-monospace,monospace;">.memory-art/_profile/taste.json</span></h3>
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">
          系统在每次 <code>feedback</code>、<code>converge</code> 与自然语言对话中静默提取你的审美偏好，并在下次生图 Warm-Start 时自动注入：
        </div>
        <div style="margin-bottom:8px;"><strong style="font-size:12px;">☀️ 偏爱光影：</strong><div class="taste-pill-list">${lightingPills}</div></div>
        <div style="margin-bottom:8px;"><strong style="font-size:12px;">📐 偏爱构图与规格：</strong><div class="taste-pill-list">${compPills}</div></div>
        <div style="margin-bottom:8px;"><strong style="font-size:12px;">🎨 偏爱色温与色板：</strong><div class="taste-pill-list">${tempPills}</div></div>
        <div style="margin-bottom:8px;"><strong style="font-size:12px;">✒️ 偏爱线稿与笔触：</strong><div class="taste-pill-list">${linePills}</div></div>
        <div style="margin-bottom:10px;"><strong style="font-size:12px;color:#fda4af;">🚫 严禁踩坑习惯 (自动注入 Negative)：</strong><div class="taste-pill-list">${banPills}</div></div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;padding-top:8px;border-top:1px solid var(--border);font-size:11.5px;color:var(--text-muted);">
          <span>累计保留正例: <b style="color:var(--teal)">${sig.keeps || 0}</b></span>
          <span>累计打回红线: <b style="color:#fda4af">${sig.rejects || 0}</b></span>
          <span>风格修正信号: <b style="color:var(--gold)">${sig.style_fixes || 0}</b></span>
          <span>闭环收敛场次: <b>${sig.sessions || refls.length}</b></span>
        </div>
      </div>

      <div class="improve-card" style="margin-bottom:0;">
        <h3><span>⚡ 4轮 ≥9.5分 自评收敛与静默进化工作流</span><span style="font-size:11px;color:var(--teal);font-family:ui-monospace,monospace;">Whisper Autopilot</span></h3>
        <div style="font-size:12px;color:var(--text-main);line-height:1.6;">
          <div style="padding:8px 10px;background:#090d16;border-radius:8px;border:1px solid var(--border);margin-bottom:8px;">
            <strong style="color:var(--gold);">1️⃣ 各类型图片自动入库带描述：</strong><br>
            无论是 <code>python3 pmem_art.py ingest &lt;图片&gt; -p "中文描述/Prompt" --apply</code>，还是 <code>/pmem-draw</code>、<code>/pmem-ui</code>、<code>/pmem-concept</code>、<code>/pmem-icon</code> 收敛胜出，都会<b>自动识别分类（角色/场景/UI/特效/风格圣经）</b>、生成中文描述并立即重建本看板。
          </div>
          <div style="padding:8px 10px;background:#090d16;border-radius:8px;border:1px solid var(--border);margin-bottom:8px;">
            <strong style="color:var(--teal);">2️⃣ 4轮 ≥9.5分 闭环自评收敛 (Converge Engine)：</strong><br>
            每次生图最多迭代 <b>4 轮</b>，六维加权调和平均，满 <b>9.5 / 10 分</b>才交付，满 4 轮取最高分；胜出图与踩坑红线自动写回记忆。
          </div>
          <div style="padding:8px 10px;background:#090d16;border-radius:8px;border:1px solid var(--border);">
            <strong style="color:#d8b4fe;">3️⃣ 浏览器 3 秒无感自动刷新：</strong><br>
            右上角 <b>🔄 自动刷新: 开启 (3s)</b> 通过轻量级 <code>.memory-art/atlas_ping.js</code> 心跳检测变更，保持当前筛选、标签页与滚动位置无感同步最新资产。
          </div>
        </div>
      </div>
    </div>

    <div class="improve-card">
      <h3><span>🏆 闭环自评收敛历史与评分曲线 (Converge Reflections)</span><span style="font-size:11px;color:var(--text-muted);font-family:ui-monospace,monospace;">.memory-art/_reflections/ (${refls.length} 场)</span></h3>
      ${reflHtml}
    </div>

    <div class="improve-card">
      <h3>
        <span>🌍 双层美术知识广度图谱 (Two-Layer Knowledge Architecture)</span>
        <span style="font-size:11px;color:var(--text-muted);font-family:ui-monospace,monospace;">🔒 项目私有: ${privCount} 张 · 🌐 跨项目共享: ${sharedCount} 张（合并去重 ${kCards.length} 张）</span>
      </h3>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;">
        <b>Layer 1 项目私有层 (<code>.memory-art/</code>)</b> 严格隔离本项目模块、红线、色板与画风卡，切换项目绝不串味；<b>Layer 2 跨项目全局共享层 (<code>~/.pmem-art/shared/</code>)</b> 仅存放无风格绑定的通用美术规律（头身比尺规、70/20/10配色比、大气透视、九宫格结构、可读剪影），新项目冷启动自动挂载，同模块匹配时私有层权重高于共享层：
      </div>
      <div class="kcard-grid">${kCardsHtml}</div>
    </div>
  `;
}

function renderRedlinesTab() {
  const redlines = getFilteredEntries().filter(e => e.kind === "style_redline" || e.kind === "visual_correction");
  if (!redlines.length) {
    return `<div class="entry-card">当前模块暂无风格红线或视觉勘误记录。</div>`;
  }
  return redlines.map((e, idx) => {
    const assets = e.assets || [];
    const good = assets.find(a => a.role === "approved" || a.role === "anchor") || assets[0];
    const bad = assets.find(a => a.role === "rejected") || assets[1];
    const goodInfo = good ? DATA.assets[good.path] : null;
    const badInfo = bad ? DATA.assets[bad.path] : null;

    return `
      <div class="compare-card">
        <div class="compare-header">
          <div class="compare-title">
            <span class="badge ${esc(e.badge)}">${esc(e.kind_label)}</span>
            <span>[${esc(e.module)} · ${esc(e.entity)}] ${esc(e.summary)}</span>
          </div>
          <span style="font-size:12px;color:var(--text-muted);">责任人: ${esc(e.author)} · ${esc(e.note_date)}</span>
        </div>
        <div style="font-size:13px;color:var(--text-main);white-space:pre-line;background:#0b101d;padding:12px 14px;border-radius:8px;border:1px solid var(--border);">${esc(e.body)}</div>
        ${e.verify ? `<div style="margin-top:8px;font-size:12px;color:var(--teal);">✔ 验收标准 (Verify): ${esc(e.verify)}</div>` : ''}

        ${(goodInfo && badInfo) ? `
          <div class="compare-grid">
            <div class="compare-box do-box">
              <div class="compare-box-head">
                <span>✅ 正确基准 (DO · Approved Anchor)</span>
                <span style="font-family:monospace;">${esc(good.path)}</span>
              </div>
              <div class="compare-img-wrap ${state.bgClass} ${state.showGuides ? 'show-guides' : ''}" onclick="openViewer('${esc(good.path)}')">
                <img src="${assetSrc(goodInfo)}" alt="Approved" loading="lazy" />
                <div class="overlay-9slice">
                  <div class="slice-line v1"></div><div class="slice-line v2"></div>
                  <div class="slice-line h1"></div><div class="slice-line h2"></div>
                </div>
              </div>
              <div class="compare-caption">${esc(good.caption || '')}</div>
            </div>

            <div class="compare-box dont-box">
              <div class="compare-box-head">
                <span>❌ 打回废案 / 待修违规 (DON'T · Rejected)</span>
                <span style="font-family:monospace;">${esc(bad.path)}</span>
              </div>
              <div class="compare-img-wrap ${state.bgClass} ${state.showGuides ? 'show-guides' : ''}" onclick="openViewer('${esc(bad.path)}')">
                <img src="${assetSrc(badInfo)}" alt="Rejected" loading="lazy" />
                <div class="overlay-9slice">
                  <div class="slice-line v1"></div><div class="slice-line v2"></div>
                  <div class="slice-line h1"></div><div class="slice-line h2"></div>
                </div>
              </div>
              <div class="compare-caption">${esc(bad.caption || '')}</div>
            </div>
          </div>

          <div class="ab-slider-container ${state.bgClass}" id="abSlider_${idx}" onmousemove="moveAbSlider(event, ${idx})" ontouchmove="moveAbSlider(event, ${idx})">
            <div class="ab-layer"><img src="${assetSrc(badInfo)}" /></div>
            <div class="ab-layer ab-before" id="abBefore_${idx}" style="background:inherit;"><img src="${assetSrc(goodInfo)}" /></div>
            <div class="ab-handle" id="abHandle_${idx}"></div>
            <span style="position:absolute;top:10px;left:12px;background:rgba(16,185,129,0.9);color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;z-index:6;">👈 左侧: ✅ 正例定稿</span>
            <span style="position:absolute;top:10px;right:12px;background:rgba(244,63,94,0.9);color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;z-index:6;">右侧: ❌ 废案对比 👉</span>
          </div>
        ` : ''}
      </div>
    `;
  }).join("");
}

window.moveAbSlider = function(ev, idx) {
  if (ev.type === "mousemove" && ev.buttons !== 1) return;
  const box = document.getElementById("abSlider_" + idx);
  if (!box) return;
  const rect = box.getBoundingClientRect();
  const clientX = ev.touches ? ev.touches[0].clientX : ev.clientX;
  let pct = ((clientX - rect.left) / rect.width) * 100;
  pct = Math.max(2, Math.min(98, pct));
  document.getElementById("abBefore_" + idx).style.clipPath = `inset(0 ${100 - pct}% 0 0)`;
  document.getElementById("abHandle_" + idx).style.left = pct + "%";
};

function renderRecipesTab() {
  const recipes = getFilteredEntries().filter(e => e.kind === "recipe" || e.ai_params);
  let htmlOut = "";
  for (const e of recipes) {
    const ai = e.ai_params || {};
    const wfJson = ai.workflow && DATA.workflows[ai.workflow] ? JSON.stringify(DATA.workflows[ai.workflow], null, 2) : null;
    const sampleAsset = (e.assets || [])[0];
    const sampleInfo = sampleAsset ? DATA.assets[sampleAsset.path] : null;

    htmlOut += `
      <div class="recipe-card">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap;">
          <div>
            <span class="badge gold">🧪 AI 生图标准配方</span>
            <strong style="font-size:15px;margin-left:8px;">[${esc(e.module)}] ${esc(e.summary)}</strong>
          </div>
          <div style="display:flex;gap:8px;">
            <button class="btn-copy" onclick='copyText(${JSON.stringify(ai.prompt || "")}, "正向 Prompt")'>📋 复制正向 Prompt</button>
            <button class="btn-copy" onclick='copyText(${JSON.stringify(ai.negative_prompt || "")}, "负向 Negative Prompt")'>🚫 复制 Negative</button>
            ${wfJson ? `<button class="btn-copy" onclick='copyText(${JSON.stringify(wfJson)}, "ComfyUI Workflow JSON")'>⚙️ 复制 ComfyUI JSON</button>` : ''}
          </div>
        </div>

        <div style="display:grid;grid-template-columns:${sampleInfo ? '240px 1fr' : '1fr'};gap:18px;align-items:start;">
          ${sampleInfo ? `
            <div class="thumb-wrap ${state.bgClass}" style="height:240px;border-radius:9px;border:1px solid var(--border);" onclick="openViewer('${esc(sampleAsset.path)}')">
              <img src="${assetSrc(sampleInfo)}" loading="lazy" />
              <span class="spec-tag">Seed: ${esc(ai.seed)}</span>
            </div>
          ` : ''}
          <div>
            <div style="display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;margin-bottom:10px;color:var(--text-muted);">
              <span>📦 底模 (Checkpoint): <b style="color:var(--text-main)">${esc(ai.model || '')}</b></span>
              <span>🎛️ 采样器: <b style="color:var(--text-main)">${esc(ai.sampler || '')}</b></span>
              <span>🌱 锁定 Seed: <b style="color:var(--gold)">${esc(ai.seed || '')}</b></span>
              <span>🦴 ControlNet: <b style="color:var(--teal)">${esc(ai.controlnet || '')}</b></span>
            </div>
            <div style="font-size:12px;color:var(--text-muted);">LoRA 权重组合: <b>${esc((ai.loras || []).join(" + "))}</b></div>
            <div style="margin-top:8px;font-size:12px;color:var(--teal);font-weight:600;">Positive Prompt (正向提示词模板):</div>
            <div class="code-block">${esc(ai.prompt || '')}</div>
            <div style="font-size:12px;color:#fda4af;font-weight:600;">Negative Prompt (防翻车负向词):</div>
            <div class="code-block">${esc(ai.negative_prompt || '')}</div>
            <div style="font-size:12.5px;color:var(--text-main);white-space:pre-line;">${esc(e.body)}</div>
          </div>
        </div>
      </div>
    `;
  }
  if (!htmlOut) {
    htmlOut = `<div class="entry-card">当前模块暂无独立 AI 配方记录，请参考全局风格圣经或切换至 character.Astra 查看完整 ComfyUI 配方。</div>`;
  }
  return htmlOut;
}

function renderMemoriesTab() {
  const entries = getFilteredEntries();
  return entries.map(e => `
    <div class="entry-card ${e.stale ? 'stale' : ''}">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:8px;">
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
          <span class="badge ${esc(e.badge)}">${esc(e.kind_label)}</span>
          <span style="font-family:monospace;font-weight:700;color:var(--teal);">${esc(e.module)} · ${esc(e.entity || '')}</span>
          <span class="badge purple" style="font-size:10.5px;">🏷️ 所属专项库: ${esc(e.project_name || getActiveProjectMeta().project_name)} (${esc(e.project_id || getActiveProjectMeta().project_id)})</span>
          ${e.scope === 'project' ? `<span class="badge info">🌐 全项目通用</span>` : ''}
          ${e.stale ? `<span class="badge warning">⚠️ STALE 需复核</span>` : ''}
          ${(e.supersedes && e.supersedes.length) ? `<span class="badge purple">🔄 替代旧记忆: ${esc(e.supersedes.join(', '))}</span>` : ''}
        </div>
        <span style="font-size:11.5px;color:var(--text-dim);">ID: ${esc(e.id)} · ${esc(e.author)} · 写于 ${esc(e.note_date)}</span>
      </div>
      <div style="font-size:14.5px;font-weight:700;margin-bottom:6px;">${esc(e.summary)}</div>
      ${e.stale ? `<div style="background:var(--gold-bg);color:#fcd34d;padding:6px 10px;border-radius:6px;font-size:12px;margin-bottom:8px;">⚠️ 过期原因: ${esc(e.stale_reasons.join('；'))}</div>` : ''}
      <div style="font-size:13px;color:var(--text-muted);white-space:pre-line;margin-bottom:10px;">${esc(e.body)}</div>
      ${e.verify ? `<div style="font-size:12px;color:var(--teal);margin-bottom:4px;">✔ 怎么验证 (Verify): ${esc(e.verify)}</div>` : ''}
      ${e.applies ? `<div style="font-size:12px;color:var(--text-dim);">📌 适用范围 (Applies): ${esc(e.applies)}</div>` : ''}
      ${(e.assets && e.assets.length) ? `
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:10px;">
          ${e.assets.map(a => {
            const info = DATA.assets[a.path];
            if (!info) return '';
            return `
              <div style="display:flex;align-items:center;gap:8px;background:#090d16;border:1px solid var(--border);padding:5px 10px;border-radius:7px;cursor:pointer;" onclick="openViewer('${esc(a.path)}')">
                <img src="${assetSrc(info)}" style="width:38px;height:38px;object-fit:contain;border-radius:4px;" class="${state.bgClass}" loading="lazy" />
                <div>
                  <div style="font-size:11.5px;font-family:monospace;color:var(--teal);">${esc(a.path)}</div>
                  <div style="font-size:11px;color:var(--text-muted);">${esc(a.caption || info.resolution)}</div>
                </div>
              </div>
            `;
          }).join("")}
        </div>
      ` : ''}
    </div>
  `).join("");
}

function renderQaTab() {
  const assets = Object.values(DATA.assets);
  return `
    <div class="entry-card">
      <h3 style="margin:0 0 8px;font-size:15px;">🛡️ 资产管线规格自动质检 (Post-Asset Validator)</h3>
      <p style="margin:0 0 14px;color:var(--text-muted);font-size:12.5px;">
        每次 AI 美术或人类画师导出图片后，<code>pmem_art.py validate</code> 自动核对各模块在 <code>modules.yaml</code> 中声明的硬性指标（分辨率、RGBA 透明通道、文件大小上限、SHA-256 哈希锚点一致性）。
      </p>
      <table style="width:100%;border-collapse:collapse;font-size:12.5px;">
        <thead>
          <tr style="border-bottom:1px solid var(--border);text-align:left;color:var(--text-muted);">
            <th style="padding:8px;">状态</th>
            <th style="padding:8px;">资产路径</th>
            <th style="padding:8px;">所属模块</th>
            <th style="padding:8px;">实测规格</th>
            <th style="padding:8px;">SHA-256 (前16位)</th>
            <th style="padding:8px;">质检结果 / 违规原因</th>
          </tr>
        </thead>
        <tbody>
          ${assets.map(a => `
            <tr style="border-bottom:1px solid rgba(255,255,255,0.05);cursor:pointer;" onclick="openViewer('${esc(a.path)}')">
              <td style="padding:8px;">${a.qa_passed ? '<span class="badge success">PASS</span>' : '<span class="badge danger">FAIL</span>'}</td>
              <td style="padding:8px;font-family:monospace;color:var(--teal);">${esc(a.path)}</td>
              <td style="padding:8px;">${esc(a.module)}</td>
              <td style="padding:8px;font-family:monospace;">${esc(a.resolution)} · ${esc(a.mode)} · ${a.size_kb} KB</td>
              <td style="padding:8px;font-family:monospace;color:var(--text-dim);">${esc(a.sha256_16)}</td>
              <td style="padding:8px;color:${a.qa_passed ? '#6ee7b7' : '#fda4af'};">
                ${a.qa_passed ? '✔ 符合模块分辨率与通道契约' : '⚠️ ' + esc(a.qa_issues.join('；'))}
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderStage(opts) {
  opts = opts || {};
  const stage = document.getElementById("mainStage");
  const keepScroll = !!opts.keepScroll && state.tab === "gallery";
  const pinnedScroll = keepScroll && stage ? stage.scrollTop : 0;
  renderHeaderAndSidebar();
  let content = renderModuleBanner();
  if (state.tab === "gallery") content += renderGalleryTab();
  else if (state.tab === "improve") content += renderImproveTab();
  else if (state.tab === "redlines") content += renderRedlinesTab();
  else if (state.tab === "recipes") content += renderRecipesTab();
  else if (state.tab === "memories") content += renderMemoriesTab();
  else if (state.tab === "qa") content += renderQaTab();
  stage.innerHTML = content;
  bindVirtualScroll();
  if (state.tab === "gallery") {
    if (keepScroll) stage.scrollTop = pinnedScroll;
    scheduleVirtualPaint(true);
    if (keepScroll) {
      requestAnimationFrame(() => { stage.scrollTop = pinnedScroll; });
    }
  }
}

window.selectModule = function(modId) {
  state.module = modId;
  state.sideMode = (modId === "ALL") ? "all" : "module";
  if (modId === "ALL") state.dayFilter = state.dayFilter || "today";
  state.tab = "gallery";
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === "gallery"));
  saveAtlasState();
  renderStage();
};

window.switchTab = function(tabName) {
  state.tab = tabName;
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.toggle("active", b.dataset.tab === tabName));
  document.querySelectorAll("#moreMenu [data-tab]").forEach(b => b.classList.toggle("active", b.dataset.tab === tabName));
  const more = document.getElementById("moreWrap");
  if (more) more.classList.remove("open");
  saveAtlasState();
  renderStage();
};

function parentDirOf(absPath) {
  const n = String(absPath || "").replace(/\\/g, "/");
  const i = n.lastIndexOf("/");
  return i > 0 ? n.slice(0, i) : n;
}

function pathToFileUrl(absPath) {
  let n = String(absPath || "").replace(/\\/g, "/");
  if (/^[A-Za-z]:\//.test(n)) {
    return "file:///" + n.split("/").map((seg, i) => (i === 0 ? seg : encodeURIComponent(seg))).join("/");
  }
  if (!n.startsWith("/")) n = "/" + n;
  return "file://" + n.split("/").map((seg, i) => (i === 0 ? "" : encodeURIComponent(seg))).join("/");
}

function isWindowsAbs(absPath) {
  return /\\/.test(String(absPath || "")) || /^[A-Za-z]:[\\/]/.test(String(absPath || ""));
}

function downloadTextFile(name, body) {
  const blob = new Blob([body], { type: "application/octet-stream" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1500);
}

function workbenchLauncherBody(win) {
  const root = String(DATA.root || "");
  const rootWin = root.replace(/\//g, "\\");
  const rootPy = root.replace(/\\/g, "/");
  // 先 cd 到项目根，再用 Path('.')，避免 bat/shell 路径引号嵌套翻车
  const pyBoot = "from pathlib import Path; from atlas_reveal import ensure_reveal_daemon; print(ensure_reveal_daemon(Path('.').resolve()))";
  if (win) {
    return [
      "@echo off",
      "chcp 65001 >nul",
      "cd /d \"" + rootWin + "\"",
      "set \"PORTFILE=%TEMP%\\pmem_atlas_port.txt\"",
      "py -3 -c \"" + pyBoot + "\" > \"%PORTFILE%\" 2>nul",
      "if errorlevel 1 python -c \"" + pyBoot + "\" > \"%PORTFILE%\" 2>nul",
      "if errorlevel 1 python3 -c \"" + pyBoot + "\" > \"%PORTFILE%\" 2>nul",
      "set /p PORT=<\"%PORTFILE%\"",
      "if \"%PORT%\"==\"\" set PORT=0",
      "if \"%PORT%\"==\"0\" (",
      "  echo 启动失败：请确认本机有 Python，且项目目录可 import atlas_reveal。",
      "  pause",
      "  exit /b 1",
      ")",
      "start \"\" \"http://127.0.0.1:%PORT%/art-atlas.html\"",
      "echo 已打开 http://127.0.0.1:%PORT%/art-atlas.html",
      ""
    ].join("\r\n");
  }
  return [
    "#!/bin/bash",
    "set -e",
    "cd " + JSON.stringify(rootPy),
    "PORT=$(python3 -c " + JSON.stringify(pyBoot) + " 2>/dev/null || python -c " + JSON.stringify(pyBoot) + ")",
    "if [ -z \"$PORT\" ] || [ \"$PORT\" = \"0\" ]; then",
    "  echo \"启动失败：请确认本机有 Python，且项目目录可 import atlas_reveal。\"",
    "  exit 1",
    "fi",
    "URL=\"http://127.0.0.1:${PORT}/art-atlas.html\"",
    "if command -v open >/dev/null 2>&1; then open \"$URL\"; elif command -v xdg-open >/dev/null 2>&1; then xdg-open \"$URL\"; else echo \"$URL\"; fi",
    ""
  ].join("\n");
}

/** 浏览器无法从 file:// 直接起 Python：下载一次性启动脚本，双击后拉起 reveal 并打开 http 工作台 */
function downloadStartWorkbenchHelper() {
  const root = String(DATA.root || "");
  const win = isWindowsAbs(root) || /win/i.test(navigator.platform || "");
  if (win) {
    downloadTextFile("启动工作台服务.bat", workbenchLauncherBody(true));
  } else {
    downloadTextFile("启动工作台服务.command", workbenchLauncherBody(false));
  }
}

async function waitForRevealBridge(msTotal, stepMs) {
  const total = Math.max(1000, Number(msTotal) || 30000);
  const step = Math.max(200, Number(stepMs) || 1000);
  const deadline = Date.now() + total;
  while (Date.now() < deadline) {
    const port = await pingRevealBridge();
    if (port) return port;
    await new Promise((r) => setTimeout(r, step));
  }
  return 0;
}

function downloadRevealHelper(absFile) {
  const win = isWindowsAbs(absFile) || /win/i.test(navigator.platform || "");
  const root = String(DATA.root || "");
  // 禁止写死 27865：多项目时用 ensure_reveal_daemon 按根路径选口
  const pyBoot = "from pathlib import Path; from atlas_reveal import ensure_reveal_daemon; print(ensure_reveal_daemon(Path('.').resolve()))";
  if (win) {
    const winPath = String(absFile).replace(/\//g, "\\");
    const rootWin = root.replace(/\//g, "\\");
    const body = [
      "@echo off",
      "chcp 65001 >nul",
      "cd /d \"" + rootWin + "\"",
      "set \"PORTFILE=%TEMP%\\pmem_atlas_port.txt\"",
      "py -3 -c \"" + pyBoot + "\" > \"%PORTFILE%\" 2>nul",
      "if errorlevel 1 python -c \"" + pyBoot + "\" > \"%PORTFILE%\" 2>nul",
      "explorer /select,\"" + winPath + "\"",
      ""
    ].join("\r\n");
    downloadTextFile("打开图片位置.bat", body);
  } else {
    const body = (
      "#!/bin/bash\ncd " + JSON.stringify(root)
      + "\npython3 -c " + JSON.stringify(pyBoot)
      + " >/dev/null 2>&1 || python -c " + JSON.stringify(pyBoot)
      + " >/dev/null 2>&1\nopen -R " + JSON.stringify(absFile) + "\n"
    );
    downloadTextFile("打开图片位置.command", body);
  }
}

function downloadDeleteHelper(absFiles) {
  const root = String(DATA.root || "");
  const win = isWindowsAbs(absFiles[0] || root) || /win/i.test(navigator.platform || "");
  const trash = (root.replace(/[\\/]+$/, "") + "/.memory-art/_trash").replace(/\\/g, win ? "\\" : "/");
  if (win) {
    const rootWin = root.replace(/\//g, "\\");
    const trashWin = trash.replace(/\//g, "\\");
    const lines = [
      "@echo off",
      "chcp 65001 >nul",
      "echo 将移入工作台垃圾桶（可找回）: " + trashWin,
      "mkdir \"" + trashWin + "\" 2>nul"
    ];
    absFiles.forEach(p => {
      const abs = String(p).replace(/\//g, "\\");
      const rel = abs.toLowerCase().startsWith(rootWin.toLowerCase() + "\\")
        ? abs.slice(rootWin.length + 1)
        : abs.split("\\").slice(-2).join("\\");
      const destDir = trashWin + "\\" + rel.replace(/\\[^\\]+$/, "");
      lines.push("mkdir \"" + destDir + "\" 2>nul");
      lines.push("move /Y \"" + abs + "\" \"" + trashWin + "\\" + rel + "\"");
    });
    lines.push("echo 完成。从垃圾桶挪回原相对路径即可恢复。");
    lines.push("explorer \"" + trashWin + "\"");
    lines.push("pause");
    downloadTextFile("移入工作台垃圾桶.bat", lines.join("\r\n") + "\r\n");
  } else {
    const lines = [
      "#!/bin/bash",
      "set -e",
      "TRASH=" + JSON.stringify(trash),
      "ROOT=" + JSON.stringify(root),
      "mkdir -p \"$TRASH\"",
      "echo 将移入工作台垃圾桶: $TRASH",
      "read -r -p '回车继续…' _"
    ];
    absFiles.forEach(p => {
      lines.push("f=" + JSON.stringify(p));
      lines.push('rel="${f#"$ROOT"/}"');
      lines.push('mkdir -p "$TRASH/$(dirname "$rel")"');
      lines.push('mv -f "$f" "$TRASH/$rel"');
    });
    lines.push("echo 完成。从垃圾桶挪回原相对路径即可恢复。");
    lines.push('open "$TRASH" || true');
    downloadTextFile("移入工作台垃圾桶.command", lines.join("\n") + "\n");
  }
}

window.openInEditor = function(relPath) {
  const abs = absAssetPath(relPath);
  copyText(abs, "绝对路径");
  const uriCursor = "cursor://file" + abs;
  const uriVs = "vscode://file" + abs;
  try {
    const a = document.createElement("a");
    a.href = uriCursor;
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    a.remove();
  } catch (e) {
    try { window.open(uriVs, "_blank"); } catch (e2) {}
  }
  showToast("已复制路径，并尝试在编辑器打开");
};

function revealPorts() {
  const ports = [];
  const push = (p) => {
    const n = Number(p || 0);
    if (n > 0 && !ports.includes(n)) ports.push(n);
  };
  push(DATA.reveal_port);
  push((window.__PMEM_ATLAS_PING__ || {}).reveal_port);
  // 与 atlas_reveal.PREFERRED_PORT_SPAN 对齐：按项目哈希偏好 + 顺延探测
  for (let p = 27865; p < 27865 + 64; p++) push(p);
  for (let p = 8765; p < 8765 + 16; p++) push(p);
  return ports;
}

function setRevealBanner(ok) {
  _revealOk = !!ok;
  const el = document.getElementById("revealBanner");
  if (el) el.classList.toggle("show", !ok);
}

function normRevealRoot(p) {
  return String(p || "").replace(/\\/g, "/").replace(/\/+$/, "").toLowerCase();
}

async function pingRevealBridge() {
  const wantRoot = normRevealRoot(DATA.root || "");
  for (const port of revealPorts()) {
    try {
      const res = await fetch("http://127.0.0.1:" + port + "/api/ping", {
        method: "GET", cache: "no-store", mode: "cors"
      });
      if (!res.ok) continue;
      const j = await res.json().catch(() => ({}));
      if (j && j.ok && j.service === "pmem-atlas-reveal" && Array.isArray(j.apis)
          && j.apis.indexOf("promote") >= 0 && j.apis.indexOf("trash") >= 0) {
        // 多项目同机：不能认领别人项目的 27865
        if (wantRoot && j.root && normRevealRoot(j.root) !== wantRoot) continue;
        DATA.reveal_port = port;
        setRevealBanner(true);
        return port;
      }
    } catch (e) {}
  }
  setRevealBanner(false);
  return 0;
}

async function revealViaBridge(relPath) {
  const q = encodeURIComponent(relPath);
  let port = Number(DATA.reveal_port || 0);
  if (!port) port = await pingRevealBridge();
  if (!port) return false;
  try {
    const res = await fetch("http://127.0.0.1:" + port + "/api/reveal?path=" + q, {
      method: "GET",
      cache: "no-store",
      mode: "cors"
    });
    if (res.ok) {
      const j = await res.json().catch(() => ({ ok: true }));
      if (j && j.ok !== false && (!j.service || j.service === "pmem-atlas-reveal")) {
        setRevealBanner(true);
        return true;
      }
    }
  } catch (e) {}
  // 端口过期时重探一次
  port = await pingRevealBridge();
  if (!port) return false;
  try {
    const res = await fetch("http://127.0.0.1:" + port + "/api/reveal?path=" + q, {
      method: "GET", cache: "no-store", mode: "cors"
    });
    if (!res.ok) return false;
    const j = await res.json().catch(() => ({ ok: true }));
    return !!(j && j.ok !== false);
  } catch (e) {
    return false;
  }
}

async function deleteViaBridge(paths) {
  const list = Array.isArray(paths) ? paths.filter(Boolean) : [];
  if (!list.length) return { ok: false, deleted: [], errors: [{ error: "empty" }] };
  let port = Number(DATA.reveal_port || 0);
  if (!port) port = await pingRevealBridge();
  if (!port) return null;
  try {
    const res = await fetch("http://127.0.0.1:" + port + "/api/delete", {
      method: "POST",
      cache: "no-store",
      mode: "cors",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paths: list })
    });
    const j = await res.json().catch(() => null);
    if (j && Array.isArray(j.deleted)) {
      setRevealBanner(true);
      return j;
    }
  } catch (e) {}
  return null;
}

function lookupAsset(assetPath) {
  const raw = String(assetPath || "");
  let norm = raw.replace(/\\/g, "/");
  const assets = DATA.assets || {};
  if (assets[raw]) return assets[raw];
  if (assets[norm]) return assets[norm];
  // 修坏绝对路径：.../pmem-art/assets/x → assets/x
  const markers = ["assets/", "docs/", ".memory-art/", ".cursor/"];
  const low = norm.toLowerCase();
  for (const m of markers) {
    const idx = low.indexOf(m);
    if (idx > 0) {
      const trimmed = norm.slice(idx);
      if (assets[trimmed]) return assets[trimmed];
      norm = trimmed;
      break;
    }
  }
  let soft = null;
  for (const [k, v] of Object.entries(assets)) {
    const kn = String(k).replace(/\\/g, "/");
    const vn = v ? String(v.path || "").replace(/\\/g, "/") : "";
    if (kn === norm || vn === norm) return v;
    // 同父目录+文件名唯一命中时接受（避免 Users/... 前缀差）
    if (pathMetaKeyMatch(kn, norm) || (vn && pathMetaKeyMatch(vn, norm))) {
      if (soft && soft !== v) { soft = null; break; } // 歧义则放弃软匹配
      soft = v;
    }
  }
  return soft;
}

function updateBatchCount() {
  const el = document.getElementById("batchCount");
  if (el) el.textContent = "已选 " + _selectedPaths.size;
  const btn = document.getElementById("btnBatchMode");
  if (btn) {
    btn.classList.toggle("batch-on", !!state.batchMode);
    btn.textContent = state.batchMode ? "🗑️ 退出批量" : "🗑️ 批量删除";
  }
  document.body.classList.toggle("batch-mode", !!state.batchMode);
}

function setBatchMode(on) {
  state.batchMode = !!on;
  if (!state.batchMode) {
    _selectedPaths.clear();
    _lastClickedIdx = -1;
  }
  updateBatchCount();
  scheduleVirtualPaint(true);
  showToast(state.batchMode ? "已进入批量删除：左上角勾选 · Ctrl+A · Shift 片选" : "已退出批量删除");
}

function clearSelection() {
  _selectedPaths.clear();
  _lastClickedIdx = -1;
  updateBatchCount();
  scheduleVirtualPaint(true);
}

function selectAllFiltered() {
  _galleryAssets.forEach(a => { if (a && a.path) _selectedPaths.add(a.path); });
  updateBatchCount();
  scheduleVirtualPaint(true);
  showToast("已全选当前筛选 " + _selectedPaths.size + " 张");
}

function toggleSelectPath(path, opts) {
  opts = opts || {};
  const idx = (opts.idx != null) ? opts.idx : _galleryAssets.findIndex(a => a.path === path);
  if (opts.shiftKey && _lastClickedIdx >= 0 && idx >= 0) {
    const a = Math.min(_lastClickedIdx, idx);
    const b = Math.max(_lastClickedIdx, idx);
    for (let i = a; i <= b; i++) {
      const p = _galleryAssets[i] && _galleryAssets[i].path;
      if (p) _selectedPaths.add(p);
    }
  } else if (_selectedPaths.has(path)) {
    _selectedPaths.delete(path);
  } else {
    _selectedPaths.add(path);
  }
  if (idx >= 0) _lastClickedIdx = idx;
  updateBatchCount();
  scheduleVirtualPaint(true);
}

function removeAssetsFromIndex(paths) {
  const set = new Set((paths || []).map(p => String(p).replace(/\\/g, "/")));
  const assets = DATA.assets || {};
  Object.keys(assets).forEach(k => {
    const nk = String(k).replace(/\\/g, "/");
    const pk = String((assets[k] && assets[k].path) || "").replace(/\\/g, "/");
    if (set.has(nk) || set.has(pk) || set.has(k)) delete assets[k];
  });
  if (Array.isArray(DATA.index_images)) {
    DATA.index_images = DATA.index_images.filter(x => {
      const p = String((x && x.path) || "").replace(/\\/g, "/");
      return !set.has(p);
    });
  }
  paths.forEach(p => _selectedPaths.delete(p));
  if (state.lbPath && set.has(String(state.lbPath).replace(/\\/g, "/"))) {
    closeViewer();
    const lb = document.getElementById("lightbox");
    if (lb) lb.classList.remove("open");
    state.lbPath = "";
  }
  renderHeaderAndSidebar();
  renderStage();
}

async function deleteAssetPaths(paths, { confirmMsg } = {}) {
  const list = Array.from(new Set((paths || []).filter(Boolean)));
  if (!list.length) {
    showToast("没有可删除的图");
    return false;
  }
  if (location.protocol === "file:") {
    const port = await pingRevealBridge();
    if (port) {
      const ok = window.confirm(
        "当前是 file:// 打开，浏览器常会拦截删除请求。\n点「确定」改用本地 http 工作台后再删（推荐）。\n点「取消」留在本页。"
      );
      if (ok) {
        location.replace("http://127.0.0.1:" + port + "/art-atlas.html");
        return false;
      }
    }
  }
  const msg = confirmMsg || ("确认移入垃圾桶 " + list.length + " 张？\n工作台将不可见；文件在 .memory-art/_trash/，可手动找回。\n只有你在垃圾桶里再删掉才永久消失。");
  if (!window.confirm(msg)) return false;
  showToast("正在移入垃圾桶…");
  const result = await deleteViaBridge(list);
  if (result && Array.isArray(result.deleted) && result.deleted.length) {
    removeAssetsFromIndex(result.deleted.concat(list));
    const n = result.deleted.length;
    const errN = (result.errors || []).length;
    showToast(errN
      ? ("已移入垃圾桶 " + n + " 张，失败 " + errN + " · 点「垃圾桶」可打开找回")
      : ("🗑️ 已移入垃圾桶 " + n + " 张 · 点工具栏「垃圾桶」可打开找回"));
    return true;
  }
  // 桥接有响应但未删成：展示真实错误（不是「未连通」）
  if (result && Array.isArray(result.deleted)) {
    const errs = (result.errors || [])
      .map(e => String((e && (e.error || e.message)) || "").trim())
      .filter(Boolean);
    const detail = errs.length ? errs.slice(0, 3).join("；") : "文件未找到或无法移动";
    showToast("移入垃圾桶失败：" + detail);
    setRevealBanner(true);
    return false;
  }
  // 桥接不可用：下载「移入垃圾桶」脚本
  try {
    downloadDeleteHelper(list.map(absAssetPath));
  } catch (e) {}
  setRevealBanner(false);
  showToast("垃圾桶服务未连通。已下载脚本；或先 python pmem_art.py atlas，再用 http://127.0.0.1:端口/art-atlas.html 打开");
  return false;
}

/** 打开工作台垃圾桶目录（删除的图在这里，可手动挪回原路径） */
window.openTrashFolder = async function() {
  showToast("正在打开垃圾桶…");
  const ok = await revealViaBridge(".memory-art/_trash");
  if (ok) {
    showToast("♻️ 已打开垃圾桶：把文件挪回原相对路径即可恢复");
    return;
  }
  showToast("定位服务未连通。请先 python pmem_art.py atlas，再手动打开 .memory-art/_trash/");
};

/** 打开教学素材目录（git 跟踪，不可工作台删除） */
window.openTeachFolder = async function() {
  const base = ((DATA.workbench_guide || {}).base_dir) || "docs/workbench_guide";
  showToast("正在打开教学文件夹…");
  const ok = await revealViaBridge(base);
  if (ok) {
    showToast("📁 已打开教学素材：" + base);
    return;
  }
  showToast("定位服务未连通。请先 python pmem_art.py atlas，再打开 " + base);
};

window.deleteSelectedAssets = function() {
  return deleteAssetPaths(Array.from(_selectedPaths), {
    confirmMsg: "确认把选中的 " + _selectedPaths.size + " 张移入垃圾桶？\n工作台不可见；.memory-art/_trash/ 可找回。只有在垃圾桶里再删才永久消失。"
  });
};

window.deleteOneAsset = function(relPath) {
  return deleteAssetPaths([relPath], {
    confirmMsg: "确认移入垃圾桶？\n" + relPath + "\n可在 .memory-art/_trash/ 找回。"
  });
};

/** 在系统访达 / 资源管理器中打开所在文件夹（并选中该图）——绝不跳网页目录 */
window.revealInFolder = async function(relPath) {
  const abs = absAssetPath(relPath);
  showToast("正在打开本地文件夹…");
  const ok = await revealViaBridge(relPath);
  if (ok) {
    showToast("📁 已在资源管理器中定位并选中该图");
    return;
  }
  try { downloadRevealHelper(abs); } catch (e2) {}
  setRevealBanner(false);
  showToast("定位服务未连通。已下载「打开图片位置」脚本，双击即可在资源管理器选中该图（不会再跳网页）");
};

function renderPromptTraceHtml(info) {
  const sid = info && info.converge_session_id;
  const sess = sid && (DATA.converge_sessions || {})[sid];
  if (!sess || !Array.isArray(sess.rounds) || !sess.rounds.length) {
    const single = (info && info.prompt) || "";
    if (!single) {
      return `<div style="color:var(--text-dim);font-size:12px;">暂无闭环提示词履历（非 converge 产出或会话未入库）</div>`;
    }
    return `<div class="prompt-trace">
      <div class="prompt-trace-head">单条 Prompt（无多轮会话）</div>
      <div class="round-card current">
        <div class="round-prompt">${esc(single)}</div>
        <div class="round-actions">
          <button class="btn-copy" onclick='copyText(${JSON.stringify(single)}, "Prompt")'>📋 复制 Prompt</button>
        </div>
      </div>
    </div>`;
  }
  const curRound = info.converge_round;
  const head = `会话 ${esc(sess.session_id)} · ${esc(sess.module || "")} · 合格线 ≥${esc(String(sess.threshold || 9.5))} · ${sess.rounds.length} 轮`;
  const goal = sess.goal ? `<div style="font-size:12px;color:var(--text-muted);">目标：${esc(sess.goal)}</div>` : "";
  const cards = sess.rounds.map((r, ri) => {
    const isCur = curRound != null && Number(r.round) === Number(curRound);
    const score = (r.score != null && r.score !== "") ? Number(r.score).toFixed(2) : "—";
    const pass = r.passed ? "达标" : "未达标";
    const dims = r.dims_parsed && Object.keys(r.dims_parsed).length
      ? Object.entries(r.dims_parsed).map(([k, v]) => `${k}:${v}`).join(" · ")
      : "";
    const prevR = ri > 0 ? sess.rounds[ri - 1] : null;
    const pack = stripPrevCritiqueFromPrompt(r.prompt || "", prevR ? { defects: prevR.defects || "" } : null);
    const own = formatOwnCritiqueHtml({
      passed: r.passed, defects: r.defects || "", next_fix: r.next_fix || ""
    }, { noteCls: "round-meta" });
    return `<div class="round-card${isCur ? " current" : ""}">
      <div class="round-top">
        <span class="round-title">${esc(r.round_label || ("第 " + r.round + " 轮"))}${isCur ? " · 当前图" : ""}</span>
        <span class="round-score">${score} · ${pass}</span>
      </div>
      ${r.generated_at ? `<div class="round-meta">时间 ${esc(r.generated_at)}</div>` : ""}
      ${r.strengths ? `<div class="round-meta">优点：${esc(r.strengths)}</div>` : ""}
      ${own}
      ${dims ? `<div class="round-meta">${esc(dims)}</div>` : ""}
      <div class="round-prompt">${esc(pack.main || "（本轮未记录 prompt）")}</div>
      <div class="round-actions">
        <button class="btn-copy" onclick='copyText(${JSON.stringify(pack.main || r.prompt || "")}, "第${r.round}轮 Prompt")'>📋 复制本轮 Prompt</button>
        ${r.image ? `<button class="btn-copy" onclick='openViewer(${JSON.stringify(r.image)})'>🔍 看本轮图</button>` : ""}
      </div>
    </div>`;
  }).join("");
  return `<div class="prompt-trace">
    <div class="prompt-trace-head"><b style="color:var(--text-main);">提示词优化履历</b><span>${head}</span>${goal}</div>
    ${cards}
  </div>`;
}

let _viewerCompare = false;
let _viewerAnchorPath = ""; // 当前终稿槽位（设为最终交稿的目标）
let _viewerSessionId = "";
let _viewerNavPaths = []; // 当前放大可左右切的图链（教学课内 / 会话轮次 / 主画廊）
let _viewerMetaByPath = {}; // path -> {prompt,score,dims,defects,next_fix,...}
let _viewerFromTeach = false;
let _viewerIgnoreCloseUntil = 0; // 打开当下这一击会落到遮罩上，短时忽略关闭

function normViewerPath(p) {
  return String(p || "").replace(/\\/g, "/");
}
function setViewerNav(paths, metaMap) {
  const seen = new Set();
  const out = [];
  (paths || []).forEach(p => {
    if (!p) return;
    const k = normViewerPath(p);
    if (seen.has(k)) return;
    seen.add(k);
    out.push(p);
  });
  _viewerNavPaths = out;
  _viewerMetaByPath = metaMap || {};
}
function galleryNavPaths() {
  return (_galleryAssets || []).map(a => a.path).filter(Boolean);
}
/** 从第 1 轮 Prompt 里抽出「分析原图/参考图不足」段，挂回原图卡 */
function extractRefCritiqueFromPrompt(prompt) {
  const text = String(prompt || "").replace(/\r\n/g, "\n");
  if (!text.trim()) return "";
  const headRe = /^(分析图片不足|分析不足|原图不足|参考图不足|上一轮不足|上轮不足|前一张不足|图片不足|评审不足)[:：]\s*/i;
  const lines = text.split("\n");
  const chunks = [];
  let capturing = false;
  let buf = [];
  const flush = () => {
    const s = buf.join("\n").trim();
    if (s) chunks.push(s);
    buf = [];
  };
  lines.forEach(line => {
    const t = line.trim();
    const m = t.match(headRe);
    if (m) {
      flush();
      const rest = t.slice(m[0].length).trim();
      if (rest) buf.push(rest);
      capturing = true;
      return;
    }
    if (!capturing) return;
    if (/^(【|约束[:：]|Round\b|第\s*\d|PROMPT\b|必须|禁止|Warm-Start)/i.test(t) && buf.length) {
      flush();
      capturing = false;
      return;
    }
    if (t) buf.push(t);
  });
  flush();
  return chunks.join("；");
}

/** 原图卡文案：ref_analysis > R1 里抽出的原图不足 > 开跑目标 */
function enrichOriginalMeta(sess) {
  const out = { role: "original", label: "原图", round_label: "原图", defects: "", next_fix: "", prompt: "" };
  if (!sess) return out;
  const analysis = String(sess.ref_analysis || "").trim();
  const r1 = (sess.rounds || []).find(r => r && Number(r.round) === 1) || (sess.rounds || [])[0] || null;
  const extracted = r1 ? extractRefCritiqueFromPrompt(r1.prompt || "") : "";
  const goal = String(sess.goal || "").trim();
  out.defects = analysis || extracted || "";
  out.prompt = analysis || "";
  if (goal) {
    out.next_fix = "据此开跑：" + goal;
  } else if (r1 && (r1.round_label || r1.round != null)) {
    out.next_fix = "据此进入 " + (r1.round_label || ("第 " + r1.round + " 轮"));
  }
  return out;
}

function sessionNavAndMeta(sess) {
  const paths = [];
  const meta = {};
  if (!sess) return { paths, meta };
  const put = (path, payload) => {
    if (!path) return;
    paths.push(path);
    meta[normViewerPath(path)] = Object.assign({}, meta[normViewerPath(path)] || {}, payload || {});
  };
  const origMeta = enrichOriginalMeta(sess);
  if (sess.ref_image) put(sess.ref_image, origMeta);
  (sess.reference_image_paths || []).forEach(rp => {
    if (rp && rp !== sess.ref_image) put(rp, Object.assign({}, origMeta));
  });
  (sess.rounds || []).forEach(r => {
    if (!r || !r.image) return;
    put(r.image, {
      role: "process",
      round: r.round,
      round_label: r.round_label || ("第 " + r.round + " 轮"),
      prompt: r.prompt || "",
      defects: r.defects || "",
      next_fix: r.next_fix || "",
      score: r.score,
      passed: r.passed,
      dims: r.dims_parsed || r.dims || {}
    });
  });
  const fin = sess.final_image || sess.winner_image;
  if (fin) {
    const k = normViewerPath(fin);
    if (!meta[k]) put(fin, { role: "final", label: "终稿", round_label: "终稿" });
    else meta[k] = Object.assign({}, meta[k], { role: meta[k].role || "final", label: meta[k].label || "终稿" });
  }
  return { paths, meta };
}
function teachNavAndMeta() {
  const lessons = guideLessons();
  const lesson = lessons.find(l => l.id === _teachId) || lessons[0];
  const paths = [];
  const meta = {};
  if (!lesson) return { paths, meta };
  const rounds = Array.isArray(lesson.rounds) ? lesson.rounds : [];
  (lesson.examples || []).forEach(ex => {
    if (!ex || !ex.path) return;
    const e = teachEnrichExample(ex, rounds);
    paths.push(e.path);
    meta[normViewerPath(e.path)] = {
      role: e.role,
      label: e.label || teachRoleLabel(e.role),
      round: e.round,
      round_label: e.label || teachRoleLabel(e.role) || (e.round != null ? ("第 " + e.round + " 轮") : ""),
      prompt: e.prompt || "",
      defects: e.defects || "",
      next_fix: e.next_fix || "",
      score: e.score,
      passed: e.passed,
      dims: e.dims || {}
    };
  });
  return { paths, meta };
}
/** 路径对齐：优先全路径；其次同父目录+文件名。禁止只用文件名（r1.png 会串课/串会话） */
function pathMetaKeyMatch(a, b) {
  const na = normViewerPath(a);
  const nb = normViewerPath(b);
  if (!na || !nb) return false;
  if (na === nb) return true;
  const pa = na.split("/");
  const pb = nb.split("/");
  if (pa.length >= 2 && pb.length >= 2) {
    return pa.slice(-2).join("/") === pb.slice(-2).join("/");
  }
  return false;
}
function lookupViewerMeta(path) {
  const key = normViewerPath(path);
  if (_viewerMetaByPath[key]) return _viewerMetaByPath[key];
  for (const [k, v] of Object.entries(_viewerMetaByPath)) {
    if (pathMetaKeyMatch(k, key)) return v;
  }
  const info = lookupAsset(path) || { path };
  const sess = sessionOfAsset(info);
  if (sess) {
    const sn = sessionNavAndMeta(sess);
    if (sn.meta[key]) return sn.meta[key];
    for (const [k, v] of Object.entries(sn.meta)) {
      if (pathMetaKeyMatch(k, key)) return v;
    }
    // 按会话轮次精确匹配 image 字段
    for (const r of (sess.rounds || [])) {
      if (r && r.image && pathMetaKeyMatch(r.image, key)) {
        return {
          role: r.passed ? "final" : "process",
          round: r.round,
          round_label: r.round_label || ("第 " + r.round + " 轮"),
          prompt: r.prompt || "",
          defects: r.defects || "",
          next_fix: r.next_fix || "",
          score: r.score,
          passed: r.passed,
          dims: r.dims_parsed || r.dims || {}
        };
      }
    }
  }
  return null;
}
/** 上一张的「分析不足」只属于上一张；从本张 Prompt 里剥掉，避免挂错图下 */
function stripPrevCritiqueFromPrompt(prompt, prevMeta) {
  let text = String(prompt || "").replace(/\r\n/g, "\n").trim();
  if (!text) return { main: "", hadPrev: false };
  const prevDefects = String((prevMeta && prevMeta.defects) || "").trim();
  const lines = text.split("\n");
  const keep = [];
  let hadPrev = false;
  const headRe = /^(分析图片不足|分析不足|上一轮不足|上轮不足|前一张不足|图片不足|评审不足)[:：]/i;
  lines.forEach(line => {
    const t = line.trim();
    if (!t) { keep.push(line); return; }
    if (headRe.test(t)) { hadPrev = true; return; }
    if (prevDefects && t.indexOf(prevDefects) >= 0 && /不足|改点|修正|未达标/.test(t) && t.length <= prevDefects.length + 48) {
      hadPrev = true;
      return;
    }
    keep.push(line);
  });
  let main = keep.join("\n").replace(/^\n+/, "").replace(/\n+$/, "").trim();
  // 整段 Prompt 若以「分析…不足」开头且无换行，整段剥掉
  if (headRe.test(main) && main.indexOf("\n") < 0) {
    hadPrev = true;
    main = "";
  }
  return { main, hadPrev };
}
function formatOwnCritiqueHtml(m, opts) {
  opts = opts || {};
  const noteCls = opts.noteCls || "iv-meta-note";
  const role = teachRoleClass(opts.role || m.role || "");
  const passed = !!m.passed;
  const defects = String(m.defects || "").trim();
  const nextFix = String(m.next_fix || "").trim();
  // 原图：分析/不足挂在原图自己下面，说明为何要出下一张
  if (role === "original") {
    const parts = [];
    if (defects) {
      parts.push(`<div class="${noteCls}" style="color:#fda4af;"><b>原图不足：</b>${esc(defects)}</div>`);
    }
    if (nextFix) {
      parts.push(`<div class="${noteCls}" style="color:var(--teal);"><b>为何要出下一张：</b>${esc(nextFix)}</div>`);
    }
    if (!parts.length && opts.allowEmptyHint) {
      parts.push(`<div class="${noteCls}" style="color:var(--text-dim);">（原图未写分析样例）</div>`);
    }
    return parts.join("");
  }
  // 达标图：不把「已清/已达标」再写成「不足」挂在终稿下
  if (passed) {
    const soft = (!defects || /已清|已达标|可交稿|无明显/.test(defects))
      ? ""
      : `<div class="${noteCls}" style="color:var(--text-muted);">本图余注：${esc(defects)}</div>`;
    return `${soft}<div class="${noteCls}" style="color:#6ee7b7;">本图结论：已达标</div>`;
  }
  const parts = [];
  if (defects) {
    parts.push(`<div class="${noteCls}" style="color:#fda4af;"><b>本图不足：</b>${esc(defects)}</div>`);
  }
  if (nextFix) {
    parts.push(`<div class="${noteCls}" style="color:var(--teal);"><b>给下一张的改点：</b>${esc(nextFix)}</div>`);
  }
  return parts.join("");
}
function prevMetaInNav(path) {
  const navPaths = _viewerNavPaths.length ? _viewerNavPaths : galleryNavPaths();
  const cur = normViewerPath(path);
  let idx = navPaths.findIndex(p => normViewerPath(p) === cur);
  if (idx < 0) {
    const base = cur.split("/").pop();
    idx = navPaths.findIndex(p => normViewerPath(p).split("/").pop() === base);
  }
  if (idx <= 0) return null;
  return lookupViewerMeta(navPaths[idx - 1]);
}
function renderViewerMeta(info) {
  // 放大层只摘要：轮次 + 总分 + 六维；Prompt/不足留给「详情 · 进化对照」
  const panel = document.getElementById("ivMetaPanel");
  const viewer = document.getElementById("imgViewer");
  if (!panel) return;
  const path = (info && info.path) || state.lbPath || "";
  const m = lookupViewerMeta(path) || {};
  const scoreVal = (m.score != null && m.score !== "") ? m.score
    : (info && info.score != null && info.score !== "" ? info.score : null);
  const hasScore = scoreVal != null && scoreVal !== "";
  const dims = (m.dims && typeof m.dims === "object" && Object.keys(m.dims).length)
    ? m.dims
    : ((info && info.dims) || {});
  const hasDims = dims && typeof dims === "object" && Object.keys(dims).length;
  const roundNum = (m.round != null) ? m.round
    : (info && info.converge_round != null ? info.converge_round : null);
  const head = m.round_label
    || (roundNum != null ? ("第 " + roundNum + " 轮") : "")
    || m.label
    || "";
  const passed = (m.passed != null) ? !!m.passed : !!(info && info.passed);
  if (!hasScore && !hasDims && !head) {
    panel.innerHTML = "";
    if (viewer) viewer.classList.remove("meta-on");
    return;
  }
  if (viewer) viewer.classList.add("meta-on");
  const scoreLine = hasScore
    ? `<div class="iv-meta-score">总分 ${Number(scoreVal).toFixed(2)}${passed ? " · 达标" : " · 未达标"}</div>`
    : "";
  const navPaths = _viewerNavPaths.length ? _viewerNavPaths : galleryNavPaths();
  const idx = navPaths.findIndex(p => normViewerPath(p) === normViewerPath(path));
  const navHint = (idx >= 0 && navPaths.length > 1)
    ? `<div class="iv-meta-navhint">← → ${idx + 1}/${navPaths.length} · Prompt/不足见「详情 · 进化对照」</div>`
    : `<div class="iv-meta-navhint">Prompt / 不足 / 改点 → 点「详情 · 进化对照」</div>`;
  panel.innerHTML = `
    <div class="iv-meta-head">
      <b style="color:var(--text-main);">${esc(head || "评分摘要")}</b>
      ${scoreLine}
    </div>
    ${formatDimsHtml(dims, "iv-meta-dim")}
    ${navHint}
  `;
}

function sessionOfAsset(info) {
  const sid = info && info.converge_session_id;
  if (sid && (DATA.converge_sessions || {})[sid]) return DATA.converge_sessions[sid];
  // 兜底：按路径反查会话（有些过程图没打上 session_id，或终稿槽被换过）
  const key = normViewerPath((info && info.path) || "");
  if (!key) return null;
  const sessions = DATA.converge_sessions || {};
  for (const sess of Object.values(sessions)) {
    if (!sess) continue;
    if (pathMetaKeyMatch(sess.final_image || "", key) || pathMetaKeyMatch(sess.winner_image || "", key)) return sess;
    if (pathMetaKeyMatch(sess.ref_image || "", key)) return sess;
    if ((sess.reference_image_paths || []).some(p => pathMetaKeyMatch(p, key))) return sess;
    if ((sess.rounds || []).some(r => r && pathMetaKeyMatch(r.image || "", key))) return sess;
  }
  return null;
}

/** 详情/教学卡片用的可显示 src；修坏路径、尊重 exists、优先可显示图 */
function resolveMediaSrc(path, opts) {
  opts = opts || {};
  const preferThumb = opts.preferThumb !== false;
  const sessionId = opts.sessionId || "";
  let raw = String(path || "").replace(/\\/g, "/").trim();
  if (!raw) return { src: "", path: "", missing: true };
  // 修：Users/xxx/.../pmem-art/assets/... → assets/...
  const markers = ["assets/", "docs/", ".memory-art/", ".cursor/"];
  let p = raw;
  const low = p.toLowerCase();
  for (const m of markers) {
    const idx = low.indexOf(m);
    if (idx > 0) { p = p.slice(idx); break; }
  }
  if (/^[A-Za-z]:\//.test(p)) {
    const root = String(DATA.root || "").replace(/\\/g, "/").replace(/\/$/, "").toLowerCase();
    const lowP = p.toLowerCase();
    if (root && lowP.indexOf(root + "/") === 0) p = p.slice(root.length + 1);
  }
  const alive = (info) => !!(info && info.exists !== false);
  let info = lookupAsset(p) || lookupAsset(raw) || null;
  // 索引里有但磁盘已删：当作未命中，继续找同名活文件
  if (info && !alive(info)) info = null;
  if (!info) {
    const base = p.split("/").pop();
    const hits = Object.keys(DATA.assets || {}).filter(k => {
      const a = DATA.assets[k];
      return alive(a) && normViewerPath(k).split("/").pop() === base;
    });
    if (hits.length === 1) {
      info = DATA.assets[hits[0]];
    } else if (sessionId && hits.length > 1) {
      const scoped = hits.filter(k => String((DATA.assets[k] || {}).converge_session_id || "") === String(sessionId));
      if (scoped.length === 1) info = DATA.assets[scoped[0]];
      else if (scoped.length > 1) {
        // 同会话多条同名时：优先终稿可见槽
        const finals = scoped.filter(k => !isWorkbenchHiddenAsset(DATA.assets[k]) && assetPlate(DATA.assets[k]) === "final");
        if (finals.length === 1) info = DATA.assets[finals[0]];
      }
    }
  }
  if (info) {
    if (!alive(info)) {
      return { src: "", path: info.path || p, missing: true, info };
    }
    const full = bustSrc(info) || assetSrc(info) || "";
    const thumb = preferThumb ? (thumbSrc(info) || "") : "";
    // thumb 与原图不同时带上 full，供 onerror 回退
    const src = (thumb && thumb !== full ? thumb : "") || full;
    return { src, full: full || src, path: info.path || p, missing: !src, info };
  }
  // 不在索引里：仍尝试相对路径（磁盘上可能有；404 由 onerror 兜底）
  return { src: p, full: p, path: p, missing: false, info: null };
}

function resolveRefPath(info) {
  const sess = sessionOfAsset(info);
  if (sess) {
    if (sess.ref_image) return sess.ref_image;
    const refs = sess.reference_image_paths || [];
    if (refs.length) return refs[0];
    const rounds = sess.rounds || [];
    for (const r of rounds) {
      const rr = (r && r.reference_image_paths) || [];
      if (rr.length) return rr[0];
    }
  }
  return "";
}

function bustSrc(info) {
  const base = assetSrc(info) || "";
  if (!base) return "";
  const m = (info && (info.mtime || info._bust)) || Date.now();
  return base + (base.includes("?") ? "&" : "?") + "t=" + encodeURIComponent(String(m));
}

function updateViewerChrome(info) {
  const refPath = resolveRefPath(info);
  const cmpBtn = document.getElementById("ivCompare");
  if (cmpBtn) {
    cmpBtn.disabled = !refPath;
    cmpBtn.classList.toggle("disabled", !refPath);
    cmpBtn.title = refPath ? ("并列对比参考图：" + refPath) : "无参考原图";
    cmpBtn.textContent = _viewerCompare && refPath ? "关闭并列" : "并列参考图";
  }
  const detailBtn = document.getElementById("ivDetail");
  const sess = sessionOfAsset(info);
  const canDetail = !!(sess && Array.isArray(sess.rounds) && sess.rounds.length) || !!resolveRefPath(info);
  if (detailBtn) {
    detailBtn.title = canDetail
      ? ("教学同款对照 · " + ((sess && sess.session_id) || "") + " · " + ((sess && sess.rounds && sess.rounds.length) || 0) + " 轮")
      : "打开详情（无闭环会话时仍显示本图信息）";
  }
  const viewer = document.getElementById("imgViewer");
  if (viewer) {
    viewer.classList.toggle("compare-on", !!(_viewerCompare && refPath));
    viewer.classList.remove("evolve-on");
  }
  const refImg = document.getElementById("ivRefImg");
  if (refImg) {
    if (refPath) {
      const refInfo = lookupAsset(refPath) || { path: refPath };
      refImg.src = bustSrc(refInfo) || String(refPath).replace(/\\/g, "/");
    } else {
      refImg.removeAttribute("src");
    }
  }
  const paths = _viewerNavPaths.length ? _viewerNavPaths : galleryNavPaths();
  const cur = normViewerPath(state.lbPath);
  let idx = paths.findIndex(p => normViewerPath(p) === cur);
  if (idx < 0 && state.lbPath) {
    const base = cur.split("/").pop();
    idx = paths.findIndex(p => normViewerPath(p).split("/").pop() === base);
  }
  const atStart = idx <= 0;
  const atEnd = idx < 0 || idx >= paths.length - 1;
  ["ivPrev", "ivPrevBtn"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.disabled = atStart;
  });
  ["ivNext", "ivNextBtn"].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.disabled = atEnd;
  });
}

let _detailPath = "";

function buildLineageExamples(info) {
  const examples = [];
  const sess = sessionOfAsset(info);
  const sn = sessionNavAndMeta(sess);
  const sid = (sess && sess.session_id) || (info && info.converge_session_id) || "";
  const seen = new Set();
  const pushCard = (path, patch) => {
    if (!path) return;
    const media = resolveMediaSrc(path, { preferThumb: true, sessionId: sid });
    const key = normViewerPath(media.path || path);
    if (seen.has(key)) {
      const hit = examples.find(e => normViewerPath(e.path) === key);
      if (hit && patch) {
        Object.assign(hit, patch);
        // 合并时保留已有可用 src；若仍空则补
        if (!hit.src && media.src) {
          hit.src = media.src;
          hit.full = media.full || media.src;
          hit.missing = !!media.missing;
        }
      }
      return;
    }
    seen.add(key);
    const meta = sn.meta[key] || sn.meta[normViewerPath(path)] || lookupViewerMeta(media.path || path) || {};
    const base = {
      path: media.path || path,
      role: (patch && patch.role) || meta.role || "process",
      label: (patch && patch.label) || meta.round_label || meta.label || PathName(media.path || path),
      prompt: meta.prompt || "",
      defects: meta.defects || "",
      next_fix: meta.next_fix || "",
      score: meta.score,
      passed: meta.passed,
      dims: meta.dims || {},
      round: meta.round,
      src: media.src || "",
      full: media.full || media.src || "",
      missing: !!media.missing || !media.src
    };
    // patch 后写，但绝不能把 src 覆盖成 undefined
    const merged = Object.assign({}, base, patch || {});
    if (!merged.src) {
      merged.src = base.src;
      merged.full = base.full;
      merged.missing = base.missing;
    }
    if (!merged.full) merged.full = merged.src || base.full;
    if (!merged.path) merged.path = base.path;
    examples.push(merged);
  };
  if (sess) {
    const ref = resolveRefPath(info) || sess.ref_image
      || ((sess.reference_image_paths || [])[0] || "");
    if (ref) {
      const om = enrichOriginalMeta(sess);
      pushCard(ref, {
        role: "original",
        label: "原图",
        prompt: om.prompt || "",
        defects: om.defects || "",
        next_fix: om.next_fix || ""
      });
    }
    (sess.rounds || []).forEach((r, ri) => {
      if (!r || !r.image) return;
      const isLast = ri === sess.rounds.length - 1;
      const fin = sess.final_image || sess.winner_image;
      const isFin = fin && pathMetaKeyMatch(fin, r.image);
      pushCard(r.image, {
        role: (r.passed && (isLast || isFin)) ? "final" : "process",
        label: r.round_label || ("过程 R" + r.round),
        prompt: r.prompt || "",
        defects: r.defects || "",
        next_fix: r.next_fix || "",
        score: r.score,
        passed: r.passed,
        dims: r.dims_parsed || r.dims || {},
        round: r.round
      });
    });
    const fin = sess.final_image || sess.winner_image;
    if (fin) pushCard(fin, { role: "final", label: "终稿" });
  } else {
    pushCard(info.path || state.lbPath, {
      role: assetPlate(info) === "final" ? "final" : "process",
      label: assetPlate(info) === "final" ? "定稿" : "当前图",
      prompt: info.prompt || "",
      score: info.score,
      defects: info.defects || "",
      next_fix: info.next_fix || "",
      dims: info.dims || {}
    });
    const ref = resolveRefPath(info);
    if (ref) pushCard(ref, { role: "original", label: "原图" });
  }
  const orig = examples.filter(e => teachRoleClass(e.role) === "original");
  const rest = examples.filter(e => teachRoleClass(e.role) !== "original");
  return { examples: orig.concat(rest), sess };
}

function renderDetailPipelineHtml(examples, sess) {
  if (!examples.length) {
    return `<div class="detail-empty">这张图没有可展示的进化对照（无原图/过程轮次）。仍可点「技术信息」看路径与记忆。</div>`;
  }
  const anchor = _viewerAnchorPath
    || (sess && (sess.final_image || sess.winner_image))
    || state.lbPath
    || _detailPath;
  const sid = (sess && sess.session_id) || "";
  const parts = [];
  examples.forEach((e, i) => {
    const role = teachRoleClass(e.role);
    if (i > 0) parts.push(`<div class="teach-arrow" aria-hidden="true">→</div>`);
    const hasScore = e.score != null && e.score !== "";
    const scoreLine = hasScore
      ? `<div class="teach-score-line">总分 ${esc(String(Number(e.score).toFixed(2)))}${e.passed ? " · 达标" : " · 未达标"}</div>`
      : "";
    const prevEx = i > 0 ? examples[i - 1] : null;
    const pack = stripPrevCritiqueFromPrompt(e.prompt || "", prevEx);
    const hasProcessAfter = examples.slice(i + 1).some(x => {
      const rr = teachRoleClass(x.role);
      return rr === "process" || rr === "final";
    });
    // 原图：不展示误导性的「无 Prompt」；分析文案走 noteLine（原图不足 / 为何要出下一张）
    let promptLine = "";
    if (role === "original") {
      const rawP = String(pack.main || e.prompt || "").trim();
      // 与「原图不足」同文时只留 note，避免重复
      if (rawP && rawP !== String(e.defects || "").trim()) {
        promptLine = `<div class="teach-prompt">${esc(rawP)}</div>`;
      }
    } else if (pack.main) {
      promptLine = `<div class="teach-prompt">${esc(pack.main)}</div>`;
    } else {
      promptLine = `<div class="teach-note">（无 Prompt）</div>`;
    }
    const noteLine = formatOwnCritiqueHtml(e, {
      noteCls: "teach-note",
      role: e.role,
      allowEmptyHint: role === "original" && hasProcessAfter
    });
    const actions = [];
    if (role === "original" && (e.defects || e.next_fix || e.prompt)) {
      const blob = [e.defects ? ("原图不足：" + e.defects) : "", e.next_fix || "", e.prompt || ""].filter(Boolean).join("\n");
      actions.push(`<button type="button" class="btn-copy" onclick='event.stopPropagation(); copyText(${JSON.stringify(blob)}, "原图分析")'>📋 原图分析</button>`);
    } else if (pack.main || e.prompt) {
      actions.push(`<button type="button" class="btn-copy" onclick='event.stopPropagation(); copyText(${JSON.stringify(pack.main || e.prompt || "")}, "Prompt")'>📋 Prompt</button>`);
    }
    actions.push(`<button type="button" class="btn-copy" onclick='event.stopPropagation(); openViewer(${JSON.stringify(e.path)}, { keepAnchor: true })'>🔍 放大</button>`);
    if (role === "process" && sid) {
      actions.push(`<button type="button" class="btn-copy" style="background:var(--success-bg);color:#6ee7b7;border-color:rgba(16,185,129,0.45);" onclick='event.stopPropagation(); promoteAsFinal(${JSON.stringify(e.path)}, ${JSON.stringify(sid)}, ${JSON.stringify(e.round)}, ${JSON.stringify(anchor)})'>设置为最终交稿</button>`);
    }
    const isCur = _detailPath && pathMetaKeyMatch(e.path, _detailPath);
    const imgHtml = (e.missing || !e.src)
      ? `<div style="height:180px;display:flex;align-items:center;justify-content:center;color:var(--text-dim);font-size:12px;border:1px dashed var(--border);border-radius:8px;background:#0b101d;">图缺失<br/><span style="opacity:.7;font-size:10px;">${esc(PathName(e.path || ""))}</span></div>`
      : `<img src="${esc(e.src)}" data-full="${esc(e.full || e.src)}" alt="" loading="eager" decoding="async" onclick='event.stopPropagation(); openViewer(${JSON.stringify(e.path)}, { keepAnchor: true })' onerror="if(!this.dataset.retried && this.dataset.full && this.dataset.full!==this.src){this.dataset.retried='1';this.src=this.dataset.full;}else{this.replaceWith(Object.assign(document.createElement('div'),{style:'height:180px;display:flex;align-items:center;justify-content:center;color:#94a3b8;font-size:12px;border:1px dashed rgba(148,163,184,.35);border-radius:8px',textContent:'图加载失败'}));}" />`;
    parts.push(`<div class="teach-ex role-${role}${isCur ? " current" : ""}" style="${isCur ? "outline:2px solid var(--teal);" : ""}">
      ${imgHtml}
      <div class="cap">
        <span class="teach-role ${role}">${teachRoleLabel(e.role)}</span>
        <span>${esc(e.label || "")}</span>
      </div>
      ${scoreLine}
      ${formatDimsHtml(e.dims, "teach-dim")}
      ${promptLine}
      ${noteLine}
      <div class="teach-actions">${actions.join("")}</div>
    </div>`);
  });
  return `<h3 style="font-size:13px;color:var(--text-muted);margin:0 0 8px;">视觉对照（原图 → 过程 → 终稿）· 提示词/六维分在每张图下方</h3>
    <div class="teach-pipeline">${parts.join("")}</div>`;
}

function renderDetailMain() {
  const main = document.getElementById("detailMain");
  if (!main) return;
  try {
    const path = _detailPath || state.lbPath;
    const info = lookupAsset(path) || { path };
    const { examples, sess } = buildLineageExamples(info);
    const navMeta = {};
    examples.forEach(e => {
      navMeta[normViewerPath(e.path)] = e;
    });
    setViewerNav(examples.map(e => e.path).filter(Boolean), navMeta);
    const missN = examples.filter(e => e.missing || !e.src).length;
    const head = `
      <div class="detail-meta-bar">
        <span>模块 <b style="color:var(--text-main);">${esc(info.module || "unassigned")}</b></span>
        <span>来源 ${esc(sourceLabel(info.source))}</span>
        ${sess ? `<span>会话 <code>${esc(sess.session_id)}</code> · ${sess.rounds.length} 轮 · 合格线 ≥${esc(String(sess.threshold || 9.5))}</span>` : `<span>无闭环会话</span>`}
        <span>卡片 ${examples.length}${missN ? ` · <b style="color:#fda4af;">缺图 ${missN}</b>` : ""}</span>
        <span>当前 <code title="${esc(absAssetPath(path))}">${esc(path)}</code></span>
      </div>
      ${sess && sess.goal ? `<div style="font-size:12.5px;color:var(--text-muted);margin:-4px 0 12px;">目标：${esc(sess.goal)}</div>` : ""}
    `;
    main.innerHTML = head + renderDetailPipelineHtml(examples, sess);
    // 弹层刚从 display:none 打开时，强制触发图片请求（避免 lazy 不刷）
    requestAnimationFrame(() => {
      main.querySelectorAll("img").forEach(img => {
        try {
          img.loading = "eager";
          const s = img.getAttribute("src");
          if (s) img.src = s;
        } catch (e) {}
      });
    });
  } catch (err) {
    console.error("renderDetailMain failed", err);
    main.innerHTML = `<div class="detail-empty">详情渲染失败：${esc(err && err.message ? err.message : "未知错误")}</div>`;
  }
}

window.closeAssetDetail = function() {
  const m = document.getElementById("detailModal");
  if (m) m.classList.remove("open");
};

window.openAssetDetail = function(assetPath) {
  const path = assetPath || state.lbPath;
  if (!path) {
    showToast("没有可打开的图");
    return;
  }
  let info = lookupAsset(path);
  if (!info) info = { path };
  closeViewer();
  const lb = document.getElementById("lightbox");
  if (lb) lb.classList.remove("open");
  _detailPath = info.path || path;
  state.lbPath = _detailPath;
  if (!isWorkbenchHiddenAsset(info) && assetPlate(info) === "final") {
    _viewerAnchorPath = _detailPath;
  } else {
    const sess = sessionOfAsset(info);
    _viewerAnchorPath = (sess && (sess.final_image || sess.winner_image)) || _viewerAnchorPath || _detailPath;
  }
  _viewerSessionId = (sessionOfAsset(info) && sessionOfAsset(info).session_id) || info.converge_session_id || "";
  // 先打开弹层再渲染，避免 display:none 里 lazy/布局导致小图空白
  const modal = document.getElementById("detailModal");
  if (modal) modal.classList.add("open");
  renderDetailMain();
};

window.closeViewer = function(force) {
  if (!force && Date.now() < _viewerIgnoreCloseUntil) return;
  const v = document.getElementById("imgViewer");
  if (v) {
    v.classList.remove("open", "compare-on", "evolve-on", "meta-on");
  }
  _viewerCompare = false;
  _viewerFromTeach = false;
  _viewerIgnoreCloseUntil = 0;
  const meta = document.getElementById("ivMetaPanel");
  if (meta) meta.innerHTML = "";
};

window.viewerStep = function(delta) {
  const paths = _viewerNavPaths.length ? _viewerNavPaths : galleryNavPaths();
  if (!paths.length || !state.lbPath) return;
  const cur = normViewerPath(state.lbPath);
  let idx = paths.findIndex(p => normViewerPath(p) === cur);
  if (idx < 0) {
    const base = cur.split("/").pop();
    idx = paths.findIndex(p => normViewerPath(p).split("/").pop() === base);
  }
  const next = idx + delta;
  if (idx < 0 || next < 0 || next >= paths.length) return;
  openViewer(paths[next], { keepAnchor: true, fromTeach: _viewerFromTeach });
};

window.toggleCompare = function(force) {
  const info = lookupAsset(state.lbPath);
  const refPath = resolveRefPath(info);
  if (!refPath) {
    showToast("没有参考原图可并列");
    _viewerCompare = false;
  } else if (typeof force === "boolean") {
    _viewerCompare = force;
  } else {
    _viewerCompare = !_viewerCompare;
  }
  updateViewerChrome(info);
};

async function promoteViaBridge(payload) {
  for (const port of revealPorts()) {
    try {
      const res = await fetch("http://127.0.0.1:" + port + "/api/promote", {
        method: "POST",
        cache: "no-store",
        mode: "cors",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const j = await res.json().catch(() => null);
      if (j && j.service === "pmem-atlas-reveal") {
        DATA.reveal_port = port;
        return j;
      }
    } catch (e) {}
  }
  return null;
}

window.promoteAsFinal = async function(sourcePath, sessionId, roundNum, finalPath) {
  const src = sourcePath || state.lbPath;
  const finalSlot = finalPath || _viewerAnchorPath || "";
  if (!src) return;
  if (!window.confirm("将此过程图设为最终交稿？\n会覆盖终稿文件内容，进化履历（提示词/轮次）保留。\n源: " + src + "\n终稿: " + (finalSlot || "(自动推断)"))) {
    return;
  }
  showToast("正在设为最终交稿…");
  const result = await promoteViaBridge({
    source_path: src,
    final_path: finalSlot,
    session_id: sessionId || _viewerSessionId || "",
    round: roundNum
  });
  if (!result || !result.ok) {
    showToast("设为终稿失败：" + ((result && result.error) || "定位服务未连通，请先 python pmem_art.py atlas"));
    return;
  }
  const fp = result.final_path;
  const info = lookupAsset(fp) || { path: fp };
  info.path = fp;
  info.plate = "final";
  info.workbench_hide = false;
  info.mtime = result.mtime || Date.now() / 1000;
  info._bust = Date.now();
  if (sessionId) info.converge_session_id = sessionId;
  if (roundNum != null) info.converge_round = roundNum;
  DATA.assets[fp] = Object.assign({}, DATA.assets[fp] || {}, info);
  if (sessionId && DATA.converge_sessions && DATA.converge_sessions[sessionId]) {
    DATA.converge_sessions[sessionId].winner_image = fp;
    DATA.converge_sessions[sessionId].final_image = fp;
  }
  _viewerAnchorPath = fp;
  renderHeaderAndSidebar();
  renderStage();
  const detailOpen = document.getElementById("detailModal") && document.getElementById("detailModal").classList.contains("open");
  if (detailOpen) {
    _detailPath = fp;
    renderDetailMain();
  } else {
    openViewer(fp, { keepAnchor: true });
  }
  showToast("✅ 已设为最终交稿：" + fp);
};

/** 半透明叠层放大原图（点空白 / Esc 关闭）；摘要轮次/总分/六维；详细 Prompt 在详情 */
window.openViewer = function(assetPath, opts) {
  opts = opts || {};
  try {
    let info = lookupAsset(assetPath);
    if (!info) {
      if (!assetPath) {
        showToast("找不到这张图的索引");
        return;
      }
      // 进化面板 / 教学样例：索引里没有时仍允许按路径预览
      info = { path: assetPath };
    }
    hideImgCtxMenu();
    const key = info.path || assetPath;
    state.lbPath = key;
    if (opts.fromTeach) _viewerFromTeach = true;
    else if (!opts.keepAnchor) _viewerFromTeach = false;

    // 建立可左右切换的图链：教学课内样例 / 会话轮次 / 主画廊
    if (opts.fromTeach || _viewerFromTeach) {
      const tn = teachNavAndMeta();
      setViewerNav(tn.paths, tn.meta);
    } else if (Array.isArray(opts.navPaths) && opts.navPaths.length) {
      setViewerNav(opts.navPaths, opts.navMeta || {});
    } else if (!opts.keepAnchor) {
      const sess0 = sessionOfAsset(info);
      const sn = sessionNavAndMeta(sess0);
      const inSess = sn.paths.some(p => normViewerPath(p) === normViewerPath(key));
      if (inSess && sn.paths.length > 1) {
        setViewerNav(sn.paths, sn.meta);
      } else if (sess0) {
        setViewerNav(galleryNavPaths(), sn.meta);
      } else {
        setViewerNav(galleryNavPaths(), {});
      }
    } else {
      const cur = normViewerPath(key);
      const inNav = _viewerNavPaths.some(p => normViewerPath(p) === cur);
      if (!inNav) {
        const sessKeep = sessionOfAsset(info)
          || (_viewerSessionId && (DATA.converge_sessions || {})[_viewerSessionId])
          || null;
        if (sessKeep) {
          const sn = sessionNavAndMeta(sessKeep);
          setViewerNav(sn.paths, Object.assign({}, _viewerMetaByPath, sn.meta));
        } else if (!_viewerNavPaths.length) {
          setViewerNav(galleryNavPaths(), _viewerMetaByPath);
        }
      }
    }

    if (!opts.keepAnchor) {
      // 从主画廊点开的定稿，记为终稿槽位
      if (!isWorkbenchHiddenAsset(info) && assetPlate(info) === "final") {
        _viewerAnchorPath = key;
      } else {
        const sessA = sessionOfAsset(info);
        _viewerAnchorPath = (sessA && (sessA.final_image || sessA.winner_image)) || _viewerAnchorPath || key;
      }
    }
    const sess = sessionOfAsset(info);
    _viewerSessionId = (sess && sess.session_id) || info.converge_session_id || _viewerSessionId || "";
    if (sess && !_viewerFromTeach) {
      const sn = sessionNavAndMeta(sess);
      _viewerMetaByPath = Object.assign({}, sn.meta, _viewerMetaByPath);
    }
    const img = document.getElementById("ivImg");
    const pathEl = document.getElementById("ivPath");
    const label = document.getElementById("ivMainLabel");
    const viewer = document.getElementById("imgViewer");
    if (!img || !viewer) {
      showToast("放大层未就绪，请刷新页面");
      return;
    }
    const media = resolveMediaSrc(key, {
      preferThumb: false,
      sessionId: (info && info.converge_session_id) || _viewerSessionId || ""
    });
    let src = media.src || bustSrc(info) || assetSrc(info) || String(key).replace(/\\/g, "/");
    if (media.missing || (info && info.exists === false && !media.src)) {
      showToast("该图文件已不在磁盘（索引残留）");
    }
    // 绝对盘符路径不能当 img src；尽量改成相对项目根
    if (/^[A-Za-z]:\//.test(src)) {
      const root = String(DATA.root || "").replace(/\\/g, "/").replace(/\/$/, "").toLowerCase();
      const low = src.toLowerCase();
      if (root && low.indexOf(root + "/") === 0) src = src.slice(root.length + 1);
    }
    img.src = src;
    if (pathEl) {
      pathEl.textContent = key;
      pathEl.title = absAssetPath(key);
    }
    if (label) {
      const meta = lookupViewerMeta(key) || {};
      const round = (info.converge_round != null ? (" · R" + info.converge_round) : "")
        || (meta.round != null ? (" · R" + meta.round) : "");
      const role = meta.role || (assetPlate(info) === "final" ? "final" : "process");
      const roleLab = role === "original" || role === "origin" || role === "ref" ? "原图"
        : (role === "final" || role === "winner" ? "定稿" : "过程/候选");
      label.textContent = roleLab + round;
    }
    // 同一击会落到刚出现的遮罩上 → 短时忽略关闭；下一帧再挂 open 更稳
    _viewerIgnoreCloseUntil = Date.now() + 400;
    viewer.classList.add("open");
    try { updateViewerChrome(info); } catch (e1) {}
    try { renderViewerMeta(info); } catch (e2) {}
  } catch (err) {
    console.error("openViewer failed", err);
    showToast("放大失败：" + (err && err.message ? err.message : "未知错误"));
  }
};

window.saveAssetAs = function(relPath) {
  const info = DATA.assets[relPath] || { path: relPath };
  const src = assetSrc(info) || String(relPath || "");
  const name = PathName(relPath) || "image.png";
  const a = document.createElement("a");
  a.href = src;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  showToast("已触发另存为：" + name);
};

let _ctxPath = "";
window.showImgCtxMenu = function(ev, relPath) {
  ev.preventDefault();
  ev.stopPropagation();
  _ctxPath = relPath;
  const menu = document.getElementById("imgCtxMenu");
  if (!menu) return false;
  menu.classList.add("open");
  const pad = 8;
  let x = ev.clientX;
  let y = ev.clientY;
  menu.style.left = x + "px";
  menu.style.top = y + "px";
  const rect = menu.getBoundingClientRect();
  if (rect.right > window.innerWidth - pad) {
    menu.style.left = Math.max(pad, window.innerWidth - rect.width - pad) + "px";
  }
  if (rect.bottom > window.innerHeight - pad) {
    menu.style.top = Math.max(pad, window.innerHeight - rect.height - pad) + "px";
  }
  return false;
};

window.hideImgCtxMenu = function() {
  const menu = document.getElementById("imgCtxMenu");
  if (menu) menu.classList.remove("open");
};

window.copyAgentContext = function(modId) {
  const m = DATA.modules[modId] || {};
  const entries = DATA.entries.filter(e => e.module === modId || e.scope === "project");
  const lines = [
    `# [pmem-art 视觉记忆上下文] 模块: ${modId} (${m.title || ''})`,
    `- 管线规格: 分辨率=${m.specs?.resolution || 'auto'}, 透明通道=${m.specs?.alpha_required ? '必须RGBA' : '不限'}, 九宫格=${JSON.stringify(m.specs?.nine_slice || null)}`,
    `- 锁定色板: ${(m.palette || []).map(p => `${p.name}(${p.hex})`).join(', ')}`,
    `## 核心红线与生图配方:`
  ];
  for (const e of entries) {
    lines.push(`- 【${e.kind_label}】(${e.id}) ${e.summary}`);
    if (e.ai_params?.prompt) lines.push(`  Prompt: ${e.ai_params.prompt}`);
    if (e.ai_params?.negative_prompt) lines.push(`  Negative: ${e.ai_params.negative_prompt}`);
  }
  copyText(lines.join("\n"), `${modId} AI 记忆上下文`);
};

window.openLightbox = function(assetPath) {
  const info = lookupAsset(assetPath);
  if (!info) {
    showToast("找不到这张图的索引");
    return;
  }
  closeViewer();
  state.lbScale = 1.0;
  state.lbPath = assetPath;
  const lb = document.getElementById("lightbox");
  const img = document.getElementById("lbImg");
  const box = document.getElementById("lbImgBox");
  box.style.transform = "scale(1)";
  img.src = assetSrc(info);
  document.getElementById("lbTitle").textContent = assetPath;
  document.getElementById("lbSpecBadge").textContent = `${info.resolution || ""} · ${info.mode || ""} · ${info.size_kb || "?"} KB`;

  const linked = (DATA.entries || []).filter(e => (e.assets || []).some(x => x.path === assetPath));
  const modCfg = (DATA.modules || {})[info.module] || {};
  const scoreLine = (info.score != null && info.score !== "")
    ? `<div>评分: <b style="color:var(--gold);">${esc(String(info.score))}</b>${info.converge_round != null ? ` · 第 ${esc(String(info.converge_round))} 轮` : ""}</div>`
    : (info.converge_round != null ? `<div>闭环轮次: <b>第 ${esc(String(info.converge_round))} 轮</b></div>` : "");
  document.getElementById("lbAside").innerHTML = `
    <div>
      <div style="font-size:11px;color:var(--text-dim);text-transform:uppercase;">来源 / 模块</div>
      <div style="font-size:15px;font-weight:700;color:var(--teal);margin-top:2px;">${esc(sourceLabel(info.source))} · ${esc(info.module || "unassigned")}</div>
      <div class="lb-path-actions">
        <button class="btn-copy" onclick="copyText(absAssetPath(state.lbPath), '绝对路径')">📋 复制绝对路径</button>
        <button class="btn-copy" onclick="revealInFolder(state.lbPath)">📁 在文件夹中显示</button>
        <button class="btn-copy" onclick="saveAssetAs(state.lbPath)">💾 另存为</button>
        <button class="btn-copy" onclick="openInEditor(state.lbPath)">📂 在编辑器打开</button>
        <button class="btn-copy" style="background:var(--danger-bg);color:#fda4af;border-color:rgba(244,63,94,0.4);" onclick="deleteOneAsset(state.lbPath)">🗑️ 删除</button>
      </div>
    </div>
    <div style="background:#090d16;padding:10px 12px;border-radius:8px;border:1px solid var(--border);font-size:12px;">
      <div>时间: <b>${esc(info.updated_at || info.day || "")}</b></div>
      <div>分辨率: <b>${esc(info.resolution || "")}</b> | 通道: <b>${esc(info.mode || "")}</b></div>
      <div>体积: <b>${info.size_kb || "?"} KB</b></div>
      ${scoreLine}
      <div style="margin-top:4px;color:${info.formal ? '#6ee7b7' : '#94a3b8'};">
        ${info.formal ? "✅ 正式模块资产" : "👁️ 可见索引（未正式 ingest）"}
      </div>
    </div>
    <div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;">提示词变化 / 优化过程</div>
      ${renderPromptTraceHtml(info)}
    </div>
    ${(modCfg.palette && modCfg.palette.length) ? `
      <div>
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:6px;">模块色卡:</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          ${modCfg.palette.map(p => `
            <div class="swatch-chip" onclick="copyText('${esc(p.hex)}', '${esc(p.hex)}')">
              <span class="swatch-box" style="background:${esc(p.hex)}"></span>
              <span class="swatch-hex">${esc(p.hex)}</span>
            </div>
          `).join("")}
        </div>
      </div>
    ` : ''}
    <div>
      <div style="font-size:12px;color:var(--text-muted);margin-bottom:8px;">关联记忆 (${linked.length}):</div>
      ${linked.length ? linked.map(e => `
        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:10px;margin-bottom:8px;">
          <span class="badge ${esc(e.badge || "info")}">${esc(e.kind_label || e.kind || "")}</span>
          <div style="font-weight:700;margin:6px 0 4px;font-size:13px;">${esc(e.summary || "")}</div>
        </div>
      `).join("") : `<div style="color:var(--text-dim);font-size:12px;">无关联正式记忆</div>`}
    </div>
  `;
  lb.classList.add("open");
};

// Event Listeners
document.querySelectorAll(".tab-btn[data-tab]").forEach(btn => {
  btn.addEventListener("click", () => switchTab(btn.dataset.tab));
});
document.querySelectorAll("#moreMenu [data-tab]").forEach(btn => {
  btn.addEventListener("click", (ev) => {
    ev.stopPropagation();
    switchTab(btn.dataset.tab);
  });
});
document.getElementById("searchInput").addEventListener("input", e => {
  state.search = e.target.value;
  clearTimeout(_searchTimer);
  _searchTimer = setTimeout(() => {
    saveAtlasState();
    renderStage();
  }, 140);
});
document.querySelectorAll("#bgMenu [data-bg]").forEach(btn => {
  btn.addEventListener("click", (ev) => {
    ev.stopPropagation();
    document.querySelectorAll("#bgMenu [data-bg]").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const lbCanvas = document.getElementById("lbCanvas");
    lbCanvas.classList.remove(state.bgClass);
    state.bgClass = btn.dataset.bg;
    lbCanvas.classList.add(state.bgClass);
    const label = document.getElementById("btnBgMenu");
    if (label) label.textContent = btn.textContent.trim().split(/\s+/)[0] + " 底色";
    const bg = document.getElementById("bgWrap");
    if (bg) bg.classList.remove("open");
    saveAtlasState();
    renderStage();
  });
});
document.getElementById("toggleGuidesBtn").addEventListener("click", e => {
  state.showGuides = !state.showGuides;
  e.currentTarget.classList.toggle("active", state.showGuides);
  document.getElementById("lbImgBox").classList.toggle("show-guides", state.showGuides);
  renderStage();
});
document.getElementById("thumbSlider").addEventListener("input", e => {
  applyThumbSize(e.target.value, { persist: false, refreshVirt: true });
});
document.getElementById("thumbSlider").addEventListener("change", e => {
  applyThumbSize(e.target.value, { persist: true, refreshVirt: true });
});
document.getElementById("thumbZoomOut").addEventListener("click", () => {
  applyThumbSize(state.thumbSize - 16);
});
document.getElementById("thumbZoomIn").addEventListener("click", () => {
  applyThumbSize(state.thumbSize + 16);
});
document.getElementById("lbClose").addEventListener("click", () => {
  document.getElementById("lightbox").classList.remove("open");
});
document.getElementById("lbCopyPath").addEventListener("click", () => {
  if (state.lbPath) copyText(absAssetPath(state.lbPath), "绝对路径");
});
document.getElementById("lbRevealFolder").addEventListener("click", () => {
  if (state.lbPath) revealInFolder(state.lbPath);
});
document.getElementById("lbOpenEditor").addEventListener("click", () => {
  if (state.lbPath) openInEditor(state.lbPath);
});
document.getElementById("lbZoomIn").addEventListener("click", () => {
  state.lbScale = Math.min(4.0, state.lbScale + 0.25);
  document.getElementById("lbImgBox").style.transform = `scale(${state.lbScale})`;
});
document.getElementById("lbZoomOut").addEventListener("click", () => {
  state.lbScale = Math.max(0.25, state.lbScale - 0.25);
  document.getElementById("lbImgBox").style.transform = `scale(${state.lbScale})`;
});
document.getElementById("lbZoomReset").addEventListener("click", () => {
  state.lbScale = 1.0;
  document.getElementById("lbImgBox").style.transform = "scale(1)";
});
document.getElementById("lbImg").addEventListener("contextmenu", (ev) => {
  if (state.lbPath) return showImgCtxMenu(ev, state.lbPath);
});

const imgViewer = document.getElementById("imgViewer");
const imgViewerCard = document.getElementById("imgViewerCard");
if (imgViewer) {
  imgViewer.addEventListener("click", (ev) => {
    // 点卡片内不关；点遮罩才关。打开当下的穿透点击靠 ignore 窗口挡住
    if (ev.target.closest && ev.target.closest("#imgViewerCard")) return;
    closeViewer(false);
  });
}
if (imgViewerCard) {
  imgViewerCard.addEventListener("click", (ev) => ev.stopPropagation());
}
function bindIvBtn(id, fn) {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener("click", (ev) => {
    ev.stopPropagation();
    fn(ev);
  });
}
bindIvBtn("ivClose", () => closeViewer(true));
bindIvBtn("ivPrev", () => viewerStep(-1));
bindIvBtn("ivNext", () => viewerStep(1));
bindIvBtn("ivPrevBtn", () => viewerStep(-1));
bindIvBtn("ivNextBtn", () => viewerStep(1));
bindIvBtn("ivCompare", () => toggleCompare());
bindIvBtn("ivReveal", () => { if (state.lbPath) revealInFolder(state.lbPath); });
bindIvBtn("ivCopy", () => { if (state.lbPath) copyText(absAssetPath(state.lbPath), "绝对路径"); });
bindIvBtn("ivSave", () => { if (state.lbPath) saveAssetAs(state.lbPath); });
bindIvBtn("ivDetail", () => { if (state.lbPath) openAssetDetail(state.lbPath); });
document.getElementById("ivImg").addEventListener("contextmenu", (ev) => {
  if (state.lbPath) return showImgCtxMenu(ev, state.lbPath);
});

document.getElementById("imgCtxMenu").addEventListener("click", (ev) => {
  const btn = ev.target.closest("button[data-act]");
  if (!btn || !_ctxPath) return;
  const act = btn.getAttribute("data-act");
  const p = _ctxPath;
  hideImgCtxMenu();
  if (act === "copy-abs") copyText(absAssetPath(p), "绝对路径");
  else if (act === "copy-rel") copyText(p, "相对路径");
  else if (act === "copy-name") copyText(PathName(p), "文件名");
  else if (act === "copy-folder") copyText(parentDirOf(absAssetPath(p)), "文件夹路径");
  else if (act === "save-as") saveAssetAs(p);
  else if (act === "reveal") revealInFolder(p);
  else if (act === "editor") openInEditor(p);
  else if (act === "viewer") openViewer(p);
  else if (act === "lightbox") openAssetDetail(p);
  else if (act === "delete") deleteOneAsset(p);
  else if (act === "batch") {
    setBatchMode(true);
    const idx = _galleryAssets.findIndex(a => a.path === p);
    toggleSelectPath(p, { idx });
  }
});

const detailModal = document.getElementById("detailModal");
const detailShell = document.getElementById("detailShell");
if (detailModal && detailShell) {
  detailModal.addEventListener("click", () => closeAssetDetail());
  detailShell.addEventListener("click", (ev) => ev.stopPropagation());
}
const detailClose = document.getElementById("detailClose");
if (detailClose) detailClose.addEventListener("click", (ev) => { ev.stopPropagation(); closeAssetDetail(); });
const detailTech = document.getElementById("detailTech");
if (detailTech) detailTech.addEventListener("click", (ev) => {
  ev.stopPropagation();
  const p = _detailPath || state.lbPath;
  if (!p) return;
  closeAssetDetail();
  openLightbox(p);
});
document.addEventListener("click", () => hideImgCtxMenu());
document.addEventListener("scroll", () => hideImgCtxMenu(), true);
document.getElementById("btnBatchMode").addEventListener("click", () => {
  setBatchMode(!state.batchMode);
});

let _teachId = "";
function guideLessons() {
  const g = DATA.workbench_guide || {};
  return Array.isArray(g.lessons) ? g.lessons : [];
}
function teachGroupOf(lesson) {
  const id = String((lesson && lesson.id) || "");
  const skill = String((lesson && lesson.skill) || "");
  if (id === "agent" || skill.indexOf("pmem-agent") >= 0) return "总控";
  if (id.indexOf("draw-") === 0 || skill.indexOf("pmem-draw") >= 0) return "生图";
  if (id === "ui" || skill.indexOf("pmem-ui") >= 0) return "界面";
  if (id.indexOf("icon") === 0 || skill.indexOf("pmem-icon") >= 0) return "图标";
  if (id.indexOf("merge") === 0 || skill.indexOf("merge-ladder") >= 0) return "合成梯";
  if (id === "style-lock" || skill.indexOf("style-lock") >= 0) return "风格";
  return "辅助";
}
const TEACH_DIM_LABELS = {
  composition: "构图",
  lighting_color: "光影",
  perspective_anatomy: "透视",
  texture_detail: "材质",
  spec_style: "风格",
  flawlessness: "完成度"
};
function formatDimsHtml(dims, cls) {
  if (!dims || typeof dims !== "object") return "";
  const keys = Object.keys(dims);
  if (!keys.length) return "";
  const chips = keys.map(k => {
    const lab = TEACH_DIM_LABELS[k] || k;
    const v = dims[k];
    const num = (typeof v === "number") ? v.toFixed(1) : String(v);
    return `<span class="${cls}">${lab} ${num}</span>`;
  }).join("");
  const wrap = cls === "evolve-dim" ? "evolve-dims"
    : (cls === "iv-meta-dim" ? "iv-meta-dims" : "teach-dims");
  return `<div class="${wrap}">${chips}</div>`;
}
function teachEnrichExample(ex, rounds) {
  const out = Object.assign({}, ex || {});
  const list = Array.isArray(rounds) ? rounds : [];
  let hit = null;
  // 例子上已有完整字段时不要用 rounds 覆盖（避免串图文案）
  const hasOwn = !!(out.prompt || out.defects || (out.dims && Object.keys(out.dims || {}).length));
  if (!hasOwn) {
    if (out.round != null) hit = list.find(r => Number(r.round) === Number(out.round));
    if (!hit && out.path) {
      hit = list.find(r => pathMetaKeyMatch(r.path || "", out.path));
    }
    if (hit) {
      ["prompt", "defects", "next_fix", "score", "passed", "dims"].forEach(k => {
        if ((out[k] == null || out[k] === "") && hit[k] != null && hit[k] !== "") out[k] = hit[k];
      });
    }
  }
  // 教学图多半不进 assets 索引；仍走统一 src 解析，缺图明确标 missing
  if (out.exists === false) {
    out.src = "";
    out.missing = true;
  } else {
    const media = resolveMediaSrc(out.path, { preferThumb: false });
    out.src = media.src || String(out.path || "").replace(/\\/g, "/");
    out.missing = !out.src;
    if (media.path) out.path = media.path;
  }
  return out;
}
window.teachSetAsFinal = function(processPath) {
  // 教学包不可改终稿；引导去正式工作台进化过程
  showToast("教学样例不能设终稿。正式图：放大 →「详情 · 进化对照」→ 点「设置为最终交稿」");
};

function teachRoleClass(role) {
  const r = String(role || "").toLowerCase();
  if (r === "original" || r === "origin" || r === "ref" || r === "reference") return "original";
  if (r === "final" || r === "winner") return "final";
  return "process";
}
function teachRoleLabel(role) {
  const c = teachRoleClass(role);
  return ({ original: "原图", process: "过程", final: "终稿" })[c] || "过程";
}
function selectTeachLesson(id) {
  const lessons = guideLessons();
  if (!lessons.length) return;
  const hit = lessons.find(l => l.id === id);
  _teachId = hit ? hit.id : lessons[0].id;
  renderTeachNav();
  renderTeachMain();
}
window.teachStep = function(delta) {
  const lessons = guideLessons();
  if (!lessons.length) return;
  let idx = lessons.findIndex(l => l.id === _teachId);
  if (idx < 0) idx = 0;
  const next = Math.max(0, Math.min(lessons.length - 1, idx + delta));
  selectTeachLesson(lessons[next].id);
};
function renderTeachNav() {
  const nav = document.getElementById("teachNav");
  if (!nav) return;
  const lessons = guideLessons();
  if (!lessons.length) {
    nav.innerHTML = `<div style="padding:10px;color:var(--text-dim);font-size:12px;">暂无教学目录。请确认 docs/workbench_guide/catalog.json 存在。</div>`;
    return;
  }
  if (!_teachId) _teachId = lessons[0].id;
  const groups = [];
  const seen = new Set();
  lessons.forEach(l => {
    const g = teachGroupOf(l);
    if (!seen.has(g)) { seen.add(g); groups.push(g); }
  });
  nav.innerHTML = groups.map(g => {
    const items = lessons.filter(l => teachGroupOf(l) === g).map(l => `
      <button type="button" data-teach="${esc(l.id)}" class="${l.id === _teachId ? "active" : ""}">
        ${esc(l.title || l.id)}
        <div class="teach-nav-skill">${esc(l.skill || "")}</div>
      </button>
    `).join("");
    return `<div class="teach-nav-group">${esc(g)}</div>${items}`;
  }).join("");
  nav.querySelectorAll("button[data-teach]").forEach(btn => {
    btn.addEventListener("click", () => selectTeachLesson(btn.getAttribute("data-teach") || ""));
  });
}
function renderTeachMain() {
  const main = document.getElementById("teachMain");
  if (!main) return;
  const lessons = guideLessons();
  const idx = Math.max(0, lessons.findIndex(l => l.id === _teachId));
  const lesson = lessons[idx] || lessons[0];
  if (!lesson) {
    main.innerHTML = `<div style="color:var(--text-dim);">没有可显示的技能课。</div>`;
    return;
  }
  const how = (lesson.how || []).map(x => `<li>${esc(x)}</li>`).join("");
  const rounds = Array.isArray(lesson.rounds) ? lesson.rounds : [];
  const examples = (lesson.examples || []).filter(e => e && e.path).map(e => teachEnrichExample(e, rounds));
  const samples = Array.isArray(lesson.samples) ? lesson.samples : [];
  const slash = String(lesson.skill || "").split("·")[0].trim() || String(lesson.skill || "").trim();
  let pipeline = "";
  if (examples.length) {
    const parts = [];
    examples.forEach((e, i) => {
      const role = teachRoleClass(e.role);
      const missing = e.exists === false;
      if (i > 0) parts.push(`<div class="teach-arrow" aria-hidden="true">→</div>`);
      const hasScore = e.score != null && e.score !== "";
      const scoreLine = hasScore
        ? `<div class="teach-score-line">总分 ${esc(String(Number(e.score).toFixed(2)))}${e.passed ? " · 达标" : " · 未达标"}</div>`
        : "";
      const dimsLine = formatDimsHtml(e.dims, "teach-dim");
      const prevEx = i > 0 ? examples[i - 1] : null;
      const promptPack = stripPrevCritiqueFromPrompt(e.prompt || "", prevEx);
      const promptLine = promptPack.main
        ? `<div class="teach-prompt">${esc(promptPack.main)}</div>`
        : ((role === "original" && (e.defects || e.next_fix)) ? "" : (role === "original" ? "" : `<div class="teach-note">（无 Prompt 样例）</div>`));
      const hasProcessAfter = examples.slice(i + 1).some(x => teachRoleClass(x.role) === "process" || teachRoleClass(x.role) === "final");
      const noteLine = formatOwnCritiqueHtml(e, {
        noteCls: "teach-note",
        role: e.role,
        allowEmptyHint: role === "original" && hasProcessAfter
      });
      const actions = [];
      if (e.prompt) {
        actions.push(`<button type="button" class="btn-copy" onclick='event.stopPropagation(); copyText(${JSON.stringify(e.prompt || "")}, "Prompt")'>📋 Prompt</button>`);
      }
      if (role === "process") {
        actions.push(`<button type="button" class="btn-copy" style="background:var(--success-bg);color:#6ee7b7;border-color:rgba(16,185,129,0.45);" onclick='event.stopPropagation(); teachSetAsFinal(${JSON.stringify(e.path)})'>设置为最终交稿</button>`);
      }
      const actLine = actions.length ? `<div class="teach-actions">${actions.join("")}</div>` : "";
      const imgBroken = missing || e.missing || !e.src;
      parts.push(`<div class="teach-ex role-${role}">
        ${imgBroken
          ? `<div style="height:180px;display:flex;align-items:center;justify-content:center;color:var(--text-dim);font-size:12px;border:1px dashed var(--border);border-radius:8px;">图缺失<br/><span style="opacity:.7;font-size:10px;">${esc(PathName(e.path || ""))}</span></div>`
          : `<img src="${esc(e.src)}" data-full="${esc(e.full || e.src)}" alt="" loading="eager" decoding="async" onclick='event.stopPropagation(); openViewer(${JSON.stringify(e.path)}, { keepAnchor: true, fromTeach: true })' onerror="if(!this.dataset.retried && this.dataset.full && this.dataset.full!==this.src){this.dataset.retried='1';this.src=this.dataset.full;}else{this.replaceWith(Object.assign(document.createElement('div'),{style:'height:180px;display:flex;align-items:center;justify-content:center;color:#94a3b8;font-size:12px;border:1px dashed rgba(148,163,184,.35);border-radius:8px',textContent:'图加载失败'}));}" />`}
        <div class="cap">
          <span class="teach-role ${role}">${teachRoleLabel(e.role)}</span>
          <span>${esc(e.label || "")}</span>
        </div>
        ${scoreLine}
        ${dimsLine}
        ${promptLine}
        ${noteLine}
        ${actLine}
      </div>`);
    });
    pipeline = `<h3 style="font-size:13px;color:var(--text-muted);margin:0 0 8px;">视觉对照（原图 → 过程 → 终稿）· 提示词/六维分在每张图下方</h3>
      <div class="teach-pipeline">${parts.join("")}</div>`;
  }
  let samplesHtml = "";
  if (samples.length) {
    const cards = samples.map(s => `<div class="teach-sample">
      <h4>${esc(s.title || s.kind || "样例")}</h4>
      <div class="body">${esc(s.body || "")}</div>
      ${s.score != null && s.score !== "" ? `<div style="margin-top:6px;color:var(--gold);font-family:ui-monospace,monospace;font-size:12px;">评分 ${esc(String(s.score))}</div>` : ""}
    </div>`).join("");
    samplesHtml = `<h3 style="font-size:13px;color:var(--text-muted);margin:16px 0 8px;">样例演示</h3>
      <div class="teach-samples">${cards}</div>`;
  }
  if (!pipeline && !samplesHtml) {
    pipeline = `<div style="color:var(--text-dim);font-size:12.5px;padding:10px 12px;border:1px dashed var(--border);border-radius:8px;">本课暂无视觉/文字样例——直接在对话框输入技能名即可。</div>`;
  }
  main.innerHTML = `
    <div class="teach-skill-row">
      <span class="teach-skill">${esc(lesson.skill || "")}</span>
      ${slash ? `<button type="button" class="btn-copy" onclick='copyText(${JSON.stringify(slash)}, "技能指令")'>📋 复制指令</button>` : ""}
    </div>
    <h2 style="margin:4px 0 0;font-size:20px;">${esc(lesson.title || "")}</h2>
    <div class="teach-when">适用：${esc(lesson.when || "")}</div>
    <h3 style="font-size:13px;color:var(--text-muted);margin:0 0 6px;">怎么用</h3>
    <ol class="teach-how">${how || "<li>见技能文档</li>"}</ol>
    ${pipeline}
    ${samplesHtml}
    <div class="teach-foot">
      <div class="teach-locked">🔒 示例图在 docs/workbench_guide/，会进 git、不进主画廊；工作台删除会被拒绝。只有改该文件夹才会变。</div>
      <div class="teach-nav-btns">
        <button type="button" class="btn-copy" ${idx <= 0 ? "disabled" : ""} onclick="teachStep(-1)">← 上一课</button>
        <button type="button" class="btn-copy" ${idx >= lessons.length - 1 ? "disabled" : ""} onclick="teachStep(1)">下一课 →</button>
        <span style="color:var(--text-dim);font-size:11px;">${idx + 1} / ${lessons.length} · ↑↓ 切课</span>
      </div>
    </div>
  `;
}
window.openTeach = function() {
  renderTeachNav();
  renderTeachMain();
  document.getElementById("teachModal").classList.add("open");
};
window.closeTeach = function() {
  document.getElementById("teachModal").classList.remove("open");
};
const teachModal = document.getElementById("teachModal");
const teachShell = document.getElementById("teachShell");
if (teachModal && teachShell) {
  teachModal.addEventListener("click", () => {
    const viewerOpen = document.getElementById("imgViewer") && document.getElementById("imgViewer").classList.contains("open");
    if (viewerOpen) return;
    closeTeach();
  });
  teachShell.addEventListener("click", (ev) => ev.stopPropagation());
}
const btnTeach = document.getElementById("btnTeach");
if (btnTeach) btnTeach.addEventListener("click", () => openTeach());
const btnOpenTrash = document.getElementById("btnOpenTrash");
if (btnOpenTrash) btnOpenTrash.addEventListener("click", () => openTrashFolder());
const teachOpenFolder = document.getElementById("teachOpenFolder");
if (teachOpenFolder) teachOpenFolder.addEventListener("click", (ev) => { ev.stopPropagation(); openTeachFolder(); });
const teachClose = document.getElementById("teachClose");
if (teachClose) teachClose.addEventListener("click", (ev) => { ev.stopPropagation(); closeTeach(); });
async function connectOrOfferWorkbenchLauncher() {
  showToast("正在探测定位服务…");
  let port = await pingRevealBridge();
  if (port) {
    showToast("已连通 · 端口 " + port);
    if (location.protocol === "file:") {
      try { sessionStorage.setItem("pmem_atlas_just_reloaded", "http-upgrade"); } catch (e) {}
      location.replace("http://127.0.0.1:" + port + "/art-atlas.html");
    }
    return port;
  }
  // 浏览器沙箱不能直接起本机 Python：下载启动脚本，用户双击一次即可
  downloadStartWorkbenchHelper();
  showToast("未连通。已下载「启动工作台服务」脚本——请双击运行；我会在后台继续探测…");
  port = await waitForRevealBridge(45000, 1200);
  if (!port) {
    showToast("仍未连通。请双击刚下载的启动脚本，或运行 python pmem_art.py atlas");
    return 0;
  }
  showToast("已连通 · 端口 " + port);
  if (location.protocol === "file:") {
    try { sessionStorage.setItem("pmem_atlas_just_reloaded", "http-upgrade"); } catch (e) {}
    location.replace("http://127.0.0.1:" + port + "/art-atlas.html");
  }
  return port;
}
const btnRevealRetry = document.getElementById("btnRevealRetry");
if (btnRevealRetry) {
  btnRevealRetry.addEventListener("click", () => { connectOrOfferWorkbenchLauncher(); });
}
const btnOpenHttpWorkbench = document.getElementById("btnOpenHttpWorkbench");
if (btnOpenHttpWorkbench) {
  btnOpenHttpWorkbench.addEventListener("click", async () => {
    const port = await connectOrOfferWorkbenchLauncher();
    if (!port) return;
    if (location.protocol !== "file:") {
      location.href = "http://127.0.0.1:" + port + "/art-atlas.html";
    }
  });
}
/** file:// 双击打开时：能连上守护就自动切到 http，否则删除/定位会被浏览器拦 */
(async function upgradeFileOriginToHttp() {
  if (location.protocol !== "file:") return;
  try {
    if (sessionStorage.getItem("pmem_atlas_skip_http_upgrade") === "1") return;
  } catch (e) {}
  const port = await pingRevealBridge();
  if (!port) {
    setRevealBanner(false);
    showToast("当前是 file://：点横幅「重试连通」可下载启动脚本（浏览器不能自己起 Python）");
    return;
  }
  try { sessionStorage.setItem("pmem_atlas_just_reloaded", "http-upgrade"); } catch (e) {}
  location.replace("http://127.0.0.1:" + port + "/art-atlas.html");
})();
window.addEventListener("keydown", e => {
  const tag = (e.target && e.target.tagName) || "";
  const typing = tag === "INPUT" || tag === "TEXTAREA" || (e.target && e.target.isContentEditable);
  const viewerOpen = document.getElementById("imgViewer") && document.getElementById("imgViewer").classList.contains("open");
  const teachOpen = document.getElementById("teachModal") && document.getElementById("teachModal").classList.contains("open");
  const detailOpen = document.getElementById("detailModal") && document.getElementById("detailModal").classList.contains("open");
  if (e.key === "Escape") {
    hideImgCtxMenu();
    if (viewerOpen && _viewerCompare) {
      toggleCompare(false);
      return;
    }
    if (viewerOpen) {
      closeViewer(true);
      return;
    }
    if (detailOpen) {
      closeAssetDetail();
      return;
    }
    if (teachOpen) {
      closeTeach();
      return;
    }
    document.getElementById("lightbox").classList.remove("open");
    if (state.batchMode) setBatchMode(false);
    return;
  }
  if (typing) return;
  if (viewerOpen && (e.key === "ArrowLeft" || e.key === "Left")) {
    e.preventDefault();
    viewerStep(-1);
    return;
  }
  if (viewerOpen && (e.key === "ArrowRight" || e.key === "Right")) {
    e.preventDefault();
    viewerStep(1);
    return;
  }
  if (teachOpen && !viewerOpen && (e.key === "ArrowUp" || e.key === "Up" || e.key === "ArrowLeft" || e.key === "Left")) {
    e.preventDefault();
    teachStep(-1);
    return;
  }
  if (teachOpen && !viewerOpen && (e.key === "ArrowDown" || e.key === "Down" || e.key === "ArrowRight" || e.key === "Right")) {
    e.preventDefault();
    teachStep(1);
    return;
  }
  if ((e.ctrlKey || e.metaKey) && (e.key === "a" || e.key === "A")) {
    if (state.tab === "gallery") {
      e.preventDefault();
      if (!state.batchMode) setBatchMode(true);
      selectAllFiltered();
    }
    return;
  }
  if (e.key === "Delete" || e.key === "Backspace") {
    if (viewerOpen || teachOpen) return;
    if (state.batchMode && _selectedPaths.size) {
      e.preventDefault();
      deleteSelectedAssets();
      return;
    }
    if (_hoveredPath) {
      e.preventDefault();
      deleteOneAsset(_hoveredPath);
    }
  }
});
pingRevealBridge();

let _autoRefreshTimer = null;

window.updateAutoRefreshUI = function() {
  const btn = document.getElementById("btnToggleAutoRefresh");
  const dot = document.getElementById("liveDot");
  if (!btn || !dot) return;
  if (state.autoRefresh) {
    btn.textContent = "🔄 自动刷新: 开启 (10s)";
    btn.classList.remove("paused");
    dot.classList.remove("paused");
  } else {
    btn.textContent = "⏸️ 自动刷新: 已暂停";
    btn.classList.add("paused");
    dot.classList.add("paused");
  }
};

window.toggleAutoRefresh = function() {
  state.autoRefresh = !state.autoRefresh;
  saveAtlasState();
  updateAutoRefreshUI();
  showToast(state.autoRefresh ? "🔄 已开启每 10 秒自动检测新资产并无感刷新" : "⏸️ 已暂停自动刷新（可点击 ⚡ 立即刷新）");
};

window.manualRefreshNow = function() {
  saveAtlasState();
  hotReloadAtlasData().then((ok) => {
    if (!ok) {
      sessionStorage.setItem("pmem_atlas_just_reloaded", "manual");
      location.reload();
    } else {
      showToast("⚡ 已热更新所有图索引");
    }
  });
};

async function hotReloadAtlasData() {
  try {
    const res = await fetch(".memory-art/atlas_data.json?_t=" + Date.now(), { cache: "no-store" });
    if (!res.ok) return false;
    const next = await res.json();
    if (!next || !next.assets) return false;
    await syncTrashFilterIntoData(next);
    DATA = next;
    // 热更新时保住画廊滚动，避免正看着中间就被拽回顶部/底部
    renderStage({ keepScroll: true });
    return true;
  } catch (e) {
    return false;
  }
}

function checkAtlasUpdateOnce() {
  if (!state.autoRefresh) return;
  try {
    const oldScript = document.getElementById("pmemPingScript");
    if (oldScript) oldScript.remove();
    const s = document.createElement("script");
    s.id = "pmemPingScript";
    s.src = ".memory-art/atlas_ping.js?_t=" + Date.now();
    s.onload = function() {
      const ping = window.__PMEM_ATLAS_PING__;
      if (ping && ping.build_id && DATA.build_id && ping.build_id !== DATA.build_id) {
        saveAtlasState();
        hotReloadAtlasData().then((ok) => {
          if (!ok) {
            sessionStorage.setItem("pmem_atlas_just_reloaded", ping.built_at || "auto");
            location.reload();
          } else {
            showToast("✨ 检测到新图，已同步");
          }
        });
      }
    };
    document.head.appendChild(s);
  } catch (e) {}
}

restoreAtlasState();
if (!state.dayFilter) state.dayFilter = "today";
if (!state.plateFilter) state.plateFilter = "final";
if (!state.sideMode) state.sideMode = "all";
applyThumbSize(state.thumbSize || THUMB_DEFAULT, { persist: false, refreshVirt: false });
document.querySelectorAll(".tab-btn[data-tab]").forEach(b => b.classList.toggle("active", b.dataset.tab === state.tab));
document.querySelectorAll("#moreMenu [data-tab]").forEach(b => b.classList.toggle("active", b.dataset.tab === state.tab));
if (state.search) document.getElementById("searchInput").value = state.search;
renderStage();
// 启动时按垃圾桶清单再滤一遍（覆盖 HTML 内嵌旧索引 / 刷新又回来）
syncTrashFilterIntoData(DATA).then((n) => {
  if (n > 0) renderStage({ keepScroll: true });
});
_autoRefreshTimer = setInterval(checkAtlasUpdateOnce, AUTO_REFRESH_MS);
try {
  const rr = sessionStorage.getItem("pmem_atlas_just_reloaded");
  if (rr) {
    sessionStorage.removeItem("pmem_atlas_just_reloaded");
    showToast(rr === "manual" ? "⚡ 已刷新至最新" : "✨ 已自动同步 (" + rr + ")");
  }
} catch (e) {}
</script>
</body>
</html>
"""

def _slim_atlas_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Drop data_uri blobs from payload unless embed_images was requested."""
    embed = bool(data.get("embed_images"))
    out = dict(data)
    assets = {}
    for path, info in (data.get("assets") or {}).items():
        if not isinstance(info, dict):
            continue
        if embed:
            assets[path] = dict(info)
        else:
            assets[path] = {k: v for k, v in info.items() if k != "data_uri"}
    out["assets"] = assets
    return out


def load_workbench_guide(root: Path) -> dict[str, Any]:
    """Load teaching catalog; images live under docs/workbench_guide (not gallery-scanned)."""
    cat_path = root / "docs" / "workbench_guide" / "catalog.json"
    if not cat_path.is_file():
        return {"version": 0, "lessons": [], "missing": True}
    try:
        doc = json.loads(cat_path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 0, "lessons": [], "error": "catalog parse failed"}
    if not isinstance(doc, dict):
        return {"version": 0, "lessons": []}
    base = str(doc.get("base_dir") or "docs/workbench_guide").replace("\\", "/").rstrip("/")

    def _guide_path(rel: str) -> tuple[str, bool]:
        rel_n = str(rel or "").replace("\\", "/").lstrip("/")
        if not rel_n:
            return "", False
        full = f"{base}/{rel_n}"
        return full, (root / full).is_file()

    lessons = []
    for lesson in doc.get("lessons") or []:
        if not isinstance(lesson, dict):
            continue
        ex_out = []
        for ex in lesson.get("examples") or []:
            if not isinstance(ex, dict):
                continue
            full, exists = _guide_path(ex.get("path") or "")
            item = {
                "role": ex.get("role") or "",
                "label": ex.get("label") or "",
                "path": full,
                "exists": exists,
            }
            for k in ("round", "score", "passed", "prompt", "defects", "next_fix"):
                if k in ex and ex.get(k) is not None:
                    item[k] = ex.get(k)
            dims = ex.get("dims") or ex.get("dims_parsed")
            if isinstance(dims, dict) and dims:
                item["dims"] = {str(k): v for k, v in dims.items()}
            ex_out.append(item)
        rounds_out = []
        for r in lesson.get("rounds") or []:
            if not isinstance(r, dict):
                continue
            full, exists = _guide_path(r.get("path") or "")
            dims = r.get("dims") or r.get("dims_parsed")
            rounds_out.append({
                "round": r.get("round"),
                "label": r.get("label") or "",
                "score": r.get("score"),
                "passed": bool(r.get("passed")),
                "prompt": r.get("prompt") or "",
                "defects": r.get("defects") or "",
                "next_fix": r.get("next_fix") or "",
                "path": full,
                "exists": exists if full else None,
                "dims": {str(k): v for k, v in dims.items()} if isinstance(dims, dict) else {},
            })
        samples_out = []
        for s in lesson.get("samples") or []:
            if not isinstance(s, dict):
                continue
            samples_out.append({
                "kind": s.get("kind") or "",
                "title": s.get("title") or "",
                "body": s.get("body") or "",
                "score": s.get("score"),
            })
        lessons.append({
            "id": lesson.get("id") or "",
            "skill": lesson.get("skill") or "",
            "title": lesson.get("title") or "",
            "when": lesson.get("when") or "",
            "how": [str(x) for x in (lesson.get("how") or []) if str(x).strip()],
            "examples": ex_out,
            "rounds": rounds_out,
            "samples": samples_out,
        })
    return {
        "version": doc.get("version") or 1,
        "title": doc.get("title") or "技能教学",
        "note": doc.get("note") or "",
        "base_dir": base,
        "lessons": lessons,
    }


def write_workbench_launchers(root: Path) -> None:
    """写出可双击的「打开工作台」脚本：拉起 reveal 守护并用 http 打开工作台。

    浏览器从 file:// 打开 HTML 时不能启动本机 Python；请双击这些脚本，或点横幅「重试连通」下载同款启动脚本。
    """
    root = root.resolve()
    root_win = str(root)
    root_posix = root.as_posix()
    # 先 cd 再 Path('.')，避免 Windows bat 路径引号嵌套
    py_boot = (
        "from pathlib import Path; from atlas_reveal import ensure_reveal_daemon; "
        "print(ensure_reveal_daemon(Path('.').resolve()))"
    )
    cmd = "\r\n".join(
        [
            "@echo off",
            "chcp 65001 >nul",
            f'cd /d "{root_win}"',
            'set "PORTFILE=%TEMP%\\pmem_atlas_port.txt"',
            f'py -3 -c "{py_boot}" > "%PORTFILE%" 2>nul',
            f'if errorlevel 1 python -c "{py_boot}" > "%PORTFILE%" 2>nul',
            f'if errorlevel 1 python3 -c "{py_boot}" > "%PORTFILE%" 2>nul',
            'set /p PORT=<"%PORTFILE%"',
            'if "%PORT%"=="" set PORT=0',
            'if "%PORT%"=="0" (',
            "  echo 启动失败：请确认本机有 Python，且项目目录可 import atlas_reveal。",
            "  pause",
            "  exit /b 1",
            ")",
            'start "" "http://127.0.0.1:%PORT%/art-atlas.html"',
            "echo 已打开 http://127.0.0.1:%PORT%/art-atlas.html",
            "",
        ]
    )
    (root / "打开工作台.cmd").write_text(cmd, encoding="utf-8", newline="\r\n")
    sh = "\n".join(
        [
            "#!/bin/bash",
            "set -e",
            f"cd {json.dumps(root_posix)}",
            f"PORT=$(python3 -c {json.dumps(py_boot)} 2>/dev/null || python -c {json.dumps(py_boot)})",
            'if [ -z "$PORT" ] || [ "$PORT" = "0" ]; then',
            '  echo "启动失败：请确认本机有 Python，且项目目录可 import atlas_reveal。"',
            "  exit 1",
            "fi",
            'URL="http://127.0.0.1:${PORT}/art-atlas.html"',
            (
                'if command -v open >/dev/null 2>&1; then open "$URL"; '
                'elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"; '
                'else echo "$URL"; fi'
            ),
            "",
        ]
    )
    command_path = root / "打开工作台.command"
    command_path.write_text(sh, encoding="utf-8", newline="\n")
    try:
        command_path.chmod(command_path.stat().st_mode | 0o111)
    except OSError:
        pass


def generate_atlas_html(data: dict[str, Any], out_path: Path) -> Path:
    proj_name = data.get("config", {}).get("project", {}).get("name", "pmem-art")
    build_id = str(data.get("build_id") or "")
    root = out_path.parent.resolve()
    # 画廊用 JPEG 缩略图缓存，避免浏览器解码整张大图导致滑动空白
    try:
        from atlas_index import ensure_gallery_thumbs

        assets = data.get("assets") if isinstance(data.get("assets"), dict) else {}
        data["_thumb_stats"] = ensure_gallery_thumbs(root, assets)
    except Exception:
        pass
    reveal_port = 0
    if not os.environ.get("PMEM_ATLAS_NO_REVEAL"):
        try:
            from atlas_reveal import ensure_reveal_daemon

            reveal_port = int(ensure_reveal_daemon(root) or 0)
        except Exception:
            reveal_port = 0
    slim = _slim_atlas_payload(data)
    slim["reveal_port"] = reveal_port
    try:
        slim["workbench_guide"] = load_workbench_guide(root)
    except Exception:
        slim["workbench_guide"] = {"version": 0, "lessons": [], "error": "load failed"}
    json_str = json.dumps(slim, ensure_ascii=False).replace("</", "<\\/")
    html_out = (
        HTML_TEMPLATE.replace("__PROJECT_NAME__", html.escape(proj_name))
        .replace("__BUILD_ID__", html.escape(build_id))
        .replace("__ATLAS_JSON__", json_str)
    )
    out_path.write_text(html_out, encoding="utf-8", newline="\n")
    try:
        write_workbench_launchers(root)
    except Exception:
        pass
    try:
        from atlas_index import write_atlas_data_sidecar

        write_atlas_data_sidecar(out_path.parent, slim)
    except Exception:
        pass
    try:
        ping_dir = out_path.parent / ".memory-art"
        if ping_dir.is_dir():
            ping_payload = {
                "build_id": build_id,
                "built_at": data.get("built_at", ""),
                "assets_count": len(data.get("assets", {})),
                "images_count": len(data.get("index_images") or data.get("assets") or {}),
                "entries_count": len(data.get("entries", [])),
                "index_id": (data.get("index_images") and len(data.get("index_images") or [])),
                "reveal_port": reveal_port,
            }
            (ping_dir / "atlas_ping.js").write_text(
                "window.__PMEM_ATLAS_PING__ = " + json.dumps(ping_payload, ensure_ascii=False) + ";\n",
                encoding="utf-8",
            )
    except Exception:
        pass
    return out_path

if __name__ == "__main__":
    from pmem_art import load_project
    root = Path(__file__).resolve().parent
    data = load_project(root, embed_images=False)
    out = generate_atlas_html(data, root / "art-atlas.html")
    print(f"Built {out} ({round(out.stat().st_size / 1024, 1)} KB)")

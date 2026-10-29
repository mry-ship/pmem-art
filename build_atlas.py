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
  .gallery-virt { position: relative; }
  .gallery-spacer { width: 100%; pointer-events: none; }
  .gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(var(--thumb-size), 1fr));
    gap: var(--thumb-gap);
  }
  .asset-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 11px; overflow: hidden; display: flex; flex-direction: column;
    content-visibility: auto;
    contain-intrinsic-size: auto calc(var(--thumb-size) * 0.78 + 72px);
  }
  .asset-card:hover {
    border-color: var(--border-strong);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.28);
  }
  .asset-card.role-rejected { border-color: rgba(244, 63, 94, 0.45); }
  .asset-card.qa-fail { border-color: var(--gold); }
  body.compact-thumbs .asset-body { display: none; }
  body.compact-thumbs .asset-card {
    contain-intrinsic-size: auto calc(var(--thumb-size) * 0.78 + 4px);
  }
  body.compact-thumbs .role-tag,
  body.compact-thumbs .spec-tag { font-size: 9px; padding: 1px 5px; }
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
    display: flex; align-items: center; justify-content: center;
    overflow: hidden; cursor: zoom-in; padding: 8px;
    background: #0b101d;
  }
  .thumb-wrap img {
    max-width: 100%; max-height: 100%; object-fit: contain;
    content-visibility: auto;
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
    backdrop-filter: blur(6px);
  }
  .role-tag.anchor, .role-tag.approved { background: rgba(16, 185, 129, 0.88); color: #fff; }
  .role-tag.rejected { background: rgba(244, 63, 94, 0.92); color: #fff; }
  .role-tag.draft_violation { background: rgba(245, 158, 11, 0.92); color: #090d16; }

  .spec-tag {
    position: absolute; bottom: 8px; right: 8px;
    background: rgba(9, 13, 22, 0.82); border: 1px solid var(--border);
    padding: 2px 7px; border-radius: 4px; font-size: 10.5px; font-family: ui-monospace, monospace;
    color: var(--text-muted);
  }
  .asset-body { padding: 11px 13px; display: flex; flex-direction: column; gap: 6px; flex: 1; }
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
    display: none; position: fixed; inset: 0; z-index: 400;
    background: rgba(0, 0, 0, 0.72); backdrop-filter: blur(8px);
    align-items: center; justify-content: center; cursor: zoom-out;
    padding: 24px;
  }
  .img-viewer.open { display: flex; }
  .img-viewer-card {
    position: relative; max-width: min(94vw, 1400px); max-height: 92vh;
    display: flex; flex-direction: column; align-items: center; gap: 10px;
    cursor: default;
  }
  .img-viewer-card img {
    max-width: 92vw; max-height: calc(92vh - 52px);
    object-fit: contain; border-radius: 10px;
    box-shadow: 0 24px 64px rgba(0,0,0,0.55);
    background: #0b101d;
  }
  .img-viewer-bar {
    display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    background: rgba(17, 24, 39, 0.92); border: 1px solid var(--border);
    border-radius: 999px; padding: 6px 10px; max-width: 94vw;
  }
  .img-viewer-bar .iv-path {
    font-family: ui-monospace, monospace; font-size: 11.5px; color: var(--teal);
    max-width: 42vw; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }

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
    </div>
  </div>

  <div class="workspace">
    <aside class="sidebar" id="moduleSidebar"></aside>
    <main class="main-stage" id="mainStage"></main>
  </div>
</div>

<!-- 半透明叠层预览（点图默认进这里；点空白关闭） -->
<div class="img-viewer" id="imgViewer" title="点击空白处关闭">
  <div class="img-viewer-card" id="imgViewerCard">
    <img id="ivImg" src="" alt="" />
    <div class="img-viewer-bar">
      <span class="iv-path" id="ivPath"></span>
      <button type="button" class="btn-copy" id="ivReveal" title="在访达中显示并选中">📁 文件夹</button>
      <button type="button" class="btn-copy" id="ivCopy" title="复制绝对路径">📋 路径</button>
      <button type="button" class="btn-copy" id="ivSave" title="另存为">💾</button>
      <button type="button" class="btn-copy" id="ivDetail" title="打开详情面板">详情</button>
      <button type="button" class="btn-copy" id="ivClose" style="background:var(--danger-bg);color:#fda4af;border-color:rgba(244,63,94,0.4);">✕</button>
    </div>
  </div>
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
  <button type="button" data-act="lightbox">🧾 打开详情</button>
</div>

<script>
let DATA = __ATLAS_JSON__;

const THUMB_MIN = 96;
const THUMB_MAX = 360;
const THUMB_DEFAULT = 180;
const MAX_DECODE = 32;          // 视口内并发解码上限（过小会滑动后空白半晌）
const VIRT_ROW_BUFFER = 6;      // 上下多挂几行，滑动少重建
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
  thumbSize: THUMB_DEFAULT
};

let _galleryAssets = [];
let _virtScrollBound = false;
let _virtRaf = 0;
let _virtRangeKey = "";
let _imgIo = null;
let _decodeBusy = 0;
let _decodeQueue = [];
let _searchTimer = 0;

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
  document.documentElement.style.setProperty("--thumb-size", n + "px");
  document.documentElement.style.setProperty("--thumb-gap", n < 140 ? "8px" : "12px");
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

function getFilteredAssets() {
  const mods = new Set(getFilteredModules());
  const q = state.search.trim().toLowerCase();
  let list = Object.values(DATA.assets || {}).filter(a => {
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
    <div class="side-sub ${state.sideMode === 'all' && state.plateFilter === 'process' ? 'active' : ''}" onclick="selectPlateFilter('process')">🧪 过程稿 <span class="count">${pc.process}</span></div>
    <div class="side-sub ${state.sideMode === 'all' && state.plateFilter === 'reference' ? 'active' : ''}" onclick="selectPlateFilter('reference')">📎 参考 <span class="count">${pc.reference}</span></div>
    <div class="side-sub ${state.sideMode === 'all' && state.plateFilter === 'rejected' ? 'active' : ''}" onclick="selectPlateFilter('rejected')">❌ 废案 <span class="count">${pc.rejected}</span></div>
    <div class="side-sub ${state.sideMode === 'all' && state.plateFilter === 'ALL' ? 'active' : ''}" onclick="selectPlateFilter('ALL')">全部状态 <span class="count">${pc.ALL}</span></div>
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
            <p>默认只看定稿，过程稿（converge / r1–rN）请进左侧「过程稿」。散图归「其他」，只工作台可见，不写 recipe。定稿 ${pc.final} · 过程 ${pc.process} · 今天 ${dc.today}</p>
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
      const pc = plateCounts();
      return `<div class="empty-today">
        <div style="font-size:16px;font-weight:700;color:var(--text-main);margin-bottom:6px;">今天还没有定稿</div>
        <div style="margin-bottom:14px;">过程稿不会出现在这里。可看过程稿，或放宽时间。</div>
        <button class="btn-copy" onclick="selectPlateFilter('process')">看过程稿（${pc.process}）</button>
        <button class="btn-copy" onclick="selectDayFilter('ALL')">定稿·全部时间</button>
        <button class="btn-copy" onclick="selectPlateFilter('ALL')">看全部状态</button>
      </div>`;
    }
    return `<div class="entry-card">当前筛选下没有图。试试「定稿 / 过程稿 / 全部时间」或清掉搜索。</div>`;
  }
  return `<div class="gallery-virt" id="galleryVirt" data-count="${assets.length}">
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
    anchor: "⚓ 锚点",
    approved: "✅ 定稿",
    rejected: "❌ 废案",
    draft_violation: "⚠️ 待修",
    draft: "草稿"
  };
  const desc = a.description || a.png_meta?.reject_reason || a.png_meta?.note || PathName(a.path);
  const catIcon = a.category_icon || "🖼️";
  const catShort = a.category_short || a.module || "散图";
  const src = thumbSrc(a);
  const srcTag = sourceLabel(a.source || (a.formal ? "module" : "other"));
  return `
    <div class="asset-card role-${esc(role)} ${a.qa_passed === false ? 'qa-fail' : ''}" data-path="${esc(a.path)}" oncontextmenu="return showImgCtxMenu(event, ${JSON.stringify(a.path)})">
      <div class="thumb-wrap ${state.bgClass} ${state.showGuides ? 'show-guides' : ''}" onclick="openViewer(${JSON.stringify(a.path)})" oncontextmenu="return showImgCtxMenu(event, ${JSON.stringify(a.path)})">
        <img src="${esc(src)}" alt="" loading="eager" decoding="async" />
        ${state.showGuides ? `<div class="overlay-9slice">
          <div class="slice-line v1"></div><div class="slice-line v2"></div>
          <div class="slice-line h1"></div><div class="slice-line h2"></div>
        </div>` : ""}
        <span class="role-tag ${esc(role)}">${roleLabels[role] || esc(role)}</span>
        <span class="cat-top-badge">${catIcon} ${esc(catShort)}</span>
        <span class="src-badge">${esc(srcTag)} · ${esc(a.updated_at || a.day || '')}</span>
        <span class="spec-tag">${esc(a.resolution || '')} · ${a.size_kb || '?'}KB</span>
      </div>
      <div class="asset-body">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:6px;">
          <div class="asset-path">${esc(a.path)}</div>
          <button class="btn-copy" style="padding:2px 6px;font-size:10px;" title="在文件夹中显示" onclick="event.stopPropagation();revealInFolder(${JSON.stringify(a.path)})">📁</button>
        </div>
        <div class="asset-desc-box ${role === 'rejected' ? 'rejected' : ''}">${esc(desc)}</div>
      </div>
    </div>
  `;
}

function galleryMetrics() {
  const stage = document.getElementById("mainStage");
  const grid = document.getElementById("galleryGrid");
  const width = (grid && grid.clientWidth) || (stage ? stage.clientWidth - 24 : 800);
  const gap = state.thumbSize < 140 ? 8 : 12;
  const cols = Math.max(1, Math.floor((width + gap) / (state.thumbSize + gap)));
  const bodyH = state.thumbSize < 140 ? 0 : 70;
  const rowH = Math.round(state.thumbSize * 0.78 + bodyH + gap);
  const rows = Math.max(1, Math.ceil((_galleryAssets.length || 0) / cols));
  return { cols, rowH, rows, gap, totalH: rows * rowH };
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
  const assets = _galleryAssets;
  if (!assets.length) {
    grid.innerHTML = "";
    topSp.style.height = "0px";
    botSp.style.height = "0px";
    _virtRangeKey = "";
    return;
  }
  const { cols, rowH, rows, totalH } = galleryMetrics();
  const scrollTop = stage.scrollTop;
  const virt = document.getElementById("galleryVirt");
  const virtTop = virt ? Math.max(0, virt.offsetTop) : 0;
  const localScroll = Math.max(0, scrollTop - virtTop);
  const viewH = stage.clientHeight;
  let startRow = Math.max(0, Math.floor(localScroll / rowH) - VIRT_ROW_BUFFER);
  let endRow = Math.min(rows, Math.ceil((localScroll + viewH) / rowH) + VIRT_ROW_BUFFER);
  if (endRow <= startRow) endRow = Math.min(rows, startRow + 1);
  const startIdx = startRow * cols;
  const endIdx = Math.min(assets.length, endRow * cols);
  const rangeKey = [startIdx, endIdx, cols, state.thumbSize, assets.length, state.showGuides ? 1 : 0].join(":");
  topSp.style.height = (startRow * rowH) + "px";
  botSp.style.height = Math.max(0, totalH - endRow * rowH) + "px";
  // 同一窗口不重建 DOM，避免滑动时反复卸载/重载图片造成空白延迟
  if (!force && rangeKey === _virtRangeKey && grid.children.length) return;
  _virtRangeKey = rangeKey;
  const slice = assets.slice(startIdx, endIdx);
  grid.style.gridTemplateColumns = `repeat(${cols}, minmax(0, 1fr))`;
  // 直接写 src：虚拟窗口已限制张数，再排队懒解码反而滑动后空白
  grid.innerHTML = slice.map(cardHtml).join("");
  if (_imgIo) { try { _imgIo.disconnect(); } catch (e) {} _imgIo = null; }
  _decodeQueue = [];
  _decodeBusy = 0;
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

function bindVirtualScroll() {
  const stage = document.getElementById("mainStage");
  if (!stage || _virtScrollBound) return;
  _virtScrollBound = true;
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

function renderStage() {
  renderHeaderAndSidebar();
  const stage = document.getElementById("mainStage");
  let content = renderModuleBanner();
  if (state.tab === "gallery") content += renderGalleryTab();
  else if (state.tab === "improve") content += renderImproveTab();
  else if (state.tab === "redlines") content += renderRedlinesTab();
  else if (state.tab === "recipes") content += renderRecipesTab();
  else if (state.tab === "memories") content += renderMemoriesTab();
  else if (state.tab === "qa") content += renderQaTab();
  stage.innerHTML = content;
  bindVirtualScroll();
  if (state.tab === "gallery") scheduleVirtualPaint(true);
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

function downloadRevealHelper(absFile) {
  const win = isWindowsAbs(absFile);
  let name, body;
  if (win) {
    const winPath = String(absFile).replace(/\//g, "\\");
    name = "打开图片位置.bat";
    body = "@echo off\r\nexplorer /select,\"" + winPath + "\"\r\n";
  } else {
    name = "打开图片位置.command";
    body = "#!/bin/bash\nopen -R " + JSON.stringify(absFile) + "\n";
  }
  const blob = new Blob([body], { type: "application/octet-stream" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 1500);
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
  const fromData = Number(DATA.reveal_port || 0);
  if (fromData) ports.push(fromData);
  const fromPing = Number((window.__PMEM_ATLAS_PING__ || {}).reveal_port || 0);
  if (fromPing && !ports.includes(fromPing)) ports.push(fromPing);
  for (const p of [8765, 8766, 8767, 8768]) {
    if (!ports.includes(p)) ports.push(p);
  }
  return ports;
}

async function revealViaBridge(relPath) {
  const q = encodeURIComponent(relPath);
  for (const port of revealPorts()) {
    try {
      const res = await fetch("http://127.0.0.1:" + port + "/api/reveal?path=" + q, {
        method: "GET",
        cache: "no-store",
        mode: "cors"
      });
      if (res.ok) {
        const j = await res.json().catch(() => ({ ok: true }));
        if (j && j.ok !== false) return true;
      }
    } catch (e) {}
  }
  return false;
}

/** 在系统访达 / 资源管理器中打开所在文件夹（并选中该图） */
window.revealInFolder = async function(relPath) {
  const abs = absAssetPath(relPath);
  const dir = parentDirOf(abs);
  copyText(abs, "文件绝对路径");
  showToast("正在打开文件夹…");
  const ok = await revealViaBridge(relPath);
  if (ok) {
    showToast("📁 已在访达/资源管理器中定位");
    return;
  }
  // 兜底：下载一键脚本（浏览器拦 file:// 时）
  try { downloadRevealHelper(abs); } catch (e2) {}
  showToast("未连上定位服务。请先在项目目录跑 python3 pmem_art.py atlas，再点 📁；或双击下载的脚本。文件夹：" + dir);
};

window.closeViewer = function() {
  const v = document.getElementById("imgViewer");
  if (v) v.classList.remove("open");
};

/** 半透明叠层放大原图（点空白 / Esc 关闭） */
window.openViewer = function(assetPath) {
  const info = DATA.assets[assetPath];
  if (!info) {
    showToast("找不到这张图的索引");
    return;
  }
  hideImgCtxMenu();
  state.lbPath = assetPath;
  const img = document.getElementById("ivImg");
  const pathEl = document.getElementById("ivPath");
  img.src = assetSrc(info);
  pathEl.textContent = assetPath;
  pathEl.title = absAssetPath(assetPath);
  document.getElementById("imgViewer").classList.add("open");
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
  const info = DATA.assets[assetPath];
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
  document.getElementById("lbAside").innerHTML = `
    <div>
      <div style="font-size:11px;color:var(--text-dim);text-transform:uppercase;">来源 / 模块</div>
      <div style="font-size:15px;font-weight:700;color:var(--teal);margin-top:2px;">${esc(sourceLabel(info.source))} · ${esc(info.module || "unassigned")}</div>
      <div class="lb-path-actions">
        <button class="btn-copy" onclick="copyText(absAssetPath(state.lbPath), '绝对路径')">📋 复制绝对路径</button>
        <button class="btn-copy" onclick="revealInFolder(state.lbPath)">📁 在文件夹中显示</button>
        <button class="btn-copy" onclick="saveAssetAs(state.lbPath)">💾 另存为</button>
        <button class="btn-copy" onclick="openInEditor(state.lbPath)">📂 在编辑器打开</button>
      </div>
    </div>
    <div style="background:#090d16;padding:10px 12px;border-radius:8px;border:1px solid var(--border);font-size:12px;">
      <div>时间: <b>${esc(info.updated_at || info.day || "")}</b></div>
      <div>分辨率: <b>${esc(info.resolution || "")}</b> | 通道: <b>${esc(info.mode || "")}</b></div>
      <div>体积: <b>${info.size_kb || "?"} KB</b></div>
      <div style="margin-top:4px;color:${info.formal ? '#6ee7b7' : '#94a3b8'};">
        ${info.formal ? "✅ 正式模块资产" : "👁️ 可见索引（未正式 ingest）"}
      </div>
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
imgViewer.addEventListener("click", () => closeViewer());
imgViewerCard.addEventListener("click", (ev) => ev.stopPropagation());
document.getElementById("ivClose").addEventListener("click", (ev) => {
  ev.stopPropagation();
  closeViewer();
});
document.getElementById("ivReveal").addEventListener("click", (ev) => {
  ev.stopPropagation();
  if (state.lbPath) revealInFolder(state.lbPath);
});
document.getElementById("ivCopy").addEventListener("click", (ev) => {
  ev.stopPropagation();
  if (state.lbPath) copyText(absAssetPath(state.lbPath), "绝对路径");
});
document.getElementById("ivSave").addEventListener("click", (ev) => {
  ev.stopPropagation();
  if (state.lbPath) saveAssetAs(state.lbPath);
});
document.getElementById("ivDetail").addEventListener("click", (ev) => {
  ev.stopPropagation();
  if (state.lbPath) openLightbox(state.lbPath);
});
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
  else if (act === "lightbox") openLightbox(p);
});
document.addEventListener("click", () => hideImgCtxMenu());
document.addEventListener("scroll", () => hideImgCtxMenu(), true);
window.addEventListener("keydown", e => {
  if (e.key === "Escape") {
    hideImgCtxMenu();
    closeViewer();
    document.getElementById("lightbox").classList.remove("open");
  }
});

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
    DATA = next;
    renderHeaderAndSidebar();
    renderStage();
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
    json_str = json.dumps(slim, ensure_ascii=False).replace("</", "<\\/")
    html_out = (
        HTML_TEMPLATE.replace("__PROJECT_NAME__", html.escape(proj_name))
        .replace("__BUILD_ID__", html.escape(build_id))
        .replace("__ATLAS_JSON__", json_str)
    )
    out_path.write_text(html_out, encoding="utf-8", newline="\n")
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

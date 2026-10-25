---
name: pmem-critique
description: 当用户输入 /pmem-critique 或 /art-check 对现有图片进行审稿挑刺时触发。对照项目历史红线与模块规格进行五维打分，指出不合理之处，并可将问题一键记入 style_redline。
---

# `/pmem-critique`（别名 `/art-check`）— 主美级五维审稿与红线入库

当用户丢入一张或多张图让 Agent「审一下 / 看看哪里不合理 / 打个分」时执行：

1. **召回模块基准**：
   - 运行 `python3 pmem_art.py search --module <模块>` 获取已有红线、色板与管线规格。
   - 运行 `python3 pmem_art.py classify <图片路径>` 获取分辨率、宽高比、Alpha 透明通道等物理参数。
2. **五维打分与挑刺（Absolute-5D，与 `converge judge` 同一套标签）**：
   - 每维满分 10，写入格式：`构图x/光影x/透视x/质感x/风格x`（例：`构图8.6/光影8.2/透视7.8/质感8.0/风格8.4`）。
   - UI/App Icon 专用标签仅在对应资产上使用；**禁止**再手填旧加和尺「风格2.5/结构2.5/…」当主报告（旧串仍可被解析，但新审稿一律 Absolute-5D）。
   - 明确列出 **✅ 合理亮点** 与 **❌ 不合理/需返修点**，并给出可直接用于下一轮重绘的 **修正 Prompt 建议**。
3. **自动沉淀红线**：
   - 若评分 `< 9.6` 或用户认可某条挑刺结论，调用 `python3 pmem_art.py feedback "<具体不合理点>" --module <模块> --asset <图片路径>` 自动写入记忆库。
4. **展示与静默边界**：默认必须向用户展示 Absolute-5D 分数卡 + ✅/❌ 要点 + 修正 Prompt；记忆写入仍勿旁白。完整 `/pmem-coach` 练习计划仅当用户明确要教练或 `--verbose` 时再展开；CLI 若打出一行「小提示」可原样转述（每会话最多 1 条）。

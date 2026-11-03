# 工作台教学素材（Workbench Guide）

给美术用的技能对照包，挂在 `art-atlas.html` 顶部 **「教学」** 按钮里。

## 给美术看

1. 打开工作台 → 点 **教学**。
2. 左侧按「总控 / 生图 / 界面 / 图标…」分组；点一课看「什么时候用、怎么用」。
3. 有示例的课会排成 **原图 → 过程 → 终稿**，点图可放大（放大层在教学弹窗之上）。
4. 生图类课会额外显示 **提示词进化 · 轮次评分**（每轮 Prompt / 不足 / 改点 / 分数）。
5. 总控 / 提示词 / 只审图等有 **样例演示** 文字卡。
6. **复制指令** 可把 `/pmem-draw` 这类斜杠命令拷到对话框。
7. 这些示例图 **不进主画廊**，工作台批量删除也删不掉。

## 给维护者看

- 目录必须进 git（`.gitignore` 已 `!docs/workbench_guide/**`）。
- 刷新示例图与目录：

```bash
python docs/workbench_guide/_write_catalog.py
python docs/workbench_guide/_seed_copy.py
python pmem_art.py atlas
```

- 第一张一律 `role: original`、标签「原图」；克隆与变体用不同素材；合成梯首张是海船原图版式，不是过程整表。

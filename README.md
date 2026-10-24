# 🎨 pmem-art — 在 Cursor 里越画越准的个人美术积累记忆

<p align="left">
  <img src="https://img.shields.io/badge/version-v0.8.0-0ea5e9?style=for-the-badge" alt="v0.8.0"/>
  <img src="https://img.shields.io/badge/python-%3E%3D3.10-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/UX-Cursor%20对话优先-8b5cf6?style=for-the-badge" alt="Cursor-first"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-f59e0b?style=for-the-badge" alt="GPL-3.0"/>
</p>

> **一句话**：你在 Cursor 里画一张 → 用中文说「哪里不对 / 这版留着」→ 记忆自动变长 → **下一张更准**。  
> 姊妹项目：[mry-ship/pmem](https://github.com/mry-ship/pmem)（代码工程记忆）· 本仓库专做 **个人项目里稳定画风下的美术迭代记忆**。

📘 [画师手册 USER_MANUAL.md](./USER_MANUAL.md) · 🧠 [架构 ARCHITECTURE.md](./ARCHITECTURE.md) · ⚖️ [LICENSE](./LICENSE) · 🖼️ [可选回看 art-atlas.html](./art-atlas.html)

---

## 这是什么 / 不是什么

| ✅ 是 | ❌ 不是 |
| :--- | :--- |
| 一个人（或小团队）在 **同一个项目、画风基线已定** 里，用 Cursor 反复生图、改图时的 **积累记忆** | 主美审稿台、管线质检台、资产管理系统 |
| 对话里一句话就能留下红线与定稿（**不用手写 YAML**） | 要求你天天敲一长串 CLI 的工具 |
| 后端悄悄按角色/UI/特效/场景/画风分叉归类 | 把分类域名甩到你脸上当主界面 |
| 偶尔打开 `art-atlas.html` 回看正反例 | 以 HTML 图谱当每天第一入口 |

**心智模型**：`生图 → 反馈 → 记忆长大 → 下次更准`（styles / icons / UI / 概念图分叉都适用）。

---

## 30 秒：你在 Cursor 里怎么用

假设项目里已经放了本仓库（或 `init` 过），并且有 `.cursor/rules/pmem-art.mdc`（`alwaysApply`）。

### ① 让 Agent 生一张

> 「给 Astra 画一张半身立绘，青瓷白袍，透明底」

Agent 会先 `search` 已有红线/定稿，再调用生图工具。

### ② 你看图，用自然语言反馈（核心）

直接说，例如：

| 你说 | 系统会记住 |
| :--- | :--- |
| **「太赛博了，别这样画」** | 红线 `style_redline`：下次禁止霓虹/赛博方向 |
| **「头太大」** / **「比例不对」** | 红线或勘误：头身约束 |
| **「这版留着」** / **「就这个」** | 定稿 `recipe`：正向锚点，下次优先沿用 |
| **「换成水彩」** / **「改成 Q 版」** | 勘误 + 画风分叉（与正比隔离） |
| **「以后都用青瓷白+墨蓝，别霓虹」** | 拍板 `art_decision` |

Agent 会执行类似：

```bash
python3 pmem_art.py feedback "太赛博了，别这样画" --module character.Astra --asset .cursor/generated/xxx.png
```

你**不用**自己写 Markdown / YAML。

### ③ 下一张会自动更准

再次生「Astra 立绘」时，Agent 会召回你刚留下的红线与定稿，把「别赛博」「留着的那版方向」写进约束。  
**画得越多、评得越多，记忆越厚，越准。**

---

## 装进你的项目（三种情况）

### 空项目 / 刚立项

```bash
# 把 pmem-art 的脚本放进项目根（或 git clone 后拷贝关键文件）
python3 pmem_art.py init --name "我的项目"
python3 pmem_art.py bootstrap --mode young --apply
```

然后打开 Cursor，直接开始生图 + 用中文评图即可。

### 已有一堆图的老项目

```bash
python3 pmem_art.py bootstrap --mode legacy --roots Art assets
python3 pmem_art.py candidates
python3 pmem_art.py accept --all   # 只提升候选，不乱移文件
```

之后同样：在对话里反馈 → 记忆增长。老文件默认 **不自动搬家**。

### 已经在 Cursor 里狂生图

把新图路径和那句 prompt 交给 Agent，或：

```bash
python3 pmem_art.py ingest .cursor/generated/xxx.png -p "角色Astra 水彩 概念图" --apply
```

分类（角色/UI/特效/画风分叉）在后台完成；低置信度进 `misc.*`，不污染正式模块。

---

## 自然语言触发词速查（中文优先）

```
红线（别再这样）: 太赛博 / 太霓虹 / 别这样画 / 不要再 / 头太大 / 比例不对 / 发色不对 / 漏抠 / 黑底
定稿（留着）    : 这版留着 / 就这个 / 定稿 / 过了 / 可以用 / 保留
修正 / 换画风   : 换成水彩 / 改成Q版 / 换成像素 / 修一下 / 改成厚涂
拍板            : 以后都用… / 就定… / 统一用… / 风格定了
```

对应命令（Agent 自动跑；你也可以自己跑）：

```bash
python3 pmem_art.py feedback "<原话>" -m <模块> [-a <图片>]
python3 pmem_art.py note "<原话>"        # 同上，更短别名
python3 pmem_art.py search -m character.Astra
python3 pmem_art.py search "赛博"
```

---

## 后端默默做的事（你通常不用管）

- 领域：`brand` / `character` / `scene` / `ui` / `vfx` / `anim` / `misc`
- 画风分叉：同一角色的水彩 / Q版 / 像素 → `character.Astra.Watercolor` 等子模块，父子继承
- 四信号分类：Prompt + 路径 + 图像特征 + 已有模块
- 可选：`art-atlas.html` 回看正反例与配方（`python3 pmem_art.py atlas`）——**偶尔用，不是主入口**

完整命令与模块规范见 📘 [USER_MANUAL.md](./USER_MANUAL.md)。

---

## License

[GNU GPL v3.0](./LICENSE) · 与 [mry-ship/pmem](https://github.com/mry-ship/pmem) 一致。

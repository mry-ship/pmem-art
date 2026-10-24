# 📘 pmem-art 画师手册 — 怎么在 Cursor 里越画越准

> **版本** v0.8.0 · **主入口**：Cursor 对话（不是 CLI 百科，不是 HTML 审稿台）  
> **适合**：一个人或小团队，在 **同一个项目、画风基线相对稳定** 时，用 Cursor 反复生图/改图。

---

## 目录

1. [第一章：它到底帮你解决什么](#第一章它到底帮你解决什么)
2. [第二章：第一次装进项目](#第二章第一次装进项目)
3. [第三章：日常循环（生图 → 说话 → 更准）](#第三章日常循环生图--说话--更准)
4. [第四章：你会说的话 → 系统怎么记](#第四章你会说的话--系统怎么记)
5. [第五章：角色 / UI / 特效 / 多画风（后台分类）](#第五章角色--ui--特效--多画风后台分类)
6. [第六章：可选工具（图谱、体检、命令）](#第六章可选工具图谱体检命令)
7. [第七章：FAQ](#第七章faq)

---

## 第一章：它到底帮你解决什么

在 Cursor 里画同一套项目视觉时，最烦的是：

1. **上周刚骂过「别画赛博霓虹」**，这周 Agent 又画出来了。  
2. **某张特别好**，过两天忘了当时方向，再也抽不回来。  
3. **水彩概念图和正比立绘搅在一起**，越改越乱。  
4. 不想学一套「美术资产管理」或天天填表。

pmem-art 的答案很简单：

> **你只管评图；评过的话变成记忆；下次生图自动带上。**

YAML、模块名、`classify` 分数——都是给 Agent / 脚本用的；你日常只说话。

---

## 第二章：第一次装进项目

### 2.1 空项目

```bash
python3 pmem_art.py init --name "我的游戏"
python3 pmem_art.py bootstrap --mode young --apply
```

会得到：

- `.memory-art/`（记忆库，跟 Git 走）
- `assets/{brand,character,scene,ui,vfx,anim}/`
- `.cursor/rules/pmem-art.mdc`（**对话规则，alwaysApply**）
- `.cursor/hooks.json`（生图前召回 / 落盘后提醒）

然后用 Cursor 打开项目，直接开画。

### 2.2 老项目（已有乱目录）

```bash
python3 pmem_art.py bootstrap --mode legacy --roots Art Content assets
python3 pmem_art.py accept --all
```

**不会擅自移动你的旧文件。** 只建立模块候选与记忆架子；之后靠对话反馈慢慢变准。

### 2.3 确认规则在

打开 `.cursor/rules/pmem-art.mdc`，应看到：生图前 search、用户说「太赛博/这版留着…」时跑 `feedback`。  
若没有，再跑一次 `init`（或从本仓库拷贝该文件）。

---

## 第三章：日常循环（生图 → 说话 → 更准）

```text
你：给 Astra 画半身立绘，青瓷白袍
    ↓
Agent：search 记忆 → 带上旧红线/定稿 → GenerateImage
    ↓
你：太赛博了，别这样画
    ↓
Agent：pmem_art.py feedback "太赛博了，别这样画" -m character.Astra -a <这张图>
    ↓
你：再画一张
    ↓
Agent：search 时已经能读到「禁止赛博」→ 新图更贴青瓷方向
```

### 你需要做的

- 正常下指令生图  
- 看完用**短中文**评一句  
- 偶尔说「这版留着」把好的钉住  

### 你不需要做的

- 手写 `.md` 记忆卡  
- 先开 `art-atlas.html` 再干活  
- 背模块 ID（说「Astra」「背包弹窗」即可，Agent 会对应）

---

## 第四章：你会说的话 → 系统怎么记

Agent（或你）统一用：

```bash
python3 pmem_art.py feedback "<原话>" [--module 模块] [--asset 图片路径]
# 别名
python3 pmem_art.py note "<原话>" ...
```

| 原话类型 | 判定 | 写入 kind | 关联图角色 |
| :--- | :--- | :--- | :--- |
| 太赛博 / 别这样画 / 头太大 / 不要再… | 否定 | `style_redline` | rejected |
| 这版留着 / 就这个 / 定稿 / 过了 | 肯定 | `recipe` | approved |
| 换成水彩 / 改成Q版 / 修一下… | 修正 | `visual_correction` | reference |
| 以后都用… / 就定… / 统一用… | 拍板 | `art_decision` | — |

文件落在：`.memory-art/entries/<模块>/CHAT….md`  
下次 `search` 会按模块（含父级）召回。

**自己试一句：**

```bash
python3 pmem_art.py feedback "太赛博了，别这样画" -m character.Astra --dry-run
python3 pmem_art.py feedback "这版留着" -m character.Astra -a assets/character/astra_standing_v3.png
python3 pmem_art.py search -m character.Astra
```

---

## 第五章：角色 / UI / 特效 / 多画风（后台分类）

你说话时不必提这些；但心里有数会更顺：

| 领域 | 典型内容 | 模块例子 |
| :--- | :--- | :--- |
| character | 立绘、表情、三视图 | `character.Astra` |
| ui | 弹窗、图标、九宫格 | `ui.InventoryHUD` |
| vfx | 刀光、序列帧 | `vfx.ArcaneSlash` |
| scene | 气氛图、场景 | `scene.FloatingRuins` |
| brand | 全局色板、风格圣经 | `brand.WorldStyle` |
| anim | Spine / Live2D 等 | `anim.*` |
| misc | 暂时看不准的 | `misc.*`（候选） |

**同一角色多种画风**：说「换成水彩」后，ingest/分类会倾向 `character.Astra.Watercolor` 子模块，和正比立绘分开，避免管线规格打架。

持续生图归档：

```bash
python3 pmem_art.py ingest .cursor/generated/foo.png -p "角色Astra 水彩 概念图" --apply
python3 pmem_art.py classify-watch --apply
```

---

## 第六章：可选工具（图谱、体检、命令）

这些是**回看 / 排查**用，不是每天第一步。

| 命令 | 何时用 |
| :--- | :--- |
| `search` / `feedback` / `note` | **每天**（或交给 Agent） |
| `ingest` / `classify` | 新图要归档时 |
| `list` | 看看有哪些模块 |
| `doctor` / `validate` | 觉得图规乱了、透明底丢了 |
| `atlas` | 想打开 `art-atlas.html` 看正反例滑杆、色板 |
| `bootstrap` / `accept` / `place` | 第一次接入 / 老项目 |
| `hook pre-gen\|post-asset\|stop` | Cursor hooks 自动调用 |

`art-atlas.html`：双击可看画廊、Do/Don't 滑杆、配方复制——**适合阶段回顾，不是对话替代品**。

---

## 第七章：FAQ

**Q：我不会 Python / 不想碰终端？**  
A：在 Cursor 里正常说话即可；规则会要求 Agent 自己跑 `search` / `feedback`。

**Q：记忆会不会把项目写乱？**  
A：反馈只追加 `.memory-art/entries/...`；老项目模式默认不移动你的现有资产。

**Q：和 ComfyUI / 本地 SD 的关系？**  
A：配方可以记在 `recipe` 里；日常仍建议在 Cursor 对话里用「这版留着 / 别这样」积累，不必先学工作流 JSON。

**Q：想暂时关掉？**  
A：说「跳过美术记忆」或「skip-art-memory」。

**Q：GPL-3.0？**  
A：是，与 mry-ship/pmem 一致，见 `LICENSE`。

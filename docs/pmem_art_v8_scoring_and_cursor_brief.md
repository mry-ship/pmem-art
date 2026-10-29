# pmem-art V8：公允评分机制 + 追平 V2 改码说明

> 给 Cursor 整份粘贴即可。权威工作区：`/Users/yanghu/Desktop/pmem-art/`  
> 先改代码与任务，**先不出图**；改完用文末验收，等确认再跑 GenerateImage。

---

## 一、背景（为何要改）

1. **V6/V7 闸门**：曾用「严格保留 DNA / 垫图一致性高 / 构图锁死」把 high/recompose 按 low 养；Desktop `skills_kit` 已松闸，任务层需保持松闸并加回展陈密度。
2. **V7 评分不公允**：`v7_image_scorer` 用 gen↔ref 的 struct/MSE 等启发式；HTML「原图 Baseline」是 `(ref, ref)` + `api_scale=low` 自测（struct=1 虚高），不能证明「原图比 bot 好」。
3. **V7 观感逊于 V2（同档）**：夜城 high 接近；粉彩 / 肖像 / 夜城 recompose 更空、更暗——主因是提示「叙事道具只保留原图已有」挤掉 V2 级镜头，且 live「多轮」多半是换 `_r1` 文件，缺陷不回流再生成。
4. **V2 分数是剧本分**（写入 dims 爬到 ≈9.7），不可与 V7 诚实分横比；但 V2 的 **goal/镜头文案** 是展陈参照。

四张 ref 不变：`style_ref_01_night_city`（9:16）、`style_ref_02_pastel_sketch`（4:3）、`style_ref_03_sunlit_portrait`（3:4）、`web_ref_01_concept_ishtar`（4:3）。

---

## 二、最公允的评分机制（设计规格）

### 2.1 目标

回答：**「这张图作为该档交付，绝对好不好 / 是否优于起点」**，而不是「像不像原图」。

### 2.2 原则

| 要 | 不要 |
| --- | --- |
| 绝对品质五维（构图 / 光影 / 透视解剖 / 质感 / 风格） | 用 MSE / struct 当主分 |
| 原图与 bot **同一套量表、同一打分器** | 原图按 low 自测、bot 按别的 scale |
| 按档看是否完成档位意图 | 全档「贴原图就高分」 |
| 诚实可复现；剧本分若保留须大字标明 | 静默 scripted 爬到 9.7 假装收敛 |

### 2.3 双轨结构

**主轨 A — Absolute-5D（HTML / STOP 主数字）**

- 输入：单张图路径（可选短档位标签）。
- 输出：五维 + 加权总分。
- **禁止**依赖 gen↔ref 的 MSE/struct 作为主分。
- 优先接 Desktop `skills_kit` 已有 VLM judge；若暂无 VLM，也必须是「只看单图」的启发式，且对 ref 自测不会因 struct=1 刷满构图/风格。
- 原图 Baseline 与每张 bot 用**完全相同**的调用。
- 权重可随档微调，五维定义不变：
  - low：质感 / 缺陷略高
  - medium：光影 + 质感
  - high / recompose：光影 + 构图意图略高
- STOP 仍可用 ≥9.60，但必须来自 A 轨。

**辅轨 B — Intent / Delta（诊断，不替代主分）**

- **Intent**：该档是否完成指令（high=戏剧光升级；recompose=机位是否真变；bold=风格是否跳）——规则或轻量分类，PASS/FAIL + 短理由。
- **Delta**：`score_A(bot) − score_A(原图)`，两边同尺。
- MSE/struct 仅 meta 日志，**零权重进总分**。

### 2.4 原图 Baseline 正确写法

```text
baseline = Absolute5D(ref_image)   # 与 bot 同一函数
# 禁止：score_image(ref, ref, scale="low")  → struct=1 虚高
```

### 2.5 与当前 V7 的差别（一句话）

现在是「相对原图像素的启发式」+「原图 low 自测」→ 原图虚高、大胆档吃亏；公允版是「绝对五维为主 + 档位意图为辅 + Delta 同尺」。

---

## 三、对照 V2：代码与任务要改什么

### 3.1 不要做

- 不要恢复全档「严格保留DNA / 参考垫图一致性高 / 构图：锁死」。
- 不要恢复 V6 的 `struct > 0.35 → ≥9.60` 保送。
- 不要用 scripted scores 冒充 VLM 达标（若保留剧本分，HTML 必须大字标明「剧本分」）。
- 不要用原图 `(ref, ref)` + low struct 当 Baseline。
- 用户可见文案用「最优方向」，不用「提质」。

### 3.2 评分落地（必做）

1. 新建 `scripts/absolute_5d_scorer.py`（或扩展现有 judge），实现上文主轨 A。
2. Baseline = `absolute_5d(ref)`，写入 report / HTML。
3. 将 `v7_image_scorer.score_image_v7(gen, ref)` 的 struct 进 composition/style **降为诊断**；主分改走 Absolute-5D。
4. Report / HTML：主分 Absolute-5D；旁注 `Δ = bot − baseline`；Intent 小标（recompose 换机位 / bold 风格跳）；注释「旧 V2 showcase 分为 scripted，不可横比」。
5. STOP ≥9.60 只认 Absolute-5D；high / recompose / bold 保持 `min_rounds≥2`。

### 3.3 任务 / 提示追平 V2（必做）

产出：`bot_tasks_v8.json` + 更新 `best_prompts_by_scale.json`。  
在 V7 松闸（无 DNA/垫图套话）基础上，**加回 V2 级展陈密度**。提示原文可从 `scripts/run_16_pmem_art_images_v2_bots.py`（或 box 同源）摘取。

| 档 | 改法 |
| --- | --- |
| **high** | 学 V2 具体光/道具/镜头。夜城：青银剑气、升空孔明灯、万家灯火；粉彩：颈间耳机、暖金粉尘、朱红/钴蓝排线；肖像：雏菊墙 + 胶片尘 + 二分光；Ishtar：体积光 / 龙锚点。**删除或弱化**「叙事道具只保留原图已有主体」→ 改为「可加风格内叙事点缀，不换主体身份」。少写重复「保持原图媒介」套话。goal 保持 **50–80%**。 |
| **recompose** | 学 V2 大机位差。夜城用「水道乌篷船 / 低机位仰高拱石桥」级，**不要**弱成「阳台仍俯城」。目标机位写死；禁止旧俯瞰 DNA。 |
| **recompose_bold** | 与 recompose **拆开**：只写目标风格圣经 + 剪影；禁止同一句混装阳台 + 赛博 + 保色板（禁 V7 bot_08 式冲突）。 |
| **medium** | 强化光雾/介质，可轻度点缀，不锁死道具归零。 |
| **low** | 保持微修；最优方向仅微质感。 |
| **best 按档** | high+ = 加法清单（光/道具/张力）；禁止锁死构图；low+ 仅微质感。 |

锁词扫描须 0 命中：`严格保留DNA`、`参考垫图一致性高`、`构图：锁死`。

### 3.4 生成路径（强烈建议同批）

1. `run_32bots_v7_live.py` → `run_32bots_v8_live.py`：R2+ 必须根据 Absolute-5D / Intent 失败项 **改写 prompt 再 GenerateImage**；禁止只换 `_r1` 文件假装收敛。或同档 2–3 张按主分选优。
2. 批跑 `PYTHONPATH` 指向 Desktop `/Users/yanghu/Desktop/pmem-art` 的 `skills_kit/` 包；禁止回退 Box 旧单体 + `bot_tasks_v6`。

### 3.5 Desktop 对齐杂项

- `pmem_art.py`：`sha256_16` 比较前 `str()` coerce（若尚未对齐）。
- `check-scale-gates --self-check` 须继续 4/4 OK。
- 垫图/AR 可继续 `validate_converge_params` 继承，但 prompt **不要**写「参考垫图一致性高」。

---

## 四、验收命令（改完请跑并贴结果）

```bash
cd /Users/yanghu/Desktop/pmem-art
export PYTHONPATH="/Users/yanghu/Desktop/pmem-art${PYTHONPATH:+:$PYTHONPATH}"
python3 pmem_art.py check-scale-gates --self-check

rg -n '严格保留DNA|参考垫图一致性高|构图：锁死|叙事道具只保留原图已有' bot_tasks_v8.json best_prompts_by_scale.json
# 上式命中须为 0

rg -n '≤60%' bot_tasks_v8.json
# high 相关须 0；应出现 50–80% 或 50%–80%

rg -n '孔明灯|sky lantern|耳机|雏菊|乌篷|仰.*桥|arch bridge' bot_tasks_v8.json
# high / 夜城 recompose 应有具体镜头

rg -n 'struct\s*>\s*0\.35' scripts/*scorer*.py skills_kit/
# 须 0

rg -n 'min_rounds' scripts/run_*v8*.py scripts/run_32*.py
# high/recompose/bold 路径须有 ≥2

# Baseline 不得再走 (ref,ref)+low struct 主分
rg -n 'score_image_v7|absolute_5d' scripts/*.py
```

另确认：

- 夜城 recompose goal 含仰桥 / 乌篷船级新机位，且无「高空俯瞰…左下飞檐」旧句。
- HTML/report 主分为 Absolute-5D；有 Δ；有「V2 剧本分不可横比」说明。
- 批跑说明里写清 `PYTHONPATH` 指向 Desktop `skills_kit`。

完成后列出改动文件；**先等确认再出图**。

---

## 五、参考路径

| 用途 | 路径 |
| --- | --- |
| 权威代码 | `/Users/yanghu/Desktop/pmem-art/` |
| V2 提示参照 | `scripts/run_16_pmem_art_images_v2_bots.py` |
| V2 图 | `pmem-art-images/generated_v2/` 或 box `/workspace/pmem-art/pmem-art-images/generated_v2/` |
| V7 任务（松闸骨架） | `bot_tasks_v7.json`、`best_prompts_by_scale.json` |
| V7 旧 scorer（勿再作主分） | `scripts/v7_image_scorer.py` |
| V7 批跑说明 | `scripts/README_V7_BATCH.md` |
| 松闸自检 | `python3 pmem_art.py check-scale-gates --self-check` |

---

## 六、交付物预期（本轮 Cursor 改完时应有）

- [ ] `scripts/absolute_5d_scorer.py`（或等价）+ Baseline 同尺
- [ ] `bot_tasks_v8.json`（无锁词；high/recompose 含 V2 级镜头）
- [ ] `best_prompts_by_scale.json` 按档加法、无锁死
- [ ] `scripts/run_32bots_v8_live.py`（真缺陷回流或选优）+ README
- [ ] Report/HTML 字段：主分、Δ、Intent；标明旧 V2 为剧本分
- [ ] 上文验收命令全绿

（出图与 32 bot showcase 等确认后再做。）

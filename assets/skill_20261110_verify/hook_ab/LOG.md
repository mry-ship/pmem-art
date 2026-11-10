# Hook 逐步对照（每次只改一个变量）

## 固定变量
- 题材：露莓果酱 8 档整表
- 提示词：见同目录 `FIXED_PROMPT.txt`（全程一字不改）
- 垫图：无（避免第二变量）
- 引擎：Cursor GenerateImage · 9:16
- 目标画法：GH 手绘软渐变（柔粉彩、无硬镜面高光、轻接触影）
- 每步同词连出 3 张，防单张运气

## 步进（果酱）
| 步 | 关了什么 | 出图 | 肉眼（好/差/一样） | 备注 |
| --- | --- | --- | --- | --- |
| 0 | 仅 pre-gen（现状） | `hook_ab_s0_a/b/c.jpg` | **好（基线）** | 三张整体偏软绘粉彩、无硬糖釉镜面；格内容有随机差 |
| 1 | + post-asset | `hook_ab_s1_a/b/c.jpg` | **一样** | 相对步0：画法档位无跳变 |
| 2 | + stop（pmem-art） | `hook_ab_s2_a/b/c.jpg` | **一样** | 相对步1：无跳变；细节随机仍在 |
| 3 | + art_shell_hook | `hook_ab_s3_a/b/c.jpg` | **一样** | 相对步2：无跳变 |

## 跨题材抽检（恢复「只关 pre-gen」后；同词各 2 张）
| 题材 | 固定提示词 | 出图 | 肉眼 |
| --- | --- | --- | --- |
| 图标A 充电宝 | `FIXED_PROMPT_ICON.txt` | `hook_ab_x_icon_a/b.jpg` | **好**：偏软绘哑光方砖，非硬糖釉；两张构图有随机差 |
| UI 三消主菜单 | `FIXED_PROMPT_UI.txt` | `hook_ab_x_ui_a/b.jpg` | **好**：软绘休闲菜单；两张版式有随机差，画法档位接近 |

## 结论（眼判）
1. **post-asset / stop / art_shell**：在「固定提示词 + 直接 GenerateImage」路径上，**关与不关画法无跳变** → 可视为与像素画法无关，可留。
2. 本序列波动主要是**引擎随机**（格内容/构图），不是后三个 hook。
3. 跨题材（图标/UI）在固定软绘措辞下也能落到软绘档，说明「固定措辞」比后三个 hook 更决定画法。
4. 测完已把 hooks **恢复为只关 pre-gen**（post-asset / stop / art_shell 已开回）。

## 机制备注（辅助，非眼判）
- pre-gen 才会改 GenerateImage description；post-asset / stop / art_shell（Shell）不改本张出图像素。
- 本对照验证了这一点：后三步「一样」符合机制预期。

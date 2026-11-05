# 提示词方案 · 蘑菇芝士果盘普通图

**判定类型：`普通图` · 依据：单张道具静物插画，未点名 UI/合成梯/克隆 · 将交给：`/pmem-draw`**  
**route 校正（以 CLI 为准）：`route_ids=['prompt.write']` · banner：【按 提示词生成器…走了】**  
后续每套方案旁标注目标出图 `route_id=draw.ordinary`（本支只写 brief，不生图）。

## 听懂的交付

- **交付物**：蘑菇芝士果盘普通单张（可棚拍道具卡，也可场景静物）。
- **已锁定**：主体=红白斑菇台 + 瑞士孔芝士楔 + 橙樱/蓝莓果 + 绿叶；参考貌见 `assets/skill_20261103/04_prop.png`（身份与造型可锁，构图不强制照搬）。
- **还晃**：画幅竖/方未钉死 → 方案里用「主体居中、安全边充足」兜住；点选前不生图。

缺画风默认对标：**休闲 merge / 货柜道具卡**（软塑胶厚实、棚柔光短接触影、饱和友好、缩略可读）——禁止无关赛博/写实脏暗。

---

## 方案 A · 棚拍居中 · `route_id=draw.ordinary`

- **中文目标句**：黑底棚拍道具卡，一只红白斑飞伞菇台居中承托厚瑞士孔芝士楔，旁摆三颗橙樱与三颗梨形蓝莓并夹三片翠绿叶；左上柔棚光、短暖接触影，软立体圆角玩具感，哑光缎面，主体占画幅约 70%，无文字无场景杂物。气质对标顶级休闲 merge 货柜道具完成度。
- **英文执行句**：Centered product-hero still life of a red-and-cream spotted toadstool platter holding a thick Swiss-cheese wedge with clear holes, three orange cherries, three pear-shaped blueberries and three green leaves; soft top-left studio key light, short warm contact shadow, soft-3D toy rounding, matte-to-satin, black void background, subject ~70% of frame, no text, no scene clutter; top casual-merge shop-prop finish.
- **本套侧重**：棚拍识别度 / 黑底剪影清晰
- **相对原话改了什么**：补齐光位、材质、安全边与商业对标句
- **建议交给**：`/pmem-draw`

## 方案 B · 俯视果盘 · `route_id=draw.ordinary`

- **中文目标句**：高位约 45° 俯视看整盘陈列：菇盖圆盘铺满视野，芝士楔偏右、果粒环绕叶脉可读；主光仍左上但更顶，接触影收成菇盖边缘一圈浅暖 AO；软立体 merge 货柜气质，背景浅灰渐变非纯黑，主体占 80%，无手无角色无字。
- **英文执行句**：High three-quarter top-down view of the full mushroom-cheese fruit platter; toadstool cap fills frame, cheese wedge offset right, fruits ring readable leaf veins; softer overhead-left key, shallow warm AO at cap rim; soft-3D casual-merge shop finish, light gray gradient backdrop, subject ~80%, no hands, no character, no type.
- **本套侧重**：机位换成俯视陈列
- **相对原话改了什么**：景别从默认棚拍正中改为高俯视盘面叙事
- **建议交给**：`/pmem-draw`

## 方案 C · 暖窗侧光 · `route_id=draw.ordinary`

- **中文目标句**：同一菇台果盘，改右侧暖窗侧光（奶油暖白），左侧青绿弱补，芝士孔洞内壁有浅透光；背景虚化一角苔绿与石径暗示，仍是静物不是风景大全；软立体玩具感，主体占 60%，禁止霓虹与写实油脂高光。对标休闲 merge 货柜温暖货架光。
- **英文执行句**：Same mushroom cheese fruit platter with cream-warm window side light from the right and cool green fill from the left; cheese holes show gentle translucent walls; softly blurred moss-and-path hint in background only, still a prop still-life; soft-3D toy look, subject ~60%, no neon, no oily photoreal highlights; casual-merge warm shelf lighting finish.
- **本套侧重**：光色戏剧（暖侧光 vs 棚光）
- **相对原话改了什么**：把默认棚光换成窗侧暖光并加极浅场景 hint
- **建议交给**：`/pmem-draw`

## 方案 D · 黏土特写 · `route_id=draw.ordinary`

- **中文目标句**：近景特写锁芝士楔断面与两三颗果的接触点，菇盖红斑只作底座边缘入画；超软黏土/软塑胶笔触、宽柔高光、孔洞边缘圆润；浅景深虚化其余果叶，方幅，主体局部占 85%。仍是普通道具图，不是合成梯也不是图标格。
- **英文执行句**：Close-up locking the cheese wedge cut face and contact points of two–three fruits; only the red spotted mushroom-cap rim enters as base; ultra-soft clay / soft-plastic stroke, broad gentle highlights, rounded hole edges; shallow DOF blurs remaining leaves; square crop, local subject ~85%; still an ordinary prop shot—not a merge ladder or icon cell.
- **本套侧重**：媒介笔触特写（黏土感）
- **相对原话改了什么**：景别收到材质特写，强调软塑胶笔触而非全道具全身
- **建议交给**：`/pmem-draw`

---

请回字母 A/B/C/D（或改口）。**点选前禁止开生图。**  
若之后出图：再跑一次 `pyw -3 -u pmem_art.py route --text "<选定方案>" --canonical "普通图：蘑菇芝士果盘"`，再进 `/pmem-draw`。

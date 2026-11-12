# 提示词方案 · prompt.write

**判定类型：`合成梯` · 依据：点名「港湾海鲜合成梯整表」· 将交给：`/pmem-merge-ladder`**  
**【按 同域合成梯：先定链型与关系，再按交付出图 走了】** `route_id=merge.ladder`（以 CLI 为准）  
本技能**不生图、不跑 converge**。点选字母后再进 `/pmem-merge-ladder`。

听懂的交付：新 IP **Brimwave Café** 港湾海鲜合成梯 **整表一组**（默认 `delivery=overview_sheet`、`levels=8`、浅奶油圆角卡）。  
已锁定：题材域=港湾海鲜咖啡馆货柜；链型默认 `shop_ladder`；商业对标=`merge.cabinet` / Gossip Harbor 玩具货柜气质（有真机垫图时跟货面，勿灌缺省软糖釉长句）。  
还晃：具体八档物种序列可在点选后微调；未点名逐格 → 禁止按 per_cell 写八张插画句交差。

---

## 方案 A · 拼盘升阶 · `route_id=merge.ladder`

**中文目标句**  
Brimwave Café 港湾海鲜合成梯整表：`chain_mode=shop_ladder`，`delivery=overview_sheet`，竖屏 4×2 浅奶油圆角卡共 8 档。同店海鲜货柜色相（奶油沙岸 `#F4C584` / 珊瑚红 `#FF4D30` / 港湾青 `#48D1FF` / 金币黄 `#FFD700`）。升级叙事为「拼盘升阶」：L1 单枚生蚝对开 → L2 柠檬蚝盘 → L3 虾串杯 → L4 烤三文鱼石板 → L5 蟹腿拼盘 → L6 冰镇龙虾半只 → L7 双龙虾冰盘 → L8 顶档港湾海鲜塔。每档 `evolve_to`+`merge_why` 写清；体量只大一圈；邻档 64px 剪影可分。软立体玩具货柜表面、圆润厚实、无硬描边、块面釉面高光。禁止换物种出店、禁止焊蛋糕/城堡、禁止抄 HUD/手指、禁止写实摄影摆盘。

**英文执行句**  
Brimwave Café harbor seafood merge ladder overview sheet, shop_ladder, 8 levels on a 4x2 cream rounded-card grid. Same-shop seafood cabinet palette (#F4C584 / #FF4D30 / #48D1FF / #FFD700). Evolution: L1 single oyster half → L2 lemon oyster plate → L3 shrimp skewer cup → L4 seared salmon on stone → L5 crab-leg platter → L6 iced half lobster → L7 twin lobster ice tray → L8 grand harbor seafood tower. Each tier needs evolve_to + merge_why; one-step size bump; 64px neighbor-readable silhouettes. Soft-sculpt toy-cabinet glaze, round thick forms, no hard outlines, blocky soft highlights. Forbid out-of-shop species jumps, cake/castle welding, HUD/hand copy, photoreal plating.

**本套侧重**：拼盘犒赏叙事清晰，末档仍是同店海鲜塔。  
**相对原话改了什么**：把「港湾海鲜合成梯整表」落成 8 档 evolve 序列 + 整表版式硬锁。  
**建议交给**：`/pmem-merge-ladder`

---

## 方案 B · 灶台加装 · `route_id=merge.ladder`

**中文目标句**  
同一 Brimwave Café 海鲜域整表 8 档，`shop_ladder`，浅奶油卡。叙事改「灶台加工加装」：L1 生虾仁碗 → L2 清蒸虾盅 → L3 蒜香烤虾盘 → L4 黄油龙虾尾 → L5 香料烤龙虾 → L6 火焰龙虾船 → L7 双尾龙虾主厨盘 → L8 港湾主厨海鲜火船。每档强调炊具/盘式零件可见升级（蒸笼→石板→船盘），仍同店红青暖色相；软立体货柜表面跟 GH 真机气质。禁止同一剪影换皮、禁止档差扎堆、禁止硬 CGI。

**英文执行句**  
Same Brimwave Café seafood overview ladder (8 cells, cream cards, shop_ladder) but kitchen-upgrade story: raw shrimp bowl → steamed cup → garlic roast plate → butter lobster tail → spiced roast lobster → flame lobster boat → twin-tail chef plate → harbor chef seafood fire boat. Each tier adds readable cookware/platter parts; same-shop warm harbor palette; soft-sculpt cabinet surface. Forbid reskin twins, packed tier sizes, hard CGI.

**本套侧重**：加工态零件递进，适合「咖啡馆后厨」品牌感。  
**相对原话改了什么**：升级轴从「拼盘堆叠」改为「灶具/盘式加装」。  
**建议交给**：`/pmem-merge-ladder`

---

## 方案 C · 潮汐犒赏 · `route_id=merge.ladder`

**中文目标句**  
Brimwave Café 合成梯整表 8 档，`shop_ladder`。叙事「潮汐珍品」：L1 沙蛤 → L2 蛤蜊汤盅 → L3 贝类拼小盘 → L4 扇贝黄油盘 → L5 帝王蟹钳 → L6 冰镇蟹堡盘 → L7 龙虾王座盘 → L8 满潮海鲜宝塔。色相仍锁奶油/珊瑚/港湾青/金；整表浅奶油圆角卡；每档 merge_why 写「为何比前档更珍/更大一圈」。禁止灰雾废土、禁止扁平贴纸、禁止末档焊无关城堡。

**英文执行句**  
Brimwave Café tide-treasure seafood merge overview, 8 cream-card tiers, shop_ladder: sand clam → clam soup cup → mixed shell plate → butter scallop → king-crab claw → iced crab tower plate → lobster throne plate → high-tide seafood pagoda. Lock cream/coral/cyan/gold; one-step bulk growth; soft toy-cabinet glaze. Forbid wasteland grit, flat stickers, unrelated castle finale.

**本套侧重**：珍品稀有感递进，末档「满潮」犒赏更强。  
**相对原话改了什么**：物种轴偏贝→蟹→龙虾王座，仍同店。  
**建议交给**：`/pmem-merge-ladder`

---

## 方案 D · 货柜轻门（保守） · `route_id=merge.ladder`

**中文目标句**  
若只要「关系稿更保守」：仍 8 档整表 `shop_ladder`，固定单一主物种 **龙虾盘** 形变：L1 小龙虾仔 → L2 单只清蒸 → L3 柠檬黄油 → L4 冰镇半只 → L5 花刀拼盘 → L6 双螯高盘 → L7 冰雕龙虾船 → L8 金边港湾龙虾塔。parts/evolve 只改盘饰与体量，禁止换物种出店。表面句与 A 相同（跟真机货面）。

**英文执行句**  
Conservative same-species lobster-platter shop_ladder overview (8 cream cards): baby lobster → steamed single → lemon-butter → iced half → carved platter → dual-claw riser → ice-boat lobster → gold-rim harbor lobster tower. Evolve platter/bulk only; no species leave-shop; same soft-cabinet surface locks as scheme A.

**本套侧重**：物种锁死、风险最低，档差全靠盘饰与体量。  
**相对原话改了什么**：把「海鲜」收成龙虾同族形变，降低混种翻车。  
**建议交给**：`/pmem-merge-ladder`

---

请回复字母（A/B/C/D）或改口。**点选前禁止开生图。**  
选定后请再跑一次 `route`，再进 `/pmem-merge-ladder`；本文件方案句可作 discuss/`--draft` 底稿。

# festival5 overview · skill 重跑 v1 反向分析

对照：原始五张 L1、关系 yaml（shop_ladder×6）、上一版 `overview_L1_L6.png`、本次 `overview_L1_L6_skill_v1.png`。

## 已改善

1. **链型**：不再「每档焊 L1 母体加小饰片」；奖牌→奖杯、气球→拱门→热气球、马戏球→大篷、礼袋→宝箱，一眼能读升级故事。
2. **糖果红线**：未焊纸杯蛋糕/派/多层蛋糕；走包装糖→棒棒糖→拐杖糖→糖罐→糖花束（符合 MergeLadder 排除项）。
3. **底色**：纯黑隔离，无白/灰方卡。
4. **机读门**：`chain_mode=shop_ladder` + `levels=6` + `evolve_to/merge_why` 已过 `relation-judge`。

## 仍不足（驱动 v2）

| 行 | 问题 | 改点 |
| :--- | :--- | :--- |
| Prize | L1 同心圆环偏弱；L2–L4 仍挂蓝环，档差主要靠金属色，缩略图偏近 | L1 锁「厚铜章+同心凹环」；L2 起剪影差（银星/金星/桂叶）更大 |
| Balloon | L1→L2 几乎只加粉绳，64px 难分 | L2 强制「明显长绳+大粉结」；L3 起颜色必须跳开纯绿 |
| Candy | L4 拐杖糖过细，格内填充偏低 | L4 加粗拐杖、占格大半；L5 罐身更高 |
| Magic | L1 易漂成满星红球，偏离「红顶+白带+黄条纹+单白星」 | 提示词逐字锁 L1 条纹构造 |
| 体量 | 若干行非严格「右更大」（气球 L6 填充不及 L4） | 明示左小右大、末档最大但留黑边 |
| L1 锁 | 编辑模型对五参考有轻度风格漂移 | 强调「第 1 列像素级贴近参考」 |

## v2 策略

只改提示词重出整表（overview 预算第 2/3 次）；关系 yaml 不动。

## v2 结果（`overview_L1_L6_skill_v2.png` / `overview_L1_L6_skill.png`）

- 黑底仍干净；糖果链仍无蛋糕/派。
- Balloon L2 粉结更明显；Prize 桂叶/奖杯剪影差够用；Box 链最稳。
- 残留：Magic L1 仍偶发「满星」漂；Prize L5 杯身有时偏小（填充低于 L4）；Candy L4 拐杖仍偏细。
- 对比拼图：`assets/festival5_merge/overview_compare_skill_rerun.png`。
- 结论：关系门+链型改动有效；整表交付继续靠提示词锁 L1/档差，预算内可再出 1 次（第 3/3）若玩家要抠 Magic L1。

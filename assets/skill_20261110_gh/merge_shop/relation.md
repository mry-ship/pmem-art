# 露莓果酱合成梯 · shop_ladder · 整表 2×4 · 关系第 1 稿
# chain_mode=shop_ladder。不写 base_body。道具无脸。
# 过程类型：同族形变货柜。每档已是甜品店里一件完整可合的货，不是原料车间，也不是同一瓶子堆配料。
# 商业对标真链（只抽链型与犒赏曲线，画面不画冰淇淋）：
#   Travel Town Ice Cream = Vanilla→Watermelon→Kiwi→RainbowPop→Cone→StrawberryCone→BigCone→Luxury→SimpleSundae→DeluxeSundae
# 压缩到本链 8 档：单颗完整小货 → 签串换代 → 叶盏盛器 → 小口瓶包装 → 丝带礼瓶 → 木匙酱罐 → 双罐礼盘 → 叶缘盛宴盘。
# 玩家点名档序，不另编假果酱链名。
# 版式由玩家写死，不跟垫图格子：深灰底、两行四列白圆角卡。垫图 gh_merge.jpg 只锁道具光泽。
# 画风跟玩家文字：Gossip Harbor 货柜。光泽卡通 3D、圆润厚实、无硬描边、暖饱和、柔光渐变。
# 禁止蛋糕、马卡龙、纸杯蛋糕。禁止抄棋盘、龙虾、沙滩、手指、Merge 字、英文。不要写实摄影，不要暗沉旧塑料。
# 五问：
# 1 同店=露莓果酱甜品店。家族基因=露莓洋红、叶绿、奶油果酱色相，不是同一纹样盖章。过程类型=同族形变。对标是冰淇淋真档序。surface 已写 Gossip Harbor 货柜气质。
# 2 无回退：圆果 → 横串 → 叶舟 → 细颈瓶 → 宽肩丝带瓶 → 敞口罐加横匙 → 椭圆礼盘 → 最宽叶缘盛宴。L8 不是退回 L3 小盏。
# 3 无缺过渡硬跳，无城堡。L3→L4 是两盏鲜莓熬成一只小口瓶，叶舟换成竖直瓶，64px 可分。
# 4 L1 是一颗完整小露莓，玻璃、丝带、木匙、礼盘、盛宴都晚出现。邻档剪影类不同，体量逐档变大，末档最大仍留边。
# 5 每档 merge_why 写两件同级合成后为何变成下一件，可倒推。不是「更豪华」。
# 6 每档一件独立 SKU。L2 是木签串不是两颗散果。L7 是一只礼盘不是两个 L6 贴在一起。
# 7 合两下能倒推。末档是同店盛宴盘，对标冰淇淋链确有 Deluxe 盛宴段。
version: gh-dewberry-jam-shop-20261110-v1
pipeline: art-merge-two-phase
delivery: overview_sheet

tracks:
  dewberry_jam:
    module: merge.DewberryJam
    chain_mode: shop_ladder
    levels: 8
    grid_rows: 2
    grid_cols: 4
    surface: "Gossip Harbor 货柜：光泽卡通 3D、圆润厚实、无硬描边、暖饱和、柔光渐变；道具干净发亮，缩略可认。深灰底、2×4 白圆角卡，垫图只锁光泽不锁格子。每格一件居中，无等级字，无英文，道具无脸。家族是露莓果酱店的洋红露莓、叶绿与奶油果酱色相，不是八档贴同一纹样。不要写实摄影，不要暗沉旧塑料，不要蛋糕，不要马卡龙，不要纸杯蛋糕，不要棋盘，不要龙虾，不要沙滩，不要手指。"
    commercial_ref: "Travel Town Ice Cream (real): Vanilla→Watermelon→Kiwi→RainbowPop→Cone→StrawberryCone→BigCone→Luxury→SimpleSundae→DeluxeSundae; compress8=single complete SKU→skewer form→leaf vessel→narrow jar→ribbon gift jar→spoon crock→paired tray→leaf feast"
    process_type: "shop_ladder_same_shop_jam_form_evolution"
    rows:
      - { level: 1, name: 单颗露莓, silhouette: "单颗圆润露莓，洋红果身一点叶蒂，完整小货，无签无瓶无盘", scale_delta: 基档, scale_pct: 0.58, evolve_to: SingleDewberry, merge_why: "—", parts_add: "—" }
      - { level: 2, name: 双莓串, silhouette: "短木签横穿两颗露莓，横向条形剪影，不再是单颗圆果", scale_delta: "+小", scale_pct: 0.62, evolve_to: TwinBerrySkewer, merge_why: "两颗单颗露莓穿上同一短木签，圆果变成横向双莓串", parts_add: "—" }
      - { level: 3, name: 莓叶盏, silhouette: "绿叶舟托一盏露莓，叶缘是主轮廓，木签消失", scale_delta: "+小", scale_pct: 0.65, evolve_to: BerryLeafCup, merge_why: "两串双莓串合成托进一只绿叶舟的莓叶盏，木签不再出现", parts_add: "—" }
      - { level: 4, name: 小口果酱瓶, silhouette: "细颈小口高瓶灌满奶油色果酱，瓶身竖直，无丝带无叶舟", scale_delta: "+中", scale_pct: 0.68, evolve_to: NarrowJamBottle, merge_why: "两盏莓叶盏熬成一只细颈小口果酱瓶，叶舟消失只剩竖直瓶", parts_add: "—" }
      - { level: 5, name: 丝带果酱瓶, silhouette: "肩更宽的矮礼瓶，大蝴蝶结左右伸出改掉外轮廓，细颈小口瓶消失", scale_delta: "+中", scale_pct: 0.71, evolve_to: RibbonJamJar, merge_why: "两只小口果酱瓶合成肩更宽的丝带果酱瓶，大蝴蝶结改掉细颈轮廓", parts_add: "—" }
      - { level: 6, name: 木匙酱罐, silhouette: "敞口酱罐加一支横出木匙，罐口敞开，蝴蝶结不再是轮廓", scale_delta: "+中", scale_pct: 0.74, evolve_to: SpoonJamCrock, merge_why: "两只丝带果酱瓶合成敞口木匙酱罐，丝带消失改由横出木匙认档", parts_add: "—" }
      - { level: 7, name: 双罐礼盘, silhouette: "椭圆浅礼盘托两只小酱罐，盘沿是主轮廓，木匙不再横出", scale_delta: "+大", scale_pct: 0.77, evolve_to: TwinJarGiftTray, merge_why: "两只木匙酱罐放上同一椭圆礼盘成为一件双罐礼盘，木匙收起，盘沿变成主轮廓", parts_add: "—" }
      - { level: 8, name: 莓叶盛宴盘, silhouette: "最宽叶缘盛宴盘，中央果酱池加露莓铺满，仍是一件货并留卡边", scale_delta: "+大", scale_pct: 0.80, evolve_to: BerryLeafFeast, merge_why: "两件双罐礼盘合成最宽的莓叶盛宴盘，果酱池与露莓铺满叶缘，比礼盘更宽仍留边", parts_add: "—" }

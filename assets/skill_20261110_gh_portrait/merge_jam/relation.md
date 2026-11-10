# 露莓果酱八档合成梯整表 · 第 1 稿
# 会话 gh-jam-portrait。delivery=overview_sheet。chain_mode=shop_ladder。levels=8。
# 过程类型：同族形变货柜。每档是一件完整小货，邻档换剪影大类，不是同一瓶子加零件。
# 画幅 9:16。格子 4 行 2 列。阅读顺序从左到右、再从上到下：L1 L2 / L3 L4 / L5 L6 / L7 L8。
# goal 用连续字符串 4×2。
#
# 垫图原件 assets/refs/gossip_harbor/gh_merge.jpg
# 风格：光泽卡通 3D、圆润厚实、无硬描边、暖饱和、柔光。
# 构图：竖屏，浅蓝色圆角棋盘格。
# 特征：每格一件完整小货。
#
# 商业对标：Gossip Harbor 橙子 8 档。
# 整果→果片→果瓣→果汁→冰沙→蛋糕→挞→甜品。
# 本链对应：整颗露莓→对半露莓→一盏露莓果瓣→一杯露莓汁→一杯露莓冰沙→一只露莓小蛋糕→一只露莓挞→一盘露莓甜品。
# 家族基因：露莓货柜的洋红、叶绿、奶油色。不是同一纹样盖章。
#
# 画面主体框高大约：0.48、0.55、0.62、0.69、0.76、0.83、0.89、0.94。末档最大，格内留细边。
# 机读 scale_pct 用门禁内单调列（L1≥0.55，L8≤0.82），出图仍按上面的框高来画。
#
# 五问：
# 1 同店同域。家族是露莓色相。过程类型是同族形变。对标是 Gossip Harbor 橙子真档序。surface 是同一货柜的光泽卡通 3D。
# 2 无回退。整果、果片、果瓣、果汁、冰沙、蛋糕、挞、甜品，一件比一件换代。
# 3 无缺过渡的大跳。末档仍是一盘露莓甜品，不另焊别的地标。
# 4 缩略可分。L1 是小整果。玻璃、蛋糕、挞、餐盘晚出现。邻档剪影大类不同。
# 5 合成理由具体，两件同级能倒推成下一件。
# 6 每档一件独立货，不是同底座堆料。第 7 档是一只挞。
# 7 合两下可倒推。末档甜品对标橙子链的甜品档。
#
# 第 4 档是一杯露莓汁。第 7 档是一只露莓挞。第 8 档是一盘露莓甜品。
# 不画瓶装、不画并排两件、不画旋涡顶饰。道具无脸。无英文、无等级数字。
# 底是不透明实底。浅色圆角格，接近垫图棋盘的浅蓝。

version: gh-jam-portrait-20261110
pipeline: art-merge-two-phase
delivery: overview_sheet

tracks:
  dewberry_jam:
    module: merge.DewberryJam
    chain_mode: shop_ladder
    levels: 8
    grid_rows: 4
    grid_cols: 2
    surface: "光泽卡通 3D、圆润厚实、无硬描边、暖饱和、柔光渐变。竖屏 4×2 浅色圆角格，接近棋盘浅蓝，不透明实底。每格一件居中，道具无脸，无英文无等级数字。家族是露莓洋红、叶绿、奶油色。"
    commercial_ref: "Gossip Harbor 橙子 8 档：整果→果片→果瓣→果汁→冰沙→蛋糕→挞→甜品"
    process_type: "同族形变货柜"
    rows:
      - { level: 1, name: 整颗露莓, silhouette: "一颗完整圆露莓，洋红果身加叶绿蒂", scale_delta: "基档", scale_pct: 0.58, evolve_to: "整果", merge_why: "—", parts_add: "—" }
      - { level: 2, name: 对半露莓, silhouette: "一颗对半切开的露莓，切面朝前", scale_delta: "+小", scale_pct: 0.61, evolve_to: "果片", merge_why: "两颗整果合成后切成一件对半露莓", parts_add: "—" }
      - { level: 3, name: 一盏露莓果瓣, silhouette: "一只小盏盛着散开的露莓果瓣", scale_delta: "+小", scale_pct: 0.64, evolve_to: "果瓣", merge_why: "两件对半露莓剥开，合成一盏露莓果瓣", parts_add: "—" }
      - { level: 4, name: 一杯露莓汁, silhouette: "一只细高透明杯，杯中是洋红露莓汁", scale_delta: "+中", scale_pct: 0.67, evolve_to: "果汁", merge_why: "两盏果瓣榨成一杯露莓汁，盏换成细高杯", parts_add: "—" }
      - { level: 5, name: 一杯露莓冰沙, silhouette: "一只矮阔杯，杯中是稠厚露莓冰沙", scale_delta: "+中", scale_pct: 0.70, evolve_to: "冰沙", merge_why: "两杯露莓汁搅成一杯更稠的露莓冰沙，细高杯换成矮阔杯", parts_add: "—" }
      - { level: 6, name: 一只露莓小蛋糕, silhouette: "一只纸杯托着的圆顶小蛋糕", scale_delta: "+中", scale_pct: 0.73, evolve_to: "蛋糕", merge_why: "两杯露莓冰沙烘成一只露莓小蛋糕，杯子换成纸杯蛋糕", parts_add: "—" }
      - { level: 7, name: 一只露莓挞, silhouette: "一只敞口圆挞，波浪挞边一圈", scale_delta: "+大", scale_pct: 0.76, evolve_to: "挞", merge_why: "两只露莓小蛋糕改成一只敞口露莓挞，纸杯换成波浪挞皮", parts_add: "—" }
      - { level: 8, name: 一盘露莓甜品, silhouette: "一只圆餐盘托着一份露莓甜品", scale_delta: "+大", scale_pct: 0.80, evolve_to: "甜品", merge_why: "两只露莓挞装上同一只圆盘，成为一盘露莓甜品", parts_add: "—" }

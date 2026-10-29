# Absolute-5D 可量化清单评分报告（gpt-6-sol）

- 模型: `gpt-6-sol`
- 量表: checklist 0/1/2 → P/100 → S/10，推荐权重 {'composition': 0.2, 'lighting_color': 0.2, 'perspective_anatomy': 0.25, 'texture_detail': 0.15, 'spec_style': 0.2}
- 成功: 32  失败: 0
- 总分: n=32 mean=8.41 median=8.4 min=7.25 max=9.81

## 按角色

- **bot**: n=32 mean=8.41 median=8.4 [7.25, 9.81]

## 维度均值

- composition: 9.16
- lighting_color: 8.48
- perspective_anatomy: 7.77
- texture_detail: 7.8
- spec_style: 8.82

## Top 5 bots

- `v7_bot_31_ishtar_canyon_recompose.jpg` total=9.81 (近乎无瑕) defects=['人物背影细节较软，个别肢体比例略显僵硬', '飞龙尺寸较小，远景识别度有限']
- `v7_bot_06_night_city_high_best.jpg` total=9.5 (近乎无瑕) defects=['人物与屋脊接触阴影略弱', '剑柄与手部连接细节略显模糊', '远景城市与云层局部边缘偏软']
- `v7_bot_30_ishtar_canyon_high_best.jpg` total=9.3 (优秀) defects=['人物比例偏小，面部与装备细节不可辨', '飞龙局部肢体与翼膜结构略显模糊', '部分栈桥和建筑连接处透视关系不够严谨', '暗部材质层次有轻微糊化']
- `v7_bot_22_sunlit_portrait_high_best.jpg` total=9.18 (优秀) defects=['右侧脸部与肩部裁切略紧，构图完整性受影响', '窗边与发丝高光局部过曝，细节损失', '衣料与发丝边缘存在轻微软化和融边', '叙事信息偏弱，主要依赖光影而非明确情境']
- `v7_bot_07_night_city_recompose.jpg` total=9.15 (优秀) defects=['整体更偏写实电影感，仙侠水墨风格不明显', '人物背部与衣袍处于较重暗部，局部细节可读性下降', '人物手部与武器区域被遮挡，人体结构验证有限']

## Bottom 5 bots

- `v7_bot_02_night_city_low_best.jpg` total=7.25 (良好) defects=['远景建筑轮廓偏糊，局部屋顶纹理重复', '天际线弧度突兀，削弱城市纵深的可信度', '水墨笔触不明显，更接近数字奇幻绘画', '人物较小且偏暗，缩图后细节难辨']
- `v7_bot_16_pastel_sketch_recompose_bold.jpg` total=7.39 (良好) defects=['未保留目标明确要求的屈膝坐姿少女剪影，改成站姿', '夕阳逆光与人物正面、腿部亮面对应不充分', '鞋底接地阴影偏弱，脚部略有漂浮感', '栏杆圆饰的透视压缩与间距变化不够统一', '天空、海面、建筑和地面网点密度偏高，缩图后背景抢眼', '服装、皮肤与地面共享颗粒处理，材质区分有限']
- `v7_bot_01_night_city_low.jpg` total=7.46 (良好) defects=['缩小后侠客较难辨认', '屋脊与人物脚部结构含混', '远景建筑细节重复、局部糊成一片', '整体更偏厚涂奇幻，水墨笔意不足']
- `v7_bot_26_ishtar_canyon_low_best.jpg` total=7.56 (良好) defects=['缩小后天井轮廓清楚，但中央人物与杂物黏连，焦点偏弱。', '中央木板、平台及右下棚架的支承与衔接关系不够清楚。', '人物四肢和随身物件辨识不足，局部轮廓混杂。', '木材与石材的笔触、色阶接近，部分材质区分不足。', '局部木板和杂物接触阴影偏弱，落地感不均。', '画面约为3:2，不符合指定4:3。', '缺少原图，无法核验主体锚点数量保持及修改幅度≤20%。']
- `v7_bot_09_pastel_sketch_low.jpg` total=7.68 (良好) defects=['头顶与右侧鞋尖留白偏紧，画面略显拥挤。', '双手手指分叉与指节转折简化，手掌体积和开合关系不够明确。', '远侧腿的遮挡连接、两鞋的空间关系略含混。', '臀部和鞋底接触阴影偏弱，落地感不足。', '衣料、皮肤与背景共用较强排线，局部材质区分不足。', '画幅约为3:2，不符合指定4:3。']

_updated_at: 2026-10-26 00:22 Asia/Shanghai (UTC+8)_

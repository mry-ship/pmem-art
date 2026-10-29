# Absolute-5D 可量化清单评分报告（gpt-6-sol）

- 模型: `gpt-6-sol`
- 量表: checklist 0/1/2 → P/100 → S/10，推荐权重 {'composition': 0.2, 'lighting_color': 0.2, 'perspective_anatomy': 0.25, 'texture_detail': 0.15, 'spec_style': 0.2}
- 成功: 52  失败: 0
- 总分: n=52 mean=8.33 median=8.44 min=6.64 max=9.9

## 按角色

- **baseline**: n=4 mean=7.51 median=7.51 [7.26, 7.76]
- **bot**: n=32 mean=8.45 median=8.44 [6.64, 9.9]
- **round_r1**: n=16 mean=8.3 median=8.52 [6.95, 9.06]

## 维度均值

- composition: 9.09
- lighting_color: 8.39
- perspective_anatomy: 7.62
- texture_detail: 7.61
- spec_style: 8.95

## Top 5 bots

- `v7_bot_16_pastel_sketch_recompose_bold.jpg` total=9.9 (近乎无瑕) defects=['人物姿态改为站立，未保留原要求的屈膝坐姿', '部分远景城市与栏杆细节较密，缩小后辨识度会下降']
- `v7_bot_32_ishtar_canyon_recompose_bold.jpg` total=9.66 (近乎无瑕) defects=['人物面部与肢体细节被背影和斗篷遮挡', '人物主体受暗部影响，局部焦点照明略弱']
- `v7_bot_21_sunlit_portrait_high.jpg` total=9.55 (近乎无瑕) defects=['白衣与肩部褶皱细节略软，材质层次有限', '颈肩接触阴影偏弱']
- `v7_bot_15_pastel_sketch_recompose.jpg` total=9.51 (近乎无瑕) defects=['手部与手指结构略显模糊', '局部粉彩笔触导致细节锐度不足', '栏杆接触处阴影略弱']
- `v7_bot_17_sunlit_portrait_low.jpg` total=9.25 (优秀) defects=['颈肩交界与衣领接触阴影略弱', '受光与阴影侧双眼明暗差较大，眼部细节略不均', '发丝局部线条较密，脸侧边缘略显松散']

## Bottom 5 bots

- `v7_bot_25_ishtar_canyon_low.jpg` total=6.64 (合格) defects=['C1/C6：缩略后中央主体偏暗，人物与杂物难以分离。', 'C3/C4：斜向梁柱和密集砖缝争夺注意力，空间层级不够清楚。', 'L1/L6：局部亮面与遮挡关系交代不足，梁木、桶及墙饰的接触阴影偏弱。', 'P1/P2/P3/P4：多组建筑边线汇聚不统一，中央木构连接及承重关系含混。', 'T1/T2/T4/T6：石材、木材与金属依赖相似描线，中央暗部局部边缘粘连。', 'S1：天井空间可辨，但俯视方向缺少明确地面与尺度线索。']
- `v7_bot_08_night_city_recompose_bold.jpg` total=7.34 (良好) defects=['孤侠身上未见可辨识的剑，缺少核心持剑设定', '人物手臂与手部被暗部和衣袖遮挡，动作结构不够清楚', '缺少明显全息旗帜；积水反射虽有呈现但局部细节偏糊']
- `v7_bot_26_ishtar_canyon_low_best.jpg` total=7.48 (良好) defects=['C1/C3/C6：缩小后中央人物与木构杂物混合，天井焦点不够突出', 'L4/L6：暗部层级偏挤，部分木板与墙体接触阴影不足', 'P1/P2/P3/P4/P6：多组墙面、窗框及木构件的透视衔接不够统一，局部连接含混', 'T2/T3/T5：石材、灰泥与木材共享较强描线和碎纹理，材质区别有限', 'S3：线描与刻蚀感偏强，厚涂笔触及体块塑造不足']
- `v7_bot_04_night_city_medium_best.jpg` total=7.49 (良好) defects=['远景城市与中景树海细节偏软，局部呈现糊化笔触', '前景屋脊和人物接触阴影不够明确', '人物肢体与衣摆轮廓较模糊，结构识别度一般', '冷色雾层削弱了局部明暗对比和材质区分', '建筑与屋顶纹理缺少更清晰的介质质感']
- `v7_bot_02_night_city_low_best.jpg` total=7.54 (良好) defects=['缩略后人物躯干与屋顶暗部粘连，主要依赖亮剑辨识', '城市中远景屋宇与灯点偏碎，局部结构糊化、材质区分不足', '弧形天际线带出球面感，与近景屋顶的透视衔接略生硬', '脚部落点及接触阴影不够明确', '剑身亮度突出，但邻近手部与衣料受光反馈偏弱', '整体偏厚重数字绘景，水墨笔触与留白表现有限']

_updated_at: 2026-10-26 00:22 Asia/Shanghai (UTC+8)_

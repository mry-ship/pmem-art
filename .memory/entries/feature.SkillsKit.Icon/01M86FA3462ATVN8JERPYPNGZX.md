---
id: 01M86FA3462ATVN8JERPYPNGZX
module: feature.SkillsKit.Icon
entity: IconAPromptFightsCrop
kind: correction
status: active
supersedes:
- 01M865KCMYX1EWA7RRNWKZSB1Y
anchors:
- skills_kit/reasonableness_gate.py
- skills_kit/prompt_scale.py
- skills_kit/converge.py
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 图标低分是裁切被档位句和空垫图抵消，闸门已放行多张棋面
verify: tilematch-icon-store 正式分 7.30/7.00；对照 reasonableness_gate 玩法句与 prompt_scale.drop_opposed_injections
applies: icon.a 从零出桌面图标，正式分被安全区替换时
source:
  kind: code
---
旧结论说闸门只放行「一枚牌面加可配花色」，多张能对上的牌和角色都会被拦。当前代码不是这样：玩法句放行相同、一组、多张、半身、角色，徽章句只拦「一枚、一颗、单枚」接近星、徽章、牌。
tilematch-icon-store 两轮正式分 7.30 和 7.00，都是安全区替换。第 1 轮三张草莓棋面分开摆、有投影。第 2 轮不垫第 1 轮，整段重画成三颗水果，上下留空。
裁切句已经写进 revised，仍然画不满。
三处装配把它抵掉了。
medium 的约束尾仍留「不做整体 recompose」；
填满句只删掉「不改机位」，不删这句。
没有参考图时第 2 轮打印「不要垫上轮成图」，改点只能靠文字重画，棋面边框会丢。
只有正文出现「高饱和」才删「避免过饱和」。
图标默认句写的是冷暖相反和软卡通厚体积，口味包仍把色压暗。
审图拿原始 prompt_directive 去对最终提示词，被删掉的那半句每轮都报「未包含本档 prompt_directive」，这是误报。

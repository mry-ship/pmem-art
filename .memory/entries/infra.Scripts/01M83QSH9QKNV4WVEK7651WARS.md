---
id: 01M83QSH9QKNV4WVEK7651WARS
module: infra.Scripts
entity: LayerSplitPipeline
kind: correction
status: active
supersedes:
- 01M83QEDHJR4QZ13DHC4FBZP5A
anchors:
- scripts/pmem_layer_split/defaults.py#ISOLATE_PROMPT
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 拆层要裁切重画；大问题是内容换样和层级叠错
verify: 展陈 layer.split：池塘/小屋/前景/背景内容与原图不符；foreground z=6 的横带压住 pond 与 mole
applies: 评判 /pmem-layer-split 叠回时：略小可放大，内容换样和谁压谁才算失败
aliases:
- 层级
- 重画换样
source:
  kind: human
---
裁切后重画是拆层的正常做法，略小可以放大贴回。
展陈童话花园这次的大问题有两类。
内容画错：池塘被画成另一只更立的香蕉船和完整椭圆塘，码头改到另一侧；
小屋屋顶轮廓变了并自带台阶；
前景路走成 S 形草岛；
背景地面的花重新铺了。
树屋内容接近，缩放可放过。
层级画错：前景用下半幅横带且 z 最高，草地和后段路压住池塘、屋脚和鼹鼠；
石板路同时进了小屋和前景；
小屋框吞进树枝和路，重画就把邻居发明进这一层。
框要按单件外轮廓包全并少包邻居，z 按谁压谁：草地留背景，树枝压屋顶所以树高于屋，只有蘑菇桌这种真正的前景遮挡才最高。

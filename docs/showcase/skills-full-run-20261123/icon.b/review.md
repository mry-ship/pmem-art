# Mode B 一致性审查 · icon.b

**会话** `showcase-icon-b-20261123` · **批次** 8/8 一次交付 · **闭环** 未开（默认批量预览）

## B1 Brief 对齐

| 项 | 要求 | 结果 |
|----|------|------|
| 枚数 | home shop merge bag star heart settings profile | ✓ 8 枚 |
| viewBox | 24 | ✓ 全部 `0 0 24 24` |
| stroke | 1.5 | ✓ 根节点统一 |
| 色 | currentColor | ✓ 无硬编码 hex |
| 端点 | 圆角 | ✓ round / round |

## B3 短透镜（自查）

| 透镜 | 结论 |
|------|------|
| ① stroke/viewBox/端点统一 | 通过 |
| ② 光学重量 | shop/settings 略轻，merge 略重，整组可接受 |
| ③ padding ~2px | 通过，无贴边 |
| ④ 24px 可认 | 通过（merge 依赖游戏语境） |
| ⑤ currentColor | 通过 |
| ⑥ 非图标库拼贴 | 手写 path |

## 分批（5+3）

- 批 1：home shop merge bag star — stroke/重量一致
- 批 2：heart settings profile — 与批 1 对齐

##  informal 维度估分（非 converge）

笔画一致 8.7 · 视觉重量 8.4 · 留白 8.6 · 功能识别 8.8 · 无瑕疵 8.9 → **批量预览达标**，未跑正式 judge。

## Mode B checklist

- [x] 同 viewBox / stroke / cap / join
- [x] currentColor
- [x] kebab-case 文件名
- [x] preview.html + style-spec.json
- [x] 未开关键枚闭环
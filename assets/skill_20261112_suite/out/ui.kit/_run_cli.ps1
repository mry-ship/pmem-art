$ErrorActionPreference = "Stop"
$root = "c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art"
$py = "C:\Users\ZhengLangPC\AppData\Local\Programs\Python\Python312\python.exe"
$outDir = Join-Path $root "assets\skill_20261112_suite\out\ui.kit"
Set-Location $root

function Invoke-PmemArt {
    param([string[]]$ArgsList, [string]$LogName)
    $outFile = Join-Path $outDir "$LogName.out.txt"
    $errFile = Join-Path $outDir "$LogName.err.txt"
    $p = Start-Process -FilePath $py -ArgumentList (@("-u","pmem_art.py") + $ArgsList) `
        -WorkingDirectory $root -RedirectStandardOutput $outFile -RedirectStandardError $errFile `
        -NoNewWindow -PassThru
    Wait-Process -Id $p.Id -Timeout 180
    Write-Host "=== $LogName EXIT=$($p.ExitCode) ==="
    if (Test-Path $outFile) { Get-Content $outFile -Raw }
    if (Test-Path $errFile) {
        $e = Get-Content $errFile -Raw
        if ($e) { Write-Host "ERR:"; Write-Host $e }
    }
    return $p.ExitCode
}

$goal = "Brimwave Cafe casual merge main-menu HUD concept, warm harbor cafe, soft glossy casual UI"
$refs = "assets/skill_20261112_suite/refs/ref_ui.png,assets/skill_20261112_suite/refs/ref_ui_dl.jpg"
$refAnalysis = "Pad images are casual-merge renovation HUD: soft glossy rounded chrome top resource pills, thick readable numerals, scene fills screen, controls overlay isometric interior. Lock chrome craft and soft-gloss casual UI vibe only. Do NOT pixel-copy Design three-choice bar, kitchen layout, or character portraits."

$code = Invoke-PmemArt -LogName "01_start" -ArgsList @(
    "converge","start",
    "--session","suite_ui_kit",
    "--module","ui.BrimwaveCafe",
    "--route-id","ui.kit",
    "--scale","high",
    "--goal",$goal,
    "--reference-image-paths",$refs,
    "--aspect-ratio","9:16",
    "--ref-analysis",$refAnalysis
)
if ($code -ne 0) { exit $code }

$code = Invoke-PmemArt -LogName "02_contract" -ArgsList @(
    "contract","set",
    "--id","suite_ui_kit",
    "--defaults","默认：concept-only；画幅9:16竖屏；只交主菜单概念稿；不拆组件表/九宫格/状态族；Cursor GenerateImage；场景满铺底",
    "--locks","题材=Brimwave Cafe海港休闲merge咖啡馆主菜单；风格=垫图软光泽休闲HUD chrome气质；顶栏单行资源；中下主CTA最大；场景铺满；控件叠场景上；暖港湾咖啡馆氛围；可读标题Brimwave Cafe与PLAY；禁止乱码",
    "--unlocks","禁止像素抄垫图厨房构图/Design三选一底栏/具体角色肖像；不锁三消RM底栏五Tab；不锁组件表",
    "--vibe","对标品类=休闲merge主菜单HUD（ui.casual_hud）：上架截图密度，顶栏资源清晰，主CTA一眼最大，chrome与港湾咖啡馆场景同系软光泽，可点控件完成度"
)
if ($code -ne 0) { exit $code }

$discuss = @"
concept-only主菜单：9:16竖屏。暖港湾咖啡馆场景铺满（窗外海港午后光、吧台甜点、茶杯蒸汽），非Design装修三选一屏。顶栏单行：等级珠+体力+金币+宝石，软圆角白底厚描边。中下最大主CTA=PLAY或Continue Level。角落小设置齿轮。可有轻量底栏Home居中（非PVP大厅）。角色情绪锚不压chrome。禁止乱码与假外框。
"@

$code = Invoke-PmemArt -LogName "03_discuss" -ArgsList @(
    "converge","discuss",
    "--id","suite_ui_kit",
    "--text",$discuss
)
if ($code -ne 0) { exit $code }

$draft = "Brimwave Cafe main menu HUD soft glossy casual UI 9:16"
$revised = @"
Mobile 9:16 casual-merge MAIN MENU HUD concept for Brimwave Cafe (NOT a Design renovation picker screen). Full-bleed warm harbor cafe interior scene under soft afternoon window light: creamy wood counters, teal accents, pastry trays, coffee steam, distant harbor boats through big windows. Soft glossy toy-plastic casual UI chrome matching pad craft (rounded white resource pills, thick blue/cream borders, chunky readable numerals with dark outlines) — do not copy pad pixel layout.
TOP single-row HUD: level circle + energy + coins + gems; tiny settings gear top-right corner, not a second row.
MID scene: friendly cafe mascot or barista as emotional anchor with face clear of chrome; leave lower floor clear for CTA.
LOWER-MID primary CTA: one oversized soft-gloss PLAY button (or Level xx), clearly largest interactive element.
OPTIONAL light bottom nav with Home centered (casual merge, not PvP lobby, not Royal Match five-tab default if it fights cafe identity).
Readable logo text "Brimwave Cafe" near top or above CTA. No gibberish, no phone bezel, no Design three-option strip, no match-3 board.
Benchmark category = casual merge main-menu HUD (ui.casual_hud): store-screenshot density, chrome same family as scene, soft glossy warm saturated finish.
"@

$checklist = "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;layout_zones=ok;no_content_clutter=ok;chrome_not_illustration=ok;cta_clear_of_faces=ok;control_craft=ok"

$code = Invoke-PmemArt -LogName "04_reason" -ArgsList @(
    "reasonableness","review",
    "--id","suite_ui_kit",
    "--skill","ui",
    "--draft",$draft,
    "--revised",$revised,
    "--checklist",$checklist,
    "--notes","concept-only; 对标品类=休闲merge主菜单HUD；垫图只锁chrome气质禁止像素抄构图"
)
exit $code

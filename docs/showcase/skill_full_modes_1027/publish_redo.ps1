# 将 Cursor assets 下 redo_* 同步到 showcase（GenerateImage 输出目录）
$Src = "$env:USERPROFILE\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets"
$Base = "$PSScriptRoot\images"
foreach ($set in @("a", "b", "c")) {
  $dst = Join-Path $Base "merge_$set"
  1..8 | ForEach-Object {
    $n = "{0:D2}" -f $_
    Copy-Item (Join-Path $Src "redo_merge_${set}_L$n.jpg") (Join-Path $dst "L$n.jpg") -Force
  }
}
$map = @{
  "redo_clone_a_compass.jpg" = "clone_a\final.jpg"
  "redo_clone_b_key.jpg"     = "clone_b_key\final.jpg"
  "redo_clone_b_ui.jpg"      = "clone_b_ui\final.jpg"
  "redo_clone_b_char.jpg"    = "clone_b_char\final.jpg"
  "redo_icon_a_master.jpg"   = "icon_a\master_1024.jpg"
  "redo_ui_concept.jpg"      = "ui\concept_final.jpg"
  "redo_ui_sheet.jpg"        = "ui\sheet_final.jpg"
}
foreach ($k in $map.Keys) {
  Copy-Item (Join-Path $Src $k) (Join-Path $Base $map[$k]) -Force
}

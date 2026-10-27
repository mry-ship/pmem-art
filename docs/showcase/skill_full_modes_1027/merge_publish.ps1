# canonical 发布：split → audit →（失败才）normalize
param(
  [Parameter(Mandatory)] [string]$Sheet,
  [Parameter(Mandatory)] [string]$OutDir,
  [Parameter(Mandatory)] [string]$Phase1,
  [Parameter(Mandatory)] [string]$Track
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location (Resolve-Path "$root\..\..\..").Path
python pmem_art.py merge split-sheet --sheet $Sheet --dir $OutDir
$ec = 0
python pmem_art.py merge audit -d $OutDir --phase1 $Phase1 -t $Track
if ($LASTEXITCODE -ne 0) {
  python pmem_art.py merge normalize -d $OutDir --phase1 $Phase1 -t $Track
  if ($LASTEXITCODE -ne 0) { $ec = 1 }
}
Pop-Location
exit $ec

$img = "C:\Users\ZhengLangPC\.cursor\skills\apikey-image\image_gen.py"
$out = "C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\birds_merge\overview_sheet_r1.png"
$prompt = @"
Casual merge-game chicken bird prop ladder sheet. Soft plastic toy style, rounded chunky cute, friendly saturated colors, soft upper-left studio light, short contact shadows, matte.
Layout: exactly 2 rows x 4 columns = 8 white rounded cards on deep charcoal, even gaps, same three-quarter slight low camera. One subject per card, no text, no level numbers.
Commercial density like Merge Mansion Bake-off chicken creature chain, NOT hen house buildings.
Top L1-L4 bottom L5-L8:
L1 tiny round yellow hatchling fluff ball almost no wings
L2 standing yellow baby chick short beak tiny wings
L3 juvenile chick feathers showing color patches short wing shape
L4 lanky pullet young chicken short tail tiny comb bud
L5 round adult hen clear full feathers visible red comb
L6 plumper laying hen fuller feathers bigger brighter red comb
L7 small flock 2-3 adult hens clustered as one card subject
L8 larger brood flock more hens clustered — birds only, NO coop, NO nest box, NO hen house, NO cage
Family warm yellow fluff to orange-brown feathers to red comb. Gentle size growth L1 to L8.
"@
python $img -o $out --size 1536x1024 $prompt
Write-Host "DONE $out exit $LASTEXITCODE"

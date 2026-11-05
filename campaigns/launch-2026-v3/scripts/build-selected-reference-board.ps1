Add-Type -AssemblyName System.Drawing
$root='C:\Users\dmbar\Downloads\Telegram Desktop\glass grad'
$out='C:\Projects\exam-photo-platform\campaigns\launch-2026-v3\reference-review\selected-references.jpg'
$refs=@(
  @{f='Screenshot_2026_10_02_09_39_38_84_1c337646f29875672b5a61192b9010f9.jpg'; x=0;y=330;w=632;h=290;l='DARK 01';n='Frosted glass, one colour source'},
  @{f='Screenshot_2026_10_02_09_39_38_84_1c337646f29875672b5a61192b9010f9.jpg'; x=632;y=760;w=632;h=420;l='DARK 02';n='Gradient used as light and depth'},
  @{f='Screenshot_2026_10_02_09_39_57_71_1c337646f29875672b5a61192b9010f9.jpg'; x=55;y=665;w=560;h=370;l='DARK 03';n='Black field, warm restrained glow'},
  @{f='Screenshot_2026_10_02_09_39_33_92_1c337646f29875672b5a61192b9010f9.jpg'; x=650;y=850;w=580;h=385;l='LIGHT 01';n='White surface, colour held at edge'},
  @{f='Screenshot_2026_10_02_09_39_19_25_1c337646f29875672b5a61192b9010f9.jpg'; x=680;y=1690;w=540;h=355;l='LIGHT 02';n='Cream field, soft warm colour pool'},
  @{f='Screenshot_2026_10_02_09_39_57_71_1c337646f29875672b5a61192b9010f9.jpg'; x=632;y=565;w=632;h=420;l='LIGHT 03';n='Blurred organic colour and texture'}
)
$W=1800;$H=2550;$margin=72;$gap=36;$cw=810;$ch=680;$ih=535
$bmp=New-Object System.Drawing.Bitmap($W,$H)
$g=[System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode='HighQuality';$g.InterpolationMode='HighQualityBicubic';$g.PixelOffsetMode='HighQuality'
$g.Clear([System.Drawing.ColorTranslator]::FromHtml('#111214'))
$fb=New-Object System.Drawing.Font('Arial',34,[System.Drawing.FontStyle]::Bold)
$fs=New-Object System.Drawing.Font('Arial',19,[System.Drawing.FontStyle]::Regular)
$fl=New-Object System.Drawing.Font('Arial',16,[System.Drawing.FontStyle]::Bold)
$fn=New-Object System.Drawing.Font('Arial',20,[System.Drawing.FontStyle]::Regular)
$ff=New-Object System.Drawing.Font('Arial',21,[System.Drawing.FontStyle]::Bold)
$white=New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#F7F3EC'))
$muted=New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#A8A49D'))
$orange=New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#FF5A32'))
$card=New-Object System.Drawing.SolidBrush([System.Drawing.ColorTranslator]::FromHtml('#1B1C1F'))
$g.DrawString('REFERENCE EDIT - WHAT TO KEEP',$fb,$white,72,50)
$g.DrawString('Six cues selected from the folder. These guide atmosphere and restraint, not literal copying.',$fs,$muted,72,120)
for($i=0;$i -lt $refs.Count;$i++){
 $r=$refs[$i];$col=$i%2;$row=[math]::Floor($i/2);$dx=$margin+$col*($cw+$gap);$dy=205+$row*($ch+$gap)
 $img=[System.Drawing.Image]::FromFile((Join-Path $root $r.f))
 $src=New-Object System.Drawing.Rectangle($r.x,$r.y,$r.w,$r.h)
 $dest=New-Object System.Drawing.Rectangle($dx,$dy,$cw,$ih)
 $g.DrawImage($img,$dest,$src,[System.Drawing.GraphicsUnit]::Pixel)
 $img.Dispose()
 $g.FillRectangle($card,$dx,$dy+$ih,$cw,$ch-$ih)
 $g.DrawString($r.l,$fl,$orange,$dx+28,$dy+$ih+20)
 $g.DrawString($r.n,$fn,$white,$dx+28,$dy+$ih+62)
}
$pen=New-Object System.Drawing.Pen([System.Drawing.ColorTranslator]::FromHtml('#333438'),2)
$g.DrawLine($pen,$margin,2370,$W-$margin,2370)
$g.DrawString('Shared rule for both routes',$ff,$white,$margin,2400)
$g.DrawString('One connected panorama across EXAM / UPLOAD / KIT. Exact logo. Equal scale. Quiet centre.',$fs,$muted,$margin,2448)
$g.DrawString('Effects stay behind the identity.',$fs,$muted,$margin,2485)
$bmp.Save($out,[System.Drawing.Imaging.ImageFormat]::Jpeg)
$g.Dispose();$bmp.Dispose();$fb.Dispose();$fs.Dispose();$fl.Dispose();$fn.Dispose();$ff.Dispose();$white.Dispose();$muted.Dispose();$orange.Dispose();$card.Dispose();$pen.Dispose()
Write-Output $out


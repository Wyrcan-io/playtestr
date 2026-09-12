$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing

$repoRoot = Split-Path -Parent $PSScriptRoot
$outputDir = Join-Path $repoRoot 'site\static\images'
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
$outputPath = Join-Path $outputDir 'social-preview.png'

$bitmap = [System.Drawing.Bitmap]::new(1200, 630)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit

$paper = [System.Drawing.ColorTranslator]::FromHtml('#fffdf9')
$ink = [System.Drawing.ColorTranslator]::FromHtml('#252323')
$muted = [System.Drawing.ColorTranslator]::FromHtml('#625e5c')
$line = [System.Drawing.ColorTranslator]::FromHtml('#d8d2cd')
$rust = [System.Drawing.ColorTranslator]::FromHtml('#652d3c')
$terminal = [System.Drawing.ColorTranslator]::FromHtml('#292728')
$terminalText = [System.Drawing.ColorTranslator]::FromHtml('#eee9e4')
$pass = [System.Drawing.ColorTranslator]::FromHtml('#bfcca1')

try {
    $graphics.Clear($paper)
    $rustBrush = [System.Drawing.SolidBrush]::new($rust)
    $inkBrush = [System.Drawing.SolidBrush]::new($ink)
    $mutedBrush = [System.Drawing.SolidBrush]::new($muted)
    $terminalBrush = [System.Drawing.SolidBrush]::new($terminal)
    $terminalTextBrush = [System.Drawing.SolidBrush]::new($terminalText)
    $passBrush = [System.Drawing.SolidBrush]::new($pass)
    $linePen = [System.Drawing.Pen]::new($line, 2)
    $paperPen = [System.Drawing.Pen]::new($paper, 5)
    $rustPen = [System.Drawing.Pen]::new($rust, 5)
    $titleFont = [System.Drawing.Font]::new('Arial', 64, [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $taglineFont = [System.Drawing.Font]::new('Arial', 29, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
    $labelFont = [System.Drawing.Font]::new('Consolas', 17, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)
    $terminalFont = [System.Drawing.Font]::new('Consolas', 21, [System.Drawing.FontStyle]::Regular, [System.Drawing.GraphicsUnit]::Pixel)

    $graphics.FillRectangle($rustBrush, 0, 0, 22, 630)
    $graphics.DrawString('>_', $labelFont, $rustBrush, 72, 60)
    $graphics.DrawString('playtestr', $titleFont, $inkBrush, 70, 105)
    $graphics.DrawString('Press the keys. Check the screen.', $taglineFont, $inkBrush, 74, 205)
    $graphics.DrawString('Catch the regression.', $taglineFont, $rustBrush, 74, 248)
    $graphics.DrawString('END-TO-END TESTING FOR INTERACTIVE CLIS AND TUIS', $labelFont, $mutedBrush, 76, 322)

    $graphics.FillRectangle($terminalBrush, 618, 78, 510, 470)
    $graphics.DrawLine($linePen, 618, 127, 1128, 127)
    $graphics.DrawEllipse($paperPen, 646, 98, 8, 8)
    $graphics.DrawEllipse($paperPen, 666, 98, 8, 8)
    $graphics.DrawEllipse($paperPen, 686, 98, 8, 8)
    $graphics.DrawString('$ playtestr test menu.json', $terminalFont, $terminalTextBrush, 652, 159)
    $graphics.DrawString('PASS', $terminalFont, $passBrush, 652, 226)
    $graphics.DrawString('step 1  expect screen', $terminalFont, $terminalTextBrush, 730, 226)
    $graphics.DrawString('PASS', $terminalFont, $passBrush, 652, 268)
    $graphics.DrawString('step 2  ArrowDown', $terminalFont, $terminalTextBrush, 730, 268)
    $graphics.DrawString('PASS', $terminalFont, $passBrush, 652, 310)
    $graphics.DrawString('step 3  selected', $terminalFont, $terminalTextBrush, 730, 310)
    $graphics.DrawString('> Run diagnostics', $terminalFont, $terminalTextBrush, 652, 390)
    $graphics.DrawString('Diagnostics: all systems healthy.', $labelFont, $passBrush, 652, 442)
    $graphics.DrawString('SPEC  >  SCREEN  >  EVIDENCE', $labelFont, $mutedBrush, 75, 508)
    $graphics.DrawLine($rustPen, 75, 551, 525, 551)

    $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    foreach ($item in @($titleFont, $taglineFont, $labelFont, $terminalFont, $rustBrush, $inkBrush, $mutedBrush, $terminalBrush, $terminalTextBrush, $passBrush, $linePen, $paperPen, $rustPen, $graphics, $bitmap)) {
        if ($null -ne $item) { $item.Dispose() }
    }
}

Write-Output $outputPath

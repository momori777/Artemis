$f = 'D:\AI_Girlfriend\README_jp.md'
$c = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)
$c = $c.Replace([char]0x2502 + '  ' + [char]0x251C, [char]0x2502 + '   ' + [char]0x251C)
$c = $c.Replace([char]0x2502 + '  ' + [char]0x2514, [char]0x2502 + '   ' + [char]0x2514)
$enc = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($f, $c, $enc)
Write-Host "Done - Japanese README directory indentation fixed"

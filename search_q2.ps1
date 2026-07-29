# Search for ??? pattern (3 question marks)
$matches1 = Select-String -Path 'D:\AI_Girlfriend\README_jp.md' -Pattern '\?\?\?'
Write-Host "=== ??? pattern ==="
foreach ($m in $matches1) {
    $line = $m.Line
    if ($line.Length -gt 80) { $line = $line.Substring(0, 80) }
    Write-Host ("{0}: {1}" -f $m.LineNumber, $line)
}

# Search for single ? that might be emoji (looking for ?> or ?* patterns)
$matches2 = Select-String -Path 'D:\AI_Girlfriend\README_jp.md' -Pattern '\?[<*#]'
Write-Host "`n=== ? followed by special char ==="
foreach ($m in $matches2) {
    $line = $m.Line
    if ($line.Length -gt 80) { $line = $line.Substring(0, 80) }
    Write-Host ("{0}: {1}" -f $m.LineNumber, $line)
}

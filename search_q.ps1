$matches = Select-String -Path 'D:\AI_Girlfriend\README_jp.md' -Pattern '\?\?'
foreach ($m in $matches) {
    $line = $m.Line
    if ($line.Length -gt 80) { $line = $line.Substring(0, 80) }
    Write-Host ("{0}: {1}" -f $m.LineNumber, $line)
}

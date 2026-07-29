$lines = [System.IO.File]::ReadAllLines('D:\AI_Girlfriend\README_jp.md', [System.Text.Encoding]::UTF8)
$line = $lines[527]
$chars = $line.ToCharArray()
for ($i = 0; $i -lt 15; $i++) {
    Write-Host ("{0}: U+{1:X4} [{2}]" -f $i, [int]$chars[$i], $chars[$i])
}

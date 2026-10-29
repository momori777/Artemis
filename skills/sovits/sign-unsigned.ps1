# Sign the GPT-SoVITS venv native extensions with the local signer certificate.
# Smart App Control on this machine blocks unsigned / unknown-reputation .pyd files
# ("应用程序控制策略已阻止此文件"), e.g. pyopenjtalk, jieba_fast, sudachipy.
# Run this after every `pip install` that adds native modules.
#
# Non-elevated friendly: it looks for the signer in LocalMachine\My first, then CurrentUser\My.
#   powershell -ExecutionPolicy Bypass -File skills\sovits\sign-unsigned.ps1 [-InstallUserStore]
#
# -InstallUserStore also registers the cert in CurrentUser Root/TrustedPublisher
# (harmless; only helps if Windows accepts user-level trust on this build).

param([switch]$InstallUserStore,
      [string]$SitePackages = '')

$ErrorActionPreference = 'Continue'

# Default to the venv that ships with this checkout (<repo>/deps/sovits-env);
# override with -SitePackages or $env:SOVITS_VENV_ROOT on another machine.
if (-not $SitePackages) {
    $venvRoot = if ($env:SOVITS_VENV_ROOT) { $env:SOVITS_VENV_ROOT } `
                else { Join-Path (Split-Path $PSScriptRoot -Parent) 'deps\sovits-env' }
    $SitePackages = Join-Path $venvRoot 'Lib\site-packages'
}
if (-not (Test-Path $SitePackages)) { Write-Output "NO_SITE_PACKAGES: $SitePackages"; exit 1 }
Write-Output "TARGET: $SitePackages"
$Subject = 'CN=GPT-SoVITS Local Signer'

$cert = Get-ChildItem Cert:\LocalMachine\My   -ErrorAction SilentlyContinue | Where-Object { $_.Subject -eq $Subject } | Sort-Object NotAfter -Descending | Select-Object -First 1
if (-not $cert) {
    $cert = Get-ChildItem Cert:\CurrentUser\My -ErrorAction SilentlyContinue | Where-Object { $_.Subject -eq $Subject } | Sort-Object NotAfter -Descending | Select-Object -First 1
}
if (-not $cert) { Write-Output 'NO_SIGNER_CERT: run trust_local_signer.ps1 as Administrator first'; exit 1 }
Write-Output "SIGNER: $($cert.Thumbprint) (store=$(if ($cert.PSPPath -like '*LocalMachine*') {'LocalMachine'} else {'CurrentUser'}))"

if ($InstallUserStore) {
    $cer = Join-Path $env:TEMP 'gptsovits_signer.cer'
    Export-Certificate -Cert $cert -FilePath $cer -Type CERT | Out-Null
    foreach ($s in @('Root', 'TrustedPublisher', 'AuthRoot')) {
        $p = "Cert:\CurrentUser\$s"
        if (Test-Path $p) {
            $have = Get-ChildItem $p -ErrorAction SilentlyContinue | Where-Object { $_.Thumbprint -eq $cert.Thumbprint }
            if ($have) { Write-Output "user ${s}: already present" }
            else { try { Import-Certificate -FilePath $cer -CertStoreLocation $p | Out-Null; Write-Output "user ${s}: installed" } catch { Write-Output "user ${s}: FAILED $($_.Exception.Message)" } }
        }
    }
}

if (-not (Test-Path $SitePackages)) { Write-Output "NO_SITE_PACKAGES: $SitePackages"; exit 1 }
$files = Get-ChildItem $SitePackages -Recurse -Include *.pyd, *.dll -File -ErrorAction SilentlyContinue
Write-Output "SCAN: $($files.Count) native files"
$signed = 0; $ok = 0; $bad = @()
foreach ($f in $files) {
    $st = (Get-AuthenticodeSignature $f.FullName).Status
    if ($st -eq 'Valid') { $ok++; continue }
    $r = $null
    try { $r = Set-AuthenticodeSignature -FilePath $f.FullName -Certificate $cert -HashAlgorithm SHA256 -TimestampServer 'http://timestamp.digicert.com' } catch { Write-Output "ERR $($f.Name): $($_.Exception.Message)"; $bad += $f.FullName; continue }
    $chk = (Get-AuthenticodeSignature $f.FullName).Status
    Write-Output ("SIGN {0}: {1} -> {2}" -f $f.Name, $st, $chk)
    if ($chk -in @('Valid', 'NotTrusted', 'UnknownError')) { $signed++ } else { $bad += $f.FullName }
}
Write-Output ("RESULT signed=$signed alreadyValid=$ok failed=$($bad.Count)")
foreach ($b in $bad) { Write-Output "  FAILED: $b" }
Write-Output 'SIGN_PASS_DONE'

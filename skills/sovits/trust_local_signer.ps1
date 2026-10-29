# GPT-SoVITS local signer bootstrap (run ONCE as Administrator)
#
# Why: this machine has Smart App Control ON (HKLM VerifiedAndReputablePolicyState=1,
# CodeIntegrity event 3077 "did not meet the Enterprise signing level requirements").
# SAC blocks unsigned native extensions (pyopenjtalk / jieba_fast / sudachipy .pyd) with
# "应用程序控制策略已阻止此文件". Pre-existing ComfyUI binaries are allowed by cloud
# reputation; freshly pip-installed / locally built ones are unknown -> blocked.
#
# This script creates a local code-signing CA (Code Signing + Enterprise Authentication EKU),
# installs it into the Local Machine trusted stores, and signs the venv native files so SAC
# treats them as enterprise-signed (the "whitelist" path that keeps SAC on).
#
# Usage (elevated):
#   powershell -ExecutionPolicy Bypass -File skills\sovits\trust_local_signer.ps1
# After that, every new pip install must be re-signed with the non-elevated helper:
#   powershell -ExecutionPolicy Bypass -File skills\sovits\sign-unsigned.ps1

$ErrorActionPreference = 'Continue'
$Log   = Join-Path $PSScriptRoot '_trust_sign.log'
function Log($m) { $line = "{0} {1}" -f (Get-Date -Format 'HH:mm:ss'), $m; Write-Output $line; Add-Content -Path $Log -Value $line -Encoding UTF8 }
Set-Content -Path $Log -Value "=== trust_local_signer start ===" -Encoding UTF8

$Subject   = 'CN=GPT-SoVITS Local Signer'
# The SoVITS venv lives in <repo>/deps/sovits-env; override with $env:SOVITS_VENV_ROOT.
$VenvRoot  = if ($env:SOVITS_VENV_ROOT) { $env:SOVITS_VENV_ROOT } `
             else { Join-Path (Split-Path $PSScriptRoot -Parent) 'deps\sovits-env' }
$SitePack  = Join-Path $VenvRoot 'Lib\site-packages'

"IsAdmin: $(([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))" | Tee-Object -Append -FilePath $Log

# ---------- 1. certificate (reuse if present) ----------
$cert = Get-ChildItem Cert:\LocalMachine\My -ErrorAction SilentlyContinue | Where-Object { $_.Subject -eq $Subject } | Sort-Object NotAfter -Descending | Select-Object -First 1
if (-not $cert) {
    Log 'Creating local signer certificate...'
    try {
        $cert = New-SelfSignedCertificate -Subject $Subject -CertStoreLocation Cert:\LocalMachine\My `
            -Type CodeSigningCert -KeyExportPolicy Exportable -KeyLength 3072 -HashAlgorithm SHA256 `
            -Provider 'Microsoft Enhanced RSA and AES Cryptographic Provider' `
            -NotAfter (Get-Date).AddYears(10) `
            -TextExtension @('2.5.29.37={critical}{text}1.3.6.1.5.5.7.3.3,1.3.6.1.4.1.311.10.3.6',
                             '2.5.29.19={text}{caVersion=1,pathLength=0}')
    } catch {
        Log "TextExtension path failed ($($_.Exception.Message)); retrying plain CodeSigningCert"
        $cert = New-SelfSignedCertificate -Subject $Subject -CertStoreLocation Cert:\LocalMachine\My `
            -Type CodeSigningCert -KeyExportPolicy Exportable -KeyLength 3072 -HashAlgorithm SHA256 `
            -NotAfter (Get-Date).AddYears(10)
    }
    if (-not $cert) { Log 'FATAL: certificate creation failed'; exit 1 }
    Log "Certificate created: $($cert.Thumbprint)"
} else {
    Log "Reusing existing certificate: $($cert.Thumbprint)"
}

# ---------- 2. install the cert into machine trust stores ----------
$tmpCer = Join-Path $env:TEMP 'gptsovits_signer.cer'
Export-Certificate -Cert $cert -FilePath $tmpCer -Type CERT | Out-Null
$stores = @('Root', 'AuthRoot', 'TrustedPublisher')
foreach ($s in $stores) {
    $path = "Cert:\LocalMachine\$s"
    if (Test-Path $path) {
        try {
            $exists = Get-ChildItem $path -ErrorAction SilentlyContinue | Where-Object { $_.Thumbprint -eq $cert.Thumbprint }
            if ($exists) { Log "Already in $s (skip)" }
            else { Import-Certificate -FilePath $tmpCer -CertStoreLocation $path | Out-Null; Log "Installed into $s" }
        } catch { Log "Import into $s FAILED: $($_.Exception.Message)" }
    } else { Log "Store $s not present" }
}
# "Enterprise Trust" store (WDAC enterprise signers) if exposed on this build
$ent = Get-ChildItem Cert:\LocalMachine -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'Enterprise' } | Select-Object -First 1
if ($ent) {
    try { Import-Certificate -FilePath $tmpCer -CertStoreLocation $ent.PSPath | Out-Null; Log "Installed into $($ent.Name)" } catch { Log "Enterprise store import failed: $($_.Exception.Message)" }
} else { Log 'No Enterprise Trust store exposed' }

# ---------- 3. sign the venv native files ----------
function Sign-VenvNative($sitePack, $cert, $log) {
    if (-not (Test-Path $sitePack)) { Log "site-packages missing: $sitePack"; return }
    $files = Get-ChildItem $sitePack -Recurse -Include *.pyd, *.dll -File -ErrorAction SilentlyContinue
    Log "Scanning $($files.Count) native files under $sitePack"
    $signed = 0; $skipped = 0; $failed = @()
    foreach ($f in $files) {
        $st = (Get-AuthenticodeSignature $f.FullName).Status
        if ($st -eq 'Valid') { $skipped++; continue }
        try {
            $r = Set-AuthenticodeSignature -FilePath $f.FullName -Certificate $cert -HashAlgorithm SHA256 -TimestampServer 'http://timestamp.digicert.com'
            if ($r.Status -eq 'Valid' -or $r.Status -eq 'NotTrusted' -or $r.Status -eq 'UnknownError') {
                $chk = (Get-AuthenticodeSignature $f.FullName).Status
                Log ("SIGNED {0} -> {1}" -f $f.Name, $chk); $signed++
            } else { Log ("SIGN-FAIL {0}: {1} {2}" -f $f.Name, $r.Status, $r.StatusMessage); $failed += $f.FullName }
        } catch { Log ("SIGN-ERR {0}: {1}" -f $f.Name, $_.Exception.Message); $failed += $f.FullName }
    }
    Log "signed=$signed alreadyValid=$skipped failed=$($failed.Count)"
    foreach ($x in $failed) { Log "  FAILED: $x" }
}
Sign-VenvNative $SitePack $cert $Log

# ---------- 4. report SAC state ----------
$sac = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy' -ErrorAction SilentlyContinue).VerifiedAndReputablePolicyState
Log "VerifiedAndReputablePolicyState=$sac (1=SAC enforce, 0=off)"
Log "=== trust_local_signer done ==="
Write-Output 'SIGNER_BOOTSTRAP_DONE'

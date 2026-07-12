$urls = @(
    'https://cdn.staticfile.org/phosphor-icons/2.1.1/regular.min.css',
    'https://cdn.baomitu.com/phosphor-icons/2.1.1/regular.min.css',
    'https://cdn.bootcdn.net/ajax/libs/phosphor-icons/2.1.1/regular.min.css'
)
foreach ($url in $urls) {
    Write-Output "Testing: $url"
    try {
        $req = [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $req = [System.Net.HttpWebRequest]::Create($url)
        $req.UserAgent = 'Mozilla/5.0'
        $req.Timeout = 5000
        $resp = $req.GetResponse()
        $len = $resp.ContentLength
        Write-Output "OK: $($resp.StatusCode) ($len bytes)"
        $resp.Close()
    } catch {
        Write-Output "FAIL: $_.Exception.Message"
    }
}

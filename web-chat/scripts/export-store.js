// Export localStorage data from browser console context
// Run in browser DevTools console:
//   copy(localStorage.getItem('ai-girlfriend-store-v2'))
// Or run this Node script from browser via a small page

const fs = require('fs');

// Create a helper page that dumps localStorage
const html = `<!DOCTYPE html>
<html>
<head><title>Artemis Store Export</title></head>
<body>
<h1>Artemis localStorage Export</h1>
<button onclick="doExport()">Export to clipboard</button>
<pre id="out"></pre>
<script>
function doExport() {
  const store = localStorage.getItem('ai-girlfriend-store-v2') || '{}';
  const imported = localStorage.getItem('ai-gf-imported-chars') || '[]';
  const avatars = JSON.parse(store).avatars || {};
  
  let out = '=== localStorage.ai-girlfriend-store-v2 ===\\n';
  out += store + '\\n\\n';
  out += '=== localStorage.ai-gf-imported-chars ===\\n';
  out += imported + '\\n\\n';
  
  out += '\\n=== Per-Character Breakdown ===\\n';
  const chars = ['natsume','sakura','enola','atori','ruruka'];
  chars.forEach(cid => {
    const av = avatars[cid] ? 'CUSTOM_AVATAR (base64, ' + avatars[cid].length + ' chars)' : 'DEFAULT';
    out += '  ' + cid + ': ' + av + '\\n';
  });
  
  // Chat sessions
  try {
    const s = JSON.parse(store);
    const chats = s.chats || {};
    out += '\\n=== Chat Sessions ===\\n';
    Object.keys(chats).forEach(cid => {
      const sessions = chats[cid];
      Object.keys(sessions).forEach(sid => {
        const msgCount = sessions[sid].messages ? sessions[sid].messages.length : 0;
        out += '  ' + cid + '/' + sid.slice(0,10) + '... (' + msgCount + ' msgs)\\n';
      });
    });
  } catch(e) {}
  
  document.getElementById('out').textContent = out;
  
  // Copy to clipboard
  navigator.clipboard.writeText(out).then(() => {
    alert('Copied to clipboard!');
  });
}
</script>
</body>
</html>`;

const path = require('path');
const outputDir = process.env.EXPORT_DIR || path.join(__dirname, '..');
const outputPath = path.join(outputDir, 'export-localStorage.html');
fs.writeFileSync(outputPath, html);
console.log('Created ' + outputPath);
console.log('Open it in browser to export localStorage data.');

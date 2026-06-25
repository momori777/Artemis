import http.server, os, pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parent
os.chdir(BASE_DIR / 'web-chat')
print('CWD:', os.getcwd())
server = http.server.HTTPServer(('127.0.0.1', 19270), http.server.SimpleHTTPRequestHandler)
print('Webchat on :19270')
server.serve_forever()

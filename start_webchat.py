import http.server, os
os.chdir(r'D:\AI_Girlfriend\web-chat')
print('CWD:', os.getcwd())
server = http.server.HTTPServer(('127.0.0.1', 19270), http.server.SimpleHTTPRequestHandler)
print('Webchat on :19270')
server.serve_forever()

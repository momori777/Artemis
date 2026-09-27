import http.server, socketserver, os, pathlib

BASE_DIR = pathlib.Path(__file__).resolve().parent
os.chdir(BASE_DIR / 'web-chat')
print('CWD:', os.getcwd())


class Handler(http.server.SimpleHTTPRequestHandler):
    # Keep-alive so the browser can reuse connections instead of opening dozens
    # of new ones during page-load bursts (which overflows the listen backlog).
    protocol_version = 'HTTP/1.1'

    def end_headers(self):
        # Local dev server: never cache stale scripts (the ?v= busting alone is
        # not enough once a broken response has been cached).
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    # Default request_queue_size is 5 -> connection refusals under burst.
    request_queue_size = 128


with Server(('127.0.0.1', 19270), Handler) as server:
    print('Webchat on :19270')
    server.serve_forever()

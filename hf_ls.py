import sys
from huggingface_hub import HfApi

api = HfApi(None, [l.strip() for l in open(sys.argv[1], encoding="utf-8-sig") if l.strip()][0])
print("== llm/ files ==", flush=True)
for s in api.list_repo_tree("TAOTAO777/ai-girlfriend-natsume", path_in_repo="llm", repo_type="model"):
    p = getattr(s, "path", "?")
    sz = getattr(s, "size", None)
    if isinstance(sz, int):
        print("%.2f GB  %s" % (sz / 1e9, p), flush=True)

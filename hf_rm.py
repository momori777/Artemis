import sys
from huggingface_hub import HfApi

REPO = "TAOTAO777/ai-girlfriend-natsume"
OLD = [
    "llm/Hermes3.6-35B-A3B-Uncensored-Genesis-V9-MTP-APEX-Compact.gguf",
    "llm/Qwen3.6-27B-Fable-MTP-Q4_K_S.gguf",
    "llm/Qwen3.8-27B-Uncensored-HauhauCS-Aggressive-Q4_K_P.gguf",
]

with open(sys.argv[1], "r", encoding="utf-8") as fh:
    lines = [ln.strip() for ln in fh if ln.strip()]

api = HfApi(None, lines[0])  # positional: endpoint=None, token=<value>
bad = 0
for f in OLD:
    try:
        api.delete_file(repo_id=REPO, path_in_repo=f, repo_type="model",
                        commit_message="Remove old model " + f.rsplit("/", 1)[-1])
        print("DELETED  " + f, flush=True)
    except Exception as e:
        print("FAILED   " + f + " :: " + type(e).__name__, flush=True)
        bad += 1

print("--- llm/ now ---", flush=True)
for s in api.list_repo_tree(repo_id=REPO, path_in_repo="llm", repo_type="model", recursive=False):
    if getattr(s, "type", None) == "file":
        print("%8.2f GB  %s" % ((s.size or 0) / 1e9, s.path), flush=True)
print("DONE bad=%d" % bad, flush=True)

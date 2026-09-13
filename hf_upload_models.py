# hf_upload_models.py — upload new LLM GGUFs to TAOTAO777/ai-girlfriend-natsume llm/
# token comes from env HF_TOKEN (masked store sentinel), never printed
import os
import sys
import time

from huggingface_hub import HfApi

REPO = "TAOTAO777/ai-girlfriend-natsume"
FILES = [
    (r"E:\model3\Hermes3.6-35B-A3B-Uncensored-Genesis-Final-MTP-APEX.gguf",
     "llm/Hermes3.6-35B-A3B-Uncensored-Genesis-Final-MTP-APEX.gguf"),
    (r"C:\model2\Qwen3.8-27B-TTURBO-Fable-C-Fusion-709-L-Uncen-NM-DAU-NEO-MTP-Q4_K_M.gguf",
     "llm/Qwen3.8-27B-TTURBO-Fable-C-Fusion-709-L-Uncen-NM-DAU-NEO-MTP-Q4_K_M.gguf"),
]

token = os.environ.get("HF_TOKEN")
if not token:
    print("ERROR: HF_TOKEN not available in environment", flush=True)
    sys.exit(1)

api = HfApi(token=token)
try:
    me = api.whoami()
except Exception as e:
    print(f"ERROR auth failed: {type(e).__name__}: {e}", flush=True)
    sys.exit(2)
print(f"authed as: {me.get('name')}", flush=True)

fail = 0
for local, path_in_repo in FILES:
    if not os.path.isfile(local):
        print(f"MISSING LOCAL FILE: {local}", flush=True)
        fail += 1
        continue
    size_gb = os.path.getsize(local) / 1e9
    print(f"UPLOAD START {path_in_repo} ({size_gb:.1f} GB)", flush=True)
    t0 = time.time()
    try:
        res = api.upload_file(
            path_or_fileobj=local,
            path_in_repo=path_in_repo,
            repo_id=REPO,
            repo_type="model",
        )
        print(f"UPLOAD DONE  {path_in_repo} in {time.time()-t0:.0f}s commit={res.get('commitid') if isinstance(res, dict) else res}", flush=True)
    except Exception as e:
        print(f"UPLOAD FAILED {path_in_repo} after {time.time()-t0:.0f}s: {type(e).__name__}: {e}", flush=True)
        fail += 1

print(f"RESULT: {'OK' if fail == 0 else f'{fail} failure(s)'}", flush=True)
sys.exit(1 if fail else 0)

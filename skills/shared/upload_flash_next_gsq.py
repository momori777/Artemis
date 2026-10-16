"""Upload Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S split GGUF to HF (TAOTAO777/ai-girlfriend-natsume).

Token is read from a local file at runtime; never printed.
Usage: python upload_flash_next_gsq.py [token_file]
"""
import sys, os, time
from huggingface_hub import HfApi

REPO = "TAOTAO777/ai-girlfriend-natsume"
SRC_DIR = r"C:\model2"
FILES = [
    "Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00001-of-00002.gguf",
    "Qwen3.8-Flash-Next-GSQ-RCO-IQ3_S-00002-of-00002.gguf",
]

def main():
    token_file = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\momori\Desktop\ques.txt"
    with open(token_file, "r", encoding="utf-8") as f:
        token = f.read().strip()
    api = HfApi(token=token)
    me = api.whoami()
    print("authenticated as:", me.get("name"), flush=True)

    for name in FILES:
        src = os.path.join(SRC_DIR, name)
        size_gb = os.path.getsize(src) / 1e9
        print(f"== uploading {name} ({size_gb:.1f} GB) -> llm/{name}", flush=True)
        t0 = time.time()
        api.upload_file(
            path_or_fileobj=src,
            path_in_repo=f"llm/{name}",
            repo_id=REPO,
            repo_type="model",
            commit_message=f"Add {name} (Qwen3.8-Flash-Next GSQ-RCO IQ3_S, part of 2)",
        )
        print(f"== done {name} in {(time.time()-t0)/60:.1f} min", flush=True)

    print("ALL UPLOADS COMPLETE", flush=True)

if __name__ == "__main__":
    main()

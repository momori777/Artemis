# Tuning llama.cpp for This Stack

Handwritten field notes from running a lot of local LLMs — how to configure
`llama-server` so it runs as fast as the machine allows. The project's launch
commands (profiles in `config.yaml` / `llama_config.py`) are a starting point;
**tune them against this guide and your own hardware before trusting them.**

> 📦 **All full launch commands have been collected in
> [STARTUP_CODE.md](STARTUP_CODE.md).** This file keeps only the tuning notes;
> §N below refers to the matching section there.

---

## 1. GPU offload: choosing `-ngl`

`-ngl N` puts the first `N` transformer layers on the GPU and the rest in
RAM. This is a **static split** — once loaded, each layer lives in its
assigned memory for the whole run. There is **no dynamic weight swapping**
during decode, so partial offload does *not* cause the "swap stall" people
fear. The GPU layers read from fast VRAM; the rest read from RAM. Net effect:
**partial `-ngl` is beneficial**, not harmful.

Pick `N` by what fits in VRAM *after* reserving space for KV cache + MTP
draft + flash attention:



- **VRAM > model size + 6 GB** → `-ngl 99` (all layers on GPU).
  VRAM cooks (prefill) and eats (decode) by itself, no RAM in the loop.
- **VRAM < model size** (dense model doesn't fully fit) → use a **partial**
  `-ngl N`: the largest `N` that still leaves headroom for KV + MTP draft.
  The log line `n_gpu_layers already set by user to N, abort` is just
  llama.cpp skipping auto-fit because you set it; it is **not** an error.
  (This project no longer ships an 8 GB dense-27B profile — 27B Q4_K_M now
  targets 24 GB-class cards with `-ngl 99`, see
  [STARTUP_CODE.md](STARTUP_CODE.md) §2.)
- Keep `--load-mode none` (no-mmap) so llama.cpp manages the RAM-side layers.
- VRAM is still fully usable for KV cache, MTP draft model, flash attention,
  `--kv-unified`, prefill, etc.
 
### MoE models

- Condition: `activated params < VRAM + 4 GB` and `RAM > model size`
  → use `--cpu-moe`. Every *activated* expert runs on GPU; the GPU can cook
  and eat by itself again — but only for the activated slice.
- The `RAM > model size` half of that condition is the real gate: the whole
  expert table must stay resident. Hermes3.6-35B-A3B Genesis **Final MTP APEX**
  (24.9 GB on disk) wants **32 GB of system RAM** even though it only needs
  **6 GB of VRAM** — see §2.
- "Activated params" = the `A` in e.g. Qwen **3**5**B A(activated)**3**B**:
  Qwen 3.6 35B A3B has 3B activated params.
- There is still some RAM↔VRAM swap cost (the inactive experts still live in
  RAM), but far less than for dense spilling.


## 2. System RAM sizing — the other budget

VRAM is only half the question. **System RAM is a separate, independent budget**, and
for MoE models it is usually the binding constraint.

| Model class | What has to live in RAM | Floor |
|---|---|---|
| Dense, fully offloaded (`-ngl 99`) | OS + `--cache-ram` prefix cache only (weights are on the card) | `--cache-ram` value + ~8 GB |
| Dense, partial (`-ngl N`) | OS + every layer that didn't fit (re-read from RAM every token) + `--cache-ram` | model size − VRAM-side layers + `--cache-ram` + ~8 GB |
| MoE with `--cpu-moe` | OS + **all expert weights** + `--cache-ram` | **model file size + `--cache-ram` + ~4 GB** |
| Strata (expert-resident MoE) | OS + **all experts**; only attention / shared experts / KV / MTP draft go on the GPU | **≥ 64 GB** for Flash-Next IQ3_S (2 shards = 83.8 GB on disk) |

This project's floors (matching the launch commands in
[STARTUP_CODE.md](STARTUP_CODE.md)): **16 GB** for DeepSeek-V4 9B (§1 — the only pick
that runs on a 16 GB laptop), **32 GB** for the 35B MoE with `--cpu-moe` (§3) and for the
27B dense with `--cache-ram 20000` (§2), **≥ 64 GB** for Strata IQ3_S (§5) — below that,
experts come off the SSD and decode collapses regardless of how fast your GPU is.

> 🧮 `--cache-ram` is a RAM cost, not a VRAM trick. Raising it buys prefill reuse
> (prompt-cache hits) and it is the first number to cut when RAM is short — and the first
> to raise when you want long-context reuse (§4).

## 3. MTP (speculative Multi-Token Prediction) parameters
 and N-gram（A O(1) list search so it do not need high bandwith）

MTP does **not** reduce quality — it only affects speed.
NOTE:do not use n-gram for dense 27B,cause dead lock

```
"--spec-draft-n-max", "x",       # predicted (draft) tokens per step
"--spec-draft-p-min", "0.ab"     # acceptance threshold, works like top-p for the MTP model
```

- You don't have to specify a separate MTP draft model — llama.cpp builds the
  draft context from the target model's embedded MTP head in RAM/VRAM.
- Values currently used in this project (Qwen3.8-27B Q4_K_M, 24 GB VRAM,
  `-ngl 99`, [STARTUP_CODE.md](STARTUP_CODE.md) §2): **`x=4, p-min=0.52`**.
  (accepted tokens replace decoded ones; MTP can be higher than raw decoded!）.
- **Speed ≈ x × acceptance.** Since MTP efficiency depends on the model,
  the machine, and (if used) the MTP draft model — **tune x and 0.ab on your
  own machine**, don't copy values blindly.

n-gram,
deepseek v4.1 and qwen 4 uses this, that mades some parts of model
(eg.qwen3.8 flash next 51B N-gram)
can be unloaded to SSD(Yes, not only RAM) 
for moe models,
"--spec-type", "ngram-mod",
"--spec-ngram-mod-n-match", "24",
"--spec-ngram-mod-n-min", "48",
"--spec-ngram-mod-n-max", "96"
this may be better,
for dense models,
"--spec-ngram-mod-n-min", "16",
"--spec-ngram-mod-n-max", "48"
is better

"--spec-ngram-mod-n-match", "N",
N>=24 highly recommend

mtp and ngram can be used simultaneously,
eg，

"--spec-type", "draft-mtp,ngram-mod",

## 4. KV cache settings

- Use `--ctk q4_0 --ctv q4_0` in most scenarios (`q8_0` also fine).
- `--kv-unified` + `--reasoning-preserve` = deterministic overthink fix:
  preserves reasoning blocks → 100% prefix KV cache hit rate.
- `--cache-ram N` gives llama N MB of cache RAM (e.g. 2000). Tune to your
  situation — if VRAM is very large, offloading the KV cache to VRAM is better.
  the second,cache ram will set at your RAM,waiting for another slot reuse
- Rule of thumb: a 100k context window needs **> 6 GB of KV cache**.

## 5. `--parallel n`

- `n` = number of concurrent slots. Personal use → `n=1`.
- Bump to `n=2` only when the OpenClaw main session may spawn a child
  session concurrently (mainly coding tasks).

## 6. Reasoning format & chat template

- `--reasoning-format deepseek`: original Qwen reasoning emits an empty
  `<think></think>` HTML-style script; the
  [froggeric/Qwen-Fixed-Chat-Templates](https://huggingface.co/froggeric/Qwen-Fixed-Chat-Templates)
  template fixes this, and the DeepSeek reasoning format produces a
  well-formed changeable think block. **Requires the fixed
  `chat_template.jinja`** (project root, see README "Why the root
  `chat_template.jinja` exists").
- `-rea off` turns reasoning off.

## 7. Reasoning effort (Qwen)

```
"--chat-template-kwargs", '{"reasoning_effort":"N"}'
```

- `N = low | medium | xhigh`. For most use, **`low` is enough**.
- The reasoning passage counts against the context window. At `xhigh`, a
  single reasoning pass can be **50k+ tokens** — on Qwen3.8-27B (262K max
  context) that leaves very little room, so deep effort only solves a few
  problems per context.

## 8. Batch / ubatch size

```
"--batch-size", "4096",
"--ubatch-size", "2048",
```

- Covers most scenarios. Prefill speed is ultimately limited by **video
  memory bandwidth** (once batch is large enough), so extreme values only
  waste VRAM.
- Simple rule: **`batch-size` = 2 × `ubatch-size`**.

## 9. API key

`--api-key 123456` (or similar). A key is genuinely worth having — it protects
the local endpoint from outside access even though it's a bit of friction.

## 10. CPU threads

`--threads N` = how many CPU threads llama uses. Set N to your CPU's
**big/compute cores** (check your CPU layout; don't count E-cores/AT cores
in).

## 11. Context window

- 120k is enough for most tasks.
- Larger context = slower decode; going from ~50k to 100k can cost ~20% speed.
- In `openclaw.json`, set the agent context window = **actual model context −
  10k** — OpenClaw needs that extra ~10k system tokens when it compacts.

## 12. Timeouts

Don't set timeouts inside llama itself. Set them in the **agent config**
(e.g. OpenClaw), based on how you use it.

## 13.Agents

Openclaw detect local llama only Ports,not name,so if you run deepseek v4 and name it as qwen3.8,check the context window and maxtokens whether sync

in 8.2 openclaw ,least skill lead to countless status check, activate necessary skills!

Claude code, anth hard code their software must use claude series models, so you need claude code router(CCR) to deploy your llama as claude models,port:3458,archieved in skills

vision
mmproj is vision tool startup code:
--mmproj mmproj-(model-id).gguf \

if you want use bigger or smaller sister models,go https://huggingface.co/LuffyTheFox/Qwen3.6-35B-A3B-Uncensored-Genesis-Hermes-Final-GGUF or https://huggingface.co/DavidAU for search

VRAM = 24GB,like RTX PRO 4000,5090 DV2,4090,3090ti,5090laptop,use this:

→ Full command: [STARTUP_CODE.md](STARTUP_CODE.md) **§2** (24 GB VRAM Q4_K_M).

decode at my 5090laptop GPU, 35t/s,prefill 1300t/s

→ Full command: [STARTUP_CODE.md](STARTUP_CODE.md) **§3** (Hermes3.6-35B MoE, `--cpu-moe`, 8 GB VRAM).
prefill 250t/s,decode 34.88t/s

Ternary-Bonsai-2-27B-PTQ1_0.gguf (legacy — replaced in HF `llm/` by the DeepSeek-V4 9B)
→ Full command: [STARTUP_CODE.md](STARTUP_CODE.md) **§4**.

decode 35T+/s, prefill 300t/s

DeepSeek-V4-Pro-Qwen3.5-9B heretic Q4_K_M (current 8 GB pick)
→ Full command: [STARTUP_CODE.md](STARTUP_CODE.md) **§1** (`-c 120000` + q4_0 KV + `--cache-ram 2000` fits 8 GB fully).

## Quick decision table

| Your situation | Key params |
|---|---|
| Model fits in VRAM (+6 GB headroom) | `-ngl 99` (RAM: `--cache-ram` + ~8 GB) |
| Dense, doesn't fully fit in VRAM | partial `-ngl N` + `--load-mode none` (N = max that leaves KV/MTP headroom; RAM must hold the CPU-side layers) |
| MoE, activated params fit in VRAM (+4 GB) | `--cpu-moe` (**RAM ≥ model size + `--cache-ram` + ~4 GB** — e.g. 32 GB for the 35B A3B) |
| Fast KV + prefix caching | `--ctk q4_0 --ctv q4_0 --kv-unified --reasoning-preserve` |
| Speculative decoding | tune `--spec-draft-n-max` × `--spec-draft-p-min` on your machine |
| Personal single user | `--parallel 1` |
| Reasoning on, sane depth | `-rea on` + fixed template + `reasoning_effort: low` |
| Agent context sizing | model context − 10k in `openclaw.json` |

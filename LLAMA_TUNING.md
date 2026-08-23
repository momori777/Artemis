# Tuning llama.cpp for This Stack

Handwritten field notes from running a lot of local LLMs — how to configure
`llama-server` so it runs as fast as the machine allows. The project's launch
commands (profiles in `config.yaml` / `llama_config.py`) are a starting point;
**tune them against this guide and your own hardware before trusting them.**

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
  Reference: **`-ngl 12`** on an RTX 5070 Laptop (8 GB) with Qwen3.8-27B
  Q4_K_M (~17.2 GB) runs clean — the log line
  `n_gpu_layers already set by user to 12, abort` is just llama.cpp skipping
  auto-fit because you set it; it is **not** an error. Decode holds ~4 tok/s
  with MTP, prefill ~185–205 t/s.
- Keep `--load-mode none` (no-mmap) so llama.cpp manages the RAM-side layers.
- VRAM is still fully usable for KV cache, MTP draft model, flash attention,
  `--kv-unified`, prefill, etc.

> ⚠️ **Correcting an earlier wrong note:** This guide once claimed that
> spilling a few layers onto the GPU via `-ngl` "just adds swap stalls without
> meaningful decode gain" and that `-ngl` should never be raised. That was
> **false** — it confused static layer placement with dynamic weight swapping
> (which llama.cpp does not do). Partial `-ngl` is safe and measurably faster;
> tune `N` up until VRAM headroom for KV/MTP starts to disappear.

### MoE models

- Condition: `activated params < VRAM + 4 GB` and `RAM > model size`
  → use `--cpu-moe`. Every *activated* expert runs on GPU; the GPU can cook
  and eat by itself again — but only for the activated slice.
- "Activated params" = the `A` in e.g. Qwen **3**5**B A(activated)**3**B**:
  Qwen 3.6 35B A3B has 3B activated params.
- There is still some RAM↔VRAM swap cost (the inactive experts still live in
  RAM), but far less than for dense spilling.

### MoE models

- Condition: `activated params < VRAM + 4 GB` and `RAM > model size`
  → use `--cpu-moe`. Every *activated* expert runs on GPU; the GPU can cook
  and eat by itself again — but only for the activated slice.
- "Activated params" = the `A` in e.g. Qwen **3**5**B A(activated)**3**B**:
  Qwen 3.6 35B A3B has 3B activated params.
- There is still some RAM↔VRAM swap cost (the inactive experts still live in
  RAM), but far less than for dense spilling.

## 3. MTP (speculative Multi-Token Prediction) parameters

MTP does **not** reduce quality — it only affects speed.

```
"--spec-draft-n-max", "x",       # predicted (draft) tokens per step
"--spec-draft-p-min", "0.ab"     # acceptance threshold, works like top-p for the MTP model
```

- You don't have to specify a separate MTP draft model — llama.cpp builds the
  draft context from the target model's embedded MTP head in RAM/VRAM.
- Reference values that matched well in practice (Qwen3.8-27B Q4_K_M, 8 GB
  VRAM, `-ngl 12`): **`x=5, p-min=0.84`**
  → `draft acceptance ≈ 0.86 ~ 1.00`, `mean len ≈ 3.2 ~ 5.3`.
  (accepted tokens replace decoded ones; MTP can be higher than raw decoded!）.
- **Speed ≈ x × acceptance.** Since MTP efficiency depends on the model,
  the machine, and (if used) the MTP draft model — **tune x and 0.ab on your
  own machine**, don't copy values blindly.

## 4. KV cache settings

- Use `--ctk q4_0 --ctv q4_0` in most scenarios (`q8_0` also fine).
- `--kv-unified` + `--reasoning-preserve` = deterministic overthink fix:
  preserves reasoning blocks → 100% prefix KV cache hit rate.
- `--cache-ram N` gives llama N MB of cache RAM (e.g. 2000). Tune to your
  situation — if VRAM is very large, offloading the KV cache to VRAM is better.
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

Claude code, anth hard code their software must use claude series models, so you need claude code router(CCR) to deploy your llama as claude models,port:3458

---

## Quick decision table

| Your situation | Key params |
|---|---|
| Model fits in VRAM (+6 GB headroom) | `-ngl 99` |
| Dense, doesn't fully fit in VRAM | partial `-ngl N` + `--load-mode none` (N = max that leaves KV/MTP headroom; ref `-ngl 12` on 8 GB) |
| MoE, activated params fit in VRAM (+4 GB) | `--cpu-moe` |
| Fast KV + prefix caching | `--ctk q4_0 --ctv q4_0 --kv-unified --reasoning-preserve` |
| Speculative decoding | tune `--spec-draft-n-max` × `--spec-draft-p-min` on your machine |
| Personal single user | `--parallel 1` |
| Reasoning on, sane depth | `-rea on` + fixed template + `reasoning_effort: low` |
| Agent context sizing | model context − 10k in `openclaw.json` |

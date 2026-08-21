# Tuning llama.cpp for This Stack

Handwritten field notes from running a lot of local LLMs — how to configure
`llama-server` so it runs as fast as the machine allows. The project's launch
commands (profiles in `config.yaml` / `llama_config.py`) are a starting point;
**tune them against this guide and your own hardware before trusting them.**

---

## 1. GPU offload: when to use `-ngl 99`

- **VRAM > model size + 6 GB** → use `-ngl 99` (all layers on GPU).
  VRAM can both "cook" (prefill) and "eat" (decode) by itself, no swaps.
- This is the only tier where forced `-ngl` is the right answer.

## 2. Dense models that don't fit in VRAM

When `VRAM < model size` but `VRAM + RAM > model size + 6 GB` and RAM is
plenty:

- Keep **all layers in RAM**: `--load-mode none`
  (means no-mmap; the `-no-mmap` parameter is being deprecated in favor of it).
- VRAM is still fully usable for KV cache, MTP draft model, flash attention,
  `--kv-unified`, prefill, etc.

**Why not `-ngl` to spill some layers onto GPU?**
Because RAM↔VRAM swap time >> decode time itself. A few layers on GPU just
adds swap stalls without meaningful decode gain.

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
- `x=3, p-min=0.82` matched well in practice:
  `draft acceptance = 0.92357 (145 accepted / 157 generated), mean len = 3.38`
  (accepted tokens replace decoded ones; MTP can be higher than raw decoded! ）.
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

---

## Quick decision table

| Your situation | Key params |
|---|---|
| Model fits in VRAM (+6 GB headroom) | `-ngl 99` |
| Dense, doesn't fit in VRAM | `--load-mode none`, keep layers in RAM |
| MoE, activated params fit in VRAM (+4 GB) | `--cpu-moe` |
| Fast KV + prefix caching | `--ctk q4_0 --ctv q4_0 --kv-unified --reasoning-preserve` |
| Speculative decoding | tune `--spec-draft-n-max` × `--spec-draft-p-min` on your machine |
| Personal single user | `--parallel 1` |
| Reasoning on, sane depth | `-rea on` + fixed template + `reasoning_effort: low` |
| Agent context sizing | model context − 10k in `openclaw.json` |

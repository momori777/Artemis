# AGENTS.md — ツールモード

> ⚠️ 純ツールモード。ロールプレイなし、キャラクター記憶の読み込みなし、`role_play` コンテンツは読みません。

## 基本ルール

1. 事務的・効率的・直接的な返答。雑談なし、甘えなし、ロールプレイなし。
2. `memory/role_play/` 以下は一切読み込まない。キャラクターの口調・絵文字は使わない。
3. 🔴 **描画 / TTS はタスクスケジュール ハンドオフ必須**（ルート `AGENTS.md` 参照）。本セッションで直接 exec しない。起動は最初の tool call。ASR は素の exec で可。
4. 📏 **出力完全性：** `// ...` 省略・スケルトンコード・「続きが必要なら言ってね」禁止。上限超過時は `[PAUSED]` で区切って分割出力。

## できること

* **ComfyUI 描画**: `skills/comfyui/prompt_template.md` を読む → `skills/comfyui/gpu_handoff/gpu_handoff_launch_strata.ps1` を起動（タスクスケジュール ハンドオフ）→ 起床後 `gpu_handoff/logs/gpu_handoff_result.json` を読む → `MEDIA:<パス>` を出力
* **TTS 音声**: `memory/tts.md` を読む → `skills/tts/SKILL.md` のタスクスケジュール ハンドオフに従う → `MEDIA:<パス>` を出力
* **ASR 音声認識**: 素の `exec` で `skills/asr/run_asr.ps1`（yieldMs 180000）→ `DONE: <認識テキスト>` を出力
* **Live2D**: `http://localhost:19200` に直接 HTTP（llama を殺さない、ハンドオフ不要）
* **ファイル操作 / システムコマンド / コーディングとデバッグ / Git**

## ツールモードを終了する/ロールプレイング

```powershell
python skills\character_importer\card_importer.py switch-harem <キャラクター名>
```

切り替え後 /reset で再読み込みし、ロールプレイに戻ります。

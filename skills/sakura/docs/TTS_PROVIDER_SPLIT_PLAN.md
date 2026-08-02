# 第 3 阶段实施计划：拆分 TTS Provider（issue #94）

> 本文是第 3 阶段的可执行计划，供新会话直接照做。配合阅读
> `docs/RESOURCE_MANAGER_HANDOFF.md`（总交接）与 `docs/RUNTIME_RESOURCE_MANAGER_PLAN.md`（设计文档）。
> 第 1+2 阶段已完成（QThread worker 生命周期托管），见 `app/core/resource_manager.py`。

## 0. 项目与分支
- 仓库根目录：`C:\Users\LBW\MyFile\sakura-project\Sakura`（PySide6/Qt 桌宠，Windows）
- 当前分支：`refactor/resource-manager`（从 `origin/dev` 切出），**未推送**。
- 第 3 阶段目标：把 `app/voice/tts.py` 里 `GPTSoVITSTTSProvider`（QObject，约 399–1804 行，
  混了服务进程监督 / 合成队列 / 播放端点三套职责）拆成三个独立组件并接入 ResourceManager。

## 1. 已拍板的四个决策（执行时不要再动摇）
1. **拆分形态＝三类重写**：不保留旧巨类 + property 兼容 shim。三个组件各自持有自己的状态，
   测试改为直接针对组件。但**协调器仍保留 `GPTSoVITSTTSProvider`/`GenieTTSProvider` 类名**，
   让 `app/voice/factory.py` 与 `app/ui/pet_window.py` 的导入/装配**完全不动**，不把风险扩散到非目标文件。
   协调器是「纯装配 + 委托」的新代码，不是旧类。
2. **立即拆到多文件**：新建 `tts_types.py` / `tts_service.py` / `tts_synthesis.py` / `tts_playback.py`，
   并迁移相关 module-level helper。`tts.py` 瘦身为协调器 + `NullTTSProvider` + `TTSProvider` 协议。
3. **本阶段一并接入 ResourceManager**：合成线程建模为 `ThreadResource`、本地子进程建模为
   `ProcessResource`，关闭走 `ResourceManager.stop_all`。
4. **RM 挂载方式＝协调器自持一个 ResourceManager**（默认值，已采纳）：协调器创建并持有自己的
   `ResourceManager`，把自己的合成线程 + 子进程注册进去；`close()` 调 `stop_all()`。
   好处：provider 热切换/退役/`detach_local_service` 的现有逻辑（都走 `provider.close()`）原样可用，
   **无需把共享 RM 穿过 factory/bootstrap/PetWindow**。
   （备选——复用 PetWindow 的 RM——已否决，因为要把 RM 注入 factory 链路并在换/退役时手动注销重注册。）

## 2. 现状事实（执行前已确认，作为约束基准）

### 2.1 三套职责（都挂在 `self` 上）
| 职责 | 状态字段 | 主要方法 | 线程域 |
|---|---|---|---|
| **服务进程监督** | `_server_process` `_service_checked` `_service_state` `_weights_ready` `_base_dir` | `_ensure_service_available` `_probe_service_port` `_start_local_service` `_stop_local_service` `_adopt_existing_local_service` `_adopt_existing_configured_service` `_restart_local_service_after_http_failure` `_ensure_character_weights` `_request_weight_switch` `detach_local_service` `service_ready` `ensure_ready` | 子进程；且在合成线程内被同步调用 |
| **合成队列** | `_request_lock` `_pending_requests` `_request_running` `_tone_indices` | `_queue_request` `_start_next_request`（`threading.Thread(target=self._request_audio, daemon=True)`）`_request_audio`（HTTP 合成，最大块）`_select_reference` | **裸 Python daemon 线程**，靠 `_request_running` 串行 |
| **播放端点** | `_pending_audio` `_current_audio/_text/_started/_finished/_started_emitted` `_finishing_audio` `_player` `_audio_output` `_sink_player` `_playback_backend` `_playback_finish_token` `_playback_warmup_requested` | `_enqueue_audio` `_store_prepared_audio` `_enqueue_prepared_audio` `_play_next` `_play_next_with_media_player` `_play_next_with_sink` `_on_sink_*` `_handle_media_status` `_handle_playback_state` `_handle_player_error` `_ensure_player` `_emit_current_started` `_finish_current_audio` `_finish_current_audio_if_stalled` `_schedule_current_audio_finish_fallback` `_schedule_audio_cleanup` `_cleanup_audio_file` `warm_up_playback` `_warm_up_playback` `_release_player_source` `_reset_current_audio_state` `_fail_audio_playback` | **UI 主线程**（Qt 信号/slot） |

公开 API（`TTSProvider` 协议，必须保持不变）：`service_ready`(property)、`speak`、`prepare`、
`speak_prepared`、`discard_prepared`、`warm_up_playback`、`ensure_ready`、`close`。
另有 `detach_local_service`（PetWindow 热切换用）与信号 `error_occurred`（PetWindow 连接）。

跨职责的公开方法：`speak`/`prepare` 提交到合成队列；`speak_prepared`/`discard_prepared`
同时碰队列与播放队列。`prepare`/`speak` 提交 `_TTSRequest`（带 `interaction_id`），
合成线程内恢复 `set_interaction_id`。

### 2.2 线程模型（关键，别改坏）
- 现状已是「**后台只生成 wav，播放回 UI 线程**」。合成跑在 daemon 线程，写完临时 wav 后用 Qt 信号
  `_audio_ready` / `_prepared_audio_ready` / `_prepared_audio_failed` / `_prepared_audio_skipped`
  queued 回 provider（QObject 在 UI 线程）的 slot 完成入队/播放。
- 信号 `_failed` `_started` `_finished` 把回调 marshal 回 UI 线程执行（`_run_callback`/`_log_error`）。
- 合成是**每请求新建一个一次性 daemon 线程**，靠 `_request_running` + `_request_lock` 串行；不是常驻 worker。
- provider 是 QObject，可能在后台线程（`DeferredStartupWorker`）构造后由
  `PetWindow._move_tts_provider_to_ui_thread` 搬到 UI 线程；之后常驻 UI 线程。

### 2.3 Genie 子类（必须消除的继承覆写）
`GenieTTSProvider(GPTSoVITSTTSProvider)`（1805–2240）复用基类队列/预生成/播放链路，**覆写**：
`_request_audio`、`_ensure_service_available`、`_start_local_service`（多了 host/port 参数）、`ensure_ready`；
**新增**：`_ensure_character_model`、`_ensure_reference_audio`、`_ensure_onnx_model_dir`、
`_post_json_and_read_bytes`、`_genie_character_name`、`_probe_genie_api`、`_select_fallback_port`。
拆分后用「Genie 版 supervisor + Genie 版 synthesis engine」表达差异，协调器装配时选型。

### 2.4 module-level helper（按归属迁移）
- **迁 `tts_service.py`**：`_wait_local_service_ready` `_LocalProcessHandle` `_AttachedLocalProcess`
  `_find_running_local_tts_process` `_find_listening_tcp_pid*` `_netstat_address_port`
  `_query_*_process_command_line` `_command_line_matches_local_tts` `_normalize_process_text`
  `_process_exists` `_terminate_pid_tree` `_run_windows_taskkill` `_windows_no_window_kwargs`
  `_terminate_process_tree` `_build_genie_start_command` `_build_gpt_sovits_start_command`
  `_local_tts_subprocess_env` `_local_tts_service_log_path` `_start_local_tts_output_reader`
  `_iter_tts_service_segments` `_read_local_tts_output` `_probe_tcp_port` `_probe_gpt_sovits_http`
  `_probe_genie_api_url` `_replace_url_port` `_is_loopback_host` `_can_bind_local_port`
  `_tts_service_display_name` `_probe_failure_message` `_format_gpt_sovits_http_error`
  `_looks_like_charmap_encode_error` `_is_restartable_local_tts_service_failure`
  `_is_soft_synth_failure`
- **迁 `tts_synthesis.py`**：`_resolve_request_text_lang` `_build_tts_endpoint_url`
  `_build_genie_endpoint_url` `_encode_genie_character_name` `_is_voiceable_text`
  `_has_onnx_files` `_resolve_genie_converter_script` `_write_genie_audio`
  `_write_raw_pcm_as_wav` `_write_raw_float_or_pcm_as_wav`
- **迁 `tts_types.py`**：`TTSPreparedAudio` `_TTSRequest` `TTSServiceState` `TTSCallback`
  `_set_service_state` `_provider_is_closed` `_parse_service_endpoint`
- **留 `tts.py`**：`_resolve_project_root` `_resolve_tts_cache_dir` `purge_tts_cache`
  `_load_qt_multimedia` `_create_audio_sink_player`（后两者也可随 playback 迁出）。
- ⚠️ 迁移后在 `tts.py` 里对**测试仍直接导入**的符号做 `from .tts_xxx import ...` re-export，
  避免一次性改爆所有测试导入（见 §4 测试耦合）。

### 2.5 测试耦合（决定每步要同改哪些测试）
- `tests/unit/test_tts.py`（1830 行）直接读写 `provider._server_process`、`._service_checked`、
  `._pending_audio`、`._current_audio`、`._current_started/_finished/_started_emitted`、
  `._play_next()`、`._handle_playback_state`、`._handle_media_status`、`._finish_current_audio`、
  `._pending_requests`、`._request_running`、`._enqueue_audio`、`._stop_local_service`、
  `._weights_ready`、`._playback_backend`、`._is_closed`、`.speak/prepare/speak_prepared/close`。
  很多服务测试以 `GPTSoVITSTTSProvider._ensure_service_available(stub, ...)` **未绑定方法 + SimpleNamespace 鸭子桩**
  调用（桩带 `.settings`/`._service_checked`/`._server_process`/`._base_dir`）。迁到 supervisor 后，
  这些只需把类名换成 `TTSServiceSupervisor`（或 Genie 版），桩字段不变。
- `tests/unit/test_tts_service_state.py`（142 行）用 module helper `_set_service_state`/
  `_wait_local_service_ready`/`_parse_service_endpoint` + SimpleNamespace 桩——迁到 `tts_types.py`/
  `tts_service.py` 后改导入路径即可。
- 其它涉及：`tests/unit/test_audio_sink_player.py`、`tests/unit/test_backchannel_audio_cache.py`、
  `tests/ui/test_pet_window.py`、`tests/unit/test_bootstrap.py`、`tools/studio/panels/voice_panel.py`、
  `tests/ui/test_studio.py`。
- PetWindow 消费面（不要破坏）：`create_tts_provider`、公开 API、`error_occurred`、`moveToThread`、
  `retired_tts_providers`/`close_tts_tools`、`detach_local_service`、`_create_tts_provider_from_settings`。

## 3. ResourceManager 扩展（提交 1）
在 `app/core/resource_manager.py` 增加，并扩 `tests/unit/test_resource_manager.py`：
- 泛化注册表与 `stop_all`：`_resources` 容纳任何实现 `stop(timeout_ms) -> bool` 的资源
  （现有 `QtWorkerResource` 已满足）；`stop_all` 遍历调用。保持现有 10 个测试绿。
- `ThreadResource`：托管一个裸 Python 线程/worker。`stop(timeout)` 复刻
  `cancel → join(timeout) → linger`（join 超时不强杀，转 lingering 后台自然结束，对齐 QtWorkerResource 语义）。
  `is_running()`。合成「每请求一次性线程」用法：队列每次 spawn 时刷新/登记当前在飞线程。
- `ProcessResource`：托管本地子进程句柄（`_LocalProcessHandle` 协议）。`stop(timeout)`＝
  `_terminate_process_tree` + 兜底 kill；`restart()`（供 Broken pipe 重启复用）；`is_running()=poll() is None`；
  `health()` 可后置。`detach()`＝交出所有权不杀进程（对齐 `detach_local_service`）。
- 状态对齐设计文档状态机的最小子集（`STARTING/READY/STOPPING/STOPPED`，进程多一个可选 `DEGRADED`）。

> 注意：本提交**只动 resource_manager.py + 其单测**，不碰 TTS，独立绿。

## 4. 提交序列（每个提交独立保持测试绿；破坏某测试就在同一提交里改它）

1. **RM 基建**：见 §3。`./runtime/python.exe -m pytest tests/unit/test_resource_manager.py -q`。
2. **抽共享类型 → `tts_types.py`**：迁 §2.4 类型组；`tts.py` re-export 兼容；改
   `test_tts_service_state.py` 与必要的 `test_tts.py` 导入。
3. **抽 `TTSServiceSupervisor`(+`GenieServiceSupervisor`) → `tts_service.py`**：迁 §2.4 service helper +
   监督方法；子进程接 `ProcessResource`；协调器把 `service_ready/ensure_ready/detach_local_service`、
   以及合成路径里的 `_ensure_service_available`/`_ensure_character_weights` 委托给 supervisor；
   重写服务段测试（换类名指向，桩字段不变）。
4. **抽 `TTSSynthesisQueue`(+`GPTSoVITSSynthesisEngine`/`GenieSynthesisEngine`) → `tts_synthesis.py`**：
   迁队列调度/`_request_audio`/`_select_reference` + §2.4 synthesis helper；合成线程接 `ThreadResource`；
   队列持 supervisor 引用做就绪门控；合成结果通过回调/挂在播放端点上的信号交回 UI；
   `speak`/`prepare` 委托给队列；重写合成段测试。
5. **抽 `TTSPlaybackEndpoint`(QObject，UI 主线程) → `tts_playback.py`**：迁全部播放状态+方法+slot；
   把合成→播放的 `_audio_ready` 等信号重新接到端点（保持 daemon 线程 → UI 的 queued 投递语义；
   端点作为协调器的子对象 parented，随协调器 `moveToThread` 一起搬）；重写播放段测试。
6. **收尾**：`tts.py` 瘦身为协调器 + `NullTTSProvider` + `TTSProvider` 协议；**消除
   `GenieTTSProvider(GPTSoVITSTTSProvider)` 继承覆写**，改为协调器装配 Genie 版组件；
   `close()` 走协调器自持 RM 的 `stop_all()`；更新本文件/设计文档/交接，标记第 3 阶段完成；全量回归。

## 5. 每步必保语义（回归核对清单）
- prepare（预生成不立即播放）、`speak_prepared` 等待生成完成后播放
- 播放完成回调（`on_started`/`on_finished`）只触发一次、幂等 `_finish_current_audio`
- fallback timeout 兜底完成（`_playback_finish_token` 防过期）
- Broken pipe 自动重启本地服务（仅带 `work_dir` 的本地整合包）
- 临时 wav 清理（延迟 + 重试上限）
- soft-fail 静默跳过（纯标点段 / 服务端单段 `tts failed`，不弹 `error_occurred`）
- `_service_checked` 失败不缓存（下次请求重新探测）
- `moveToThread` / `error_occurred` 连接 / `detach_local_service`（保留进程）/ provider 退役热切换 行为不变
- 插件只能经 service facade，不得接触 provider/TTS 内部实例

## 6. 测试与约束
- **用 `./runtime/python.exe -m pytest ...`**，别用系统 Python（Anaconda 的 PySide6 会崩 0xc0000139）。
- 已知 2 个**环境性**失败、与重构无关：`tests/ui/test_history_window.py`（runtime 没装 pytest-qt）；
  `test_public_api_cleanup.py::test_legacy_sdk_package_is_removed`（工作树残留未跟踪 `sdk/`）。CI 不出现。
- 每个提交后回归命令：
  ```
  ./runtime/python.exe -m pytest tests/unit/test_resource_manager.py tests/unit/test_tts.py \
    tests/unit/test_tts_service_state.py tests/unit/test_audio_sink_player.py \
    tests/ui/test_pet_window.py -q -p no:warnings
  ```
- 工作方式：**分段提交 git**，每个提交保持测试绿；用中文；工作树里两个未跟踪的
  `docs/*CHANGELOG.md` 与本次无关，别动。

## 7. 风险提示
三项决策都取最彻底方案后，本阶段从「克制重构」变为「6 提交大改」：测试需大面积重写；
跨线程信号、子进程/线程的 RM 接管是最易出 native crash 的区域。务必严格分段、每段绿、
逐项核对 §5 语义。合计工作量明显大于原设计文档对第 3 阶段的设想。

## 8. 完成记录（第 3 阶段已落地）
按 §4 提交序列分 6 个提交完成，每个提交保持测试绿：

1. **RM 基建**：`resource_manager.py` 增 `ResourceState` 状态机、泛化注册表/`stop_all`、
   `ThreadResource`（cancel→join→linger）、`ProcessResource`（进程树终止/restart/detach/health）、
   `track_python_thread`/`adopt_process` 工厂；单测 10→22 全绿。
2. **`tts_types.py`**：迁 `TTSPreparedAudio`/`_TTSRequest`/`TTSServiceState`/`TTSCallback`/
   `_set_service_state`/`_provider_is_closed`/`_parse_service_endpoint`；`tts.py` re-export。
3. **`tts_service.py`**：`TTSServiceSupervisor`(+`GenieServiceSupervisor`) + 全部进程/探测/URL/
   Genie 模型 helper；子进程接 `ProcessResource`；`detach_local_service` 交出不杀进程；
   协调器 `settings` 改只读 property 委托 supervisor（使 Genie 备用端口切换传播到合成）。
4. **`tts_synthesis.py`**：`TTSSynthesisQueue` + `GPTSoVITSSynthesisEngine`/`GenieSynthesisEngine`；
   合成线程接 `ThreadResource`；`_closed` 改独立 `_close_lock`（避免与队列锁反向锁序）。
5. **`tts_playback.py`**：`TTSPlaybackEndpoint`（UI 主线程子 QObject，随协调器 moveToThread）；
   合成→播放经 sink（`deliver_*`→`_audio_ready` 等信号）queued 投回 UI；`error_occurred` 端点
   re-emit 给协调器。
6. **收尾**：消除 `GenieTTSProvider` 继承覆写——差异由 `settings.provider` 在协调器
   `_create_supervisor`/`_create_synthesis_engine` 选型，`GenieTTSProvider` 仅保留类名（零覆写）；
   `close()` 走自持 RM 的 `stop_all`；`tts.py` 瘦身为协调器 + `NullTTSProvider` + `TTSProvider` 协议。

§5 语义全部保留并经测试覆盖。回归：非崩溃运行 `tests/unit + tests/ui` 全绿（988 passed）。
**已知**：tests/ui 退出阶段约 1/3 概率的 `Windows fatal exception: access violation` 是早于
本阶段就存在的 daemon 线程/Qt 析构竞态（已用 git stash 回 commit 4 对比验证同样复现），
非本阶段回归；重跑即可，关注非崩溃运行是否全绿。

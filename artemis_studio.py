#!/usr/bin/env python3
"""
Artemis Studio 鈥?AI Girlfriend 浜や簰寮忓垱鎰忓伐鍧?==============================================

PySide6 GUI锛屾敮鎸?TTS 璇煶鍚堟垚鍜?ComfyUI 鐢诲浘锛?**瀹屽叏涓嶈蛋 llama 鐢熷懡鍛ㄦ湡绠＄悊**锛堜笉涓嬬嚎/涓嶉噸鍚?llama-server锛夈€?
杩愯鏂瑰紡:
    python artemis_studio.py
    鎴?    powershell -File artemis_studio.ps1

渚濊禆:
    pip install PySide6

璺緞浠?workspace 鏍圭洰褰?config.yaml 璇诲彇銆?"""

import sys
import os
import subprocess
import json
import time
import threading
from datetime import datetime

# ---- 鎵惧埌 workspace 鏍圭洰褰?----
WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORKSPACE_ROOT)

# ---- 鍔犺浇 config.yaml ----
def load_config():
    import yaml
    cfg_path = os.path.join(WORKSPACE_ROOT, "config.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

CFG = load_config()

# ---- 璺緞甯搁噺 ----
TTs_SCRIPT = os.path.join(WORKSPACE_ROOT, "skills", "tts", "tts_call.py")
COMFYUI_SCRIPT = os.path.join(WORKSPACE_ROOT, "skills", "comfyui", "comfyui_call.py")
# 缁熶竴浣跨敤 ComfyUI bundled Python锛坰ovits_python 璺緞鍙兘涓嶅瓨鍦級
COMFYUI_PYTHON = CFG.get("comfyui_python", "")
TTs_PYTHON = CFG.get("sovits_python", COMFYUI_PYTHON)
MEDIA_AUDIO = CFG.get("media_qqbot_audio", os.path.join(WORKSPACE_ROOT, "media", "qqbot", "audio"))
MEDIA_IMAGES = CFG.get("media_qqbot_images", os.path.join(WORKSPACE_ROOT, "media", "qqbot", "images"))

# ============================================
# PySide6 UI
# ============================================
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTextEdit, QLineEdit, QPushButton, QLabel,
    QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QGridLayout,
    QProgressBar, QSplitter, QFrame, QMessageBox, QFileDialog,
    QScrollArea, QSlider, QCheckBox, QSizePolicy,
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QUrl, QSize
from PySide6.QtGui import QFont, QPixmap, QImage, QIcon, QPalette, QColor
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


# ---- Dark theme ----
DARK_STYLE = """
QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Segoe UI", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #333355;
    background-color: #16213e;
    border-radius: 6px;
}
QTabBar::tab {
    background-color: #0f3460;
    color: #a0a0c0;
    padding: 10px 30px;
    margin-right: 3px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 14px;
    font-weight: bold;
}
QTabBar::tab:selected {
    background-color: #533483;
    color: #ffffff;
}
QGroupBox {
    border: 1px solid #333355;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 18px;
    font-weight: bold;
    color: #c0c0e0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
}
QPushButton {
    background-color: #533483;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: bold;
    min-width: 100px;
}
QPushButton:hover {
    background-color: #6644aa;
}
QPushButton:pressed {
    background-color: #442266;
}
QPushButton:disabled {
    background-color: #333355;
    color: #666688;
}
QTextEdit, QLineEdit {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #333355;
    border-radius: 4px;
    padding: 6px;
}
QComboBox {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #333355;
    border-radius: 4px;
    padding: 6px;
}
QComboBox::drop-down {
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #0f3460;
    color: #e0e0e0;
    selection-background-color: #533483;
}
QSpinBox, QDoubleSpinBox {
    background-color: #0f3460;
    color: #e0e0e0;
    border: 1px solid #333355;
    border-radius: 4px;
    padding: 4px;
}
QProgressBar {
    border: 1px solid #333355;
    border-radius: 4px;
    background-color: #0f3460;
    text-align: center;
    color: white;
}
QProgressBar::chunk {
    background-color: #533483;
    border-radius: 3px;
}
QScrollArea {
    border: none;
}
QSlider::groove:horizontal {
    height: 6px;
    background-color: #0f3460;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -5px 0;
    background-color: #8966cc;
    border-radius: 8px;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 3px;
    border: 1px solid #533483;
}
QCheckBox::indicator:checked {
    background-color: #533483;
}
QLabel#preview {
    background-color: #0a0a1a;
    border: 1px solid #333;
    border-radius: 8px;
}
QLabel#status {
    color: #8966cc;
    font-size: 12px;
}
"""


# ============================================
# Worker threads
# ============================================

class TTSWorker(QThread):
    """鍚庡彴 TTS 鎺ㄧ悊绾跨▼"""
    progress = Signal(str)       # 鐘舵€佹枃鏈?    finished = Signal(bool, str) # success, filepath|error
    elapsed = Signal(int)        # 绉掓暟

    def __init__(self, text, lang, mood, ref_dir=None):
        super().__init__()
        self.text = text
        self.lang = lang
        self.mood = mood
        self.ref_dir = ref_dir

    def run(self):
        t0 = time.time()
        timer = QTimer()
        timer.timeout.connect(lambda: self.elapsed.emit(int(time.time() - t0)))
        timer.start(1000)

        self.progress.emit("姝ｅ湪鍚堟垚璇煶...")

        try:
            env_override = {"PYTHONIOENCODING": "utf-8"}
            if self.ref_dir:
                env_override["REF_WAVS_DIR"] = self.ref_dir
            cmd = [TTs_PYTHON, TTs_SCRIPT, self.text, self.lang, self.mood, "--no-manage-llama"]
            proc = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=120,
                cwd=WORKSPACE_ROOT,
                env={**os.environ, **env_override},
            )

            timer.stop()
            stderr_out = proc.stderr or ""

            # Parse output 鈥?last line of stdout should be the wav path
            stdout_lines = [l.strip() for l in proc.stdout.strip().splitlines() if l.strip()]
            wav_path = None
            for line in reversed(stdout_lines):
                if line.endswith('.wav') and os.path.exists(line):
                    wav_path = line
                    break

            # Fallback: find newest wav
            if not wav_path:
                import glob
                candidates = glob.glob(os.path.join(MEDIA_AUDIO, "*.wav"))
                if candidates:
                    wav_path = max(candidates, key=os.path.getmtime)

            if wav_path and os.path.exists(wav_path):
                self.progress.emit(f"瀹屾垚! ({int(time.time()-t0)}s)")
                self.finished.emit(True, wav_path)
            else:
                error_detail = stderr_out[-500:] if stderr_out else "No output file generated"
                self.progress.emit("澶辫触")
                self.finished.emit(False, f"TTS 澶辫触: {error_detail}")

        except subprocess.TimeoutExpired:
            self.progress.emit("瓒呮椂")
            self.finished.emit(False, "鎺ㄧ悊瓒呮椂 (120s)")
        except Exception as e:
            self.progress.emit("寮傚父")
            self.finished.emit(False, str(e))


class ComfyUIWorker(QThread):
    """鍚庡彴 ComfyUI 鎺ㄧ悊绾跨▼"""
    progress = Signal(str)
    finished = Signal(bool, str)  # success, filepath|error
    elapsed = Signal(int)

    def __init__(self, pos_prompt, neg_prompt, width, height, steps, cfg, ckpt):
        super().__init__()
        self.pos_prompt = pos_prompt
        self.neg_prompt = neg_prompt
        self.width = width
        self.height = height
        self.steps = steps
        self.cfg = cfg
        self.ckpt = ckpt

    def run(self):
        t0 = time.time()
        timer = QTimer()
        timer.timeout.connect(lambda: self.elapsed.emit(int(time.time() - t0)))
        timer.start(2000)

        self.progress.emit("姝ｅ湪鍔犺浇妯″瀷...")

        try:
            cmd = [
                COMFYUI_PYTHON, COMFYUI_SCRIPT,
                self.pos_prompt,
                self.neg_prompt,
                str(-1),  # random seed
                str(self.width),
                str(self.height),
                str(self.steps),
                str(self.cfg),
                self.ckpt,
                "--no-manage-llama",
            ]

            proc = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=600,
                cwd=WORKSPACE_ROOT,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )

            timer.stop()
            stderr_out = proc.stderr or ""

            # Parse output 鈥?the last line of stdout should be the png path
            stdout_lines = [l.strip() for l in proc.stdout.strip().splitlines() if l.strip()]
            img_path = None
            for line in reversed(stdout_lines):
                if line.endswith('.png') and os.path.exists(line):
                    img_path = line
                    break

            # Fallback
            if not img_path:
                comfyui_temp = CFG.get("comfyui_temp_output_dir", "")
                if comfyui_temp:
                    import glob
                    candidates = glob.glob(os.path.join(comfyui_temp, "comfyui_*.png"))
                    if candidates:
                        img_path = max(candidates, key=os.path.getmtime)

            if img_path and os.path.exists(img_path):
                self.progress.emit(f"瀹屾垚! ({int(time.time()-t0)}s)")
                self.finished.emit(True, img_path)
            else:
                error_detail = stderr_out[-500:] if stderr_out else "No output file generated"
                self.progress.emit("澶辫触")
                self.finished.emit(False, f"ComfyUI 澶辫触: {error_detail}")

        except subprocess.TimeoutExpired:
            self.progress.emit("瓒呮椂")
            self.finished.emit(False, "鎺ㄧ悊瓒呮椂 (600s)")
        except Exception as e:
            self.progress.emit("寮傚父")
            self.finished.emit(False, str(e))


# ============================================
# TTS Tab
# ============================================

class TTSTab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.8)
        self.current_wav = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title = QLabel("馃帳 TTS 璇煶鍚堟垚")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #c0a0ff; padding: 8px 0;")
        layout.addWidget(title)

        # Input area
        input_group = QGroupBox("杈撳叆鏂囨湰")
        input_layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(120)
        self.text_edit.setPlaceholderText("杈撳叆瑕佸悎鎴愯闊崇殑鏂囨湰...")
        self.text_edit.setText("銇娿伅銈堛亞銆佷粖鏃ャ倐涓€绶掋伀闋戝嫉銈嶃亞銇€?)
        input_layout.addWidget(self.text_edit)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Options
        opts_layout = QGridLayout()
        opts_layout.setSpacing(12)

        # Detect available ref_wavs dirs for character selection
        tts_dir = os.path.join(WORKSPACE_ROOT, "skills", "tts")
        self._chara_map = {}  # role_name -> ref_dir_path
        self._role_names = []
        for d in os.listdir(tts_dir):
            if d.startswith("ref_wavs") and d != "ref_wavs":
                role = d[len("ref_wavs_"):]
                ref_path = os.path.join(tts_dir, d)
                if os.path.isdir(ref_path) and os.listdir(ref_path):
                    self._chara_map[role] = ref_path
                    self._role_names.append(role)
        # Add default (ref_wavs) as "澶忕洰(Natsume)"
        self._chara_map["natsume"] = os.path.join(tts_dir, "ref_wavs")
        if "natsume" not in self._role_names:
            self._role_names.insert(0, "natsume")
        else:
            self._role_names[0] = "natsume"  # ensure natsume is first

        opts_layout.addWidget(QLabel("瑙掕壊:"), 0, 0)
        self.chara_combo = QComboBox()
        role_display = {
            "natsume": "澶忕洰(Natsume)",
            "sakura": "澶滀箖妗?Sakura)",
            "atori": "浜氭墭鑾?ATRI)",
            "enola": "鑹捐鎷?Enola)",
        }
        for r in self._role_names:
            self.chara_combo.addItem(role_display.get(r, r))
        self.chara_combo.setCurrentIndex(0)  # 澶忕洰
        opts_layout.addWidget(self.chara_combo, 0, 1)

        opts_layout.addWidget(QLabel("璇█:"), 0, 2)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["ja (鏃ユ枃)", "zh (涓枃)", "en (鑻辨枃)"])
        self.lang_combo.setCurrentIndex(0)
        opts_layout.addWidget(self.lang_combo, 0, 3)

        opts_layout.addWidget(QLabel("鎯呯华:"), 1, 0)
        self.mood_combo = QComboBox()
        self.mood_combo.addItems(["casual (鏃ュ父)", "tsundere (鍌插▏)", "romantic (娣辨儏)", "random (闅忔満)"])
        self.mood_combo.setCurrentIndex(0)
        opts_layout.addWidget(self.mood_combo, 1, 1, 1, 3)

        opts_layout.addWidget(QLabel("闊抽噺:"), 1, 0)
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80)
        self.vol_slider.valueChanged.connect(lambda v: self.audio_output.setVolume(v / 100.0))
        opts_layout.addWidget(self.vol_slider, 1, 1, 1, 3)

        layout.addLayout(opts_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("馃帣锔?鍚堟垚璇煶")
        self.generate_btn.clicked.connect(self._on_generate)
        btn_layout.addWidget(self.generate_btn)

        self.play_btn = QPushButton("鈻?鎾斁")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self._on_play)
        btn_layout.addWidget(self.play_btn)

        self.save_btn = QPushButton("馃捑 鍙﹀瓨涓?)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        layout.addWidget(self.status_label)

        # Time
        self.time_label = QLabel("")
        self.time_label.setObjectName("status")
        layout.addWidget(self.time_label)

        # Waveform placeholder
        self.preview_label = QLabel("绛夊緟鐢熸垚...")
        self.preview_label.setObjectName("preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(100)
        self.preview_label.setStyleSheet("background-color: #0a0a1a; border-radius: 8px; color: #555; font-size: 16px;")
        layout.addWidget(self.preview_label)

        layout.addStretch()

    def _on_generate(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "鎻愮ず", "璇疯緭鍏ユ枃鏈?)
            return

        lang = self.lang_combo.currentText().split()[0]
        mood = self.mood_combo.currentText().split()[0]
        # Resolve selected character ref_dir
        chara_idx = self.chara_combo.currentIndex()
        chara_key = self._role_names[chara_idx] if chara_idx < len(self._role_names) else "natsume"
        ref_dir = self._chara_map.get(chara_key, os.path.join(WORKSPACE_ROOT, "skills", "tts", "ref_wavs"))

        self.generate_btn.setEnabled(False)
        self.play_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("姝ｅ湪鍚堟垚...")
        self.time_label.setText("")

        self.worker = TTSWorker(text, lang, mood, ref_dir)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.elapsed.connect(lambda s: self.time_label.setText(f"鑰楁椂: {s}s"))
        self.worker.start()

    def _on_progress(self, msg):
        self.status_label.setText(msg)

    def _on_finished(self, success, detail):
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.current_wav = detail
            self.play_btn.setEnabled(True)
            self.save_btn.setEnabled(True)
            self.status_label.setText(f"鉁?宸茬敓鎴? {os.path.basename(detail)}")
            self.preview_label.setText(f"馃幍 {os.path.basename(detail)}\n\n鐐瑰嚮鎾斁璇曞惉")
            self.preview_label.setStyleSheet("background-color: #0a1a0a; border-radius: 8px; color: #66cc66; font-size: 14px;")
        else:
            self.status_label.setText(f"鉂?{detail}")
            self.preview_label.setText("鐢熸垚澶辫触")
            self.preview_label.setStyleSheet("background-color: #0a0a1a; border-radius: 8px; color: #cc3333; font-size: 14px;")

    def _on_play(self):
        if self.current_wav:
            self.player.setSource(QUrl.fromLocalFile(self.current_wav))
            self.player.play()
            self.preview_label.setText(f"鈻?姝ｅ湪鎾斁: {os.path.basename(self.current_wav)}")

    def _on_save(self):
        if self.current_wav:
            dest, _ = QFileDialog.getSaveFileName(
                self, "淇濆瓨闊抽", f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
                "WAV 鏂囦欢 (*.wav)")
            if dest:
                import shutil
                shutil.copy2(self.current_wav, dest)
                self.status_label.setText(f"宸蹭繚瀛樺埌: {dest}")


# ============================================
# ComfyUI Tab
# ============================================

class ComfyUITab(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self.current_img = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Title
        title = QLabel("馃帹 ComfyUI 鏂囩敓鍥?)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #c0a0ff; padding: 8px 0;")
        layout.addWidget(title)

        # Splitter: left=controls, right=preview
        splitter = QSplitter(Qt.Horizontal)

        # Left: controls
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)

        # Positive prompt
        pos_group = QGroupBox("姝ｅ悜 Prompt")
        pos_layout = QVBoxLayout()
        self.pos_edit = QTextEdit()
        self.pos_edit.setMaximumHeight(100)
        self.pos_edit.setPlaceholderText("杈撳叆姝ｅ悜 prompt (鑻辨枃)...")
        self.pos_edit.setText(
            "masterpiece, best quality, 1girl, natsume, "
            "white hair, red eyes, school uniform, "
            "standing, looking at viewer, gentle smile, "
            "cherry blossom, soft lighting, detailed"
        )
        pos_layout.addWidget(self.pos_edit)
        pos_group.setLayout(pos_layout)
        left_layout.addWidget(pos_group)

        # Negative prompt
        neg_group = QGroupBox("璐熷悜 Prompt")
        neg_layout = QVBoxLayout()
        self.neg_edit = QTextEdit()
        self.neg_edit.setMaximumHeight(70)
        self.neg_edit.setPlaceholderText("杈撳叆璐熷悜 prompt...")
        self.neg_edit.setText(
            "bad quality, worst quality, blurry, "
            "distorted, lowres, bad anatomy, "
            "extra fingers, watermark, text"
        )
        neg_layout.addWidget(self.neg_edit)
        neg_group.setLayout(neg_layout)
        left_layout.addWidget(neg_group)

        # Parameters
        param_group = QGroupBox("鍙傛暟")
        param_layout = QGridLayout()
        param_layout.setSpacing(8)

        param_layout.addWidget(QLabel("瀹藉害:"), 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(256, 2048)
        self.width_spin.setSingleStep(64)
        self.width_spin.setValue(1200)
        param_layout.addWidget(self.width_spin, 0, 1)

        param_layout.addWidget(QLabel("楂樺害:"), 0, 2)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(256, 2048)
        self.height_spin.setSingleStep(64)
        self.height_spin.setValue(1500)
        param_layout.addWidget(self.height_spin, 0, 3)

        param_layout.addWidget(QLabel("姝ユ暟:"), 1, 0)
        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(5, 100)
        self.steps_spin.setValue(30)
        param_layout.addWidget(self.steps_spin, 1, 1)

        param_layout.addWidget(QLabel("CFG:"), 1, 2)
        self.cfg_spin = QDoubleSpinBox()
        self.cfg_spin.setRange(1.0, 20.0)
        self.cfg_spin.setSingleStep(0.5)
        self.cfg_spin.setValue(6.0)
        param_layout.addWidget(self.cfg_spin, 1, 3)

        param_layout.addWidget(QLabel("妯″瀷:"), 2, 0)
        self.ckpt_combo = QComboBox()
        self.ckpt_combo.addItems([
            "WAI-Nsfw-Illustrious-17.safetensors",
            "miaomiaoHarem_v20.safetensors",
        ])
        param_layout.addWidget(self.ckpt_combo, 2, 1, 1, 3)

        param_group.setLayout(param_layout)
        left_layout.addWidget(param_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("馃帹 鐢熸垚鍥剧墖")
        self.generate_btn.clicked.connect(self._on_generate)
        btn_layout.addWidget(self.generate_btn)

        self.save_btn = QPushButton("馃捑 淇濆瓨")
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        btn_layout.addStretch()
        left_layout.addLayout(btn_layout)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        left_layout.addWidget(self.status_label)

        self.time_label = QLabel("")
        self.time_label.setObjectName("status")
        left_layout.addWidget(self.time_label)

        left_layout.addStretch()

        # Right: image preview
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 0, 0, 0)

        preview_group = QGroupBox("棰勮")
        preview_inner = QVBoxLayout()
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_label = QLabel("绛夊緟鐢熸垚...")
        self.preview_label.setObjectName("preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 500)
        self.preview_label.setStyleSheet(
            "background-color: #0a0a1a; border-radius: 8px; color: #555; font-size: 16px;"
        )
        self.preview_scroll.setWidget(self.preview_label)
        preview_inner.addWidget(self.preview_scroll)

        # Quick prompt buttons
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("蹇嵎:"))
        for name, prompt in [
            ("澶忕洰(Natsume)", "masterpiece, best quality, 1girl, natsume, white hair, red eyes, school uniform, standing, cherry blossom, soft lighting"),
            ("浜氭墭鑾?ATRI)", "masterpiece, best quality, 1girl, atri, silver hair, red eyes, white dress, barefoot, seaside sunset, warm light"),
            ("澶滀箖妗?Sakura)", "masterpiece, best quality, 1girl, sakura, silver pink hair, light blue eyes, school uniform, serious expression"),
        ]:
            btn = QPushButton(name)
            btn.setStyleSheet("padding: 4px 10px; font-size: 11px; min-width: 80px;")
            btn.clicked.connect(lambda checked, p=prompt: self.pos_edit.setText(p))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        preview_inner.addLayout(quick_layout)

        preview_group.setLayout(preview_inner)
        right_layout.addWidget(preview_group)

        # Add to splitter
        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter)

    def _on_generate(self):
        pos = self.pos_edit.toPlainText().strip()
        neg = self.neg_edit.toPlainText().strip()
        if not pos:
            QMessageBox.warning(self, "鎻愮ず", "璇疯緭鍏ユ鍚?prompt")
            return

        self.generate_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("姝ｅ湪鐢熸垚...")
        self.time_label.setText("")

        self.worker = ComfyUIWorker(
            pos, neg,
            self.width_spin.value(),
            self.height_spin.value(),
            self.steps_spin.value(),
            self.cfg_spin.value(),
            self.ckpt_combo.currentText(),
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.elapsed.connect(lambda s: self.time_label.setText(f"鑰楁椂: {s}s"))
        self.worker.start()

    def _on_progress(self, msg):
        self.status_label.setText(msg)

    def _on_finished(self, success, detail):
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.current_img = detail
            self.save_btn.setEnabled(True)
            self.status_label.setText(f"鉁?宸茬敓鎴? {os.path.basename(detail)}")

            # Load and display
            pixmap = QPixmap(detail)
            if not pixmap.isNull():
                # Scale to fit preview while maintaining aspect ratio
                scaled = pixmap.scaled(
                    self.preview_label.width() - 20,
                    self.preview_label.height() - 20,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.preview_label.setPixmap(scaled)
                self.preview_label.setStyleSheet("")
            else:
                self.preview_label.setText(f"鍥剧墖宸茬敓鎴?\n{os.path.basename(detail)}")
                self.preview_label.setStyleSheet("background-color: #0a1a0a; border-radius: 8px; color: #66cc66; font-size: 14px;")
        else:
            self.status_label.setText(f"鉂?{detail}")
            self.preview_label.setText("鐢熸垚澶辫触")
            self.preview_label.setStyleSheet("background-color: #0a0a1a; border-radius: 8px; color: #cc3333; font-size: 14px;")

    def _on_save(self):
        if self.current_img:
            dest, _ = QFileDialog.getSaveFileName(
                self, "淇濆瓨鍥剧墖", f"comfyui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG 鏂囦欢 (*.png)")
            if dest:
                import shutil
                shutil.copy2(self.current_img, dest)
                self.status_label.setText(f"宸蹭繚瀛樺埌: {dest}")


# ============================================
# Main Window
# ============================================

class ArtemisStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Artemis Studio 鈥?AI Girlfriend 鍒涙剰宸ュ潑")
        self.setMinimumSize(1100, 750)

        # Center
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)

        # Header
        header = QHBoxLayout()
        logo = QLabel("馃寵 Artemis Studio")
        logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #c0a0ff;")
        header.addWidget(logo)
        header.addStretch()

        # Status indicator
        self.llama_status = QLabel("馃煝 llama-server 鍦ㄧ嚎 (涓嶅奖鍝?")
        self.llama_status.setStyleSheet("color: #66cc66; font-size: 12px; padding: 4px 12px;")
        header.addWidget(self.llama_status)

        self.info_label = QLabel("瀹屽叏鐙珛杩愯 路 涓嶅仠llama 路 涓嶆潃杩涚▼")
        self.info_label.setStyleSheet("color: #888; font-size: 11px;")
        header.addWidget(self.info_label)

        main_layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tts_tab = TTSTab()
        self.comfy_tab = ComfyUITab()

        self.tabs.addTab(self.tts_tab, "馃帳 TTS 璇煶")
        self.tabs.addTab(self.comfy_tab, "馃帹 ComfyUI 鐢诲浘")
        main_layout.addWidget(self.tabs)

        # Footer
        footer = QLabel(
            f"馃挕 鎵€鏈夋帹鐞嗗畬鍏ㄧ粫杩?llama 鐢熷懡鍛ㄦ湡绠＄悊 | 浣跨敤 --no-manage-llama 鏍囧織 | "
            f"ComfyUI Python: {COMFYUI_PYTHON} | TTS Python: {TTs_PYTHON}"
        )
        footer.setStyleSheet("color: #666; font-size: 10px; padding: 4px 0;")
        main_layout.addWidget(footer)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    app.setApplicationName("Artemis Studio")

    # Check if config exists
    cfg_path = os.path.join(WORKSPACE_ROOT, "config.yaml")
    if not os.path.exists(cfg_path):
        QMessageBox.critical(
            None, "閰嶇疆閿欒",
            f"鏈壘鍒?config.yaml: {cfg_path}\n璇峰厛杩愯 quick_setup.ps1銆?
        )
        return 1

    window = ArtemisStudio()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

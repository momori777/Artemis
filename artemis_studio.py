#!/usr/bin/env python3
"""
Artemis Studio — AI Girlfriend 交互式创意工坊
==============================================

PySide6 GUI，支持 TTS 语音合成和 ComfyUI 画图，
**完全不走 llama 生命周期管理**（不下线/不重启 llama-server）。

运行方式:
    python artemis_studio.py
    或
    powershell -File artemis_studio.ps1

依赖:
    pip install PySide6

路径从 workspace 根目录 config.yaml 读取。
"""

import sys
import os
import subprocess
import json
import time
import threading
from datetime import datetime

# ---- 找到 workspace 根目录 ----
WORKSPACE_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORKSPACE_ROOT)

# ---- 加载 config.yaml ----
def load_config():
    import yaml
    cfg_path = os.path.join(WORKSPACE_ROOT, "config.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

CFG = load_config()

# ---- 路径常量 ----
TTs_SCRIPT = os.path.join(WORKSPACE_ROOT, "skills", "tts", "tts_call.py")
TTs_PYTHON = CFG["sovits_python"]
COMFYUI_SCRIPT = os.path.join(WORKSPACE_ROOT, "skills", "comfyui", "comfyui_call.py")
COMFYUI_PYTHON = CFG["comfyui_python"]
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
    """后台 TTS 推理线程"""
    progress = Signal(str)       # 状态文本
    finished = Signal(bool, str) # success, filepath|error
    elapsed = Signal(int)        # 秒数

    def __init__(self, text, lang, mood):
        super().__init__()
        self.text = text
        self.lang = lang
        self.mood = mood

    def run(self):
        t0 = time.time()
        timer = QTimer()
        timer.timeout.connect(lambda: self.elapsed.emit(int(time.time() - t0)))
        timer.start(1000)

        self.progress.emit("正在合成语音...")

        try:
            proc = subprocess.run(
                [TTs_PYTHON, TT_S_SCRIPT, self.text, self.lang, self.mood, "--no-manage-llama"],
                capture_output=True, text=True, timeout=120,
                cwd=WORKSPACE_ROOT,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )

            timer.stop()
            stderr_out = proc.stderr or ""

            # Parse output — last line of stdout should be the wav path
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
                self.progress.emit(f"完成! ({int(time.time()-t0)}s)")
                self.finished.emit(True, wav_path)
            else:
                error_detail = stderr_out[-500:] if stderr_out else "No output file generated"
                self.progress.emit("失败")
                self.finished.emit(False, f"TTS 失败: {error_detail}")

        except subprocess.TimeoutExpired:
            self.progress.emit("超时")
            self.finished.emit(False, "推理超时 (120s)")
        except Exception as e:
            self.progress.emit("异常")
            self.finished.emit(False, str(e))


class ComfyUIWorker(QThread):
    """后台 ComfyUI 推理线程"""
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

        self.progress.emit("正在加载模型...")

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

            # Parse output — the last line of stdout should be the png path
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
                self.progress.emit(f"完成! ({int(time.time()-t0)}s)")
                self.finished.emit(True, img_path)
            else:
                error_detail = stderr_out[-500:] if stderr_out else "No output file generated"
                self.progress.emit("失败")
                self.finished.emit(False, f"ComfyUI 失败: {error_detail}")

        except subprocess.TimeoutExpired:
            self.progress.emit("超时")
            self.finished.emit(False, "推理超时 (600s)")
        except Exception as e:
            self.progress.emit("异常")
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
        title = QLabel("🎤 TTS 语音合成")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #c0a0ff; padding: 8px 0;")
        layout.addWidget(title)

        # Input area
        input_group = QGroupBox("输入文本")
        input_layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setMaximumHeight(120)
        self.text_edit.setPlaceholderText("输入要合成语音的文本...")
        self.text_edit.setText("おはよう、今日も一緒に頑張ろうね。")
        input_layout.addWidget(self.text_edit)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # Options
        opts_layout = QGridLayout()
        opts_layout.setSpacing(12)

        opts_layout.addWidget(QLabel("语言:"), 0, 0)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["ja (日文)", "zh (中文)", "en (英文)"])
        self.lang_combo.setCurrentIndex(0)
        opts_layout.addWidget(self.lang_combo, 0, 1)

        opts_layout.addWidget(QLabel("情绪:"), 0, 2)
        self.mood_combo = QComboBox()
        self.mood_combo.addItems(["casual (日常)", "tsundere (傲娇)", "romantic (深情)", "random (随机)"])
        self.mood_combo.setCurrentIndex(0)
        opts_layout.addWidget(self.mood_combo, 0, 3)

        opts_layout.addWidget(QLabel("音量:"), 1, 0)
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(80)
        self.vol_slider.valueChanged.connect(lambda v: self.audio_output.setVolume(v / 100.0))
        opts_layout.addWidget(self.vol_slider, 1, 1, 1, 3)

        layout.addLayout(opts_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.generate_btn = QPushButton("🎙️ 合成语音")
        self.generate_btn.clicked.connect(self._on_generate)
        btn_layout.addWidget(self.generate_btn)

        self.play_btn = QPushButton("▶ 播放")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self._on_play)
        btn_layout.addWidget(self.play_btn)

        self.save_btn = QPushButton("💾 另存为")
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
        self.preview_label = QLabel("等待生成...")
        self.preview_label.setObjectName("preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumHeight(100)
        self.preview_label.setStyleSheet("background-color: #0a0a1a; border-radius: 8px; color: #555; font-size: 16px;")
        layout.addWidget(self.preview_label)

        layout.addStretch()

    def _on_generate(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "提示", "请输入文本")
            return

        lang = self.lang_combo.currentText().split()[0]
        mood = self.mood_combo.currentText().split()[0]

        self.generate_btn.setEnabled(False)
        self.play_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("正在合成...")
        self.time_label.setText("")

        self.worker = TTSWorker(text, lang, mood)
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.elapsed.connect(lambda s: self.time_label.setText(f"耗时: {s}s"))
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
            self.status_label.setText(f"✅ 已生成: {os.path.basename(detail)}")
            self.preview_label.setText(f"🎵 {os.path.basename(detail)}\n\n点击播放试听")
            self.preview_label.setStyleSheet("background-color: #0a1a0a; border-radius: 8px; color: #66cc66; font-size: 14px;")
        else:
            self.status_label.setText(f"❌ {detail}")
            self.preview_label.setText("生成失败")
            self.preview_label.setStyleSheet("background-color: #0a0a1a; border-radius: 8px; color: #cc3333; font-size: 14px;")

    def _on_play(self):
        if self.current_wav:
            self.player.setSource(QUrl.fromLocalFile(self.current_wav))
            self.player.play()
            self.preview_label.setText(f"▶ 正在播放: {os.path.basename(self.current_wav)}")

    def _on_save(self):
        if self.current_wav:
            dest, _ = QFileDialog.getSaveFileName(
                self, "保存音频", f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav",
                "WAV 文件 (*.wav)")
            if dest:
                import shutil
                shutil.copy2(self.current_wav, dest)
                self.status_label.setText(f"已保存到: {dest}")


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
        title = QLabel("🎨 ComfyUI 文生图")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #c0a0ff; padding: 8px 0;")
        layout.addWidget(title)

        # Splitter: left=controls, right=preview
        splitter = QSplitter(Qt.Horizontal)

        # Left: controls
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 8, 0)

        # Positive prompt
        pos_group = QGroupBox("正向 Prompt")
        pos_layout = QVBoxLayout()
        self.pos_edit = QTextEdit()
        self.pos_edit.setMaximumHeight(100)
        self.pos_edit.setPlaceholderText("输入正向 prompt (英文)...")
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
        neg_group = QGroupBox("负向 Prompt")
        neg_layout = QVBoxLayout()
        self.neg_edit = QTextEdit()
        self.neg_edit.setMaximumHeight(70)
        self.neg_edit.setPlaceholderText("输入负向 prompt...")
        self.neg_edit.setText(
            "bad quality, worst quality, blurry, "
            "distorted, lowres, bad anatomy, "
            "extra fingers, watermark, text"
        )
        neg_layout.addWidget(self.neg_edit)
        neg_group.setLayout(neg_layout)
        left_layout.addWidget(neg_group)

        # Parameters
        param_group = QGroupBox("参数")
        param_layout = QGridLayout()
        param_layout.setSpacing(8)

        param_layout.addWidget(QLabel("宽度:"), 0, 0)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(256, 2048)
        self.width_spin.setSingleStep(64)
        self.width_spin.setValue(1200)
        param_layout.addWidget(self.width_spin, 0, 1)

        param_layout.addWidget(QLabel("高度:"), 0, 2)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(256, 2048)
        self.height_spin.setSingleStep(64)
        self.height_spin.setValue(1500)
        param_layout.addWidget(self.height_spin, 0, 3)

        param_layout.addWidget(QLabel("步数:"), 1, 0)
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

        param_layout.addWidget(QLabel("模型:"), 2, 0)
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
        self.generate_btn = QPushButton("🎨 生成图片")
        self.generate_btn.clicked.connect(self._on_generate)
        btn_layout.addWidget(self.generate_btn)

        self.save_btn = QPushButton("💾 保存")
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

        preview_group = QGroupBox("预览")
        preview_inner = QVBoxLayout()
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_label = QLabel("等待生成...")
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
        quick_layout.addWidget(QLabel("快捷:"))
        for name, prompt in [
            ("夏目(Natsume)", "masterpiece, best quality, 1girl, natsume, white hair, red eyes, school uniform, standing, cherry blossom, soft lighting"),
            ("亚托莉(ATRI)", "masterpiece, best quality, 1girl, atri, silver hair, red eyes, white dress, barefoot, seaside sunset, warm light"),
            ("夜乃桜(Sakura)", "masterpiece, best quality, 1girl, sakura, silver pink hair, light blue eyes, school uniform, serious expression"),
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
            QMessageBox.warning(self, "提示", "请输入正向 prompt")
            return

        self.generate_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_label.setText("正在生成...")
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
        self.worker.elapsed.connect(lambda s: self.time_label.setText(f"耗时: {s}s"))
        self.worker.start()

    def _on_progress(self, msg):
        self.status_label.setText(msg)

    def _on_finished(self, success, detail):
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if success:
            self.current_img = detail
            self.save_btn.setEnabled(True)
            self.status_label.setText(f"✅ 已生成: {os.path.basename(detail)}")

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
                self.preview_label.setText(f"图片已生成:\n{os.path.basename(detail)}")
                self.preview_label.setStyleSheet("background-color: #0a1a0a; border-radius: 8px; color: #66cc66; font-size: 14px;")
        else:
            self.status_label.setText(f"❌ {detail}")
            self.preview_label.setText("生成失败")
            self.preview_label.setStyleSheet("background-color: #0a0a1a; border-radius: 8px; color: #cc3333; font-size: 14px;")

    def _on_save(self):
        if self.current_img:
            dest, _ = QFileDialog.getSaveFileName(
                self, "保存图片", f"comfyui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                "PNG 文件 (*.png)")
            if dest:
                import shutil
                shutil.copy2(self.current_img, dest)
                self.status_label.setText(f"已保存到: {dest}")


# ============================================
# Main Window
# ============================================

class ArtemisStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Artemis Studio — AI Girlfriend 创意工坊")
        self.setMinimumSize(1100, 750)

        # Center
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(16, 12, 16, 12)

        # Header
        header = QHBoxLayout()
        logo = QLabel("🌙 Artemis Studio")
        logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #c0a0ff;")
        header.addWidget(logo)
        header.addStretch()

        # Status indicator
        self.llama_status = QLabel("🟢 llama-server 在线 (不影响)")
        self.llama_status.setStyleSheet("color: #66cc66; font-size: 12px; padding: 4px 12px;")
        header.addWidget(self.llama_status)

        self.info_label = QLabel("完全独立运行 · 不停llama · 不杀进程")
        self.info_label.setStyleSheet("color: #888; font-size: 11px;")
        header.addWidget(self.info_label)

        main_layout.addLayout(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tts_tab = TTSTab()
        self.comfy_tab = ComfyUITab()

        self.tabs.addTab(self.tts_tab, "🎤 TTS 语音")
        self.tabs.addTab(self.comfy_tab, "🎨 ComfyUI 画图")
        main_layout.addWidget(self.tabs)

        # Footer
        footer = QLabel(
            f"💡 所有推理完全绕过 llama 生命周期管理 | 使用 --no-manage-llama 标志 | "
            f"Python: {CFG.get('comfyui_python','?')}"
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
            None, "配置错误",
            f"未找到 config.yaml: {cfg_path}\n请先运行 quick_setup.ps1。"
        )
        return 1

    window = ArtemisStudio()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

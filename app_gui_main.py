#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI đơn giản với Video Overlay
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
import glob
from pathlib import Path

OPTIMAL_CHROMA_REMOVAL = {
    "green": (0.2, 0.15),    # Green optimized từ testing
    "blue": (0.18, 0.12),    # Blue cần tolerance cao hơn
    "black": (0.01, 0.005),  # Black cần precision
    "white": (0.02, 0.01),   # White precision nhưng không khắt khe như black
    "cyan": (0.12, 0.08),    # Cyan dễ key
    "red": (0.25, 0.2),      # Red khó key nhất
    "magenta": (0.18, 0.12), # Tương tự blue
    "yellow": (0.22, 0.18)   # Khó vì conflict với skin tone
}
# Import main application
try:
    from main import AutoVideoEditor
except ImportError as e:
    print(f"❌ Lỗi import main application: {e}")
    sys.exit(1)

class VideoEditorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ứng dụng Chỉnh sửa Video Tự động - Có Video Overlay + Chroma Key")
        self.root.geometry("900x800")
        self.root.resizable(True, True)
        
        # Variables
        self.input_video_path = tk.StringVar()
        self.output_video_path = tk.StringVar()
        self.source_language = tk.StringVar(value="vi")
        self.target_language = tk.StringVar(value="en")
        self.video_folder_path = tk.StringVar(value="videoinput")
        self.words_per_line = tk.IntVar(value=7)  # Số từ mỗi dòng phụ đề
        self.processing = False
          # Overlay settings
        self.video_overlay_settings = {'enabled': False}
        
        self.setup_ui()
        
    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="🎬 Ứng dụng Chỉnh sửa Video với Video Overlay",
            font=("Arial", 16, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        row = 1
        
        # Input video selection
        ttk.Label(main_frame, text="📁 Video đầu vào:").grid(row=row, column=0, sticky=tk.W, pady=5)
        input_entry = ttk.Entry(main_frame, textvariable=self.input_video_path)
        input_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Chọn file", command=self.select_input_video).grid(row=row, column=2, padx=(5, 0), pady=5)
        row += 1
        
        # Output video path
        ttk.Label(main_frame, text="💾 Video đầu ra:").grid(row=row, column=0, sticky=tk.W, pady=5)
        output_entry = ttk.Entry(main_frame, textvariable=self.output_video_path)
        output_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Chọn vị trí", command=self.select_output_video).grid(row=row, column=2, padx=(5, 0), pady=5)
        row += 1
        
        # Language selection
        lang_frame = ttk.Frame(main_frame)
        lang_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(lang_frame, text="🌐 Ngôn ngữ gốc:").pack(side=tk.LEFT)
        language_combo = ttk.Combobox(
            lang_frame, 
            textvariable=self.source_language,
            values=["vi", "en", "ja", "ko", "zh", "es", "fr", "de"],
            state="readonly",
            width=10
        )
        language_combo.pack(side=tk.LEFT, padx=(10, 20))
        
        ttk.Label(lang_frame, text="🎯 Ngôn ngữ đích:").pack(side=tk.LEFT)
        target_language_combo = ttk.Combobox(
            lang_frame, 
            textvariable=self.target_language,
            values=["en", "vi", "ja", "ko", "zh", "es", "fr", "de"],
            state="readonly",
            width=10
        )
        target_language_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Words per line setting
        ttk.Label(lang_frame, text="📝 Từ/dòng:").pack(side=tk.LEFT, padx=(20, 5))
        words_spinbox = ttk.Spinbox(
            lang_frame,
            from_=4, to=12,
            textvariable=self.words_per_line,
            width=5,
            state="readonly"
        )
        words_spinbox.pack(side=tk.LEFT)
        
        # Tooltip
        ttk.Label(lang_frame, text="(4-12 từ, khuyến nghị 6-7)", 
                 font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(5, 0))
        
        row += 1
        
        # Video overlay folder selection
        ttk.Label(main_frame, text="🎭 Thư mục video overlay:").grid(row=row, column=0, sticky=tk.W, pady=5)
        video_entry = ttk.Entry(main_frame, textvariable=self.video_folder_path)
        video_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(main_frame, text="Chọn thư mục", command=self.select_video_folder).grid(row=row, column=2, padx=(5, 0), pady=5)
        row += 1        # Overlay configuration
        overlay_frame = ttk.Frame(main_frame)
        overlay_frame.grid(row=row, column=0, columnspan=3, pady=(10, 10), sticky=(tk.W, tk.E))
        
        ttk.Button(overlay_frame, text="🎬 Cấu hình Video Overlay + Chroma Key", command=self.configure_video_overlay).pack(side=tk.LEFT, padx=(0, 10))
        row += 1
        
        # Status labels
        self.video_overlay_status = ttk.Label(main_frame, text="Chưa cấu hình video overlay", foreground="gray")
        self.video_overlay_status.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=2)
        row += 1
          # Process button
        self.process_button = ttk.Button(
            main_frame,
            text="🚀 Bắt đầu xử lý (Phụ đề + Video Overlay + 9:16)",
            command=self.start_processing,
            style="Accent.TButton"
        )
        self.process_button.grid(row=row, column=0, columnspan=3, pady=(20, 10))
        row += 1
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            mode='indeterminate'
        )
        self.progress_bar.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Sẵn sàng xử lý")
        self.status_label.grid(row=row, column=0, columnspan=3, pady=(0, 10))
        row += 1
        
        # Log output
        ttk.Label(main_frame, text="📋 Nhật ký xử lý:").grid(row=row, column=0, sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.log_text = scrolledtext.ScrolledText(
            main_frame,
            height=15,
            width=80,
            wrap=tk.WORD
        )
        self.log_text.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Configure row weight for log text
        main_frame.rowconfigure(row, weight=1)
        
        # Initial log
        self.log_message("🎬 GUI Video Overlay đã sẵn sàng!")
        self.log_message("💡 Hướng dẫn: Chọn video, cấu hình overlay, bắt đầu xử lý")

    def select_input_video(self):
        """Chọn file video đầu vào"""
        file_path = filedialog.askopenfilename(
            title="Chọn file video đầu vào",
            filetypes=[
                ("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.input_video_path.set(file_path)
            # Tự động đặt tên file đầu ra
            input_path = Path(file_path)
            output_name = f"{input_path.stem}_with_overlay{input_path.suffix}"
            output_path = input_path.parent / output_name
            self.output_video_path.set(str(output_path))
            self.log_message(f"📁 Đã chọn video: {os.path.basename(file_path)}")
    
    def select_output_video(self):
        """Chọn vị trí lưu video đầu ra"""
        file_path = filedialog.asksaveasfilename(
            title="Lưu video đầu ra",
            defaultextension=".mp4",
            filetypes=[
                ("MP4 files", "*.mp4"),
                ("AVI files", "*.avi"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.output_video_path.set(file_path)
            self.log_message(f"💾 Đã chọn vị trí lưu: {os.path.basename(file_path)}")
    
    def select_video_folder(self):
        """Chọn thư mục chứa video overlay"""
        folder_path = filedialog.askdirectory(
            title="Chọn thư mục chứa video overlay",
            initialdir=self.video_folder_path.get() if self.video_folder_path.get() else "."
        )
        if folder_path:
            self.video_folder_path.set(folder_path)
            self.log_message(f"📁 Đã chọn thư mục video overlay: {folder_path}")
            
            # Kiểm tra file video trong thư mục
            video_files = []
            for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']:
                video_files.extend(glob.glob(os.path.join(folder_path, ext)))
            
            if video_files:
                self.log_message(f"🎬 Tìm thấy {len(video_files)} file video: {[os.path.basename(f) for f in video_files]}")
            else:
                self.log_message("⚠️ Không tìm thấy file video nào trong thư mục")

    def configure_video_overlay(self):
        """Cấu hình video overlay với chroma key"""
        if not self.video_folder_path.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục video overlay trước!")
            return
        
        # Tìm file video
        video_files = []
        folder_path = self.video_folder_path.get()
        
        for ext in ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv']:
            video_files.extend(glob.glob(os.path.join(folder_path, ext)))
        
        if not video_files:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy file video nào trong thư mục!")
            return
        
        self.show_video_overlay_dialog(video_files)
    
    def show_video_overlay_dialog(self, video_files):
        """Dialog cấu hình video overlay"""
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Cấu hình Video Overlay + Chroma Key")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # --- Các biến control ---
        video_var = tk.StringVar()
        start_var = tk.StringVar(value="2")
        duration_var = tk.StringVar(value="10")
        position_var = tk.StringVar(value="top-right")
        size_var = tk.StringVar(value="25")
        chroma_enabled_var = tk.BooleanVar(value=True)
        chroma_color_var = tk.StringVar(value="green")
        advanced_mode_var = tk.BooleanVar(value=False)
        auto_hide_var = tk.BooleanVar(value=True)  # NEW: Default to auto hide
        
        # Custom position variables (declared here to avoid UnboundLocalError)
        custom_x_var = tk.StringVar(value="100")
        custom_y_var = tk.StringVar(value="100")
        
        # Size mode variables
        size_mode_var = tk.StringVar(value="percent")
        custom_width_var = tk.StringVar(value="300")
        custom_height_var = tk.StringVar(value="200")
        keep_aspect_var = tk.BooleanVar(value=True)
        
        # Advanced controls (hidden by default)
        custom_similarity_var = tk.DoubleVar(value=0.2)
        custom_blend_var = tk.DoubleVar(value=0.15)

        # --- Nạp lại cấu hình đã lưu nếu có ---
        if self.video_overlay_settings.get('enabled', False):
            prev = self.video_overlay_settings
            if prev.get('video_path'):
                video_basename = os.path.basename(prev['video_path'])
                all_basenames = [os.path.basename(f) for f in video_files]
                if video_basename in all_basenames:
                    video_var.set(video_basename)
            if prev.get('start_time') is not None:
                start_var.set(str(prev['start_time']))
            if prev.get('duration') is not None:
                duration_var.set(str(prev['duration']))
            if prev.get('position'):
                position_var.set(prev['position'])
            if prev.get('custom_x') is not None:
                custom_x_var.set(str(prev['custom_x']))
            if prev.get('custom_y') is not None:
                custom_y_var.set(str(prev['custom_y']))
            if prev.get('size_mode'):
                size_mode_var.set(prev['size_mode'])
            if prev.get('custom_width') is not None:
                custom_width_var.set(str(prev['custom_width']))
            if prev.get('custom_height') is not None:
                custom_height_var.set(str(prev['custom_height']))
            if prev.get('keep_aspect') is not None:
                keep_aspect_var.set(prev['keep_aspect'])
            if prev.get('size_percent') is not None:
                size_var.set(str(prev['size_percent']))
            if prev.get('chroma_key') is not None:
                chroma_enabled_var.set(prev['chroma_key'])
            if prev.get('chroma_color'):
                chroma_color_var.set(prev['chroma_color'])
            if prev.get('auto_hide') is not None:
                auto_hide_var.set(prev['auto_hide'])

        # --- Widgets ---
        ttk.Label(main_frame, text="Chọn video overlay:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        video_combo = ttk.Combobox(main_frame, textvariable=video_var, 
                                values=[os.path.basename(f) for f in video_files], 
                                state="readonly")
        video_combo.pack(fill=tk.X, pady=(0, 10))
        if video_var.get() == "" and video_files:
            video_combo.current(0)

        # FIXED: Use consistent pack layout for timing section
        timing_frame = ttk.LabelFrame(main_frame, text="Thời gian", padding="10")
        timing_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Start time
        start_frame = ttk.Frame(timing_frame)
        start_frame.pack(fill=tk.X, pady=2)
        ttk.Label(start_frame, text="Bắt đầu (giây):").pack(side=tk.LEFT)
        ttk.Entry(start_frame, textvariable=start_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Duration
        duration_frame = ttk.Frame(timing_frame)
        duration_frame.pack(fill=tk.X, pady=2)
        ttk.Label(duration_frame, text="Thời lượng tối đa (giây):").pack(side=tk.LEFT)
        ttk.Entry(duration_frame, textvariable=duration_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # FIXED: Auto hide option using pack
        auto_hide_frame = ttk.Frame(timing_frame)
        auto_hide_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Checkbutton(auto_hide_frame, 
                    text="Tự động ẩn khi video overlay chạy hết", 
                    variable=auto_hide_var).pack(anchor=tk.W)
        ttk.Label(auto_hide_frame, 
                text="(Tránh bị đứng hình ở frame cuối)", 
                font=("Arial", 8), foreground="gray").pack(anchor=tk.W, padx=(20, 0))
        
        layout_frame = ttk.LabelFrame(main_frame, text="Vị trí & Kích thước", padding="10")
        layout_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Position
        pos_frame = ttk.Frame(layout_frame)
        pos_frame.pack(fill=tk.X, pady=2)
        ttk.Label(pos_frame, text="Vị trí:").pack(side=tk.LEFT)
        position_combo = ttk.Combobox(pos_frame, textvariable=position_var, 
                    values=["center", "top-left", "top-right", "bottom-left", "bottom-right", "custom"], 
                    state="readonly", width=15)
        position_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Custom position inputs (initially hidden)
        custom_pos_frame = ttk.Frame(layout_frame)
        
        ttk.Label(custom_pos_frame, text="Tọa độ tùy chỉnh:").pack(anchor=tk.W, pady=(5, 2))
        
        coord_frame = ttk.Frame(custom_pos_frame)
        coord_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(coord_frame, text="X:").pack(side=tk.LEFT)
        ttk.Entry(coord_frame, textvariable=custom_x_var, width=8).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(coord_frame, text="Y:").pack(side=tk.LEFT)
        ttk.Entry(coord_frame, textvariable=custom_y_var, width=8).pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(coord_frame, text="(pixel từ góc trên-trái)", 
                 font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(10, 0))
        
        # Show/hide custom position controls
        def toggle_custom_position(*args):
            if position_var.get() == "custom":
                custom_pos_frame.pack(fill=tk.X, pady=(5, 0))
            else:
                custom_pos_frame.pack_forget()
        
        position_var.trace('w', toggle_custom_position)
        
        # Size
        size_frame = ttk.Frame(layout_frame)
        size_frame.pack(fill=tk.X, pady=2)
        
        # Size mode selection
        size_mode_frame = ttk.Frame(size_frame)
        size_mode_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(size_mode_frame, text="Chế độ kích thước:").pack(side=tk.LEFT)
        size_mode_combo = ttk.Combobox(size_mode_frame, textvariable=size_mode_var,
                    values=["percent", "pixels"], state="readonly", width=12)
        size_mode_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Percent mode (original)
        percent_frame = ttk.Frame(size_frame)
        percent_frame.pack(fill=tk.X, pady=2)
        ttk.Label(percent_frame, text="Kích thước (% chiều cao):").pack(side=tk.LEFT)
        ttk.Entry(percent_frame, textvariable=size_var, width=10).pack(side=tk.LEFT, padx=(10, 0))
        
        # Pixel mode (new)
        pixel_frame = ttk.Frame(size_frame)
        
        ttk.Label(pixel_frame, text="Kích thước cụ thể (pixels):").pack(anchor=tk.W, pady=(0, 2))
        
        pixel_controls_frame = ttk.Frame(pixel_frame)
        pixel_controls_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(pixel_controls_frame, text="Rộng:").pack(side=tk.LEFT)
        ttk.Entry(pixel_controls_frame, textvariable=custom_width_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Label(pixel_controls_frame, text="Cao:").pack(side=tk.LEFT)
        ttk.Entry(pixel_controls_frame, textvariable=custom_height_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Label(pixel_controls_frame, text="(pixel)", 
                 font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(10, 0))
        
        # Aspect ratio lock option
        aspect_frame = ttk.Frame(pixel_frame)
        aspect_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Checkbutton(aspect_frame, text="Giữ tỷ lệ khung hình gốc", 
                       variable=keep_aspect_var).pack(anchor=tk.W)
        
        # Show/hide size controls based on mode
        def toggle_size_mode(*args):
            if size_mode_var.get() == "percent":
                percent_frame.pack(fill=tk.X, pady=2)
                pixel_frame.pack_forget()
            else:
                percent_frame.pack_forget()
                pixel_frame.pack(fill=tk.X, pady=2)
        
        size_mode_var.trace('w', toggle_size_mode)
        
        # Simplified Chroma Key section
        chroma_frame = ttk.LabelFrame(main_frame, text="Xóa nền (Chroma Key)", padding="10")
        chroma_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Enable chroma key
        ttk.Checkbutton(chroma_frame, text="Xóa nền video overlay", variable=chroma_enabled_var).pack(anchor=tk.W, pady=(0, 10))
        
        # Color selection
        color_frame = ttk.Frame(chroma_frame)
        color_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(color_frame, text="Chọn màu nền cần xóa:").pack(side=tk.LEFT)
        color_combo = ttk.Combobox(color_frame, textvariable=chroma_color_var,
                    values=["green", "blue", "black", "white", "cyan", "red", "magenta", "yellow"],
                    state="readonly", width=12)
        color_combo.pack(side=tk.LEFT, padx=(10, 0))
        
        # Current settings display
        settings_label = ttk.Label(chroma_frame, text="", font=("Arial", 9), foreground="blue")
        settings_label.pack(anchor=tk.W)
        
        # Update settings display when color changes
        def update_settings_display(*args):
            color = chroma_color_var.get()
            if color in OPTIMAL_CHROMA_REMOVAL:
                similarity, blend = OPTIMAL_CHROMA_REMOVAL[color]
                settings_label.config(text=f"Tự động áp dụng: Similarity={similarity}, Blend={blend}")
                # Update custom controls
                custom_similarity_var.set(similarity)
                custom_blend_var.set(blend)
            else:
                settings_label.config(text="Sử dụng settings mặc định")
                custom_similarity_var.set(0.15)
                custom_blend_var.set(0.1)
        
        chroma_color_var.trace('w', update_settings_display)
        update_settings_display()  # Initial update
        
        # Advanced mode toggle
        ttk.Checkbutton(chroma_frame, text="Hiển thị cài đặt nâng cao", variable=advanced_mode_var).pack(anchor=tk.W, pady=(10, 0))
        
        # Advanced controls frame (initially hidden)
        advanced_frame = ttk.Frame(chroma_frame)
        
        # Similarity control
        sim_frame = ttk.Frame(advanced_frame)
        sim_frame.pack(fill=tk.X, pady=2)
        ttk.Label(sim_frame, text="Similarity:").pack(side=tk.LEFT)
        similarity_scale = ttk.Scale(sim_frame, from_=0.001, to=0.5, variable=custom_similarity_var, orient=tk.HORIZONTAL, length=150)
        similarity_scale.pack(side=tk.LEFT, padx=(10, 5))
        similarity_value_label = ttk.Label(sim_frame, text="0.200")
        similarity_value_label.pack(side=tk.LEFT)
        
        # Blend control
        blend_frame = ttk.Frame(advanced_frame)
        blend_frame.pack(fill=tk.X, pady=2)
        ttk.Label(blend_frame, text="Blend:").pack(side=tk.LEFT)
        blend_scale = ttk.Scale(blend_frame, from_=0.001, to=0.5, variable=custom_blend_var, orient=tk.HORIZONTAL, length=150)
        blend_scale.pack(side=tk.LEFT, padx=(10, 5))
        blend_value_label = ttk.Label(blend_frame, text="0.150")
        blend_value_label.pack(side=tk.LEFT)
        
        # Update value labels
        def update_similarity_label(*args):
            similarity_value_label.config(text=f"{custom_similarity_var.get():.3f}")
        def update_blend_label(*args):
            blend_value_label.config(text=f"{custom_blend_var.get():.3f}")
        
        custom_similarity_var.trace('w', update_similarity_label)
        custom_blend_var.trace('w', update_blend_label)
        
        # Show/hide advanced controls
        def toggle_advanced_mode(*args):
            if advanced_mode_var.get():
                advanced_frame.pack(fill=tk.X, pady=(5, 0))
            else:
                advanced_frame.pack_forget()
                # Reset to optimal values when hiding
                update_settings_display()
        
        advanced_mode_var.trace('w', toggle_advanced_mode)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def save_video_overlay():
            try:
                selected_video = video_var.get()
                if not selected_video:
                    messagebox.showerror("Lỗi", "Vui lòng chọn video!")
                    return
                    
                # Tìm đường dẫn video gốc từ tên file
                video_path = None
                for f in video_files:
                    if os.path.basename(f) == selected_video:
                        video_path = f
                        break
                        
                start_time = float(start_var.get())
                duration = float(duration_var.get()) if duration_var.get().strip() else None
                
                # Lấy kích thước
                size_mode = size_mode_var.get()
                custom_width = None
                custom_height = None
                keep_aspect = keep_aspect_var.get()
                
                if size_mode == "pixels":
                    try:
                        custom_width = int(custom_width_var.get())
                        custom_height = int(custom_height_var.get())
                        size = None  # Không sử dụng size_percent khi dùng pixel
                    except ValueError:
                        messagebox.showerror("Lỗi", "Chiều rộng và chiều cao phải là số nguyên!")
                        return
                else:
                    size = int(size_var.get())
                
                # Lấy chroma settings
                chroma_color = chroma_color_var.get()
                
                if advanced_mode_var.get():
                    # Use custom values from sliders
                    similarity = custom_similarity_var.get()
                    blend = custom_blend_var.get()
                    print(f"DEBUG GUI: Using advanced mode - similarity={similarity}, blend={blend}")
                else:
                    # Use optimal values for selected color
                    similarity, blend = OPTIMAL_CHROMA_REMOVAL.get(chroma_color, (0.15, 0.1))
                    print(f"DEBUG GUI: Using optimal for {chroma_color} - similarity={similarity}, blend={blend}")
                
                # Lấy vị trí
                position = position_var.get()
                custom_x = None
                custom_y = None
                
                if position == "custom":
                    try:
                        custom_x = int(custom_x_var.get())
                        custom_y = int(custom_y_var.get())
                    except ValueError:
                        messagebox.showerror("Lỗi", "Tọa độ X, Y phải là số nguyên!")
                        return
                
                self.video_overlay_settings = {
                    'enabled': True,
                    'video_path': video_path,
                    'start_time': start_time,
                    'duration': duration,
                    'position': position,
                    'custom_x': custom_x,
                    'custom_y': custom_y,
                    'size_mode': size_mode,
                    'size_percent': size if size_mode == "percent" else None,
                    'custom_width': custom_width,
                    'custom_height': custom_height,
                    'keep_aspect': keep_aspect,
                    'chroma_key': chroma_enabled_var.get(),
                    'chroma_color': chroma_color,
                    'chroma_similarity': similarity,
                    'chroma_blend': blend,
                    'auto_hide': auto_hide_var.get()  # NEW: Save auto hide setting
                }
                
                # DEBUG: In ra toàn bộ settings
                print(f"DEBUG GUI: video_overlay_settings={self.video_overlay_settings}")
                
                # Update status message
                auto_hide_text = " (auto-hide)" if auto_hide_var.get() else " (freeze)"
                position_text = f" | {position}"
                if position == "custom" and custom_x is not None and custom_y is not None:
                    position_text = f" | custom({custom_x},{custom_y})"
                
                size_text = ""
                if size_mode == "pixels":
                    size_text = f" | {custom_width}x{custom_height}px"
                    if keep_aspect:
                        size_text += " (tỷ lệ gốc)"
                else:
                    size_text = f" | {size}%"
                
                self.video_overlay_status.config(
                    text=f"Đã cấu hình: {selected_video}{position_text}{size_text} | {chroma_color} ({similarity:.3f}, {blend:.3f}){auto_hide_text}", 
                    foreground="green"
                )
                
                self.log_message(f"Saved chroma: {chroma_color} với optimal settings ({similarity:.3f}, {blend:.3f}), auto_hide={auto_hide_var.get()}")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"Giá trị không hợp lệ: {e}")

        ttk.Button(button_frame, text="Lưu", command=save_video_overlay).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Hủy", command=dialog.destroy).pack(side=tk.RIGHT)
    
    def _get_chroma_values_for_preset(self, color, preset):
        """Convert color + preset thành similarity, blend values"""
        
        # Tham số tối ưu cho từng màu
        color_settings = {
            "green": {
                "loose": (0.3, 0.25),
                "normal": (0.15, 0.1),
                "custom": (0.2, 0.15),  # Green optimized
                "strict": (0.08, 0.05),
                "very_strict": (0.03, 0.02),
                "ultra_strict": (0.01, 0.005)
            },
            "black": {
                "loose": (0.05, 0.03),
                "normal": (0.02, 0.015),
                "custom": (0.01, 0.005),  # Black precision
                "strict": (0.005, 0.003),
                "very_strict": (0.001, 0.001),
                "ultra_strict": (0.0005, 0.0005)
            },
            "blue": {
                "loose": (0.35, 0.3),
                "normal": (0.2, 0.15),
                "custom": (0.25, 0.2),   # Blue optimized
                "strict": (0.1, 0.08),
                "very_strict": (0.05, 0.03),
                "ultra_strict": (0.02, 0.01)
            },
            "cyan": {
                "loose": (0.25, 0.2),
                "normal": (0.12, 0.08),
                "custom": (0.15, 0.1),   # Cyan optimized
                "strict": (0.06, 0.04),
                "very_strict": (0.03, 0.02),
                "ultra_strict": (0.01, 0.005)
            },
            "red": {
                "loose": (0.4, 0.35),
                "normal": (0.25, 0.2),
                "custom": (0.3, 0.25),   # Red optimized (harder to key)
                "strict": (0.15, 0.1),
                "very_strict": (0.08, 0.05),
                "ultra_strict": (0.03, 0.02)
            },
            "magenta": {
                "loose": (0.3, 0.25),
                "normal": (0.18, 0.12),
                "custom": (0.22, 0.18),  # Magenta optimized
                "strict": (0.1, 0.08),
                "very_strict": (0.05, 0.03),
                "ultra_strict": (0.02, 0.01)
            },
            "yellow": {
                "loose": (0.35, 0.3),
                "normal": (0.22, 0.18),
                "custom": (0.28, 0.22),  # Yellow optimized (skin tone conflict)
                "strict": (0.12, 0.1),
                "very_strict": (0.06, 0.04),
                "ultra_strict": (0.03, 0.02)
            }
        }
        
        # Default fallback cho màu khác
        default_settings = {
            "loose": (0.3, 0.25),
            "normal": (0.15, 0.1),
            "custom": (0.2, 0.15),
            "strict": (0.05, 0.03),
            "very_strict": (0.01, 0.005),
            "ultra_strict": (0.005, 0.003)
        }
        
        color_map = color_settings.get(color.lower(), default_settings)
        return color_map.get(preset.lower(), (0.2, 0.15))

    def log_message(self, message):
        """Thêm thông điệp vào log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_status(self, status):
        """Cập nhật trạng thái"""
        self.status_label.config(text=status)
        self.root.update_idletasks()

    def start_processing(self):
        """Bắt đầu xử lý video với các tuỳ chọn hiện tại"""
        try:
            # Lấy thông tin từ GUI
            input_video_path = self.input_video_path.get()
            output_video_path = self.output_video_path.get()
            source_language = self.source_language.get()
            target_language = self.target_language.get()
            video_overlay_settings = self.video_overlay_settings
            words_per_line = self.words_per_line.get()

            # Kiểm tra đầu vào
            if not input_video_path or not output_video_path:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng chọn file video đầu vào và vị trí lưu file đầu ra.")
                return

            # --- BỔ SUNG LOGIC TỰ ĐỘNG ÁP DỤNG CHROMA CUSTOM ---
            if not video_overlay_settings or not video_overlay_settings.get('enabled', False):
                # Có thể chỉ định sẵn một video overlay mặc định nếu muốn, hoặc để None
                self.video_overlay_settings = {
                    'enabled': True,
                    'video_path': None,       # Nếu muốn mặc định là None, hoặc chỉ định path overlay video
                    'start_time': 2,
                    'duration': 8,
                    'position': 'top-right',
                    'size_percent': 25,
                    'chroma_key': True,
                    'chroma_color': 'green',
                    'chroma_sensitivity': 'custom'
                }
                video_overlay_settings = self.video_overlay_settings
            # --- END ---

            self.status_label.config(text="⏳ Đang xử lý... Vui lòng chờ.")
            self.progress_var.set(0)
            self.progress_bar.start()

            # Thực hiện xử lý trong thread riêng để không block GUI
            def worker():
                try:
                    self.log_message("🚀 Bắt đầu xử lý video tự động...")
                    editor = AutoVideoEditor()  # import ở đầu file: from main import AutoVideoEditor
                    editor.process_video(
                        input_video_path=input_video_path,
                        output_video_path=output_video_path,
                        source_language=source_language,
                        target_language=target_language,
                        video_overlay_settings=video_overlay_settings,
                        words_per_line=words_per_line
                    )
                    self.status_label.config(text="✅ Hoàn thành!")
                    self.log_message("✅ Xử lý xong! File kết quả đã lưu.")
                except Exception as e:
                    self.status_label.config(text="❌ Lỗi xử lý!")
                    self.log_message(f"❌ Lỗi: {e}")
                finally:
                    self.progress_bar.stop()
                    self.progress_var.set(0)

            threading.Thread(target=worker, daemon=True).start()

        except Exception as e:
            self.status_label.config(text="❌ Lỗi xử lý!")
            self.log_message(f"❌ Lỗi: {e}")


def main():
    root = tk.Tk()
    app = VideoEditorGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()

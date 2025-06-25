#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ứng dụng Chỉnh sửa Video Tự động với Phụ đề và Tỉ lệ 9:16
Tác giả: Video Editor Bot
Mô tả: Tự động tạo phụ đề, dịch sang tiếng Anh và chuyển đổi video sang tỉ lệ 9:16
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
import argparse
from video_processor import VideoProcessor
from subtitle_generator import SubtitleGenerator
from translator import Translator
from aspect_ratio_converter import AspectRatioConverter

class AutoVideoEditor:
    def __init__(self):
        self.video_processor = VideoProcessor()
        self.subtitle_generator = SubtitleGenerator()
        self.translator = Translator()
        self.aspect_converter = AspectRatioConverter()
        
    def process_video(self, input_video_path, output_video_path, source_language='vi', target_language='en', img_folder=None, overlay_times=None, video_overlay_settings=None, custom_timeline=False, words_per_line=7):
        """
        Xử lý video chính theo các bước:
        1. Trích xuất audio
        2. Tạo phụ đề từ audio
        3. Dịch phụ đề sang tiếng Anh
        4. Ghép phụ đề vào video
        5. Chuyển đổi tỉ lệ khung hình thành 9:16
        
        Args:
            custom_timeline (bool): Sử dụng timeline tùy chỉnh cho 3 ảnh (1.png, 2.png, 3.png)
        """
        print("🎬 Bắt đầu xử lý video...")
        
        try:
            # Tạo thư mục tạm
            temp_dir = tempfile.mkdtemp()
            print(f"📁 Thư mục tạm: {temp_dir}")
            
            # Bước 1: Trích xuất audio từ video
            print("🎵 Bước 1: Trích xuất audio từ video...")
            audio_path = os.path.join(temp_dir, "extracted_audio.wav")
            self.video_processor.extract_audio(input_video_path, audio_path)
            
            # Bước 2: Tạo phụ đề từ audio
            print("📝 Bước 2: Tạo phụ đề từ audio...")
            original_subtitle_path = os.path.join(temp_dir, "original_subtitle.srt")
            self.subtitle_generator.generate_subtitle(
                audio_path, 
                original_subtitle_path, 
                language=source_language,
                words_per_line=words_per_line
            )
            
            # Bước 3: Dịch phụ đề sang ngôn ngữ đích
            print(f"🌐 Bước 3: Dịch phụ đề từ {source_language} sang {target_language}...")
            translated_subtitle_path = os.path.join(temp_dir, f"{target_language}_subtitle.srt")
            self.translator.translate_subtitle(
                original_subtitle_path,
                translated_subtitle_path,
                source_lang=source_language,
                target_lang=target_language
            )
            
            # Bước 4: Ghép phụ đề và overlay vào video
            print("🎞️ Bước 4: Ghép phụ đề và overlay vào video...")
            video_with_subtitle_path = os.path.join(temp_dir, "video_with_subtitle.mp4")
            
            # Xử lý video overlay nếu có
            if video_overlay_settings and video_overlay_settings.get('enabled', False):
                print("🎬 Đang xử lý video overlay với chroma key...")
                
                # DEBUG: In ra toàn bộ video_overlay_settings
                print(f"DEBUG MAIN: video_overlay_settings={video_overlay_settings}")
                
                try:
                    temp_video_overlay_path = os.path.join(temp_dir, "temp_with_video_overlay.mp4")
                    
                    # Kiểm tra nếu có multiple overlays
                    if 'multiple_overlays' in video_overlay_settings:
                        # Xử lý multiple overlays
                        overlays = video_overlay_settings['multiple_overlays']
                        print(f"🎬 Xử lý {len(overlays)} video overlay...")
                        self._process_multiple_video_overlays(
                            input_video_path, 
                            temp_video_overlay_path, 
                            overlays, 
                            temp_dir
                        )
                    else:
                        # Xử lý single overlay (từ GUI)
                        from video_overlay import add_video_overlay_with_chroma
                        settings = video_overlay_settings
                        
                        # DEBUG: In ra settings được truyền vào
                        print(f"DEBUG MAIN: Single overlay settings={settings}")
                        
                        # Lấy chroma parameters từ GUI settings
                        chroma_color = settings.get('chroma_color', 'green')
                        chroma_similarity = settings.get('chroma_similarity', 0.2)
                        chroma_blend = settings.get('chroma_blend', 0.15)
                        
                        # DEBUG: In ra chroma values
                        print(f"DEBUG MAIN: chroma_color={chroma_color}, similarity={chroma_similarity}, blend={chroma_blend}")
                        
                        # Convert color name to hex
                        if not str(chroma_color).startswith('0x'):
                            chroma_color = self._get_chroma_color(chroma_color)
                        
                        add_video_overlay_with_chroma(
                            main_video_path=input_video_path,
                            overlay_video_path=settings['video_path'],
                            output_path=temp_video_overlay_path,
                            start_time=settings.get('start_time', 0),
                            duration=settings.get('duration'),
                            position=settings.get('position', 'top-right'),
                            size_percent=settings.get('size_percent', 25),
                            chroma_key=settings.get('chroma_key', True),
                            chroma_color=chroma_color,
                            chroma_similarity=chroma_similarity,
                            chroma_blend=chroma_blend,
                            auto_hide=settings.get('auto_hide', True),
                            custom_x=settings.get('custom_x'),
                            custom_y=settings.get('custom_y'),
                            custom_width=settings.get('custom_width'),
                            custom_height=settings.get('custom_height'),
                            keep_aspect=settings.get('keep_aspect', True)
                        )
                    
                    # Sau đó thêm phụ đề và image overlay lên video đã có video overlay
                    if img_folder and overlay_times and os.path.exists(img_folder):
                        self.video_processor.add_subtitle_to_video(
                            temp_video_overlay_path,
                            translated_subtitle_path,
                            video_with_subtitle_path,
                            img_folder,
                            overlay_times
                        )
                    else:
                        # Chỉ thêm phụ đề
                        self.video_processor.add_subtitle_to_video(
                            temp_video_overlay_path,
                            translated_subtitle_path,
                            video_with_subtitle_path
                        )
                    
                except Exception as e:
                    print(f"⚠️ Lỗi video overlay: {e}, sử dụng phương pháp cũ...")
                    # Fallback về phương pháp cũ
                    if img_folder and overlay_times and os.path.exists(img_folder):
                        self.video_processor.add_subtitle_to_video(
                            input_video_path,
                            translated_subtitle_path,
                            video_with_subtitle_path,
                            img_folder,
                            overlay_times
                        )
                    else:
                        self.video_processor.add_subtitle_to_video(
                            input_video_path,
                            translated_subtitle_path,
                            video_with_subtitle_path
                        )
            
            # Xử lý image overlay và phụ đề (nếu không có video overlay)
            elif img_folder and os.path.exists(img_folder):
                # Kiểm tra nếu sử dụng custom timeline
                if custom_timeline:
                    print("🎯 Sử dụng custom timeline cho 3 ảnh...")
                    try:
                        from video_overlay import add_images_with_custom_timeline
                        success = add_images_with_custom_timeline(
                            input_video_path,
                            translated_subtitle_path,
                            video_with_subtitle_path,
                            img_folder
                        )
                        if not success:
                            print("⚠️ Custom timeline thất bại, sử dụng phương pháp cũ...")
                            self.video_processor.add_subtitle_to_video(
                                input_video_path,
                                translated_subtitle_path,
                                video_with_subtitle_path
                            )
                    except ImportError:
                        print("⚠️ Module video_overlay không có, sử dụng phương pháp cũ...")
                        self.video_processor.add_subtitle_to_video(
                            input_video_path,
                            translated_subtitle_path,
                            video_with_subtitle_path
                        )
                elif overlay_times:
                    # Sử dụng video overlay module với multiple overlays
                    try:
                        from video_overlay import add_multiple_overlays
                        success = add_multiple_overlays(
                            input_video_path,
                            translated_subtitle_path,
                            video_with_subtitle_path,
                            img_folder,
                            overlay_times
                        )
                        if not success:
                            print("⚠️ Overlay thất bại, sử dụng phương pháp cũ...")
                            self.video_processor.add_subtitle_to_video(
                                input_video_path,
                                translated_subtitle_path,
                                video_with_subtitle_path,
                                img_folder,
                                overlay_times
                            )
                    except ImportError:
                        print("⚠️ Module video_overlay không có, sử dụng phương pháp cũ...")
                        self.video_processor.add_subtitle_to_video(
                            input_video_path,
                            translated_subtitle_path,
                            video_with_subtitle_path,
                            img_folder,
                            overlay_times
                        )
                else:
                    # Chỉ ghép phụ đề với thư mục ảnh (không có overlay times)
                    self.video_processor.add_subtitle_to_video(
                        input_video_path,
                        translated_subtitle_path,
                        video_with_subtitle_path
                    )
            else:
                # Chỉ ghép phụ đề
                self.video_processor.add_subtitle_to_video(
                    input_video_path,
                    translated_subtitle_path,
                    video_with_subtitle_path
                )
            
            # Bước 5: Chuyển đổi tỉ lệ khung hình thành 9:16
            print("📱 Bước 5: Chuyển đổi tỉ lệ khung hình thành 9:16...")
            self.aspect_converter.convert_to_9_16(
                video_with_subtitle_path,
                output_video_path
            )
            
            print(f"✅ Hoàn thành! Video đã được lưu tại: {output_video_path}")
            
            # Dọn dẹp thư mục tạm
            import shutil
            shutil.rmtree(temp_dir)
            print("🧹 Đã dọn dẹp thư mục tạm")
            
        except Exception as e:
            print(f"❌ Lỗi trong quá trình xử lý: {str(e)}")
            raise
    def _process_multiple_video_overlays(self, input_video_path, output_path, settings_list, temp_dir):
        """Xử lý nhiều video overlay"""
        current_video = input_video_path
        
        for i, settings in enumerate(settings_list):
            temp_output = os.path.join(temp_dir, f"temp_overlay_{i}.mp4")
            
            print(f"Áp dụng video overlay {i+1}/{len(settings_list)}...")
            
            from video_overlay import add_video_overlay_with_chroma
            
            # Xử lý chroma parameters từ GUI
            chroma_color = settings.get('chroma_color', 'green')
            chroma_similarity = settings.get('chroma_similarity', 0.2)
            chroma_blend = settings.get('chroma_blend', 0.15)
            
            print(f"Processing chroma: color={chroma_color}, similarity={chroma_similarity}, blend={chroma_blend}")
            
            # Convert color name to hex nếu cần
            if not str(chroma_color).startswith('0x'):
                chroma_color = self._get_chroma_color(chroma_color)
            
            # Đảm bảo similarity và blend là số
            try:
                if isinstance(chroma_similarity, str):
                    chroma_similarity = float(chroma_similarity)
                if isinstance(chroma_blend, str):
                    chroma_blend = float(chroma_blend)
            except (ValueError, TypeError):
                print(f"Invalid chroma values, using defaults")
                chroma_similarity = 0.2
                chroma_blend = 0.15
            
            add_video_overlay_with_chroma(
                main_video_path=current_video,
                overlay_video_path=settings['video_path'],
                output_path=temp_output,
                start_time=settings.get('start_time', 0),
                duration=settings.get('duration'),
                position=settings.get('position', 'top-right'),
                size_percent=settings.get('size_percent', 25),
                chroma_key=settings.get('chroma_key', True),
                color=chroma_color,  # Sử dụng alias từ test_chroma_key.py
                similarity=chroma_similarity,  # Sử dụng alias từ test_chroma_key.py
                auto_hide=settings.get('auto_hide', True),
                custom_x=settings.get('custom_x'),
                custom_y=settings.get('custom_y'),
                custom_width=settings.get('custom_width'),
                custom_height=settings.get('custom_height'),
                keep_aspect=settings.get('keep_aspect', True)
            )
            
            current_video = temp_output
        
        # Copy kết quả cuối cùng
        import shutil
        shutil.copy2(current_video, output_path)
        return True

    def _get_chroma_color(self, color_name):
        """Chuyển đổi tên màu thành mã hex"""
        colors = {
            "green": "0x00ff00",
            "blue": "0x0000ff", 
            "cyan": "0x00ffff",
            "red": "0xff0000",
            "magenta": "0xff00ff",
            "yellow": "0xffff00",
            "black": "0x000000",
        }
        return colors.get(color_name.lower(), "0x00ff00")
    
    def _get_chroma_sensitivity(self, preset_name):
        """Chuyển đổi preset độ nhạy thành giá trị"""
        presets = {
            "loose": (0.3, 0.3),
            "normal": (0.1, 0.1),
            "custom": (0.2, 0.2), #Green
            "strict": (0.05, 0.05),
            "very_strict": (0.01, 0.01), #Black
            "ultra_strict": (0.005, 0.005)
        }
        return presets.get(preset_name.lower(), (0.01, 0.01))

def main():
    parser = argparse.ArgumentParser(
        description="Ứng dụng Chỉnh sửa Video Tự động với Phụ đề và Tỉ lệ 9:16"
    )
    parser.add_argument(
        "input_video_path", 
        help="Đường dẫn đến file video đầu vào"
    )
    parser.add_argument(
        "output_video_path", 
        help="Đường dẫn để lưu file video đầu ra"
    )
    parser.add_argument(
        "--source-lang", 
        default="vi", 
        help="Ngôn ngữ gốc của video (mặc định: vi - tiếng Việt)"
    )
    parser.add_argument(
        "--target-lang", 
        default="en", 
        help="Ngôn ngữ đích cho phụ đề (mặc định: en - English)"
    )
    
    args = parser.parse_args()
    
    # Kiểm tra file đầu vào có tồn tại
    if not os.path.exists(args.input_video_path):
        print(f"❌ File video đầu vào không tồn tại: {args.input_video_path}")
        sys.exit(1)
    
    # Tạo thư mục đầu ra nếu chưa tồn tại
    output_dir = os.path.dirname(args.output_video_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Khởi tạo và chạy ứng dụng
    editor = AutoVideoEditor()
    editor.process_video(
        input_video_path=args.input_video_path, 
        output_video_path=args.output_video_path, 
        source_language=args.source_lang,
        target_language=args.target_lang
    )

if __name__ == "__main__":
    main()

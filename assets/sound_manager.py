# File: sound_manager.py
import os
import sys

import pygame


def resource_path(relative_path):
    """Đường dẫn tuyệt đối tới tài nguyên (chạy được cả khi đóng gói bằng PyInstaller)."""
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)


class SoundManager:
    SOUND_NAMES = ("correct", "wrong", "click")

    def __init__(self):
        self.sounds = {}  

        # [TRỌNG TÂM 1] Khởi tạo bộ phát âm thanh của pygame (chỉ cần 1 lần)
        try:
            pygame.mixer.init()
        except pygame.error as e:
            print(f"Không khởi tạo được âm thanh: {e}")
            return

        # [TRỌNG TÂM 2] Nạp sẵn tất cả âm thanh vào RAM ngay từ đầu
        for name in self.SOUND_NAMES:
            path = resource_path(f"duanbrainquest/assets/sounds/{name}.mp3")
            if os.path.exists(path):
                self.sounds[name] = pygame.mixer.Sound(path)
            else:
                print(f"CẢNH BÁO: Không tìm thấy file âm thanh: {path}")

    def play(self, name):
        """Phát âm thanh theo tên: 'correct', 'wrong' hoặc 'click'."""
        sound = self.sounds.get(name)
        if sound:
            # [TRỌNG TÂM 3] play() chạy nền, không chặn giao diện -> không cần thread
            sound.play()

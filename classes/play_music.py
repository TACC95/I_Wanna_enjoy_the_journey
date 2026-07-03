import random
import pygame

class PlayMusic:
    def __init__(self):
        # 场景音乐映射：{ room_id: [音乐文件路径列表] }
        self.room_music = {}
        self.current_room = None
        self.playlist = []
        self.current_track_index = 0
        self.volume = 0.5
        pygame.mixer.music.set_volume(self.volume)

    def load_music_mapping(self, mapping_dict):
        """导入音乐配置"""
        self.room_music = mapping_dict

    def play_for_room(self, room_id):
        """根据房间ID播放对应音乐列表"""
        if room_id == self.current_room:
            return  # 同一房间不重新开始播放

        self.current_room = room_id
        self.playlist = self.room_music.get(room_id, [])
        self.current_track_index = 0
        if self.playlist:
            self._start_track(self.current_track_index)

    def _start_track(self, index):
        """播放列表中指定索引的音乐"""
        if 0 <= index < len(self.playlist):
            pygame.mixer.music.load(self.playlist[index])
            pygame.mixer.music.play()
            # 设置播放结束事件，以便自动切换下一首
            pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)

    def update(self):
        """在主循环中调用，处理音乐结束自动切换"""
        # 检测音乐结束事件
        for event in pygame.event.get(eventtype=pygame.USEREVENT + 1):
            self.current_track_index += 1
            if self.current_track_index < len(self.playlist):
                self._start_track(self.current_track_index)
            else:
                # 循环播放整个列表
                self.current_track_index = 0
                self._start_track(0)

    def stop(self):
        pygame.mixer.music.stop()

    def set_volume(self, vol):
        self.volume = vol
        pygame.mixer.music.set_volume(vol)
# sound_manager.py
import pygame
import os


class SoundManager:

    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        pygame.mixer.set_num_channels(16)

        self.sounds        = {}   # SFX name -> Sound
        self.music_tracks  = {}   # music name -> Sound
        self.enabled       = True
        self.master_volume = 0.8
        self.music_volume  = 0.4

        # Reserve channel 0 and 1 exclusively for music
        # so SFX never accidentally cut music off
        self._music_channel = pygame.mixer.Channel(0)
        self._fade_channel  = pygame.mixer.Channel(1)

        self.current_music  = None

        self.footstep_timer    = 0
        self.footstep_interval = 18

        self._load_sounds()
        self._load_music()

    # ------------------------------------------------------------------

    def _load_sounds(self):
        sound_files = {
            "win":          "sounds/win.wav",
            "lose":         "sounds/lose.wav",
            "alert":        "sounds/alert.wav",
            "footstep":     "sounds/footstep.wav",
            "day_complete": "sounds/day_complete.wav",
            "spin":         "sounds/spin.wav",
            "buy":          "sounds/buy.wav",
            "game_over":    "sounds/game_over.wav",
            "exit_zone":    "sounds/exit_zone.wav",
            "card_deal":    "sounds/card_deal.wav",
            "chip":         "sounds/chip.wav",
        }
        for name, path in sound_files.items():
            if os.path.exists(path):
                try:
                    self.sounds[name] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"SoundManager: could not load {path} — {e}")
                    self.sounds[name] = None
            else:
                self.sounds[name] = None

    def _load_music(self):
        """
        Pre-load all music files at startup as Sound objects.
        This is the key fix — Sound.play() is non-blocking unlike
        mixer.music.load() which reads from disk and freezes the game.
        """
        music_files = {
            "casino":  "sounds/music_casino.ogg",
            "chase":   "sounds/music_chase.ogg",
            "victory": "sounds/music_victory.ogg",
        }
        for name, path in music_files.items():
            if os.path.exists(path):
                try:
                    self.music_tracks[name] = pygame.mixer.Sound(path)
                except Exception as e:
                    print(f"SoundManager: could not load music {path} — {e}")
                    self.music_tracks[name] = None
            else:
                self.music_tracks[name] = None

    # ------------------------------------------------------------------

    def play(self, name, volume=1.0):
        """Play SFX — uses sfx_volume only, never touches music_volume."""
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound:
            sound.set_volume(volume * self.master_volume)
            pygame.mixer.find_channel(True).play(sound)

    # ------------------------------------------------------------------

    def switch_music(self, name):
        """
        Switch to a new music track instantly — no blocking load().
        Uses fadeout on the current channel and fadein on the new one.
        Since Sound objects are pre-loaded, this is completely non-blocking.
        """
        if self.current_music == name:
            return

        track = self.music_tracks.get(name)
        if not track:
            self.current_music = name
            return

        vol = self.music_volume if self.enabled else 0.0
        track.set_volume(vol)

        # Fade out whatever is currently playing
        self._music_channel.fadeout(600)

        # Play new track on music channel, looping forever (-1)
        self._music_channel.play(track, loops=-1, fade_ms=600)

        self.current_music = name

    def stop_music(self, fade_ms=800):
        self._music_channel.fadeout(fade_ms)
        self.current_music = None

    def update_music_volume(self):
        """Sync music volume — uses music_volume only, never touches master_volume."""
        vol = self.music_volume if self.enabled else 0.0
        if self.current_music and self.music_tracks.get(self.current_music):
            self.music_tracks[self.current_music].set_volume(vol)
        if not self.enabled:
            self._music_channel.stop()

    # ------------------------------------------------------------------

    def update_footstep(self, player_moving):
        if not player_moving:
            self.footstep_timer = 0
            return
        self.footstep_timer += 1
        if self.footstep_timer >= self.footstep_interval:
            self.play("footstep", volume=0.3)
            self.footstep_timer = 0

    def toggle(self):
        self.enabled = not self.enabled
        self.update_music_volume()
        return self.enabled
"""Short synthesized effects for the Windows desktop game."""

import math
import random
import struct
import tempfile
import wave
from pathlib import Path

try:
    import winsound
except ImportError:
    winsound = None


SAMPLE_RATE = 22_050

# Each voice specifies a delay, duration, two pitch endpoints and a peak level.
EFFECTS = {
    "start": ((0.00, 0.15, 329.63, 329.63, 0.13),
              (0.09, 0.15, 440.00, 440.00, 0.13),
              (0.17, 0.19, 659.25, 659.25, 0.14)),
    "crystal": ((0.00, 0.11, 784.00, 784.00, 0.15),
                (0.05, 0.14, 1174.66, 1174.66, 0.13)),
    "hit": ((0.00, 0.19, 170.00, 51.00, 0.21),
            (0.02, 0.15, 264.00, 68.00, 0.11)),
    "won": ((0.00, 0.18, 440.00, 440.00, 0.14),
            (0.10, 0.18, 554.37, 554.37, 0.14),
            (0.20, 0.21, 659.25, 659.25, 0.16),
            (0.30, 0.32, 880.00, 880.00, 0.17)),
    "lost": ((0.00, 0.20, 349.23, 293.66, 0.15),
             (0.13, 0.18, 261.63, 220.00, 0.15),
             (0.25, 0.26, 174.61, 130.81, 0.16)),
    "pause": ((0.00, 0.12, 580.00, 410.00, 0.10),),
}


def _write_effect(path, voices, *, noisy=False):
    length = max(round((delay + duration) * SAMPLE_RATE)
                 for delay, duration, *_ in voices)
    samples = [0.0] * length
    noise = random.Random(14)
    previous_noise = 0.0

    for delay, duration, start_pitch, end_pitch, volume in voices:
        offset = round(delay * SAMPLE_RATE)
        count = min(round(duration * SAMPLE_RATE), length - offset)
        phase = 0.0
        for index in range(count):
            progress = index / (count - 1)
            pitch = start_pitch + (end_pitch - start_pitch) * progress
            phase += math.tau * pitch / SAMPLE_RATE
            attack = min(index / (0.006 * SAMPLE_RATE), 1.0)
            envelope = attack * (1.0 - progress) ** 2
            tone = 0.83 * math.sin(phase) + 0.17 * math.sin(2.0 * phase)
            if noisy:
                previous_noise = 0.70 * previous_noise + 0.30 * noise.uniform(-1, 1)
                tone += 0.40 * previous_noise
            samples[offset + index] += volume * envelope * tone

    pcm = [round(max(-1.0, min(1.0, sample)) * 32_767) for sample in samples]
    with wave.open(str(path), "wb") as sound:
        sound.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
        sound.writeframes(struct.pack(f"<{length}h", *pcm))


class SoundEffects:
    def __init__(self):
        self._directory = None
        self._files = {}
        self._playing = False
        if winsound is None:
            return

        try:
            self._directory = tempfile.TemporaryDirectory(prefix="starflight-audio-")
            for event, voices in EFFECTS.items():
                path = Path(self._directory.name) / f"{event}.wav"
                _write_effect(path, voices, noisy=event == "hit")
                self._files[event] = str(path)
        except OSError:
            self.close()

    @property
    def available(self):
        return self._directory is not None

    def play(self, event):
        path = self._files.get(event)
        if path is None:
            return
        try:
            flags = winsound.SND_ASYNC | winsound.SND_FILENAME | winsound.SND_NODEFAULT
            winsound.PlaySound(path, flags)
            self._playing = True
        except RuntimeError:
            self.close()

    def stop(self):
        if self._playing:
            self._playing = False
            try:
                winsound.PlaySound(None, 0)
            except RuntimeError:
                pass

    def close(self):
        self.stop()
        self._files.clear()
        if self._directory is not None:
            directory = self._directory
            self._directory = None
            try:
                directory.cleanup()
            except OSError:
                pass

import asyncio
import sounddevice as sd
import numpy as np
import requests
import time
import pygame
from datetime import datetime
from scipy.io.wavfile import write
from shazamio import Shazam
from io import BytesIO
from PIL import Image

# === CONFIG ===
RECORD_SECONDS = 12
SAMPLE_RATE = 44100
CHANNELS = 1
SNIPPET_FILE = "snippet.wav"
CHECK_INTERVAL = 30

SCREEN_WIDTH = 1280  # Updated for 16:9 resolution
SCREEN_HEIGHT = 720
FONT_SIZE = 24
LINE_SPACING = 8

# === INIT PYGAME DISPLAY ===
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Vinyl Vision")
font = pygame.font.SysFont("Arial", FONT_SIZE)
clock = pygame.time.Clock()

def draw_text_block(text, color=(255, 255, 255), y_offset=20, max_width=SCREEN_WIDTH - 40):
    lines = []
    words = text.split()
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)

    for i, line in enumerate(lines):
        rendered = font.render(line, True, color)
        rect = rendered.get_rect(midtop=(SCREEN_WIDTH // 2, y_offset + i * (FONT_SIZE + LINE_SPACING)))
        screen.blit(rendered, rect)

def draw_image_with_text(img_surface, main_text="", sub_text=""):
    screen.fill((0, 0, 0))
    if img_surface:
        img_rect = img_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        screen.blit(img_surface, img_rect)
    if main_text:
        draw_text_block(main_text, y_offset=20)
    if sub_text:
        draw_text_block(sub_text, y_offset=SCREEN_HEIGHT - 100)
    pygame.display.flip()

def load_album_image_from_url(url):
    try:
        img_data = requests.get(url).content
        image = Image.open(BytesIO(img_data)).convert("RGB")
        image = image.resize((600, 600))
        return pygame.image.fromstring(image.tobytes(), image.size, image.mode)
    except Exception as e:
        print(f"Warning: Error loading image: {e}")
        return None

# === ASYNC SHAZAM WRAPPER ===
async def identify_song(file_path):
    shazam = Shazam()
    try:
        out = await shazam.recognize(file_path)
        if out.get("track"):
            track = out['track']
            title = track.get('title', 'Unknown')
            artist = track.get('subtitle', '')
            image_url = track.get('images', {}).get('coverart', '')
            return f"{title} - {artist}", image_url
    except Exception as e:
        print(f"Error: Shazam error: {e}")
    return None, None

# === MAIN LOOP ===
current_img = None
current_text = "Waiting for audio..."
status_text = "Starting..."
draw_image_with_text(current_img, current_text, status_text)

while True:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            exit()

    match_found = False
    while not match_found:
        try:
            for remaining in range(RECORD_SECONDS, 0, -1):
                countdown_text = f"Listening... {remaining}s remaining"
                draw_image_with_text(current_img, current_text, countdown_text)
                time.sleep(1)

            print("Recording...")
            recording = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16')
            sd.wait()
            sd.stop()
            sd.sleep(100)
            write(SNIPPET_FILE, SAMPLE_RATE, recording)

            # === DEBUGGING: Check if audio was detected ===
            amplitude = np.abs(recording).mean()
            audio_status = "Audio signal detected" if amplitude > 100 else "Low or no audio signal"
            print(f"Average amplitude: {amplitude:.2f} — {audio_status}")
            draw_image_with_text(current_img, current_text, audio_status)
            time.sleep(1)

            print("Sending to Shazam...")
            draw_image_with_text(current_img, current_text, "Identifying track...")
            title, image_url = asyncio.run(identify_song(SNIPPET_FILE))

            if title and image_url:
                new_img = load_album_image_from_url(image_url)
                if new_img:
                    current_img = new_img
                    current_text = title
                    print(f"Found: {title}")
                    match_found = True
            else:
                print("No match found. Retrying immediately...")
                draw_image_with_text(current_img, current_text, "No match. Trying again...")
                time.sleep(1)
        except Exception as e:
            print(f"Audio error: {e}")
            draw_image_with_text(current_img, current_text, f"Audio error. Retrying...")
            time.sleep(2)

    for remaining in range(CHECK_INTERVAL, 0, -1):
        status_text = f"Checking for new track in {remaining}s"
        draw_image_with_text(current_img, current_text, status_text)
        time.sleep(1)

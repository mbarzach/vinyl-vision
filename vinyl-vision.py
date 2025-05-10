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

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FONT_SIZE = 24
LINE_SPACING = 8
TEXT_SECTION_WIDTH = SCREEN_WIDTH // 3
IMAGE_SECTION_WIDTH = SCREEN_WIDTH - TEXT_SECTION_WIDTH

# === INIT PYGAME DISPLAY ===
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Vinyl Vision")
font = pygame.font.SysFont("Arial", FONT_SIZE)
clock = pygame.time.Clock()

def draw_text_info(metadata: dict, img_surface=None, signal_detected=False):
    screen.fill((0, 0, 0))

    # Draw album art in left 2/3
    if img_surface:
        img_rect = img_surface.get_rect(center=(IMAGE_SECTION_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(img_surface, img_rect)

    # Draw metadata in right 1/3, left-aligned and vertically centered
    text_lines = [f"{label}: {value}" for label, value in metadata.items()]
    total_text_height = len(text_lines) * (FONT_SIZE + LINE_SPACING)
    y_start = (SCREEN_HEIGHT - total_text_height) // 2
    x_left = IMAGE_SECTION_WIDTH - 10  # Adjusted to move text closer to image

    for i, line in enumerate(text_lines):
        rendered = font.render(line, True, (255, 255, 255))
        rect = rendered.get_rect(topleft=(x_left, y_start + i * (FONT_SIZE + LINE_SPACING)))
        screen.blit(rendered, rect)

    # Draw audio signal indicator in top right
    radius = 10
    x_circle = SCREEN_WIDTH - 20
    y_circle = 20
    if signal_detected:
        pygame.draw.circle(screen, (0, 255, 0), (x_circle, y_circle), radius)
    else:
        pygame.draw.circle(screen, (255, 255, 255), (x_circle, y_circle), radius, 2)

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
            album = next((m.get('text') for m in track.get('sections', [{}])[0].get('metadata', [])
                         if m.get('title', '').lower() == 'album'), 'Unknown')
            image_url = track.get('images', {}).get('coverart', '')
            return {
                "Title": title,
                "Artist": artist,
                "Album": album
            }, image_url
    except Exception as e:
        print(f"Error: Shazam error: {e}")
    return None, None

# === MAIN LOOP ===
current_img = None
current_metadata = {"Status": "Waiting for audio..."}
signal_detected = False

draw_text_info(current_metadata, current_img, signal_detected)

while True:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            exit()

    match_found = False
    while not match_found:
        try:
            for remaining in range(RECORD_SECONDS, 0, -1):
                draw_text_info(current_metadata, current_img, signal_detected)
                time.sleep(1)

            print("Recording...")
            recording = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                               channels=CHANNELS, dtype='int16')
            sd.wait()
            sd.stop()
            sd.sleep(100)
            write(SNIPPET_FILE, SAMPLE_RATE, recording)

            amplitude = np.abs(recording).mean()
            signal_detected = amplitude > 100
            print(f"Average amplitude: {amplitude:.2f} — {'Detected' if signal_detected else 'Not detected'}")

            current_metadata["Status"] = "Identifying track..."
            draw_text_info(current_metadata, current_img, signal_detected)
            time.sleep(1)

            print("Sending to Shazam...")
            metadata, image_url = asyncio.run(identify_song(SNIPPET_FILE))

            if metadata and image_url:
                new_img = load_album_image_from_url(image_url)
                if new_img:
                    current_img = new_img
                    current_metadata = metadata
                    current_metadata["Status"] = "Match found."
                    print(f"Found: {metadata['Title']} - {metadata['Artist']}")
                    match_found = True
                    draw_text_info(current_metadata, current_img, signal_detected)
            else:
                print("No match found. Retrying immediately...")
                current_metadata = {"Status": "No match. Trying again..."}
                draw_text_info(current_metadata, current_img, signal_detected)
                time.sleep(1)

        except Exception as e:
            print(f"Audio error: {e}")
            current_metadata = {"Status": "Audio error. Retrying..."}
            draw_text_info(current_metadata, current_img, False)
            time.sleep(2)

    for remaining in range(CHECK_INTERVAL, 0, -1):
        current_metadata["Status"] = f"Checking for new track in {remaining}s"
        draw_text_info(current_metadata, current_img, signal_detected)
        time.sleep(1)

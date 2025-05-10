# Vinyl Vision

**Vinyl Vision** is a Raspberry Pi-powered album art display tool designed to complement analog listening setups. It listens to a short audio sample, identifies the track using Shazam, and shows the album artwork on an HDMI display. The visual component is kept separate from audio output to preserve high-quality audio paths (e.g. direct RCA from a turntable).

---

##

This project was built to:

* Identify vinyl or analog audio playing in real time
* Display the album art and song title visually
* Keep all audio routing external to avoid degrading sound quality
* Integrate a turntable with a home sound system connected through a TV

This was designed for setups where a Sonos soundbar takes HDMI ARC from the TV. By routing everything through the TV, the turntable can connect through analog inputs and audio stays untouched while video from the Pi displays album information.

---

## Features

* Uses `sounddevice` to capture audio from a USB input
* Sends audio samples to the Shazam API via `shazamio`. Sample length is an input variable in seconds. 10–15 seconds is recommended for reliable matching
* Displays track title and album cover using `pygame`
* Fullscreen 16:9 output (1280×720) for HDMI TVs or monitors
* Displays debug info onscreen: whether an audio signal is detected, and when it’s listening, searching, or waiting

---

## Hardware Setup

The Raspberry Pi is used only for identifying and displaying album artwork. Audio is kept separate to avoid affecting sound quality.

In a typical setup, the record player's RCA output is split. One path goes to a USB audio interface for identification. The other goes directly to the TV or AV receiver. The Pi outputs video only to HDMI, and the display and sound are combined at the TV input. For example, this can be used with a surround sound system where the TV routes audio to a soundbar over HDMI ARC.

## Requirements

* Raspberry Pi (Zero 2 W or better)
* HDMI output (TV or monitor)
* USB audio input card (with RCA or 1/8" line-in)
* Python 3.9+

Python dependencies:

```bash
pip install -r requirements.txt
```

Where `requirements.txt` should include:

```
pygame
numpy
sounddevice
scipy
shazamio
Pillow
requests
```

---

## Basic Usage

From your project directory:

```bash
python3 vinyl-vision.py
```

Or if using a virtual environment:

```bash
source venv/bin/activate
python3 vinyl-vision.py
```

Press `ESC` to exit fullscreen.

---

## Finding Your Audio Devices

This project assumes you're using a USB audio capture device.

To find your device name:

```bash
arecord -l
```

To confirm channel count and format:

```bash
arecord -D hw:1,0 --dump-hw-params
```

Typical result:

```
CHANNELS: 1
FORMAT: S16_LE
RATE: [44100 48000]
```

If you’re using PulseAudio:

```bash
pactl list short sources
```

Look for something like:

```
alsa_input.usb-Your_Device_Name.mono-fallback
```

---

## Autostart on Boot (Optional)

If you want this to run automatically:

1. Create a `vinyl-vision.service` file in `/etc/systemd/system`
2. Use `ExecStart=/path/to/python /path/to/vinyl-vision.py`
3. Enable with:

```bash
sudo systemctl enable vinyl-vision.service
```

---

## What This Doesn’t Do

* It doesn’t handle audio routing or playback
* It doesn’t store history or metadata
* It doesn’t cache artwork

This is intentional — to preserve pure, unaltered audio through a separate signal chain.

---

## Credits

Built by Michael Barzach. Open to contributions.

# MLH Hardware Checklist — Rewind

Walk to the MLH desk with this list. Read items off directly.

## ✅ Confirmed We Have
- [x] 1× Raspberry Pi 4B Kit (SD card, USB-C power, HDMI)
- [x] 1× Logitech USB webcam
- [x] 1× SenseCAP Indicator (we will flash custom LVGL firmware)
- [x] 1× Arduino Base Shield (plugs onto Pi header via Grove HAT — we only use it as Grove breakout)
- [x] Both team laptops (handle all audio — Web Speech API in the browser)

## 🎯 Still Need Tonight

Ask the MLH rep for these. Read the script below:

> "Hi, can I check out — 1 Grove Base HAT for Raspberry Pi if you have one, 2 Grove buttons, 2 Grove LEDs (green preferred), 1 Grove servo motor if available, and 6 Grove cables? We already have the Pi, webcam, SenseCAP, and Arduino shield. Thanks!"

- [ ] **1× Grove Base HAT for Raspberry Pi** *(preferred)*, OR use the Arduino Base Shield we already have (works via I2C to Pi GPIO — slightly less clean but fine)
- [ ] **2× Grove Button** (small PCB, physical push button, white 4-pin socket)
- [ ] **2× Grove LED** (green preferred — RGB if available for polish)
- [ ] **1× Grove Servo Motor** (micro servo, for the cardboard privacy shutter over the camera lens — high-impact demo moment)
- [ ] **6× Grove 4-pin cables** (white cables with latching connectors)
- [ ] **1× Breadboard** (half-size, for any one-off wiring)
- [ ] **A few jumper wires** (male-to-female for GPIO debugging)

## 📦 Enclosure Materials (since no 3D printer)
- [ ] **Clean cardboard** (small Amazon boxes work great — organizers usually have them)
- [ ] **Matte black spray paint** or thick black Sharpie
- [ ] **X-acto knife or box cutter** (for clean camera/screen holes)
- [ ] **Hot glue or double-sided tape**
- [ ] **Velcro strips** (wall mount — non-permanent, roommate-friendly pitch)

**Princeton makerspace option:** If open this weekend, ask about **laser cutter** access for clean acrylic or MDF panels. Bigger visual win if time allows — but cardboard is the default.

## 🚫 Explicitly Skip
- ❌ **Arduino Uno/Nano board** — Pi 4B has 40 GPIO pins. No second microcontroller needed.
- ❌ **USB microphone** — laptop's built-in mic + Web Speech API handles STT in the browser.
- ❌ **Echo Dot / Nest Mini / Google Home** — closed consumer devices, integrating them requires Alexa/Google Skills (10+ hour cloud detour, breaks privacy pitch). If you want the "smart home" demo prop vibe, set one on the table *unplugged* as a visual, mention "future integration" in the pitch.
- ❌ **Raspberry Pi Camera Module (CSI ribbon)** — USB Logitech already in plan, faster setup.

## ⚡ Immediate Sanity Checks After Getting Hardware

1. **Pi boots.** Plug in power + monitor + keyboard (or SSH). Confirm desktop or `$`.
2. **Webcam works.** `lsusb` shows Logitech. `fswebcam test.jpg` produces an image file.
3. **Check if Logitech has a mic.** `arecord -l` — if you see the Logitech listed as an audio capture device, we have free Pi-side voice input as a stretch. If not, laptop mic is the plan anyway.
4. **Grove stack works.** Plug Grove HAT (or Arduino shield) onto Pi. Plug Grove LED into port D5. Python test:
   ```python
   from gpiozero import LED
   led = LED(5)
   led.on()
   ```
   LED lights → wiring is good. ~20 minutes from desk-return to first light.
5. **SenseCAP appears as serial device.** Plug via USB. `ls /dev/tty*` — new device like `/dev/ttyACM0` or `/dev/ttyUSB0`. That's the port for firmware comms.

Once all five pass → the "dumb loop" is proven. Move to Phase 1 coding.

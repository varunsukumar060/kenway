# KENWAY 🤖

> A local, offline, edge-first Linux desktop assistant.
> Rule-based executor first. LLM is the backup brain — not the main one.

**Built for:** Linux Mint 22.3 XFCE | AMD dual-core | 8GB RAM  
**No cloud. No mic. No bloat.**

---

## Philosophy

- **DIRECT MODE (default):** Pure regex/rule-based command parsing. Zero LLM. Instant.
- **LLM MODE (toggle):** Ollama kicks in only when you flip the tray switch. Smart parser, not a chatbot.

KENWAY is your **executor**, not your talking parrot.

---

## Features

- 🔊 Offline voice output (pyttsx3 + espeak-ng)
- 👋 Greets you on boot, says goodbye on shutdown
- 🧠 Dual-brain: rule engine + optional local LLM
- 🖥️ Screen reader (OCR via pytesseract + mss)
- 📂 Sandboxed file read/write
- 🚀 App launcher + system controls
- 🌐 Browser automation (YouTube, Google, etc.)
- 🗖 System tray with LLM toggle button
- ⌨️ Hotkey-triggered floating input bar (Super+Space)

---

## Project Structure

```
kenway/
├── main.py                  # Entry point + event loop
├── config.yaml              # Paths, app allowlist, LLM settings
├── requirements.txt
├── .gitignore
│
├── core/
│   ├── voice.py             # pyttsx3 TTS engine
│   ├── intent_parser.py     # DIRECT MODE: regex rule engine
│   ├── llm_bridge.py        # LLM MODE: Ollama wrapper
│   ├── executor.py          # Routes parsed intent → skill handlers
│   ├── screen.py            # Screenshot + OCR
│   ├── file_manager.py      # Sandboxed file read/write
│   └── hooks.py             # Boot greeting / shutdown goodbye
│
├── skills/
│   ├── browser_skill.py     # YouTube, Google, open URLs
│   ├── app_skill.py         # Launch/close applications
│   ├── system_skill.py      # Volume, brightness, battery, shutdown
│   ├── file_skill.py        # File operations
│   ├── window_skill.py      # wmctrl + xdotool window control
│   └── media_skill.py       # VLC, Spotify
│
└── ui/
    ├── input_bar.py         # Floating PyQt5 input (hotkey: Super+Space)
    └── tray_icon.py         # System tray + LLM toggle
```

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/varunsukumar060/kenway.git
cd kenway

# 2. System dependencies
sudo apt install espeak-ng tesseract-ocr python3-xlib \
                 wmctrl xdotool chromium-chromedriver python3-pip

# 3. Python dependencies
pip install -r requirements.txt

# 4. Ollama (for LLM mode only)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:1.5b

# 5. Run KENWAY
python3 main.py
```

---

## Systemd Auto-start (Boot Greeting)

```bash
mkdir -p ~/.config/systemd/user
cp kenway-greet.service ~/.config/systemd/user/
systemctl --user enable kenway-greet.service
systemctl --user start kenway-greet.service
```

---

## Releases

| Version | Status | Features |
|---------|--------|----------|
| v0.1 | ✅ Done | Voice engine, boot hooks, tray icon, main loop |
| v0.2 | 🔜 | Rule-based intent parser + executor routing |
| v0.3 | 🔜 | Browser skills (YouTube, Google) |
| v0.4 | 🔜 | App launcher + system controls |
| v0.5 | 🔜 | Screen reader + file manager |
| v0.6 | 🔜 | LLM bridge + full dual-brain mode |

---

## License
MIT — built by Varun Sukumar K

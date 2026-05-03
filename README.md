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

### Step 1 — System dependencies
```bash
sudo apt install espeak-ng tesseract-ocr python3-xlib \
                 wmctrl xdotool chromium-chromedriver \
                 python3-pip python3-full python3-venv playerctl
```

### Step 2 — Clone the repo
```bash
git clone https://github.com/varunsukumar060/kenway.git
cd kenway
```

### Step 3 — Create and activate virtual environment
> Linux Mint 22 / Ubuntu 24.04 uses an externally-managed Python.
> Always use a venv — never use --break-system-packages.

```bash
python3 -m venv venv
source venv/bin/activate
```

Your prompt changes to `(venv) varun_sukumar@...` — that means it worked.

### Step 4 — Install Python packages inside venv
```bash
pip install -r requirements.txt
```

### Step 5 — Run KENWAY
```bash
python3 main.py
```

> **Every time you open a new terminal to work on KENWAY, activate the venv first:**
> ```bash
> cd ~/kenway && source venv/bin/activate
> ```

---

## Ollama Setup (LLM Mode only)

Only needed if you want to toggle LLM mode ON. Not required for DIRECT MODE.

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:1.5b
ollama serve &
```

---

## Systemd Auto-start (Boot Greeting)

```bash
nano kenway-greet.service
# Change /home/varun/kenway path if needed

mkdir -p ~/.config/systemd/user
cp kenway-greet.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable kenway-greet.service
systemctl --user start kenway-greet.service
```

---

## Daily Usage

| Action | How |
|--------|-----|
| Open command bar | `Super + Space` |
| Toggle LLM mode | Right-click tray icon → LLM Mode |
| Open input bar via tray | Right-click tray → Open Input Bar |
| Quit KENWAY | Right-click tray → Quit KENWAY |

### Example Commands (Direct Mode — no LLM needed)
```
play gangnam style on youtube
open vs code
volume up
battery status
close spotify
read my screen
search python tutorials on google
open file ~/Documents/notes.txt
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

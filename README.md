# Murmur

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20windows%20%7C%20macos-lightgrey)

**Murmur** is a minimal, modern, and elegant speech-to-text overlay for your desktop, inspired by Whisper for Mac.  
It features a beautiful, glassy DNA animation UI and works as a floating, non-intrusive overlay triggered by a keyboard shortcut.

---

## ✨ Features

- 🧬 Minimalistic, glassy DNA animation overlay
- 🎤 Speech-to-text using OpenAI Whisper (via faster-whisper)
- ⚡️ Super lightweight and fast
- 🖥️ Non-intrusive, frameless, and transparent
- ⌨️ Global hotkey to start/stop listening (`ctrl+alt+space` by default)
- 🪟 Works on Linux, Windows, and MacOS
- 🛠️ Easy to configure and extend

---

## 📸 Preview

> ![Murmur UI Preview](docs/screenshot.gif)  
> _Minimal glassy overlay with DNA animation (cyan)_

---

## 🚀 Installation

```bash
git clone https://github.com/YOUR-USERNAME/murmur.git
cd murmur
pip install -r requirements.txt
```

---

## 🏃 Usage

```bash
python sst.py
```

- Press `ctrl+alt+space` to toggle the overlay and start/stop listening.
- The overlay will float above all windows and transcribe your speech to text.

---

## ⚙️ Configuration

You can change the hotkey, model, and other settings at the top of `sst.py`:

```python
HOTKEY = "ctrl+alt+space"
MODEL_SIZE = "base.en"
```

---

## 🤝 Contributing

Pull requests, issues, and suggestions are welcome!  
Please open an issue or PR to discuss improvements.

---

## 📄 License

MIT License

---

## 🙏 Credits

- [OpenAI Whisper](https://github.com/openai/whisper)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter)
- Inspired by Whisper for Mac

---
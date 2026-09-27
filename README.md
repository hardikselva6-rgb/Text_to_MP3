# 🎧 Commute Audio Study Studio & Telegram Bot

A 100% free, high-clarity Text-to-Speech audio learning tool designed to convert study notes, textbook summaries, and flashcards into high-retention audio for daily bike commutes and walks.

Powered by **Microsoft Edge Neural TTS** (`edge-tts`) and integrated with **Telegram** for seamless mobile and lock-screen listening.

---

## 🌟 Key Features

* 📱 **100% Standalone Mobile Bot:** Send text, notes, or documents via Telegram—no laptop needed on the go.
* 🎙️ **Studio-Grade Neural Voices (Free & Unlimited):**
  * 🇮🇳 **Indian English:** `Neerja` (Crisp Female) & `Prabhat` (Deep Male)
  * 🇬🇧 **British English:** `Sonia` (Calm Female) & `Ryan` (Narrative Male)
  * 🇺🇸 **US English:** `Jenny` (Natural Female) & `Guy` (Baritone Male)
* 🧠 **Active Recall Mode:** Automatically detects questions in your notes and inserts a 3-second reflection silence before revealing the answer.
* 📄 **Multi-Format Document Support:** Upload `.txt`, `.md`, `.pdf`, and `.docx` files directly in Telegram.
* 🚴 **Commute & Cycling Ready:**
  * Background / Lock-screen playback with screen turned off.
  * Control playback (**Play / Pause / Skip**) with Bluetooth earbud buttons.
  * 100% offline playback once received (zero mobile data used during rides).
  * Built-in speed adjustment ($1.0\times, 1.2\times, 1.5\times, 2.0\times$).

---

## 📌 Telegram Bot Commands

| Command | Description |
| :--- | :--- |
| `/start` | Launch bot & view current voice/speed settings |
| `/voice` | Switch between Indian, British, and US English neural voices |
| `/speed` | Adjust speaking rate (`0.9x`, `1.0x`, `1.1x`, `1.2x`, `1.3x`) |
| `/recall` | Toggle Active Recall mode ON/OFF (adds 3s pauses after questions) |
| `/prompt` | Get optimized AI prompt templates for 10-minute commute scripts |

---

## 🚀 Deployment & Local Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt

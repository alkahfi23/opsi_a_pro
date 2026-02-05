# 🚀 OPSI A PRO — Trading Signal Engine

OPSI A PRO adalah **automated crypto market scanner** yang menghasilkan **trading signal berbasis struktur market, regime awareness, dan risk management**.

Project ini dibuat sebagai **research & engineering project**, ditujukan untuk edukasi, observasi market, dan pengembangan sistem trading yang disiplin — **bukan auto-trading bot**.

---

## ✨ Highlights

- 📡 Automated market scanner (cron-like)
- 🧠 Market regime awareness
- 🎯 Risk-aware signal generation
- 🧾 Signal history & lifecycle tracking
- 📩 Telegram notification integration
- 🛑 Anti-duplicate & cooldown per symbol
- ⏰ Time-based trading filter
- ☁️ Cloud friendly (Render / VPS safe)

---

## ❓ What This Project Is

- ✅ Signal generator  
- ✅ Market monitoring tool  
- ✅ Research framework  
- ✅ Telegram alert system  

## ❌ What This Project Is NOT

- ❌ Auto trading bot  
- ❌ High-frequency trading system  
- ❌ Guaranteed profit system  
- ❌ Financial advice  

---

## 🧩 Project Structure

```
.
├── scanner_bot.py     # Automated scanner (no UI)
├── signals.py         # Signal generation logic
├── history.py         # Signal lifecycle & performance tracking
├── exchange.py        # Exchange abstraction layer
├── telegram_bot.py    # Telegram alert sender
├── scheduler.py       # Trading time rules
├── app.py             # Optional Streamlit dashboard
├── config.py          # Configuration
└── README.md
```

---

## ⚙️ Environment Setup

Set environment variables before running:

```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## ▶️ Running the Scanner

```bash
python scanner_bot.py
```

The scanner will:
- Run continuously
- Scan only during optimal market hours
- Prevent duplicate signals
- Apply cooldown per symbol
- Send alerts to Telegram

---

## 📊 Signal Lifecycle

```
OPEN → TP1 HIT → TP2 HIT
   ↘
     SL HIT
```

Signals are tracked and updated automatically based on market price.

---

## 📈 Performance Tracking

The system tracks historical signals and computes:
- Total trades
- Win rate
- Expectancy (simplified)
- Overall bot rating

These metrics are **informational only** and meant for research evaluation.

---

## ⚠️ Disclaimer

This project is provided **for educational and research purposes only**.

- No trading advice
- No profit guarantee
- Use at your own risk
- Crypto markets are highly volatile

The author is not responsible for any financial loss.

---

## 🛠️ Status

- Stable
- Actively developed
- Cloud deployment tested (Render / VPS)

---

## 📄 License

MIT License

---

Built as a learning tool — not a shortcut to profit.

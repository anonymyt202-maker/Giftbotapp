# 🎁 GiftBot V5 — WebApp

Python + Aiogram 3 + FastAPI + Telegram WebApp

---

## 📁 Loyiha tuzilmasi

```
giftbotv5_webapp/
├── bot/                  ← Aiogram 3 bot
│   ├── handlers/         ← start, games, support
│   ├── keyboards/        ← inline klaviaturalar
│   └── main.py
├── api/                  ← FastAPI backend
│   ├── routers/          ← gifts, orders, users, accounts, admin
│   ├── auth.py           ← WebApp initData verification
│   └── main.py
├── db/                   ← SQLAlchemy models
│   ├── models/           ← User, Gift, Order, TgAccount, Referral, PromoCode
│   ├── base.py
│   └── session.py
├── gift_sender/          ← Telethon gift yuboruvchi
│   └── sender.py
├── webapp/               ← HTML WebApp fayllar
│   ├── admin.html        ← Admin panel SPA
│   └── user.html         ← User gift shop SPA
├── migrations/           ← Alembic migratsiyalar
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── run.py                ← Bot + API birga
```

---

## ⚙️ O'rnatish

### 1. .env fayl
```bash
cp .env.example .env
# .env faylni to'ldiring
```

```env
BOT_TOKEN=your_bot_token
ADMIN_IDS=123456789
API_BASE_URL=https://your-domain.com
SECRET_KEY=random_32_char_secret
API_ID=your_api_id
API_HASH=your_api_hash
CARD_NUMBER=5614681256483730
STARS_TO_UZS=140
```

### 2. Virtual environment
```bash
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 3. Ishga tushirish
```bash
python run.py
```

Bot va API bir vaqtda ishga tushadi.

---

## 🐳 Docker bilan

```bash
cp .env.example .env
# .env ni to'ldiring

docker-compose up -d
```

---

## 🌐 Railway / Render deploy

1. GitHub ga push qiling
2. Railway → New Project → Deploy from GitHub
3. Environment variables qo'shing (.env dagi barcha qiymatlar)
4. Start command: `python run.py`
5. Port: `8000`

---

## 📱 WebApp URL lar

| URL | Maqsad |
|-----|--------|
| `https://your-domain.com/webapp/admin` | Admin panel |
| `https://your-domain.com/webapp/user`  | Foydalanuvchi gift shop |
| `https://your-domain.com/api/docs`     | API dokumentatsiya |

---

## 🤖 Bot komandalar

| Komanda | Kim uchun | Tavsif |
|---------|-----------|--------|
| `/start` | Barchasi | Bosh menyu |
| `/admin` | Faqat admin | Admin panel (WebApp) |

---

## 🎁 Gift qo'shish (Admin Panel)

1. Bot da `/admin` → **Admin Panelni Ochish**
2. **Giftlar** tab → **+ Gift qo'shish**
3. To'ldirish:
   - **Nom**: `Ayiq🧸` (emoji ham yozsa bo'ladi)
   - **Stars narxi**: `15`
   - **Telegram Gift ID**: `5168043015958052`
   - Sticker/rasm URL (ixtiyoriy)
   - Kategoriya

---

## 📱 Telegram Account ulash

1. Admin Panel → **Accountlar** tab
2. **Login** — telefon + kod + 2FA
3. **Session yuklash** — tayyor `.session` faylni yuklash

---

## 🗄️ Database

SQLite (default) — `giftbot.db` fayli avtomatik yaratiladi.

PostgreSQL uchun `.env` da:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/giftbot
```

Qo'shimcha: `pip install asyncpg`

---

## 🔐 Admin autentifikatsiya

WebApp Telegram `initData` orqali tekshiriladi (HMAC-SHA256).  
Faqat `.env` dagi `ADMIN_IDS` da ko'rsatilgan Telegram ID lar kirishi mumkin.

---

## 📊 API Endpoints

Barcha endpointlar: `https://your-domain.com/api/docs`

Asosiylar:
- `GET /api/gifts` — giftlar ro'yxati
- `POST /api/orders` — gift sotib olish
- `GET /api/users/me` — balans va ma'lumotlar
- `GET /api/admin/dashboard` — statistika (admin)
- `POST /api/accounts/login/start` — account login (admin)

# 🚀 Render-এ Deploy করার গাইড (আসল ব্যবহারের জন্য)

এই অ্যাপ এখন **PostgreSQL** (Render-এ) আর **SQLite** (লোকালে) — দুটোতেই চলে।
ক্লাউডে `DATABASE_URL` সেট থাকলে অটো PostgreSQL ব্যবহার করবে, তাই ডেটা আর মুছে যাবে না।

---

## ধাপ ১: কোড GitHub-এ তুলুন

Render GitHub থেকে কোড নেয়। তাই আগে একটা GitHub repo লাগবে।

```bash
cd quickservice_web
git init
git add .
git commit -m "QuickService BD web app"
```

এরপর github.com-এ গিয়ে একটা নতুন (খালি) repository বানান — যেমন `quickservice-bd`।
তারপর:

```bash
git remote add origin https://github.com/<your-username>/quickservice-bd.git
git branch -M main
git push -u origin main
```

> `.gitignore` ফাইল আছে, তাই `quickservice.db` আর `.env` ভুলেও আপলোড হবে না।

---

## ধাপ ২: Render-এ অ্যাকাউন্ট

1. https://render.com — এ গিয়ে **GitHub দিয়ে Sign Up** করুন (ফ্রি)।
2. Render-কে আপনার GitHub repo দেখার permission দিন।

---

## ধাপ ৩: Blueprint দিয়ে এক ক্লিকে deploy (সবচেয়ে সহজ)

প্রজেক্টে `render.yaml` ফাইল আছে — এটা একসাথে **ওয়েব সার্ভিস + ফ্রি PostgreSQL** দুটোই বানিয়ে দেয়।

1. Render dashboard → **New +** → **Blueprint**
2. আপনার `quickservice-bd` repo সিলেক্ট করে **Connect**
3. Render `render.yaml` পড়ে সব নিজে সাজিয়ে দেবে — **Apply** চাপুন
4. কয়েক মিনিট অপেক্ষা করুন। হয়ে গেলে একটা লিংক পাবেন:
   `https://quickservice-bd.onrender.com`

ব্যস! `SECRET_KEY` আর `DATABASE_URL` Render নিজে সেট করে দেবে।

---

## ধাপ ৩ (বিকল্প): ম্যানুয়ালি deploy

Blueprint ব্যবহার না করতে চাইলে:

**প্রথমে database:**
1. New + → **PostgreSQL** → নাম দিন → Free plan → Create
2. তৈরি হলে **Internal Database URL** কপি করুন

**তারপর web service:**
1. New + → **Web Service** → repo সিলেক্ট
2. সেটিংস:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
3. **Environment** ট্যাবে দুটো variable যোগ করুন:
   - `DATABASE_URL` = (কপি করা database URL)
   - `SECRET_KEY` = (একটা লম্বা random লেখা, যেমন `kj38fhKD9...`)
4. **Create Web Service** চাপুন

---

## ধাপ ৪: চালু হওয়ার পর

- লিংকে গিয়ে **Sign Up** করে টেস্ট করুন
- Admin panel: `https://your-app.onrender.com/login`
  → `admin@bd.com` / `admin123`
- **⚠️ গুরুত্বপূর্ণ:** প্রথম login-এর পর admin পাসওয়ার্ড পাল্টে নিন
  (এখন seed করা পাসওয়ার্ড সবাই জানে)

---

## ⚠️ ফ্রি tier সম্পর্কে জেনে রাখুন

- **Sleep:** ১৫ মিনিট কেউ না এলে সার্ভার ঘুমিয়ে যায়। পরের ভিজিটে চালু হতে ৩০–৫০ সেকেন্ড লাগে। (paid plan-এ এটা থাকে না)
- **Free PostgreSQL:** Render-এর ফ্রি ডেটাবেস ৩০ দিন পর expire হতে পারে — আসল প্রোডাকশনে paid database নেওয়া ভালো।
- **আইকন/ফন্ট:** Tabler icons, Google Fonts, Leaflet ম্যাপ — সব CDN থেকে আসে, তাই ইউজারের ইন্টারনেট লাগবে (যেটা স্বাভাবিক)।

---

## 🔁 কোড আপডেট করলে

শুধু আবার push করুন — Render অটো রি-ডিপ্লয় করবে:

```bash
git add .
git commit -m "update"
git push
```

---

## 💳 আসল পেমেন্ট (পরে)

এখন bKash/Nagad শুধু দেখানোর জন্য (টাকা কাটে না)। আসল লেনদেন চাইলে
bKash/Nagad-এর **merchant/sandbox API** integrate করতে হবে — সেটা চাইলে পরে যোগ করে দেওয়া যাবে।

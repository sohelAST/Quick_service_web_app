# QuickService BD — Web App (FastAPI)

আপনার Android অ্যাপ **QuickServiceBD**-এর সম্পূর্ণ ওয়েব ভার্সন।
একই বেগুনি ডিজাইন (#5B2EFF), একই সার্ভিস, একই ফ্লো — তিন রোল (Customer / Worker / Admin)।

## ✅ সম্পূর্ণ ফিচার লিস্ট

### 👤 Customer side
- Login / Register (পাসওয়ার্ড hash সহ)
- Home — সার্ভিস গ্রিড + Popular Workers
- Booking (worker, address, date)
- **Payment** — bKash / Nagad / Rocket / Card / Cash on Delivery
- **Chat** — worker-এর সাথে মেসেজ
- **Live Tracking** — Leaflet + OpenStreetMap (ফ্রি, API key লাগে না)
- My Bookings (live status)

### 👷 Worker side
- Worker হিসেবে Sign Up (profession সিলেক্ট)
- Dashboard — Total / Active / Earnings stats
- Tabs: Active / Completed / All
- Auto-assign + Accept / Reject / Complete
- Customer-এর সাথে Chat

### 🛡️ Admin panel
- Login: **admin@bd.com** / **admin123** (auto-তৈরি)
- Dashboard — Customers / Workers / Bookings / Earnings stats
- Manage Users / Workers / Bookings লিস্ট
- শুধু admin ঢুকতে পারে (security protected)

## 🚀 চালানোর নিয়ম
```bash
cd quickservice_web
pip install -r requirements.txt
uvicorn main:app --reload
```
ব্রাউজারে: http://127.0.0.1:8000

## 🧪 কীভাবে টেস্ট করবেন
1. **Worker** হিসেবে Sign Up (profession = Plumbing)
2. আলাদা incognito-তে **Customer** Sign Up → Plumbing বুক → Payment করুন
3. Worker dashboard → job দেখুন → Accept → Chat → Complete
4. **Admin** login (admin@bd.com / admin123) → সব stats ও লিস্ট দেখুন

## 📁 স্ট্রাকচার
```
quickservice_web/
├── main.py                 # সব backend route
├── requirements.txt
└── templates/
    ├── base.html           # theme + navbar
    ├── login.html  register.html
    ├── home.html   book.html  bookings.html
    ├── payment.html         # 💳 payment
    ├── chat.html            # 💬 chat
    ├── track.html           # 📍 live map
    ├── worker.html          # 👷 worker dashboard
    ├── admin.html           # 🛡️ admin dashboard
    └── admin_list.html      # admin manage lists
```

## ⚠️ Production-এর আগে
- `SessionMiddleware`-এর `secret_key` পাল্টান
- bKash/Nagad-এর আসল sandbox/merchant API integrate করুন
- Chat এখন polling (৫ সেকেন্ডে refresh) — চাইলে WebSocket-এ আপগ্রেড করা যাবে
- SQLite → PostgreSQL (বড় স্কেলে)

"""
QuickService BD - Web App (FastAPI)
Demo: User side - Login/Register + Services + Workers + Booking
Original Android app re-created as a Python web app (same design, same flow).
"""
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import sqlite3, hashlib, os

BASE = os.path.dirname(__file__)
app = FastAPI(title="QuickService BD")
# Secret key from environment in production; fallback for local dev only
app.add_middleware(SessionMiddleware,
                   secret_key=os.environ.get("SECRET_KEY", "dev-secret-change-me"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE, "templates"))

# ---------- Database: PostgreSQL in production (DATABASE_URL set), SQLite locally ----------
DATABASE_URL = os.environ.get("DATABASE_URL", "")
USE_PG = DATABASE_URL.startswith("postgres")
DB = os.path.join(BASE, "quickservice.db")  # used only for SQLite

if USE_PG:
    import psycopg2, psycopg2.extras
    # Render gives postgres://; psycopg2 needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ---------- Data (same services as the Android app) ----------
SERVICES = [
    {"name": "Plumbing",    "icon": "🔧", "color": "#5B2EFF"},
    {"name": "Electrician", "icon": "⚡", "color": "#FF9F43"},
    {"name": "AC Repair",   "icon": "❄️", "color": "#2D8CFF"},
    {"name": "Tub-well",    "icon": "🚰", "color": "#28C76F"},
    {"name": "Water Pump",  "icon": "💧", "color": "#00BCD4"},
    {"name": "Cleaning",    "icon": "🧹", "color": "#EA5455"},
    {"name": "Carpenter",   "icon": "🔨", "color": "#8C3494"},
    {"name": "More",        "icon": "➕", "color": "#8A8A8A"},
]

WORKERS = [
    {"name": "Karim Mia",   "role": "Plumber",     "rating": 4.8, "reviews": 124, "online": True,  "exp": 6},
    {"name": "Rahim Uddin", "role": "Electrician", "rating": 4.9, "reviews": 210, "online": True,  "exp": 8},
    {"name": "Sumon Ahmed", "role": "AC Technician","rating": 4.7, "reviews": 98,  "online": False, "exp": 5},
    {"name": "Jamal Hosen", "role": "Cleaner",     "rating": 4.6, "reviews": 76,  "online": True,  "exp": 4},
]

PAYMENT_METHODS = [
    {"name": "bKash",            "icon": "📱", "color": "#E2136E", "desc": "Send money to our bKash"},
    {"name": "Nagad",            "icon": "📲", "color": "#EC1C24", "desc": "Send money to our Nagad"},
    {"name": "Rocket",           "icon": "🚀", "color": "#8C3494", "desc": "Send money to our Rocket"},
    {"name": "Card",             "icon": "💳", "color": "#1A73E8", "desc": "Pay with debit/credit card"},
    {"name": "Cash on Delivery", "icon": "💵", "color": "#28C76F", "desc": "Pay after service done"},
]

# ---------- DB helpers ----------
class ConnWrapper:
    """Wraps a DB connection so the same '?'-style SQL works on both
    SQLite and PostgreSQL. On Postgres, '?' is converted to '%s' and
    INSERTs automatically capture the new id via RETURNING."""
    def __init__(self, conn):
        self._conn = conn
    def execute(self, sql, params=()):
        if USE_PG:
            sql = sql.replace("?", "%s")
            is_insert = sql.strip().lower().startswith("insert")
            if is_insert and "returning" not in sql.lower():
                sql = sql.rstrip().rstrip(";") + " RETURNING id"
            cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql, params)
            last = None
            if is_insert:
                row = cur.fetchone()
                last = row["id"] if row else None
            return _CurWrapper(cur, last)
        else:
            cur = self._conn.cursor()
            cur.execute(sql, params)
            return _CurWrapper(cur, cur.lastrowid)
    def commit(self): self._conn.commit()
    def close(self): self._conn.close()

class _CurWrapper:
    def __init__(self, cur, lastrowid=None):
        self._cur = cur
        self.lastrowid = lastrowid
    def fetchone(self): return self._cur.fetchone()
    def fetchall(self): return self._cur.fetchall()

def db():
    if USE_PG:
        conn = psycopg2.connect(DATABASE_URL)
        return ConnWrapper(conn)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return ConnWrapper(conn)

# Column types differ slightly between the two engines
def _schema():
    pk = "SERIAL PRIMARY KEY" if USE_PG else "INTEGER PRIMARY KEY AUTOINCREMENT"
    ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if USE_PG else "TEXT DEFAULT CURRENT_TIMESTAMP"
    return pk, ts

def init_db():
    pk, ts = _schema()
    conn = db()
    conn.execute(f"""CREATE TABLE IF NOT EXISTS users(
        id {pk},
        name TEXT, email TEXT UNIQUE, phone TEXT, password TEXT,
        role TEXT DEFAULT 'customer', profession TEXT DEFAULT '',
        lat REAL DEFAULT 0, lng REAL DEFAULT 0)""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS bookings(
        id {pk},
        user_id INTEGER, worker_id INTEGER, service TEXT, worker TEXT,
        address TEXT, date TEXT, status TEXT DEFAULT 'Pending', amount INTEGER DEFAULT 500,
        payment_method TEXT DEFAULT '', paid INTEGER DEFAULT 0)""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS messages(
        id {pk},
        booking_id INTEGER, sender_id INTEGER, sender_type TEXT,
        message TEXT, ts {ts})""")
    # Seed an admin account (admin@bd.com / admin123)
    if not conn.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
        conn.execute("INSERT INTO users(name,email,phone,password,role) VALUES(?,?,?,?,?)",
                     ("Admin", "admin@bd.com", "+8801700000000", hash_pw("admin123"), "admin"))
    conn.commit(); conn.close()

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def current_user(request):
    uid = request.session.get("uid")
    if not uid: return None
    conn = db(); u = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone(); conn.close()
    return u

init_db()

# ---------- Routes ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not current_user(request):
        return RedirectResponse("/login")
    return templates.TemplateResponse(request, "home.html", {
        "user": current_user(request),
        "services": SERVICES, "workers": WORKERS})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str = ""):
    return templates.TemplateResponse(request, "login.html", {"error": error})

@app.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = db()
    u = conn.execute("SELECT * FROM users WHERE email=? OR phone=?", (email, email)).fetchone()
    conn.close()
    if u and u["password"] == hash_pw(password):
        request.session["uid"] = u["id"]
    if u and u["password"] == hash_pw(password):
        request.session["uid"] = u["id"]
        dest = {"worker": "/worker", "admin": "/admin"}.get(u["role"], "/")
        return RedirectResponse(dest, status_code=303)
    return RedirectResponse("/login?error=Invalid+email+or+password", status_code=303)

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, error: str = ""):
    return templates.TemplateResponse(request, "register.html", {"error": error})

@app.post("/register")
def register(request: Request, name: str = Form(...), email: str = Form(...),
             phone: str = Form(...), password: str = Form(...),
             role: str = Form("customer"), profession: str = Form("")):
    conn = db()
    try:
        cur = conn.execute(
            "INSERT INTO users(name,email,phone,password,role,profession) VALUES(?,?,?,?,?,?)",
            (name, email, phone, hash_pw(password), role, profession))
        conn.commit()
        request.session["uid"] = cur.lastrowid
        conn.close()
        return RedirectResponse("/worker" if role == "worker" else "/", status_code=303)
    except Exception:
        try: conn._conn.rollback()
        except Exception: pass
        conn.close()
        return RedirectResponse("/register?error=Email+already+exists", status_code=303)

@app.get("/book/{service}", response_class=HTMLResponse)
def book_page(request: Request, service: str):
    if not current_user(request): return RedirectResponse("/login")
    return templates.TemplateResponse(request, "book.html", {
        "user": current_user(request),
        "service": service, "workers": WORKERS})

@app.post("/book")
def book(request: Request, service: str = Form(...), worker: str = Form(...),
         address: str = Form(...), date: str = Form(...)):
    u = current_user(request)
    if not u: return RedirectResponse("/login")
    conn = db()
    # Try to assign a registered worker whose profession matches the service
    w = conn.execute(
        "SELECT id,name FROM users WHERE role='worker' AND profession=? LIMIT 1",
        (service,)).fetchone()
    if w:
        worker_id, worker_name, status = w["id"], w["name"], "Assigned"
    else:
        worker_id, worker_name, status = None, worker, "Pending"
    cur = conn.execute(
        "INSERT INTO bookings(user_id,worker_id,service,worker,address,date,status,amount) VALUES(?,?,?,?,?,?,?,?)",
        (u["id"], worker_id, service, worker_name, address, date, status, 500))
    bid = cur.lastrowid
    conn.commit(); conn.close()
    return RedirectResponse(f"/payment/{bid}", status_code=303)

@app.get("/bookings", response_class=HTMLResponse)
def bookings(request: Request):
    u = current_user(request)
    if not u: return RedirectResponse("/login")
    conn = db()
    rows = conn.execute("SELECT * FROM bookings WHERE user_id=? ORDER BY id DESC", (u["id"],)).fetchall()
    conn.close()
    return templates.TemplateResponse(request, "bookings.html", {
        "user": u, "bookings": rows})

@app.get("/worker", response_class=HTMLResponse)
def worker_dashboard(request: Request, tab: str = "active"):
    u = current_user(request)
    if not u: return RedirectResponse("/login")
    if u["role"] != "worker": return RedirectResponse("/")
    conn = db()
    jobs = conn.execute(
        "SELECT b.*, cu.name AS customer_name, cu.phone AS customer_phone "
        "FROM bookings b JOIN users cu ON b.user_id=cu.id "
        "WHERE b.worker_id=? ORDER BY b.id DESC", (u["id"],)).fetchall()
    conn.close()
    # Stats
    total = len(jobs)
    active = sum(1 for j in jobs if j["status"] in ("Assigned", "Active"))
    earnings = sum(j["amount"] for j in jobs if j["status"] == "Completed")
    # Filter by tab
    if tab == "active":
        shown = [j for j in jobs if j["status"] in ("Assigned", "Active")]
    elif tab == "completed":
        shown = [j for j in jobs if j["status"] == "Completed"]
    else:
        shown = jobs
    return templates.TemplateResponse(request, "worker.html", {
        "user": u, "jobs": shown, "tab": tab,
        "total": total, "active": active, "earnings": earnings})

@app.post("/job/{job_id}/{action}")
def job_action(request: Request, job_id: int, action: str):
    u = current_user(request)
    if not u or u["role"] != "worker": return RedirectResponse("/login")
    status_map = {"accept": "Active", "reject": "Rejected", "complete": "Completed"}
    new_status = status_map.get(action)
    if new_status:
        conn = db()
        conn.execute("UPDATE bookings SET status=? WHERE id=? AND worker_id=?",
                     (new_status, job_id, u["id"]))
        conn.commit(); conn.close()
    return RedirectResponse("/worker", status_code=303)

# ---------- Payment ----------
@app.get("/payment/{bid}", response_class=HTMLResponse)
def payment_page(request: Request, bid: int):
    u = current_user(request)
    if not u: return RedirectResponse("/login")
    conn = db()
    b = conn.execute("SELECT * FROM bookings WHERE id=? AND user_id=?", (bid, u["id"])).fetchone()
    conn.close()
    if not b: return RedirectResponse("/bookings")
    return templates.TemplateResponse(request, "payment.html", {
        "user": u, "booking": b, "methods": PAYMENT_METHODS})

@app.post("/payment/{bid}")
def pay(request: Request, bid: int, method: str = Form(...)):
    u = current_user(request)
    if not u: return RedirectResponse("/login")
    conn = db()
    paid = 0 if method == "Cash on Delivery" else 1
    conn.execute("UPDATE bookings SET payment_method=?, paid=? WHERE id=? AND user_id=?",
                 (method, paid, bid, u["id"]))
    conn.commit(); conn.close()
    return RedirectResponse("/bookings", status_code=303)

# ---------- Chat ----------
@app.get("/chat/{bid}", response_class=HTMLResponse)
def chat_page(request: Request, bid: int):
    u = current_user(request)
    if not u: return RedirectResponse("/login")
    conn = db()
    b = conn.execute("SELECT * FROM bookings WHERE id=?", (bid,)).fetchone()
    if not b or (u["id"] != b["user_id"] and u["id"] != b["worker_id"]):
        conn.close(); return RedirectResponse("/")
    msgs = conn.execute("SELECT * FROM messages WHERE booking_id=? ORDER BY id", (bid,)).fetchall()
    conn.close()
    other = b["worker"] if u["role"] == "customer" else "Customer"
    return templates.TemplateResponse(request, "chat.html", {
        "user": u, "booking": b, "messages": msgs, "other": other})

@app.post("/chat/{bid}")
def chat_send(request: Request, bid: int, message: str = Form(...)):
    u = current_user(request)
    if not u or not message.strip(): return RedirectResponse(f"/chat/{bid}")
    conn = db()
    conn.execute("INSERT INTO messages(booking_id,sender_id,sender_type,message) VALUES(?,?,?,?)",
                 (bid, u["id"], u["role"], message.strip()))
    conn.commit(); conn.close()
    return RedirectResponse(f"/chat/{bid}", status_code=303)

# ---------- Live Tracking ----------
@app.get("/track/{bid}", response_class=HTMLResponse)
def track_page(request: Request, bid: int):
    u = current_user(request)
    if not u: return RedirectResponse("/login")
    conn = db()
    b = conn.execute("SELECT * FROM bookings WHERE id=?", (bid,)).fetchone()
    w = conn.execute("SELECT lat,lng,name FROM users WHERE id=?", (b["worker_id"],)).fetchone() if b and b["worker_id"] else None
    conn.close()
    if not b: return RedirectResponse("/bookings")
    # Default to Dhaka if worker has no location set
    wlat = w["lat"] if w and w["lat"] else 23.8103
    wlng = w["lng"] if w and w["lng"] else 90.4125
    return templates.TemplateResponse(request, "track.html", {
        "user": u, "booking": b, "wlat": wlat, "wlng": wlng,
        "wname": (w["name"] if w else b["worker"])})

# ---------- Admin ----------
def require_admin(request):
    u = current_user(request)
    return u if (u and u["role"] == "admin") else None

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    u = require_admin(request)
    if not u: return RedirectResponse("/login")
    conn = db()
    n_users = conn.execute("SELECT COUNT(*) c FROM users WHERE role='customer'").fetchone()["c"]
    n_workers = conn.execute("SELECT COUNT(*) c FROM users WHERE role='worker'").fetchone()["c"]
    n_bookings = conn.execute("SELECT COUNT(*) c FROM bookings").fetchone()["c"]
    earnings = conn.execute("SELECT COALESCE(SUM(amount),0) s FROM bookings WHERE status='Completed'").fetchone()["s"]
    conn.close()
    return templates.TemplateResponse(request, "admin.html", {
        "user": u, "n_users": n_users, "n_workers": n_workers,
        "n_bookings": n_bookings, "earnings": earnings})

@app.get("/admin/{what}", response_class=HTMLResponse)
def admin_manage(request: Request, what: str):
    u = require_admin(request)
    if not u: return RedirectResponse("/login")
    conn = db()
    if what == "users":
        rows = conn.execute("SELECT * FROM users WHERE role='customer' ORDER BY id DESC").fetchall()
    elif what == "workers":
        rows = conn.execute("SELECT * FROM users WHERE role='worker' ORDER BY id DESC").fetchall()
    elif what == "bookings":
        rows = conn.execute(
            "SELECT b.*, cu.name AS customer_name FROM bookings b "
            "JOIN users cu ON b.user_id=cu.id ORDER BY b.id DESC").fetchall()
    else:
        conn.close(); return RedirectResponse("/admin")
    conn.close()
    return templates.TemplateResponse(request, "admin_list.html", {
        "user": u, "what": what, "rows": rows})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")

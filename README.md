# 🍜 Vote Thai Food

ระบบโหวตเมนูอาหารไทยที่คุณชื่นชอบ พร้อมรูปภาพประกอบและระบบจัดอันดับแบบ Real-time

![Thai Food Voting](https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/Pad_Thai.JPG/250px-Pad_Thai.JPG)

---

## ✨ Features

- 🗳️ **โหวตได้หลายรายการ** — เลือกเมนูโปรดได้ไม่จำกัด
- 📊 **จัดอันดับ Real-time** — คะแนนอัปเดตทันทีหลังโหวต
- 🖼️ **รูปภาพประกอบทุกเมนู** — ดึงจาก Wikimedia Commons (CC)
- 💾 **บันทึกข้อมูลจริง** — ใช้ SQLite เก็บคะแนน ไม่หายหลัง refresh
- 🔒 **ป้องกันโหวตซ้ำ** — ใช้ session ID ต่อเบราว์เซอร์
- 📱 **Responsive** — ใช้ได้ทั้งมือถือและเดสก์ท็อป

---

## 🍽️ เมนูที่มีในระบบ (20 รายการ)

| # | เมนู | ราคา |
|---|------|------|
| 1 | ผัดไทยกุ้งสด | 150 ฿ |
| 2 | ต้มยำกุ้งน้ำข้น | 250 ฿ |
| 3 | แกงเขียวหวานไก่ | 180 ฿ |
| 4 | แกงมัสมั่นเนื้อ | 250 ฿ |
| 5 | ส้มตำไทย | 80 ฿ |
| 6 | ข้าวผัดกระเพราหมูสับไข่ดาว | 120 ฿ |
| 7 | ข้าวผัดปู | 180 ฿ |
| 8 | ยำวุ้นเส้นทะเล | 180 ฿ |
| 9 | ต้มข่าไก่ | 160 ฿ |
| 10 | คอหมูย่าง | 150 ฿ |
| ... | และอีก 10 รายการ | — |

---

## 🚀 วิธีรัน

### Option 1 — Python (แนะนำ ไม่ต้องติดตั้งอะไรเพิ่ม)

ต้องการแค่ **Python 3.6+** เท่านั้น

```bash
# 1. Clone repo
git clone https://github.com/watcharataninthon/Vote-Thaifood.git
cd Vote-Thaifood

# 2. รัน API backend (port 3001)
python3 food_vote_server.py &

# 3. รัน Frontend (port 5500)
python3 -m http.server 5500

# 4. เปิดเบราว์เซอร์
open http://localhost:5500/food-vote.html
```

### Option 2 — Docker (สำหรับ Production)

ต้องการ **Docker** และ **Docker Compose**

```bash
cd food-vote-backend
docker-compose up --build
```

จากนั้นเปิด `food-vote.html` ในเบราว์เซอร์ (แก้ `API` ใน HTML เป็น `http://localhost:3000`)

---

## 🗂️ โครงสร้างไฟล์

```
Vote-Thaifood/
│
├── food-vote.html          # หน้าโหวต (Frontend)
├── food_vote_server.py     # API Server แบบเบา (Python + SQLite)
│
└── food-vote-backend/      # Production Backend (Node.js + Docker)
    ├── docker-compose.yml  # PostgreSQL + Redis + API
    ├── Dockerfile
    ├── init.sql            # สร้าง Schema + Seed 20 เมนู
    └── src/
        ├── index.js        # Express server
        ├── db.js           # PostgreSQL connection
        ├── redis.js        # Redis client
        └── routes/
            └── votes.js    # Vote logic ทั้งหมด
```

---

## 🛠️ Tech Stack

### Frontend
| ส่วน | เทคโนโลยี |
|------|-----------|
| UI | HTML + CSS + Vanilla JS |
| รูปภาพ | Wikimedia Commons (CC License) |
| State | localStorage (session fallback) |

### Backend — Lightweight
| ส่วน | เทคโนโลยี |
|------|-----------|
| Server | Python 3 `http.server` |
| Database | SQLite3 (built-in) |
| Dependencies | ไม่มี (zero dependency) |

### Backend — Production
| ส่วน | เทคโนโลยี |
|------|-----------|
| Server | Node.js + Express |
| Database | PostgreSQL 16 |
| Cache / Leaderboard | Redis 7 (Sorted Set) |
| Container | Docker + Docker Compose |

---

## 📡 API Endpoints

| Method | Path | คำอธิบาย |
|--------|------|----------|
| `GET` | `/health` | ตรวจสอบสถานะ server |
| `GET` | `/rankings` | ดึงอันดับเมนูทั้งหมด |
| `GET` | `/votes/mine` | เมนูที่ session นี้โหวตไปแล้ว |
| `POST` | `/vote/:id` | โหวตเมนู (ต้องส่ง `x-session-id` header) |
| `DELETE` | `/vote/:id` | ถอนโหวต |

ตัวอย่าง:
```bash
# โหวตเมนู #1
curl -X POST http://localhost:3001/vote/1 \
  -H "x-session-id: my-browser-uuid"

# ดูอันดับ
curl http://localhost:3001/rankings
```

---

## 🖼️ Credit

รูปภาพอาหารจาก [Wikimedia Commons](https://commons.wikimedia.org/wiki/Category:Cuisine_of_Thailand) ภายใต้สัญญาอนุญาต Creative Commons

---

## 📄 License

MIT

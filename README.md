# Retail Management API (WIP)

A learning project built with **FastAPI** and **SQLAlchemy**, designed to explore modern backend development best practices through a clean and well-structured CRUD API.

This project models a multi-store retail system with support for:
- Product catalog and pricing
- Inventory management across stores
- Transaction processing
- Customer accounts
- Employee management

All models use **UUID primary keys** and **timezone-aware timestamps**, with type-safe constraints powered by SQLAlchemy’s expression language.

---

## 🧠 Project Goals

- Learn and apply **FastAPI** for building production-style APIs  
- Gain hands-on experience with **SQLAlchemy ORM** and database design  
- Write clean, maintainable, and well-tested Python backend code  
- Practice proper project structure, documentation, and version control  
- Eventually expose this as a full-featured example CRUD API with optional frontend integration  

---

## 🚧 Current Progress

- [x] Database models (SQLAlchemy ORM + type-safe constraints)
- [ ] API endpoints (FastAPI routes)
- [ ] CRUD operations
- [ ] Logging setup
- [ ] Unit & integration tests
- [ ] Minimal frontend (optional)

---

## 🗂️ Tech Stack

- **FastAPI** — API framework  
- **SQLAlchemy ORM** — database models and queries  
- **PostgreSQL / SQLite** — database backend (depending on environment)  
- **Pydantic** — data validation and serialization  
- **Uvicorn** — ASGI server  
- **Pytest** — testing framework  

---

## 🏗️ Setup (WIP)

> Detailed setup instructions will be added once the API layer is implemented.

For now:
```bash
# Clone the repo
git clone https://github.com/<your-username>/retail-management-api.git
cd retail-management-api

# Install dependencies
pip install -r requirements.txt

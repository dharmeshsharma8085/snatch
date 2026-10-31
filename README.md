# snatch
# 🔐 SNATCH — Smart Device Security Platform

**Your Device. Your Safety.**

SNATCH is an intelligent device security and theft protection platform powered by Agentic AI. It aims to help users monitor their devices, detect suspicious activities, manage security incidents, and coordinate emergency responses.

## 🚀 Features

- **Risk Intelligence:** Detects suspicious device activity using a deterministic risk engine.
- **Multi-Agent System:** Uses LangGraph to orchestrate specialized agents.
- **Device Management:** Register and manage user devices.
- **Heartbeat Monitoring:** Track device connectivity and online/offline status.
- **Location Intelligence:** Process authorized device location updates.
- **Battery Guardian:** Analyze battery conditions.
- **Evidence Manager:** Generate SHA-256 evidence hashes.
- **Incident Management:** Create, retrieve, verify, and cancel incidents.
- **Authentication:** Secure user registration, password hashing, and JWT authentication.
- **Database:** PostgreSQL-powered data persistence.

## 🛠️ Tech Stack

- Python
- FastAPI
- LangGraph
- OpenAI API
- PostgreSQL
- SQLAlchemy
- Pydantic
- Docker
- JWT Authentication

## 📁 Project Structure

```text
SNATCH/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── core/
│   │   ├── database/
│   │   ├── graph/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   └── tests/
├── mobile/
│   ├── android/
│   └── ios/
├── infrastructure/
└── docs/
```

## ⚙️ Getting Started

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd SNATCH
```

### 2. Start PostgreSQL

```bash
docker compose up -d
```

### 3. Setup Python environment

```bash
cd backend

python -m venv .venv
```

Activate environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file inside the backend directory.

Configure your own credentials:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

DATABASE_URL=postgresql+psycopg://snatch_user:your_password@127.0.0.1:5433/snatch_db

JWT_SECRET_KEY=your_random_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Never commit your `.env` file or expose your API keys.

### 6. Initialize database

```bash
python -m app.database.init_db
```

### 7. Run the backend

```bash
python -m uvicorn app.main:app --reload
```

Open API documentation:

http://127.0.0.1:8000/docs

## 🧪 Run Tests

```bash
python -m pytest ./tests -v
```

## 🔒 Security & Limitations

SNATCH is currently under active development.

- Risk scores are experimental indicators, not confirmed theft probabilities.
- Offline status does not automatically indicate theft.
- Location access requires appropriate device authorization and consent.
- Emergency response workflows do not yet guarantee real notification delivery.
- Evidence hashing does not yet provide forensic-grade chain of custody.

## 🎯 Vision

Our vision is to make device security smarter, more proactive, and accessible through intelligent technology.

**Built with passion, innovation, and purpose.**

---

⭐ If you find SNATCH interesting, follow the project as it evolves.

**SNATCH — Your Device. Your Safety.**

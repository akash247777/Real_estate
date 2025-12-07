# 🏠 RealtyFeed Explorer

A modern real estate explorer built with React + Vite on the frontend and a Flask API backend. It fetches property listings, supports natural-language search powered by Gemini, and overlays rich location insights using Google Maps services.
# DEMO


https://github.com/user-attachments/assets/54cbe73d-16ca-4268-b503-79815e1fe44d



## ✨ Features
- 🔍 Natural-language search for properties via `/api/search` (Gemini → SQL).
- 🗺️ Interactive maps with nearby amenities and Street View.
- 🧭 Commute calculator with mock route info and polyline rendering.
- 🌿 Environmental insights: air quality, solar potential, and pollen (mocked where noted).
- 🧠 AI Location Analysis summarizing nearby amenities and lifestyle factors.
- 🌓 Full dark mode support via `ThemeContext` and Tailwind.

## 🧩 Architecture
- **Frontend (React + Vite)**
  - Entry: `index.html`, `index.tsx`, `App.tsx`
  - Context: `contexts/ThemeContext.tsx`
  - Components: cards, modal, maps, galleries, search bar
  - Services: RealtyFeed fetch, Google APIs, search API client
- **Backend (Flask)**
  - `backend/api_server.py` exposes `/api/search` and `/api/health`
  - Uses Gemini to convert queries → SQL for a SQL Server database
  - Transforms SQL results into frontend `Property` objects

## 📁 Folder Structure
```
Real_estate/
├── App.tsx
├── index.html
├── index.tsx
├── components/
│   ├── AILocationAnalysis.tsx
│   ├── CommuteCalculator.tsx
│   ├── EnvironmentalInsights.tsx
│   ├── GalleryAndStreetView.tsx
│   ├── Header.tsx
│   ├── ImageWithLoader.tsx
│   ├── LoadingSpinner.tsx
│   ├── MapComponent.tsx
│   ├── PropertyCard.tsx
│   └── PropertyModal.tsx
├── contexts/ThemeContext.tsx
├── services/
│   ├── embeddingService.ts
│   ├── googleApiService.ts
│   ├── googleMapsLoader.ts
│   ├── realtyService.ts
│   └── searchService.ts
├── backend/
│   ├── api_server.py
│   └── demo.py
├── constants.ts
├── types.ts
├── vite.config.ts
├── tsconfig.json
├── package.json
└── requirements.txt
```
Architecture Diagram

<img width="1308" height="1990" alt="diagram-export-7-12-2025-2_11_47-pm" src="https://github.com/user-attachments/assets/3c5ef23c-4771-44a3-a2f8-58ccaaf0a1a8" />


## 🛠️ Tech Stack
- **Frontend**: `react`, `vite`, Tailwind CDN, Font Awesome CDN
- **Backend**: `flask`, `flask-cors`, `sqlalchemy`, `pyodbc`
- **AI**: `google-generativeai` (Gemini 2.5 Flash)
- **Maps & Data**: Google Maps JavaScript API, Places, Geometry

## 🚀 Getting Started

### 1) Prerequisites
- Node.js 18+
- Python 3.10+
- SQL Server with a database named `Real_estate` (configurable via env)
- ODBC Driver 17 for SQL Server installed

### 2) Install dependencies
Frontend:
```
npm install
```
Backend:
```
pip install -r requirements.txt
```

### 3) Configure environment
Create a `.env` in the project root for the backend:
```
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
DB_SERVER=YOUR_SERVER\SQLEXPRESS
DB_NAME=Real_estate
DB_USER=your_user
DB_PASSWORD=your_password
```

Update frontend `constants.ts` with your keys:
```
export const GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY";
export const REALTY_API_URL = "https://api.realtyfeed.com/reso/odata/Property?...";
export const REALTY_TOKEN = "YOUR_REALTYFEED_TOKEN";
```

Note: Current repo includes sample tokens for development; replace with your own.

### 4) Run in development
Combined dev (frontend + backend):
```
npm run dev
```
- Backend: `http://localhost:5000` (Flask)
- Frontend: `http://localhost:5173` (Vite)

Or run separately:
```
npm run dev:backend
npm run dev:frontend
```

### 5) Build & Preview
```
npm run build
npm run preview
```

## 🔌 API Endpoints
- `GET /api/health`: Health check with DB status.
- `POST /api/search`: Body `{ query: string }` → returns `{ success, sql, results, count, message }`.

Search flow:
- Frontend calls `/api/search` with natural language.
- Backend uses Gemini to generate SQL based on the documented schema.
- Executes SQL via SQLAlchemy/pyodbc.
- Transforms rows to the `Property` shape expected by the UI.

## 🗺️ Maps & Insights
- Loads Google Maps via `services/googleMapsLoader.ts` using `GOOGLE_MAPS_API_KEY`.
- Nearby places and amenities are queried via Places service.
- Some services (solar/pollen/routes) use mocked data; swap to live API endpoints by uncommenting in `googleApiService.ts` and ensuring proper billing/quotas.

## 🔐 Security & Keys
- Do not commit real API keys/tokens.
- Use `.env` for backend; use environment variables or secure config for frontend in production.
- Restrict Google API keys to allowed origins and services.

## 💡 Tips
- If Google Maps fails to initialize, check quotas and that Maps JavaScript API is enabled.
- If `/api/search` returns DB errors, verify SQL Server connectivity and driver installation.
- Tailwind is loaded via CDN; consider local setup for production hardening.

## 📸 UI Overview
- `App.tsx` orchestrates search, loading, error states, and property grid.
- `PropertyCard.tsx` shows price, address, beds/baths/area with image.
- `PropertyModal.tsx` presents details, map, commute, AI analysis, and environmental tabs.
- `MapComponent.tsx` displays map, amenities, Street View, and route overlays.

## 🧪 Testing (Manual)
- Search examples:
  - "Show me 3-bed properties under $500k"
  - "Homes with pool near South Carolina"
- Validate map and Street View in the modal for properties with coordinates.

## 📄 License
This project is private to your workspace. Replace tokens and keys before sharing. ✍️

---
Made with ❤️ for explorations in real estate.

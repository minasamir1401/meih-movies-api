# Project Structure for GitHub

## Repository Organization

This project consists of two main parts that should be organized as follows for GitHub deployment:

### Backend (meih-movies-api)
- Location: `/backend`
- Framework: FastAPI (Python)
- Deployment: Render
- Key files:
  - `main.py` - Entry point
  - `requirements.txt` - Python dependencies
  - `render.yaml` - Render deployment configuration
  - `setup_render.sh` - Build script for Render
  - `start_render.sh` - Start script for Render
  - `Procfile` - Heroku/Render process file
  - `scraper/` - Scraping engine
  - `proxy-service/` - Node.js proxy service

### Frontend (meih-clone)
- Location: `/meih-netflix-clone`
- Framework: React + Vite + TypeScript
- Deployment: Vercel
- Key files:
  - `package.json` - NPM dependencies and scripts
  - `vite.config.ts` - Vite configuration
  - `tsconfig.json` - TypeScript configuration
  - `src/` - Source code
  - `src/services/api.ts` - API service
  - `src/components/` - React components
  - `src/pages/` - Page components
  - `tailwind.config.js` - Tailwind CSS configuration

## Recommended GitHub Structure

```
meih-streaming-platform/
├── backend/
│   ├── scraper/
│   ├── proxy-service/
│   ├── main.py
│   ├── requirements.txt
│   ├── render.yaml
│   ├── setup_render.sh
│   ├── start_render.sh
│   ├── Procfile
│   └── README.md
├── meih-netflix-clone/
│   ├── src/
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── README.md
├── README.md
└── LICENSE
```

## Deployment Instructions

### Backend (Render)
1. Push to GitHub
2. Connect Render to the repository
3. Set up as Web Service
4. Configure environment variables:
   - `NODE_PROXY_URL`: `http://localhost:3001`

### Frontend (Vercel)
1. Push to GitHub
2. Connect Vercel to the repository
3. Set up environment variables:
   - `VITE_API_URL`: `https://your-backend-url.onrender.com`
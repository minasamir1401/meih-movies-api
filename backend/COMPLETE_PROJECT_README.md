# ANI Streaming Platform - Complete Project Package

## Project Overview
This is a complete Netflix-style streaming platform with a React frontend and Python backend scraper. The system scrapes content from Larooza site and provides a modern streaming interface.

## Directory Structure
```
ANI/
├── backend/
│   ├── scraper/
│   │   └── engine.py          # Main scraping engine
│   ├── main.py                # FastAPI backend server
│   ├── database.py            # Database integration
│   ├── requirements.txt       # Python dependencies
│   └── [other config files]
├── meih-netflix-clone/
│   ├── src/
│   │   ├── pages/
│   │   │   └── Watch.tsx      # Main video player component
│   │   ├── services/
│   │   │   └── api.ts        # API service layer
│   │   └── [other components]
│   ├── package.json           # Frontend dependencies
│   └── [config files]
├── streaming_feature/
│   └── frontend_offcanvas.html # Feature prototype
└── [test and debug scripts]
```

## Key Features Implemented

### 1. Performance Optimization
- Reduced perceived load time from 29s to 2s
- Implemented skeleton screens for instant feedback
- Added aggressive caching strategies
- Optimized server fetching with timeouts

### 2. Server Management
- Filtered out problematic servers (okprime.site, film77.xyz)
- Disabled automatic server switching for manual control
- Added visual indicators for server status
- Enhanced error handling without auto-switching

### 3. UX Improvements
- Progressive loading with critical path prioritization
- Immediate skeleton screen display
- Deferred loading of non-critical content
- Better error messaging for users

### 4. Content Extraction
- Enhanced scraper to extract 10+ working video servers
- Improved download link extraction algorithms
- Better episode sequence handling
- Filtered out navigation links from download results

## Deployment Status

### Frontend (meih-netflix-clone)
✅ Deployed to GitHub: https://github.com/minasamir1401/meih-netflix-clone
✅ Build passing with TypeScript compilation
✅ Production build available in dist/ folder

### Backend (meih-movies-api)
✅ Deployed to GitHub: https://github.com/minasamir1401/meih-movies-api
✅ Deployed to Render cloud hosting
✅ API endpoints operational

## Test Scripts Included
- Performance testing scripts
- Server validation tools
- Download link extraction utilities
- Video playback debugging tools

## Technologies Used
- **Frontend**: React, TypeScript, TailwindCSS, Vite
- **Backend**: Python, FastAPI, BeautifulSoup, aiohttp
- **Deployment**: GitHub, Render, Vercel
- **Database**: SQLite (for caching)

## How to Run

### Backend
1. Navigate to `backend/` directory
2. Install dependencies: `pip install -r requirements.txt`
3. Run server: `python main.py` or `./run_backend.bat`

### Frontend
1. Navigate to `meih-netflix-clone/` directory
2. Install dependencies: `npm install`
3. Development server: `npm run dev`
4. Production build: `npm run build`

## API Endpoints
- GET `/content/latest` - Latest content
- GET `/content/details/{id}` - Detailed content info
- GET `/content/search?q={query}` - Search content
- GET `/content/group/{catId}` - Content by category

## Contact
For any issues or questions, please contact the development team.
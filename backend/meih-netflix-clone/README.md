# MEIH Netflix Clone - Frontend

## Overview

This is the frontend application for the MEIH Movies streaming platform. It provides a Netflix-like interface for browsing and watching movies and TV shows scraped from various sources.

## Features

- Netflix-style UI with rows and categories
- Movie and TV show browsing
- Search functionality
- Video playback
- Responsive design for all devices
- Dark theme

## Tech Stack

- **Framework**: React with TypeScript
- **Styling**: Tailwind CSS
- **Routing**: React Router
- **State Management**: React Hooks
- **Animations**: Framer Motion
- **Icons**: React Icons
- **Slider**: Swiper
- **Build Tool**: Vite
- **Deployment**: Vercel.com (recommended)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd meih-netflix-clone
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

4. **Build for production**
   ```bash
   npm run build
   ```

5. **Preview production build**
   ```bash
   npm run preview
   ```

## Environment Variables

Create a `.env` file in the root directory:

```env
VITE_API_BASE_URL=http://localhost:10000  # Backend API URL
```

## Project Structure

```
meih-netflix-clone/
├── src/
│   ├── components/        # Reusable UI components
│   ├── pages/            # Page components
│   ├── services/         # API service functions
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── index.html            # HTML template
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── vite.config.ts        # Vite configuration
├── tailwind.config.js    # Tailwind CSS configuration
└── README.md             # This file
```

## Components

### Core Components

- **Navbar**: Navigation header with search
- **Hero**: Featured content banner
- **MovieCard**: Individual movie/show card
- **MovieRow**: Horizontal row of movies/shows
- **Row**: Generic content row
- **ErrorBoundary**: Error handling component

### Pages

- **Home**: Main landing page with content rows
- **Movies**: Movies category page
- **Series**: TV shows category page
- **Category**: Specific category page
- **Details**: Content details page
- **Search**: Search results page
- **Watch**: Video player page

## Styling

The application uses Tailwind CSS for styling with a dark theme. Custom styles can be added in `src/index.css`.

## API Integration

The frontend communicates with the backend API through the `src/services/api.ts` file. All API calls are centralized there for easy maintenance.

## Deployment

See [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) for detailed deployment instructions.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

## License

This project is licensed under the MIT License.
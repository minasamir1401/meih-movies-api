import { Routes, Route } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import Navbar from './components/Navbar';
import ErrorBoundary from './components/ErrorBoundary';

const Home = lazy(() => import('./pages/Home'));
const Watch = lazy(() => import('./pages/Watch'));
const Search = lazy(() => import('./pages/Search'));
const CategoryPage = lazy(() => import('./pages/Category'));

const App = () => {
  return (
    <div className="bg-[#0a0a0a] min-h-screen selection:bg-red-600/30">
      <ErrorBoundary>
        <Navbar />
        <Suspense fallback={
          <div className="bg-[#0a0a0a] h-screen text-white flex flex-col items-center justify-center">
              <div className="w-12 h-12 border-2 border-red-600 border-t-transparent rounded-full animate-spin mb-4"></div>
              <p className="text-[10px] font-black uppercase tracking-widest text-gray-500">جاري التحميل...</p>
          </div>
        }>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<Search />} />
            <Route path="/category/:catId" element={<CategoryPage />} />
            <Route path="/details/:id" element={<Watch />} />
            <Route path="/watch/:id" element={<Watch />} />
          </Routes>
        </Suspense>
      </ErrorBoundary>
    </div>
  );
};

export default App;

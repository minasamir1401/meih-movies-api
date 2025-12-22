import { useEffect, useState, useRef } from 'react';
import Hero from '../components/Hero';
import MovieCard from '../components/MovieCard';
import MovieRow from '../components/MovieRow';
import { fetchLatest, ContentItem } from '../services/api';
import { FaFire, FaThLarge, FaBolt } from 'react-icons/fa';

const Home = () => {
  const [content, setContent] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [heroMovie, setHeroMovie] = useState<any>(null);
  const [page, setPage] = useState(1);
  const [loadingMore, setLoadingMore] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchLatest(1)
      .then(data => {
        const safeData = Array.isArray(data) ? data : [];
        setContent(safeData);
        if (safeData.length > 0) setHeroMovie(safeData[0]);
      })
      .catch(err => {
          console.error(err);
          setError("فشل في تحميل المحتوى. تأكد من تشغيل السيرفر.");
      })
      .finally(() => setLoading(false));
  }, []);

  const loadMore = async () => {
      if (loadingMore) return;
      setLoadingMore(true);
      try {
          const nextPage = page + 1;
          const newData = await fetchLatest(nextPage);
          const safeNewData = Array.isArray(newData) ? newData : [];
          if (safeNewData.length > 0) {
              setPage(nextPage);
              setContent(prev => {
                  const safePrev = Array.isArray(prev) ? prev : [];
                  const ids = new Set(safePrev.map(p => p.id));
                  const validNew = safeNewData.filter(n => n && n.id && !ids.has(n.id));
                  return [...safePrev, ...validNew];
              });
          }
      } catch (e) {
          console.error(e);
      } finally {
          setLoadingMore(false);
      }
  };

  const observerTarget = useRef(null);

  useEffect(() => {
      const observer = new IntersectionObserver(
          entries => {
              if (entries[0].isIntersecting && !loadingMore && !loading && content.length > 0) {
                  loadMore();
              }
          },
          { threshold: 1.0 }
      );

      if (observerTarget.current) observer.observe(observerTarget.current);
      return () => observer.disconnect();
  }, [loadingMore, loading, content]);

  return (
    <div className="bg-[#0a0a0a] min-h-screen pb-20">
      {loading ? (
          <div className="h-screen flex flex-col items-center justify-center text-white">
              <div className="w-20 h-20 border-[3px] border-red-600 border-t-transparent rounded-full animate-spin mb-8"></div>
              <p className="text-xs font-black uppercase tracking-[0.4em] text-gray-500 animate-pulse">يتم الآن عرض عالمك الترفيهي...</p>
          </div>
      ) : error ? (
          <div className="h-screen flex flex-col items-center justify-center text-red-500 p-8 text-center">
              <div className="w-24 h-24 bg-red-600/10 rounded-full flex items-center justify-center mb-8 border border-red-600/20">
                 <FaBolt className="text-4xl text-red-600" />
              </div>
              <h2 className="text-4xl font-black mb-4 tracking-tighter italic">خطأ في الاتصال</h2>
              <p className="text-gray-500 font-bold mb-10 max-w-md">{error}</p>
              <button onClick={() => window.location.reload()} className="bg-white text-black font-black italic px-12 py-4 rounded-2xl hover:bg-red-600 hover:text-white transition-all transform hover:scale-105 active:scale-95 shadow-xl">أعد المحاولة الآن</button>
          </div>
      ) : (
          <>
            <Hero movie={heroMovie} />
            
            <main className="relative z-20 -mt-16 sm:-mt-24 md:-mt-32">
                {/* Categorized Rows */}
                <div className="px-4 sm:px-6 md:px-12 mb-12 sm:mb-16 md:mb-20 space-y-8 sm:space-y-12 md:space-y-16">
                   <MovieRow title="أحدث المسلسلات العربية" catId="arabic-series46" />
                   <MovieRow title="عالم الأنمي والكرتون" catId="anime-movies-7" />
                   <MovieRow title="أفلام تركية مميزة" catId="8-aflam3isk" />
                   <MovieRow title="أفلام أجنبية حصرية" catId="all_movies_13" />
                </div>

                {/* Main Grid Feed */}
                <div className="px-4 sm:px-6 md:px-12">
                    <div className="flex flex-row-reverse items-center justify-between mb-8 sm:mb-10 md:mb-12 bg-white/[0.02] p-6 sm:p-8 rounded-[1.5rem] sm:rounded-[2.5rem] border border-white/5 backdrop-blur-xl transition-all hover:bg-white/[0.04]">
                        <div className="text-right">
                            <h2 className="text-white text-2xl sm:text-3xl md:text-4xl font-black italic tracking-tighter flex items-center justify-end">
                                استكشف المزيد <FaFire className="ml-3 sm:ml-4 text-red-600 animate-bounce" />
                            </h2>
                            <p className="text-gray-500 text-[8px] sm:text-[9px] md:text-[10px] font-black uppercase tracking-[0.3em] mt-1 sm:mt-2">تصفح المكتبة الشاملة المحدثة يومياً</p>
                        </div>
                        <div className="hidden sm:flex items-center space-x-reverse space-x-4 bg-black/60 px-4 sm:px-6 py-2 sm:py-3 rounded-xl sm:rounded-2xl border border-white/5 shadow-inner">
                            <span className="text-[10px] sm:text-xs text-gray-400 font-black italic">عرض الكل</span>
                            <FaThLarge className="text-red-600" />
                        </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6 gap-y-10 sm:gap-y-12">
                        {content.map((item) => (
                            <MovieCard key={item.id} movie={item} />
                        ))}
                    </div>

                    <div ref={observerTarget} className="h-40 sm:h-60 flex flex-col items-center justify-center mt-12 sm:mt-20">
                        {loadingMore && (
                            <div className="flex flex-col items-center space-y-4 sm:space-y-6">
                                <div className="w-10 h-10 sm:w-12 sm:h-12 border-[3px] border-red-600 border-t-transparent rounded-full animate-spin"></div>
                                <p className="text-gray-500 font-black italic text-[9px] sm:text-[10px] uppercase tracking-[0.4em] animate-pulse">نحضر لك المزيد من الأفلام...</p>
                            </div>
                        )}
                    </div>
                </div>
            </main>
          </>
      )}

      {/* Decorative Background Glows */}
      <div className="fixed top-0 right-0 w-[500px] h-[500px] bg-red-600/5 blur-[150px] pointer-events-none -z-10 rounded-full"></div>
      <div className="fixed bottom-0 left-0 w-[500px] h-[500px] bg-red-600/5 blur-[150px] pointer-events-none -z-10 rounded-full"></div>
    </div>
  );
};

export default Home;

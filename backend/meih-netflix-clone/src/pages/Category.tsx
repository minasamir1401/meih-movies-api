import { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { fetchByCategory, ContentItem } from '../services/api';
import MovieCard from '../components/MovieCard';
import { FaArrowDown, FaLayerGroup } from 'react-icons/fa';

const categoryNames: Record<string, string> = {
  'all_movies_13': 'أفلام أجنبية',
  'arabic-movies33': 'أفلام عربية',
  'indian-movies9': 'أفلام هندية',
  '6-asian-movies': 'أفلام آسيوي',
  'anime-movies-7': 'أفلام أنمي',
  '7-aflammdblgh': 'أفلام مدبلجة',
  '8-aflam3isk': 'أفلام تركية',
  'arabic-series46': 'مسلسلات عربية',
};

const CategoryPage = () => {
    const { catId } = useParams();
    const [items, setItems] = useState<ContentItem[]>([]);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const observerTarget = useRef(null);

    const categoryTitle = catId ? categoryNames[catId] || 'تصنيف' : 'تصنيف';

    useEffect(() => {
        if (catId) {
            setItems([]);
            setPage(1);
            loadData(catId, 1, true);
        }
    }, [catId]);

    const loadData = async (id: string, p: number, initial = false) => {
        if (initial) setLoading(true);
        else setLoadingMore(true);
        
        try {
            const data = await fetchByCategory(id, p);
            if (initial) setItems(Array.isArray(data) ? data : []);
            else {
                setItems(prev => {
                    const safePrev = Array.isArray(prev) ? prev : [];
                    const safeNew = Array.isArray(data) ? data : [];
                    const existingIds = new Set(safePrev.map(i => i.id));
                    const uniqueNew = safeNew.filter(i => i && i.id && !existingIds.has(i.id));
                    return [...safePrev, ...uniqueNew];
                });
            }
        } catch (e) {
            console.error(e);
        } finally {
            if (initial) setLoading(false);
            else setLoadingMore(false);
        }
    };

    useEffect(() => {
        const observer = new IntersectionObserver(
            entries => {
                if (entries[0].isIntersecting && !loadingMore && !loading && items.length > 0) {
                    const nextPage = page + 1;
                    setPage(nextPage);
                    if (catId) loadData(catId, nextPage);
                }
            },
            { threshold: 1.0 }
        );

        if (observerTarget.current) observer.observe(observerTarget.current);
        return () => observer.disconnect();
    }, [items, loading, loadingMore, page, catId]);

    return (
        <div className="min-h-screen bg-[#0a0a0a] pt-24 sm:pt-32 pb-12 sm:pb-20 px-4 sm:px-6 md:px-12">
            <div className="max-w-[1920px] mx-auto">
                <div className="flex flex-col md:flex-row-reverse items-center justify-between mb-8 sm:mb-16 gap-6 sm:gap-8 bg-white/[0.02] p-6 sm:p-10 rounded-[1.5rem] sm:rounded-[2.5rem] border border-white/5 shadow-3xl backdrop-blur-xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-red-600/5 rounded-full blur-[100px] -z-10"></div>
                    <div className="text-right relative z-10">
                        <h1 className="text-red-600 text-[8px] sm:text-[10px] font-black uppercase tracking-[0.4em] mb-2 sm:mb-4">اكتشف الآن</h1>
                        <h2 className="text-3xl sm:text-4xl md:text-6xl font-black italic text-white leading-none tracking-tighter">{categoryTitle}</h2>
                    </div>
                    <div className="flex items-center space-x-reverse space-x-3 sm:space-x-4 bg-black/60 px-4 sm:px-8 py-3 sm:py-4 rounded-xl sm:rounded-2xl border border-white/5 shadow-inner">
                        <span className="text-gray-500 font-black italic text-[10px] sm:text-xs uppercase tracking-widest whitespace-nowrap">تصفية ذكية</span>
                        <div className="h-4 w-[1px] bg-white/10 mx-1 sm:mx-2"></div>
                        <FaLayerGroup className="text-red-600 text-base sm:text-lg" />
                    </div>
                </div>

                {loading && items.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-32 sm:py-48">
                        <div className="w-12 h-12 sm:w-16 sm:h-16 border-[3px] border-red-600 border-t-transparent rounded-full animate-spin"></div>
                        <p className="mt-6 sm:mt-8 text-gray-500 font-black italic text-[8px] sm:text-[10px] uppercase tracking-[0.4em] animate-pulse">جاري جلب المحتوى...</p>
                    </div>
                ) : (
                    <>
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6 gap-y-10 sm:gap-y-12">
                            {items.map((item) => (
                                <MovieCard key={item.id} movie={item} />
                            ))}
                        </div>

                        <div ref={observerTarget} className="h-40 sm:h-60 flex flex-col items-center justify-center mt-12 sm:mt-20">
                            {loadingMore && (
                                <div className="flex flex-col items-center space-y-4 sm:space-y-6">
                                    <div className="w-10 h-10 sm:w-12 sm:h-12 border-[3px] border-red-600 border-t-transparent rounded-full animate-spin"></div>
                                    <p className="text-gray-500 font-black italic text-[9px] sm:text-[10px] uppercase tracking-[0.5em]">المزيد في الطريق</p>
                                </div>
                            )}
                            {!loadingMore && items.length > 0 && (
                                <div className="opacity-20 hover:opacity-100 transition-opacity">
                                    <FaArrowDown className="text-white text-2xl sm:text-3xl animate-bounce" />
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default CategoryPage;

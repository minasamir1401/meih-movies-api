import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { searchItems, ContentItem } from '../services/api';
import MovieCard from '../components/MovieCard';
import { FaSearch, FaArrowRight } from 'react-icons/fa';

const Search = () => {
    const [searchParams] = useSearchParams();
    const query = searchParams.get('q') || '';
    const navigate = useNavigate();
    const [results, setResults] = useState<ContentItem[]>([]);
    const [loading, setLoading] = useState(false);
    const [filter, setFilter] = useState<'all' | 'movie' | 'series'>('all');

    useEffect(() => {
        if (query) {
            setLoading(true);
            searchItems(query)
                .then(res => setResults(Array.isArray(res) ? res : []))
                .catch(console.error)
                .finally(() => setLoading(false));
        }
    }, [query]);

    const filteredResults = results.filter(item => {
        if (filter === 'all') return true;
        return item.type === filter;
    });

    return (
        <div className="min-h-screen bg-[#0a0a0a] pt-24 sm:pt-32 pb-12 sm:pb-20 px-4 sm:px-6 md:px-12">
            <div className="max-w-[1920px] mx-auto">
                
                {/* Header Section */}
                <div className="flex flex-col md:flex-row-reverse items-center justify-between mb-8 sm:mb-16 gap-6 sm:gap-8 bg-white/[0.02] p-6 sm:p-10 rounded-[1.5rem] sm:rounded-[2.5rem] border border-white/5 shadow-3xl backdrop-blur-xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-red-600/5 rounded-full blur-[100px] -z-10"></div>
                    <div className="text-right relative z-10">
                        <h1 className="text-red-600 text-[8px] sm:text-[10px] font-black uppercase tracking-[0.4em] mb-2 sm:mb-4">نتائج البحث</h1>
                        <h2 className="text-3xl sm:text-4xl md:text-5xl font-black italic text-white leading-none tracking-tighter truncate max-w-[250px] sm:max-w-md">
                            {query ? `"${query}"` : 'ابحث عن فيلم...'}
                        </h2>
                    </div>
                    <div className="flex items-center space-x-reverse space-x-2 sm:space-x-4 relative z-10">
                        {['all', 'movie', 'series'].map((t) => (
                            <button
                                key={t}
                                onClick={() => setFilter(t as any)}
                                className={`px-4 sm:px-6 py-2 sm:py-3 rounded-xl sm:rounded-2xl text-[10px] sm:text-xs font-black italic transition-all border ${
                                    filter === t 
                                        ? 'bg-red-600 border-red-500 text-white shadow-xl shadow-red-600/30' 
                                        : 'bg-black/40 border-white/5 text-gray-500 hover:text-white hover:border-white/20'
                                }`}
                            >
                                {t === 'all' ? 'الكل' : t === 'movie' ? 'أفلام' : 'مسلسلات'}
                            </button>
                        ))}
                    </div>
                </div>

                {loading ? (
                    <div className="flex flex-col items-center justify-center py-32 sm:py-48 text-white">
                        <div className="w-12 h-12 sm:w-16 sm:h-16 border-[3px] border-red-600 border-t-transparent rounded-full animate-spin"></div>
                        <p className="mt-6 sm:mt-8 text-gray-500 font-black italic text-[9px] sm:text-[10px] uppercase tracking-[0.4em] animate-pulse">جاري البحث في الأرشيف...</p>
                    </div>
                ) : filteredResults.length > 0 ? (
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 sm:gap-6 gap-y-10 sm:gap-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        {filteredResults.map((item) => (
                            <MovieCard key={item.id} movie={item} />
                        ))}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center py-32 sm:py-48 text-center px-4">
                        <div className="w-20 h-20 sm:w-24 sm:h-24 bg-red-600/10 rounded-full flex items-center justify-center mb-8 border border-red-600/20">
                            <FaSearch className="text-3xl sm:text-4xl text-red-600" />
                        </div>
                        <h3 className="text-2xl sm:text-3xl font-black italic text-white mb-4 tracking-tighter">لا توجد نتائج</h3>
                        <p className="text-gray-500 font-medium max-w-sm mb-10 text-sm sm:text-base">لم نجد أي مطابقات لبحثك. حاول كتابة كلمات أخرى أو العودة للرئيسية.</p>
                        <button 
                            onClick={() => navigate('/')} 
                            className="group flex flex-row-reverse items-center bg-white text-black font-black italic px-8 sm:px-12 py-3 sm:py-4 rounded-xl sm:rounded-2xl hover:bg-red-600 hover:text-white transition-all shadow-xl shadow-white/5"
                        >
                            <FaArrowRight className="ml-3 group-hover:translate-x-1 transition-transform" /> العودة للرئيسية
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Search;

import { useEffect, useState, useRef } from 'react';
import { fetchByCategory, ContentItem } from '../services/api';
import MovieCard from './MovieCard';
import { FaChevronLeft, FaChevronRight } from 'react-icons/fa';

interface MovieRowProps {
    title: string;
    catId: string;
}

const MovieRow = ({ title, catId }: MovieRowProps) => {
    const [items, setItems] = useState<ContentItem[]>([]);
    const [loading, setLoading] = useState(true);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        fetchByCategory(catId, 1)
            .then(res => setItems(Array.isArray(res) ? res : []))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [catId]);

    const scroll = (direction: 'left' | 'right') => {
        if (scrollRef.current) {
            const { scrollLeft, clientWidth } = scrollRef.current;
            const scrollAmount = clientWidth * 0.8;
            const scrollTo = direction === 'left' ? scrollLeft - scrollAmount : scrollLeft + scrollAmount;
            scrollRef.current.scrollTo({ left: scrollTo, behavior: 'smooth' });
        }
    };

    if (loading && (!items || items.length === 0)) return null;

    return (
        <div className="mb-8 md:mb-16 group relative">
            <div className="flex flex-row-reverse items-center justify-between mb-4 md:mb-6 px-4 md:px-0">
                <h2 className="text-white text-xl md:text-2xl font-black italic tracking-tight border-r-4 border-red-600 pr-3 md:pr-4">
                    {title}
                </h2>
                <button className="text-[9px] md:text-[10px] text-gray-500 font-bold uppercase tracking-widest hover:text-red-500 transition-colors">
                    عرض الكل
                </button>
            </div>

            <div className="relative text-right">
                {/* Scroll Buttons - Hidden on Mobile */}
                <button 
                    onClick={() => scroll('left')}
                    className="absolute left-0 top-0 bottom-4 z-30 bg-black/60 p-4 rounded-r-2xl opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600 hidden md:flex items-center"
                >
                    <FaChevronLeft className="text-white" />
                </button>
                <button 
                    onClick={() => scroll('right')}
                    className="absolute right-0 top-0 bottom-4 z-30 bg-black/60 p-4 rounded-l-2xl opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600 hidden md:flex items-center"
                >
                    <FaChevronRight className="text-white" />
                </button>

                <div 
                    ref={scrollRef}
                    className="flex overflow-x-auto space-x-4 md:space-x-6 space-x-reverse px-4 md:px-0 scrollbar-hide scroll-smooth pb-4"
                >
                    {(Array.isArray(items) ? items : []).map((item) => (
                        <div key={item.id} className="min-w-[140px] sm:min-w-[180px] md:min-w-[220px]">
                            <MovieCard movie={item} />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default MovieRow;

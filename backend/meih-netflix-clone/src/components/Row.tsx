import { useRef } from 'react';
import { FaChevronLeft, FaChevronRight } from 'react-icons/fa';
import MovieCard from './MovieCard';

interface RowProps {
  title: string;
  items: any[];
  isLarge?: boolean;
}

const Row = ({ title, items, isLarge }: RowProps) => {
  const rowRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: 'left' | 'right') => {
    if (rowRef.current) {
      const { scrollLeft, clientWidth } = rowRef.current;
      const scrollTo = direction === 'left' ? scrollLeft - clientWidth : scrollLeft + clientWidth;
      rowRef.current.scrollTo({ left: scrollTo, behavior: 'smooth' });
    }
  };

  return (
    <div className="space-y-6 md:space-y-4 px-6 md:px-12 my-12">
      <div className="flex flex-row-reverse items-center justify-between px-2">
        <h2 className="text-white text-xl md:text-3xl font-black italic tracking-tight">{title}</h2>
        <div className="h-1 flex-1 mx-8 bg-gradient-to-l from-red-600/50 to-transparent rounded-full opacity-30"></div>
      </div>
      
      <div className="group relative">
        <div 
          className="absolute top-0 bottom-0 left-[-20px] z-40 m-auto h-12 w-12 cursor-pointer opacity-0 transition-opacity group-hover:opacity-100 flex items-center justify-center bg-black/80 backdrop-blur-md rounded-full shadow-2xl border border-white/10 text-white" 
          onClick={() => scroll('left')}
        >
            <FaChevronLeft className="text-xl" />
        </div>
        
        <div 
          ref={rowRef}
          className="flex items-center space-x-6 overflow-x-scroll scrollbar-hide scroll-smooth pb-6 pt-4"
        >
          {items.map((item) => (
            <div key={item.id} className="flex-shrink-0 w-[200px] md:w-[240px]">
                <MovieCard 
                  id={item.id} 
                  title={item.title} 
                  poster={item.poster} 
                  duration={item.duration}
                  isLarge={isLarge}
                />
            </div>
          ))}
        </div>

        <div 
          className="absolute top-0 bottom-0 right-[-20px] z-40 m-auto h-12 w-12 cursor-pointer opacity-0 transition-opacity group-hover:opacity-100 flex items-center justify-center bg-black/80 backdrop-blur-md rounded-full shadow-2xl border border-white/10 text-white" 
          onClick={() => scroll('right')}
        >
            <FaChevronRight className="text-xl" />
        </div>
      </div>
    </div>
  );
};

export default Row;

import { useEffect, useState } from 'react';
import MovieCard from '../components/MovieCard';
import { fetchLatest } from '../services/api';

const Series = () => {
    const [series, setSeries] = useState<any[]>([]);
    const [page, setPage] = useState(1);
  
    useEffect(() => {
      fetchLatest(page).then(data => {
          const onlySeries = data.filter((item: any) => item.type === 'series');
          if(page === 1) setSeries(onlySeries);
          else setSeries(prev => [...prev, ...onlySeries]);
      });
    }, [page]);
  
    return (
      <div className="bg-[#141414] min-h-screen pt-24 px-4 md:px-12">
        <h1 className="text-white text-3xl font-bold mb-8">TV Series</h1>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {series.map((s: any, i) => (
               <MovieCard key={`${s.id}-${i}`} movie={s} />
          ))}
        </div>
        <div className="flex justify-center mt-8 pb-8">
            <button 
                onClick={() => setPage(p => p + 1)}
                className="bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700 transition"
            >
                Load More
            </button>
        </div>
      </div>
    );
  };
  
  export default Series;

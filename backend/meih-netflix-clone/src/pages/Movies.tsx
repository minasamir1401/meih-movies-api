import { useEffect, useState } from 'react';
import MovieCard from '../components/MovieCard';
import { fetchLatest } from '../services/api';

const Movies = () => {
  const [movies, setMovies] = useState<any[]>([]);
  const [page, setPage] = useState(1);

  useEffect(() => {
    fetchLatest(page).then(data => {
        const onlyMovies = data.filter((item: any) => item.type === 'movie');
        if(page === 1) setMovies(onlyMovies);
        else setMovies(prev => [...prev, ...onlyMovies]);
    });
  }, [page]);

  return (
    <div className="bg-[#141414] min-h-screen pt-24 px-4 md:px-12">
      <h1 className="text-white text-3xl font-bold mb-8">Movies</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {movies.map((m: any, i) => (
             <MovieCard key={`${m.id}-${i}`} movie={m} />
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

export default Movies;

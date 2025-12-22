import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FaPlay } from 'react-icons/fa';

interface MovieProps {
  id?: string;
  title?: string;
  poster?: string;
  duration?: string;
  movie?: {
    id: string;
    title: string;
    poster: string;
    duration?: string;
  };
  isLarge?: boolean;
}

const MovieCard = ({ id, title, poster, duration, movie, isLarge = false }: MovieProps) => {
  const finalId = id || movie?.id;
  const finalTitle = title || movie?.title;
  const finalPoster = poster || movie?.poster;
  const finalDuration = duration || movie?.duration;

  if (!finalId) return null;

  return (
    <Link to={`/watch/${encodeURIComponent(finalId)}`} className="block group">
      <motion.div 
        className={`relative cursor-pointer transition-all duration-300 ease-in-out rounded-xl md:rounded-2xl overflow-hidden shadow-2xl bg-[#1a1a1a] aspect-[2/3] ${isLarge ? 'md:h-[400px]' : ''}`}
        whileHover={{ y: -8, scale: 1.02 }}
      >
        <img
          src={finalPoster || "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=2070&auto=format&fit=crop"}
          alt={finalTitle}
          className="object-cover w-full h-full transition-transform duration-700 group-hover:scale-110 opacity-90 group-hover:opacity-100"
          loading="lazy"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=2070&auto=format&fit=crop";
          }}
        />
        
        {/* Play Icon Overlay */}
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-300 scale-150 group-hover:scale-100 bg-black/20">
           <div className="bg-red-600/90 p-3 md:p-4 rounded-full shadow-lg shadow-red-600/40">
              <FaPlay className="text-white text-base md:text-xl ml-1" />
           </div>
        </div>

        {/* Duration Badge */}
        {finalDuration && (
          <div className="absolute bottom-2 md:bottom-3 right-2 md:right-3 bg-black/80 backdrop-blur-md px-1.5 md:px-2 py-0.5 md:py-1 rounded text-[8px] md:text-[10px] font-black text-white border border-white/10 z-20">
            {finalDuration}
          </div>
        )}

        {/* Dubbed Badge */}
        {finalTitle?.includes('مدبلج') && (
           <div className="absolute top-2 md:top-3 left-2 md:left-3 bg-red-600 px-1.5 md:px-2 py-0.5 rounded text-[8px] md:text-[9px] font-black text-white uppercase z-20">
             مدبلج
           </div>
        )}

        {/* Bottom Shade */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60 group-hover:opacity-90 transition-opacity"></div>
      </motion.div>
      
      {/* Arabic Title Below */}
      <div className="mt-2 md:mt-3 px-1">
        <p className="text-white text-xs md:text-sm font-bold text-right leading-tight group-hover:text-red-500 transition-colors line-clamp-2 dir-rtl">
          {finalTitle}
        </p>
      </div>
    </Link>
  );
};

export default MovieCard;

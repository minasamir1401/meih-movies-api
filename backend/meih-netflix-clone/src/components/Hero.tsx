import { useNavigate } from 'react-router-dom';
import { FaPlay, FaInfoCircle, FaStar } from 'react-icons/fa';

interface HeroProps {
  movie: any;
}

const Hero = ({ movie }: HeroProps) => {
  const navigate = useNavigate();

  if (!movie) return (
    <div className="h-[60vh] md:h-[80vh] bg-[#0a0a0a] flex items-center justify-center">
        <div className="w-12 h-12 border-2 border-red-600 border-t-transparent rounded-full animate-spin"></div>
    </div>
  );

  return (
    <div className="relative h-[70vh] md:h-[85vh] w-full text-white overflow-hidden">
      {/* Background Image with Parallax-like feel */}
      <div className="absolute inset-0">
          <img 
             src={movie.poster} 
             alt={movie.title} 
             className="w-full h-full object-cover object-center scale-110 md:scale-105"
             onError={(e) => {
               const target = e.target as HTMLImageElement;
               target.src = "https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=2070&auto=format&fit=crop";
             }}
          />
          {/* Gradients to blend */}
          <div className="absolute inset-0 bg-gradient-to-r from-[#0a0a0a] via-[#0a0a0a]/40 to-transparent z-10 hidden md:block" />
          <div className="absolute inset-0 bg-black/50 md:bg-black/40 z-[5]" />
          <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0a] via-[#0a0a0a]/20 to-transparent z-10" />
      </div>

      <div className="absolute bottom-[15%] md:top-[35%] right-4 sm:right-8 md:right-16 lg:right-24 z-20 max-w-2xl text-right">
         <div className="flex flex-row-reverse items-center space-x-reverse space-x-3 mb-4 md:mb-6">
            <span className="bg-red-600 text-[8px] md:text-[10px] font-black italic px-2 md:px-3 py-1 rounded-md uppercase tracking-widest">عرض حصري</span>
            <div className="hidden sm:flex items-center space-x-reverse space-x-1 text-yellow-500 text-xs">
                <FaStar /><FaStar /><FaStar /><FaStar /><FaStar className="text-gray-600" />
            </div>
         </div>
         
         <h1 className="text-3xl sm:text-4xl md:text-5xl lg:text-7xl font-black mb-4 md:mb-6 drop-shadow-2xl italic tracking-tighter leading-tight">{movie.title}</h1>
         
         <p className="text-gray-300 text-sm md:text-lg lg:text-xl mb-6 md:mb-10 line-clamp-2 md:line-clamp-3 drop-shadow-lg font-medium leading-relaxed dir-rtl max-w-xl">
           {movie.description || "عمل سينمائي رائع يستحق المشاهدة، استمتع بأفضل تجربة ترفيهية متوفرة الآن بجودة عالية وحصرياً على منصة LMINA."}
         </p>

         <div className="flex flex-row-reverse items-center gap-4 md:gap-6">
            <button 
              onClick={() => navigate(`/watch/${movie.id}`)}
              className="group flex flex-row-reverse items-center bg-white text-black px-6 md:px-10 py-3 md:py-4 rounded-xl md:rounded-2xl font-black italic hover:bg-red-600 hover:text-white transition-all duration-300 transform hover:scale-105 active:scale-95 shadow-xl shadow-white/5 text-xs md:text-base"
            >
              <FaPlay className="ml-2 md:ml-3 group-hover:animate-pulse" /> شاهد الآن
            </button>
            <button 
              onClick={() => navigate(`/watch/${movie.id}`)}
              className="flex flex-row-reverse items-center bg-white/10 backdrop-blur-md text-white border border-white/10 px-6 md:px-10 py-3 md:py-4 rounded-xl md:rounded-2xl font-black italic hover:bg-white/20 transition-all duration-300 text-xs md:text-base"
            >
              <FaInfoCircle className="ml-2 md:ml-3 text-red-600" /> تفاصيل
            </button>
         </div>
      </div>

      {/* Hero Shade for content below */}
      <div className="absolute bottom-0 w-full h-32 bg-gradient-to-t from-[#0a0a0a] to-transparent z-10" />
    </div>
  );
};

export default Hero;

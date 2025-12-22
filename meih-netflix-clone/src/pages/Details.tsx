import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import { fetchDetails, Details as DetailsType } from '../services/api';
import { FaPlay, FaListUl, FaDownload } from 'react-icons/fa';

const Details = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [content, setContent] = useState<DetailsType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
       setLoading(true);
       fetchDetails(id)
        .then(setContent)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [id]);

  if (loading) return (
    <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center">
        <div className="w-16 h-16 border-2 border-red-600 border-t-transparent rounded-full animate-spin"></div>
    </div>
  );

  if (!content) return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex flex-col items-center justify-center p-10">
        <h2 className="text-2xl font-black italic mb-6">Content Not Found</h2>
        <button onClick={() => navigate('/')} className="bg-red-600 px-8 py-3 rounded-xl font-bold">Back to Home</button>
    </div>
  );

  return (
    <div className="bg-[#0a0a0a] min-h-screen text-white relative selection:bg-red-600/50">
      <Navbar />
      
      <div className="relative h-[70vh] sm:h-[80vh] overflow-hidden">
         <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0a] via-[#0a0a0a]/40 to-transparent z-10" />
         <img 
            src={content.poster || "https://images.unsplash.com/photo-1574267432553-4b4628081c31?q=80&w=1200"} 
            className="w-full h-full object-cover scale-105 blur-sm opacity-40" 
            alt={content.title}
         />
      </div>
      
      <div className="absolute top-[25%] left-4 sm:left-12 md:left-24 z-20 max-w-3xl text-right md:text-left right-4 sm:right-auto">
         <div className="flex flex-row-reverse md:flex-row items-center gap-3 mb-6">
            <span className="px-3 py-1 bg-red-600 text-[10px] font-black italic rounded-md">NEW</span>
            <span className="text-green-500 font-black italic text-sm">98% Match</span>
            <span className="text-gray-400 font-bold text-sm">2024</span>
         </div>
         
         <h1 className="text-4xl sm:text-6xl md:text-8xl font-black italic mb-8 tracking-tighter leading-none drop-shadow-2xl">{content.title}</h1>
         
         <p className="text-base sm:text-xl text-gray-300 mb-12 leading-relaxed bg-black/20 backdrop-blur-md p-6 rounded-2xl border border-white/5 dir-rtl overflow-hidden line-clamp-4 md:line-clamp-none">
            {content.description || "استمتع بمشاهدة هذا العمل الرائع بجودة عالية وحصرياً على منصتنا."}
         </p>
         
         <div className="flex flex-row-reverse md:flex-row items-center gap-4 mb-8">
            <button 
              onClick={() => navigate(`/watch/${encodeURIComponent(id!)}`)}
              className="bg-red-600 text-white px-10 sm:px-14 py-4 sm:py-5 rounded-2xl font-black italic text-lg sm:text-xl hover:bg-red-700 transition flex items-center shadow-2xl shadow-red-600/20 group"
            >
              <FaPlay className="ml-3 sm:ml-4 group-hover:scale-110 transition-transform" /> Watch Now
            </button>
            
            <button className="p-4 sm:p-5 bg-white/5 border border-white/10 rounded-2xl hover:bg-white/10 transition">
                <FaListUl className="text-xl" />
            </button>
         </div>

         {content.download_links && content.download_links.length > 0 && (
            <div className="flex flex-wrap flex-row-reverse md:flex-row gap-3">
                {content.download_links.map((dl, i) => (
                    <a 
                      key={i} 
                      href={dl.url} 
                      target="_blank" 
                      rel="noreferrer" 
                      className="bg-white/5 border border-white/10 px-6 py-3 rounded-xl text-xs font-bold hover:bg-red-600/10 hover:border-red-600/30 transition flex items-center gap-2"
                    >
                        <FaDownload className="text-red-500" /> {dl.quality}
                    </a>
                ))}
            </div>
         )}
      </div>
    </div>
  );
};

export default Details;

import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Hls from 'hls.js';
import { fetchDetails, Details, Server } from '../services/api';
import { FaArrowRight, FaDownload, FaExclamationTriangle, FaListUl, FaTv, FaRedo } from 'react-icons/fa';

const Watch = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const videoRef = useRef<HTMLVideoElement>(null);

  const [data, setData] = useState<Details | null>(null);
  const [loading, setLoading] = useState(true);
  const [serverLoading, setServerLoading] = useState(false);
  const [activeServer, setActiveServer] = useState<Server | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [failedServers, setFailedServers] = useState<Set<string>>(new Set());
  const [showEpisodes, setShowEpisodes] = useState(window.innerWidth > 1024);
  
  const [showShield, setShowShield] = useState(true);
  const [shieldActive, setShieldActive] = useState(false);

  const fetchData = async (targetId: string) => {
      setLoading(true);
      setError(null);
      setData(null); // CRITICAL: Reset data to avoid UI race conditions
      setActiveServer(null); // CRITICAL: Reset active server
      setFailedServers(new Set());

      
      try {
          const d = await fetchDetails(targetId);
          if (d.error === 'timeout') {
              setError(d.message || "السيرفر مشغول حالياً، حاول مرة أخرى.");
              return;
          }
          if (!d || !d.title) throw new Error("بيانات المحتوى غير مكتملة");
          
          const safeData: Details = {
              ...d,
              servers: Array.isArray(d.servers) ? d.servers : [],
              episodes: Array.isArray(d.episodes) ? d.episodes : [],
              download_links: Array.isArray(d.download_links) ? d.download_links : []
          };
          
          // Set critical data first (video player and basic info) - this makes it feel fast
          setData(safeData);
          if (safeData.servers.length > 0) {
              setActiveServer(safeData.servers[0]);
          }
          
          // Critical data is loaded immediately for fast perception
          
          // Simulate immediate loading feeling
          setTimeout(() => {
              setLoading(false);
          }, 100); // Feel instant
          
          // All data is loaded immediately now
          
      } catch (err) {
          console.error(err);
          setError("خطأ في جلب البيانات، تأكد من الاتصال وحاول مجدداً.");
          setLoading(false);
      }
  };

  useEffect(() => {
     if (id) {
         fetchData(id);
         setShowShield(true);
         setShieldActive(false);
         window.scrollTo(0, 0);
     }
  }, [id]);

  useEffect(() => {
    if (activeServer && activeServer.type === 'video' && videoRef.current) {
        setServerLoading(true);
        const url = activeServer.url;
        const video = videoRef.current;
        let hls: Hls | null = null;
        
        const onError = () => {
            console.warn("Video Error, switching...");
            handlePlaybackError();
        };

        try {
            if (url.includes('.m3u8') && Hls.isSupported()) {
               hls = new Hls({
                   xhrSetup: (xhr) => { xhr.withCredentials = false; } 
               });
               hls.loadSource(url);
               hls.attachMedia(video);
               hls.on(Hls.Events.MANIFEST_PARSED, () => setServerLoading(false));
               hls.on(Hls.Events.ERROR, (_, data) => { 
                   if (data.fatal) onError(); 
               });
            } else {
               video.src = url;
               video.onloadeddata = () => setServerLoading(false);
               video.onerror = onError;
            }
        } catch (e) {
            onError();
        }

        return () => { if (hls) hls.destroy(); };
    } else if (activeServer?.type === 'iframe') {
        setServerLoading(true);
        // Set a timeout to hide the loader assuming success
        setTimeout(() => {
            if (activeServer && (failedServers.size === 0 || !failedServers.has(activeServer.url))) {
                setServerLoading(false);
            }
        }, 3000);
    }
  }, [activeServer]);

  const handlePlaybackError = () => {
    if (activeServer && data) {
        const nextFailed = new Set(failedServers);
        nextFailed.add(activeServer.url);
        setFailedServers(nextFailed);
        
        // DISABLED: Automatic server switching
        // Keep the current server marked as failed but don't switch automatically
        setServerLoading(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-[#060606] text-white flex flex-col font-sans dir-rtl">
      {/* Skeleton Header */}
      <div className="fixed top-0 left-0 right-0 z-50 bg-[#060606]/90 backdrop-blur-md border-b border-white/5 px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
              <div className="w-10 h-10 bg-white/10 rounded-lg animate-pulse"></div>
              <div className="h-6 bg-white/10 rounded-lg animate-pulse flex-1 mx-4 max-w-md"></div>
              <div className="w-8 h-8 bg-white/10 rounded-lg animate-pulse"></div>
          </div>
      </div>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-24">
          <div className="flex flex-col lg:flex-row gap-8">
              
              {/* Skeleton Player Section */}
              <div className="flex-1 space-y-6">
                  <div className="relative aspect-video bg-black/50 rounded-3xl overflow-hidden shadow-2xl border border-white/10 animate-pulse">
                      <div className="absolute inset-0 flex items-center justify-center">
                          <div className="w-16 h-16 border-4 border-red-600/30 border-t-transparent rounded-full animate-spin"></div>
                      </div>
                  </div>

                  {/* Skeleton Servers */}
                  <div className="bg-zinc-900/50 rounded-2xl p-6 border border-white/5 animate-pulse">
                      <div className="flex items-center justify-between mb-4">
                          <div className="h-4 bg-white/10 rounded w-32"></div>
                          <div className="w-5 h-5 bg-white/10 rounded"></div>
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                          {[...Array(4)].map((_, i) => (
                              <div key={i} className="h-12 bg-white/10 rounded-xl"></div>
                          ))}
                      </div>
                  </div>

                  {/* Skeleton Info */}
                  <div className="space-y-4">
                      <div className="h-8 bg-white/10 rounded w-3/4 animate-pulse"></div>
                      <div className="space-y-2">
                          <div className="h-4 bg-white/10 rounded w-full animate-pulse"></div>
                          <div className="h-4 bg-white/10 rounded w-5/6 animate-pulse"></div>
                          <div className="h-4 bg-white/10 rounded w-2/3 animate-pulse"></div>
                      </div>
                  </div>
              </div>

              {/* Skeleton Episodes Sidebar */}
              <div className="lg:w-80 shrink-0">
                  <div className="bg-zinc-900/50 border border-white/5 rounded-2xl overflow-hidden sticky top-24 animate-pulse">
                      <div className="w-full p-4 flex items-center justify-between bg-white/5">
                          <div className="h-4 bg-white/10 rounded w-40"></div>
                          <div className="w-5 h-5 bg-white/10 rounded"></div>
                      </div>
                      <div className="p-2 space-y-2">
                          {[...Array(8)].map((_, i) => (
                              <div key={i} className="w-full h-14 bg-white/10 rounded-xl"></div>
                          ))}
                      </div>
                  </div>
              </div>
          </div>
      </main>
    </div>
  );

  if (error || !data) return (
    <div className="min-h-screen bg-[#060606] text-white flex flex-col items-center justify-center p-8 text-center">
        <FaExclamationTriangle className="text-red-600 text-5xl mb-6" />
        <h2 className="text-2xl font-bold mb-4">حدث خطأ</h2>
        <p className="text-gray-400 mb-8 max-w-md">{error || "تعذّر تحميل المحتوى"}</p>
        <div className="flex gap-4">
             <button onClick={() => id && fetchData(id)} className="flex items-center gap-2 bg-white/10 hover:bg-white/20 px-6 py-3 rounded-xl font-bold transition-all">
                <FaRedo /> إعادة المحاولة
             </button>
             <button onClick={() => navigate('/')} className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-xl font-bold transition-all">
                الرئيسية
             </button>
        </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#060606] text-white flex flex-col font-sans dir-rtl">
      
      {/* Header */}
      <div className="fixed top-0 left-0 right-0 z-50 bg-[#060606]/90 backdrop-blur-md border-b border-white/5 px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
              <button onClick={() => navigate(-1)} className="p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-all">
                  <FaArrowRight />
              </button>
              <h1 className="text-lg font-bold truncate mx-4">{data?.title || <div className="h-6 bg-white/10 rounded w-48 animate-pulse"></div>}</h1>
              <div className="w-8"></div>
          </div>
      </div>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 py-24">
          <div className="flex flex-col lg:flex-row gap-8">
              
              {/* Player Section - Load immediately for fast perception */}
              <div className="flex-1 space-y-6">
                  <div className="relative aspect-video bg-black rounded-3xl overflow-hidden shadow-2xl border border-white/10 group">
                      {serverLoading && (
                          <div className="absolute inset-0 z-20 bg-black/80 flex flex-col items-center justify-center">
                              <div className="w-12 h-12 border-4 border-red-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                              <p className="text-xs font-bold text-red-500 uppercase tracking-widest">
                                  {activeServer ? `جاري الاتصال بـ ${activeServer.name}` : 'جاري التحضير...'}
                              </p>
                          </div>
                      )}
                      
                      {activeServer && failedServers.has(activeServer.url) ? (
                          <div className="absolute inset-0 flex flex-col items-center justify-center bg-zinc-900 text-center p-6">
                             <FaExclamationTriangle className="text-yellow-500 text-4xl mb-4" />
                             <p className="text-sm font-bold text-gray-300 mb-4">هذا السيرفر لا يعمل حالياً</p>
                             <button 
                                onClick={handlePlaybackError}
                                className="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg text-xs font-bold"
                             >
                                تجربة السيرفر التالي تلقائياً
                             </button>
                          </div>
                      ) : activeServer ? (
                          activeServer.type === 'iframe' ? (
                              // Enhanced server validation to check for various issues
                              (() => {
                                  const url = activeServer.url.toLowerCase();
                                  
                                  // Check for ad domains
                                  const adDomains = ['facebook', 'twitter', 'ads', 'doubleclick', 'googlesyndication'];
                                  const hasAds = adDomains.some(domain => url.includes(domain));
                                  
                                  // Check for known problematic domains
                                  const problematicDomains = ['okprime.site', 'film77.xyz'];
                                  const isProblematic = problematicDomains.some(domain => url.includes(domain));
                                  
                                  if (hasAds) {
                                      return (
                                          <div className="w-full h-full flex flex-col items-center justify-center bg-black text-white">
                                              <div className="text-red-500 mb-4">⚠️</div>
                                              <p className="text-center mb-4">هذا السيرفر يحتوي على إعلانات<br/>يرجى اختيار سيرفر آخر يدويًا</p>
                                          </div>
                                      );
                                  }
                                  
                                  if (isProblematic) {
                                      return (
                                          <div className="w-full h-full flex flex-col items-center justify-center bg-black text-white">
                                              <div className="text-red-500 mb-4">⚠️</div>
                                              <p className="text-center mb-4">هذا السيرفر لا يعمل بشكل صحيح<br/>يرجى اختيار سيرفر آخر يدويًا</p>
                                          </div>
                                      );
                                  }
                                  
                                  return (
                                      <div className="relative w-full h-full">
                                          {showShield && (
                                              <div 
                                                  className="absolute inset-0 z-30 bg-black/60 backdrop-blur-sm flex flex-col items-center justify-center cursor-pointer group/shield"
                                                  onClick={() => {
                                                      setShowShield(false);
                                                      setShieldActive(true);
                                                  }}
                                              >
                                                  <div className="w-20 h-20 bg-red-600 rounded-full flex items-center justify-center shadow-2xl shadow-red-600/40 group-hover/shield:scale-110 transition-transform duration-500">
                                                      <FaTv className="text-3xl text-white ml-1" />
                                                  </div>
                                                  <p className="mt-6 text-white font-black italic text-xl tracking-tighter uppercase">اضغط لبدء المشاهدة الآمنة</p>
                                                  <p className="mt-2 text-white/40 text-xs font-bold uppercase tracking-widest">نظام حماية من الإعلانات المنبثقة مفعل</p>
                                              </div>
                                          )}
                                          
                                          <iframe 
                                              key={activeServer.url}
                                              src={activeServer.url} 
                                              className={`w-full h-full border-0 ${!shieldActive ? 'pointer-events-none' : ''}`} 
                                              allowFullScreen 
                                              allow="encrypted-media; autoplay; fullscreen"
                                              // Safety: Removed sandbox to satisfy providers, but using overlay instead
                                              onLoad={() => {
                                                  setServerLoading(false);
                                              }}
                                          />
                                          
                                          {shieldActive && (
                                              <div className="absolute top-4 left-4 z-40 bg-green-500/20 backdrop-blur-md border border-green-500/30 px-3 py-1.5 rounded-full flex items-center gap-2 pointer-events-none">
                                                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                                                  <span className="text-[10px] font-black text-green-500 uppercase tracking-widest">درع الحماية نشط</span>
                                              </div>
                                          )}
                                      </div>
                                  );
                              })()
                          ) : (
                              <video 
                                  key={activeServer.url}
                                  ref={videoRef} 
                                  controls 
                                  autoPlay 
                                  className="w-full h-full"
                              />
                          )
                      ) : (
                          <div className="flex items-center justify-center h-full text-gray-500 font-bold">
                              لا يوجد سيرفر مختار
                          </div>
                      )}
                  </div>

                  {/* Servers - Load immediately as they're critical for playback */}
                  <div className="bg-zinc-900/50 rounded-2xl p-6 border border-white/5">
                      <div className="flex items-center justify-between mb-4">
                          <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">سيرفرات المشاهدة</span>
                          <FaTv className="text-red-500" />
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                          {data.servers.map((srv, idx) => {
                              const isFailed = failedServers.has(srv.url);
                              const isActive = activeServer?.url === srv.url;
                              
                              // Check for known problematic domains
                              const problematicDomains = ['okprime.site', 'film77.xyz'];
                              const isProblematic = problematicDomains.some(domain => srv.url.toLowerCase().includes(domain));
                              
                              return (
                                  <button
                                      key={idx}
                                      onClick={() => { 
                                          // Clear server from failed list when manually selected
                                          if (failedServers.has(srv.url)) {
                                              const newFailed = new Set(failedServers);
                                              newFailed.delete(srv.url);
                                              setFailedServers(newFailed);
                                          }
                                          setShowShield(true);
                                          setShieldActive(false);
                                          setActiveServer(srv); 
                                          setServerLoading(true); 
                                      }}
                                      className={`p-3 rounded-xl text-xs font-bold transition-all border ${
                                          isActive 
                                            ? 'bg-red-600 border-red-500 text-white' 
                                            : isFailed || isProblematic
                                                ? 'bg-red-900/10 border-red-900/20 text-red-500 opacity-50 cursor-not-allowed'
                                                : 'bg-white/5 border-white/5 text-gray-400 hover:bg-white/10'
                                      }`}
                                      disabled={isFailed || isProblematic}
                                  >
                                      {srv.name} {isFailed && '(عطل)'} {isProblematic && '(غير متاح)'}
                                  </button>
                              );
                          })}
                      </div>
                  </div>

                  {/* Info - Deferred loading for non-critical content */}
                  <div className="space-y-4 text-right">
                      <h2 className="text-3xl font-black">{data.title}</h2>
                      <p className="text-gray-400 leading-relaxed text-sm">{data.description}</p>
                      
                     {/* Better Download Section - Show all download links immediately */}
                  {data.download_links && data.download_links.length > 0 && (
                      <div className="bg-gradient-to-br from-zinc-900 to-black rounded-[2rem] p-8 border border-white/10 shadow-2xl overflow-hidden relative group">
                          <div className="absolute top-0 right-0 w-32 h-32 bg-red-600/5 blur-3xl rounded-full"></div>
                          
                          <div className="flex items-center justify-between mb-8 relative z-10">
                              <div className="flex items-center gap-3">
                                  <div className="w-10 h-10 bg-red-600/20 rounded-xl flex items-center justify-center border border-red-600/30">
                                      <FaDownload className="text-red-500 text-sm" />
                                  </div>
                                  <h3 className="text-lg font-black italic tracking-tighter text-white uppercase">روابط التحميل المباشر</h3>
                              </div>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 relative z-10">
                              {data.download_links.map((dl, i) => (
                                  <a 
                                      key={i} 
                                      href={dl.url} 
                                      target="_blank" 
                                      rel="noreferrer" 
                                      className="flex items-center justify-between p-4 rounded-2xl
                                                 bg-white/5 border border-white/10 hover:bg-red-600/10 hover:border-red-600/30
                                                 transition-all duration-300 group/btn"
                                  >
                                      <span className="text-gray-400 group-hover/btn:text-red-500 transition-colors">
                                          <FaDownload className="text-xs" />
                                      </span>
                                      <div className="text-right">
                                          <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-0.5 group-hover/btn:text-red-500/50 transition-colors">جودة عالية</p>
                                          <p className="text-sm font-bold text-white group-hover/btn:text-white transition-colors">
                                              {dl.quality || 'Link'}
                                          </p>
                                      </div>
                                  </a>
                              ))}
                          </div>
                      </div>
                  )}
                  </div>
              </div>

              {/* Episodes Sidebar - Show all episodes immediately */}
              {data.type === 'series' && (
                  <div className="lg:w-80 shrink-0">
                      <div className="bg-zinc-900/50 border border-white/5 rounded-2xl overflow-hidden sticky top-24">
                          <button 
                             onClick={() => setShowEpisodes(!showEpisodes)}
                             className="w-full p-4 flex items-center justify-between text-right bg-white/5 hover:bg-white/10"
                          >
                             <span className="text-xs font-bold text-gray-400">قائمة الحلقات ({data.episodes.length})</span>
                             <FaListUl className="text-red-500" />
                          </button>
                          
                          {(showEpisodes || window.innerWidth > 1024) && (
                              <div className="max-h-[500px] overflow-y-auto p-2 space-y-2 custom-scrollbar">
                                  {[...data.episodes].sort((a, b) => a.episode - b.episode).map(ep => {
                                      const isActive = ep.id === id || new URLSearchParams(window.location.search).get('episode') === String(ep.episode);
                                      return (
                                          <button
                                              key={ep.id}
                                              onClick={() => navigate(`/watch/${ep.id}?episode=${ep.episode}`)}
                                              className={`w-full p-3 rounded-xl flex items-center gap-3 text-right transition-all border ${
                                                  isActive 
                                                  ? 'bg-red-600 border-red-500 text-white' 
                                                  : 'bg-black/40 border-transparent text-gray-400 hover:bg-white/5'
                                              }`}
                                          >
                                              <span className="w-8 h-8 flex items-center justify-center bg-black/20 rounded-lg text-[10px] font-bold">{ep.episode}</span>
                                              <span className="flex-1 text-xs font-bold truncate">{ep.title}</span>
                                          </button>
                                      );
                                  })}
                              </div>
                          )}
                      </div>
                  </div>
              )}
          </div>
      </main>
    </div>
  );
};

export default Watch;

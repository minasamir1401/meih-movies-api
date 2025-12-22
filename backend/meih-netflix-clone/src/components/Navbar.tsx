import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FaSearch,
  FaUser,
  FaBars,
  FaTimes,
  FaFilm,
  FaTv,
  FaHome
} from 'react-icons/fa';

/* =======================
   CATEGORIES (IMPORTANT)
======================= */
const categories = [
  { name: 'الرئيسية', path: '/', icon: <FaHome /> },
  { name: 'أفلام أجنبية', path: '/category/all_movies_13', icon: <FaFilm /> },
  { name: 'أفلام عربية', path: '/category/arabic-movies33', icon: <FaFilm /> },
  { name: 'أفلام هندية', path: '/category/indian-movies9', icon: <FaFilm /> },
  { name: 'أفلام آسيوي', path: '/category/6-asian-movies', icon: <FaFilm /> },
  { name: 'أفلام أنمي', path: '/category/anime-movies-7', icon: <FaFilm /> },
  { name: 'أفلام مدبلجة', path: '/category/7-aflammdblgh', icon: <FaFilm /> },
  { name: 'أفلام تركية', path: '/category/8-aflam3isk', icon: <FaFilm /> },
  { name: 'مسلسلات عربية', path: '/category/arabic-series46', icon: <FaTv /> },
];

const Navbar = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isSearchActive, setIsSearchActive] = useState(false);
  const [searchInput, setSearchInput] = useState('');
  const navigate = useNavigate();

  /* =======================
     SCROLL EFFECT
  ======================= */
  useEffect(() => {
    const onScroll = () => setIsScrolled(window.scrollY > 10);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  /* =======================
     SEARCH
  ======================= */
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchInput.trim()) return;
    navigate(`/search?q=${searchInput}`);
    setIsSearchActive(false);
    setIsMenuOpen(false);
  };

  return (
    <>
      {/* =======================
          NAVBAR
      ======================= */}
      <nav
        className={`
          fixed top-0 left-0 right-0 h-[72px]
          z-[9999] transition-all duration-300
          ${isScrolled || isMenuOpen
            ? 'bg-black/95 backdrop-blur-xl shadow-2xl'
            : 'bg-gradient-to-b from-black to-transparent'}
        `}
      >
        <div className="max-w-[1920px] mx-auto h-full px-4 md:px-10 flex items-center justify-between">

          {/* MOBILE MENU BUTTON */}
          <button
            onClick={() => setIsMenuOpen(prev => !prev)}
            className="xl:hidden text-white text-2xl p-2 rounded-xl
                       border border-white/10 hover:bg-white/10"
          >
            {isMenuOpen ? <FaTimes /> : <FaBars />}
          </button>

          {/* SEARCH + USER */}
          <div className="flex items-center gap-4 relative">
            <form onSubmit={handleSearch} className="relative">
              <input
                type="text"
                value={searchInput}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchInput(e.target.value)}
                placeholder="بحث..."
                className={`
                  bg-white/10 border border-white/20 text-sm p-3 rounded-2xl
                  placeholder-gray-400 focus:outline-none focus:border-red-600
                  transition-all duration-300 text-right dir-rtl text-white
                  ${isSearchActive
                    ? 'w-44 sm:w-64 opacity-100 pr-12 pl-10'
                    : 'w-0 opacity-0 pointer-events-none'}
                `}
              />

              <button
                type="button"
                onClick={() => setIsSearchActive(true)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-300"
              >
                <FaSearch />
              </button>

              {searchInput && (
                <button
                  type="button"
                  onClick={() => setSearchInput('')}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-300"
                >
                  <FaTimes />
                </button>
              )}
            </form>

            <div className="hidden sm:flex w-10 h-10 bg-gradient-to-br
                            from-red-600 to-red-800 rounded-xl
                            items-center justify-center shadow-lg">
              <FaUser className="text-white text-sm" />
            </div>
          </div>

          {/* LOGO */}
          <Link to="/" className="flex items-center gap-2">
            <img
              src="/favicon.png"
              alt="LMINA"
              className="h-8 sm:h-10 object-contain"
            />
          </Link>
        </div>

        {/* DESKTOP MENU */}
        <div className="hidden xl:block">
          <ul className="flex flex-row-reverse justify-center gap-8
                         text-[13px] font-black italic uppercase text-gray-300">
            {categories.map(cat => (
              <li key={cat.path}>
                <Link
                  to={cat.path}
                  className="relative hover:text-white py-2 group"
                >
                  {cat.name}
                  <span className="absolute bottom-0 left-0 w-0 h-[2px]
                                   bg-red-600 transition-all group-hover:w-full" />
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </nav>

      {/* =======================
          MOBILE MENU
      ======================= */}
      {isMenuOpen && (
        <div className="xl:hidden fixed inset-0 top-[72px]
                        bg-black z-[9998] overflow-y-auto">
          <div className="p-6 space-y-4 pb-32">
            {categories.map(cat => (
              <Link
                key={cat.path}
                to={cat.path}
                onClick={() => setIsMenuOpen(false)}
                className="flex flex-row-reverse items-center justify-between
                           p-5 rounded-2xl
                           bg-white/10 border border-white/10
                           text-white"
              >
                <span className="text-lg font-bold">
                  {cat.name}
                </span>
                <span className="text-red-500 text-xl">
                  {cat.icon}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </>
  );
};

export default Navbar;

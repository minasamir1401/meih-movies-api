import yt_dlp
import logging
import asyncio

logger = logging.getLogger(__name__)

class VideoDownloader:
    def __init__(self):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    async def get_info(self, url: str):
        # 1. Handle Local Watch/Details Links or Direct Larooza Links
        is_larooza = any(x in url for x in ['larozavideo', 'larooza', 'laroza'])
        if "/watch/" in url or "/details/" in url or is_larooza:
            try:
                from scraper.engine import scraper
                import base64
                
                target_url = url
                if "/watch/" in url or "/details/" in url:
                    id_part = url.split("/")[-1].split("?")[0]
                    if not id_part.startswith("http"):
                        target_url = base64.urlsafe_b64decode(id_part).decode()
                
                # If it's a Larooza link (direct or decoded), use scraper
                if any(x in target_url for x in ['larozavideo', 'larooza', 'laroza']):
                    logger.info(f"Routing Larooza link to scraper: {target_url}")
                    # Normalize: downloader works better with the video.php page
                    target_url = target_url.replace('play.php', 'video.php').replace('download.php', 'video.php')
                    
                    safe_id = base64.urlsafe_b64encode(target_url.encode()).decode()
                    data = await scraper.fetch_details(safe_id)
                    
                    if data and data.get('download_links'):
                        formats = []
                        for dl in data['download_links']:
                            formats.append({
                                'ext': 'mp4',
                                'resolution': dl['quality'],
                                'url': dl['url'],
                                'type': 'video'
                            })
                        return {
                            'title': data.get('title'),
                            'thumbnail': data.get('poster'),
                            'duration': 0,
                            'uploader': 'Larooza',
                            'source': 'Larooza',
                            'formats': formats
                        }
                    elif data:
                         return {"error": "لم يتم العثور على روابط تحميل لهذا الفيديو (ربما محمي أو غير متاح حالياً)."}
            except Exception as e:
                logger.error(f"Larooza-specific extraction failed: {e}")

        # 2. Universal yt-dlp Path (YouTube, TikTok, etc.)
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, lambda: self._extract(url))
            
            if not info:
                return {"error": "Could not extract info"}
            
            # Live stream check
            if info.get('is_live') or info.get('live_status') == 'is_upcoming':
                return {"error": "هذا الفيديو لم يبدأ عرضه بعد أو هو بث مباشر حالياً."}

            formats = []
            seen_resolutions = set()
            
            # Extract usable formats
            raw_formats = info.get('formats', [])
            if not raw_formats and info.get('url'):
                raw_formats = [info] # For direct links

            for f in raw_formats:
                if f.get('vcodec') != 'none' or f.get('acodec') != 'none':
                    ext = f.get('ext', 'mp4')
                    res = f.get('resolution') or f.get('format_note') or f.get('height') or 'Unknown'
                    f_url = f.get('url')
                    if not f_url: continue

                    # Clean resolution label
                    if isinstance(res, int): res = f"{res}p"
                    
                    if res in seen_resolutions and f.get('vcodec') != 'none': continue
                    if f.get('vcodec') != 'none': seen_resolutions.add(res)

                    formats.append({
                        'id': f.get('format_id'),
                        'ext': ext,
                        'resolution': res,
                        'filesize': f.get('filesize') or f.get('filesize_approx'),
                        'url': f_url,
                        'type': 'video' if f.get('vcodec') != 'none' else 'audio'
                    })

            return {
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'source': info.get('extractor_key'),
                'formats': formats[::-1]
            }
        except Exception as e:
            logger.error(f"Universal Downloader error: {e}")
            return {"error": f"فشل في جلب البيانات: {str(e)}"}

    def _extract(self, url):
        opts = self.ydl_opts.copy()
        # Add extra robustness for TikTok and newer sites
        opts.update({
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'socket_timeout': 15,
        })
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

downloader = VideoDownloader()

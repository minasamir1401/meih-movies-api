"""
Mock Data for Testing - Arabic Movies & Series
بيانات تجريبية للاختبار - أفلام ومسلسلات عربية
"""

MOCK_LATEST_CONTENT = [
    {
        "id": "mock-1",
        "title": "فيلم الهرم الرابع",
        "poster": "https://image.tmdb.org/t/p/w500/xvzxqKWltnj8qQiVVLoq8qhfJ9H.jpg",
        "type": "movie",
        "year": "2024",
        "rating": "7.5",
        "description": "فيلم مصري كوميدي اجتماعي"
    },
    {
        "id": "mock-2",
        "title": "مسلسل الاختيار 3",
        "poster": "https://image.tmdb.org/t/p/w500/6DrHO1jr3qVrViUO6s6kFiAGM7.jpg",
        "type": "series",
        "year": "2024",
        "rating": "8.2",
        "description": "مسلسل درامي مصري"
    },
    {
        "id": "mock-3",
        "title": "فيلم كيرة والجن",
        "poster": "https://image.tmdb.org/t/p/w500/yF1eOkaYvwiORauRCPWznV9xVvi.jpg",
        "type": "movie",
        "year": "2023",
        "rating": "6.8",
        "description": "فيلم رعب مصري"
    },
    {
        "id": "mock-4",
        "title": "مسلسل جعفر العمدة",
        "poster": "https://image.tmdb.org/t/p/w500/8cdWjvBV6B1hHdlq3cxHn1OVAn7.jpg",
        "type": "series",
        "year": "2024",
        "rating": "7.9",
        "description": "مسلسل كوميدي مصري"
    },
    {
        "id": "mock-5",
        "title": "فيلم الحريفة 2",
        "poster": "https://image.tmdb.org/t/p/w500/rktDFPbfHfUbArZ6OOOKsXcv0Bm.jpg",
        "type": "movie",
        "year": "2024",
        "rating": "7.1",
        "description": "فيلم كوميدي مصري"
    },
    {
        "id": "mock-6",
        "title": "مسلسل الكبير أوي",
        "poster": "https://image.tmdb.org/t/p/w500/eSzpy96DwBujGFj0xMbXBcGcfxX.jpg",
        "type": "series",
        "year": "2023",
        "rating": "8.5",
        "description": "مسلسل كوميدي مصري"
    },
    {
        "id": "mock-7",
        "title": "فيلم الفيل الأزرق 2",
        "poster": "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg",
        "type": "movie",
        "year": "2019",
        "rating": "7.3",
        "description": "فيلم رعب نفسي مصري"
    },
    {
        "id": "mock-8",
        "title": "مسلسل لعبة نيوتن",
        "poster": "https://image.tmdb.org/t/p/w500/zra8NrzxaEeunRWJmUm3HZOL4sd.jpg",
        "type": "series",
        "year": "2021",
        "rating": "8.0",
        "description": "مسلسل إثارة مصري"
    },
    {
        "id": "mock-9",
        "title": "فيلم 122",
        "poster": "https://image.tmdb.org/t/p/w500/vB8o2p4ETnrfiWEgVxHmHWP9yRl.jpg",
        "type": "movie",
        "year": "2019",
        "rating": "6.9",
        "description": "فيلم رعب مصري"
    },
    {
        "id": "mock-10",
        "title": "مسلسل الهيبة",
        "poster": "https://image.tmdb.org/t/p/w500/2OgNQGfNJIWPJWFmHbHihzVqCdL.jpg",
        "type": "series",
        "year": "2023",
        "rating": "8.3",
        "description": "مسلسل درامي لبناني"
    },
    {
        "id": "mock-11",
        "title": "فيلم الخلية",
        "poster": "https://image.tmdb.org/t/p/w500/mKvw1Ic9enfFlCPBNJGiejRPMUO.jpg",
        "type": "movie",
        "year": "2017",
        "rating": "7.4",
        "description": "فيلم إثارة مصري"
    },
    {
        "id": "mock-12",
        "title": "مسلسل زي الشمس",
        "poster": "https://image.tmdb.org/t/p/w500/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg",
        "type": "series",
        "year": "2024",
        "rating": "7.6",
        "description": "مسلسل رومانسي مصري"
    }
]

MOCK_DETAILS = {
    "mock-1": {
        "title": "فيلم الهرم الرابع",
        "poster": "https://image.tmdb.org/t/p/w500/xvzxqKWltnj8qQiVVLoq8qhfJ9H.jpg",
        "type": "movie",
        "year": "2024",
        "rating": "7.5",
        "description": "فيلم كوميدي اجتماعي مصري من بطولة محمد رمضان",
        "servers": [
            {"name": "السيرفر الأول", "url": "https://www.youtube.com/embed/dQw4w9WgXcQ"},
            {"name": "السيرفر الثاني", "url": "https://www.youtube.com/embed/dQw4w9WgXcQ"}
        ],
        "download_links": [
            {"quality": "1080p", "url": "#", "size": "2.5 GB"},
            {"quality": "720p", "url": "#", "size": "1.2 GB"}
        ],
        "episodes": []
    },
    "mock-2": {
        "title": "مسلسل الاختيار 3",
        "poster": "https://image.tmdb.org/t/p/w500/6DrHO1jr3qVrViUO6s6kFiAGM7.jpg",
        "type": "series",
        "year": "2024",
        "rating": "8.2",
        "description": "مسلسل درامي مصري يتناول أحداث سياسية",
        "servers": [],
        "download_links": [],
        "episodes": [
            {"number": "1", "title": "الحلقة 1", "url": "mock-2-ep1"},
            {"number": "2", "title": "الحلقة 2", "url": "mock-2-ep2"},
            {"number": "3", "title": "الحلقة 3", "url": "mock-2-ep3"},
            {"number": "4", "title": "الحلقة 4", "url": "mock-2-ep4"},
            {"number": "5", "title": "الحلقة 5", "url": "mock-2-ep5"}
        ]
    }
}

def get_mock_latest(page=1):
    """Get mock latest content"""
    return MOCK_LATEST_CONTENT

def get_mock_details(content_id):
    """Get mock content details"""
    return MOCK_DETAILS.get(content_id, {
        "title": "محتوى تجريبي",
        "poster": "https://via.placeholder.com/500x750?text=Mock+Content",
        "type": "movie",
        "year": "2024",
        "rating": "7.0",
        "description": "هذا محتوى تجريبي للاختبار",
        "servers": [{"name": "سيرفر تجريبي", "url": "https://www.youtube.com/embed/dQw4w9WgXcQ"}],
        "download_links": [],
        "episodes": []
    })

def get_mock_search(query):
    """Get mock search results"""
    return [item for item in MOCK_LATEST_CONTENT if query.lower() in item['title'].lower()]

def get_mock_category(category_id, page=1):
    """Get mock category content"""
    return MOCK_LATEST_CONTENT[:6]  # Return first 6 items for any category

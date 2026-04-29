"""
Skill: Web Scraping & Data Collection via Apify
Thu thập dữ liệu thị trường, đối thủ, khách hàng tiềm năng cho Studio Flow
"""
from apify_client import ApifyClient
from config import config

client = ApifyClient(config.APIFY_API_TOKEN)


def scrape_facebook_page(page_url: str, max_posts: int = 20) -> list[dict]:
    """
    Scrape bài đăng từ Facebook Page của đối thủ hoặc thị trường.
    Actor: apify/facebook-pages-scraper
    """
    run_input = {
        "startUrls": [{"url": page_url}],
        "maxPosts": max_posts,
        "maxPostComments": 5,
    }
    run = client.actor("apify/facebook-pages-scraper").call(run_input=run_input)
    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    return items


def scrape_google_search(query: str, max_results: int = 20) -> list[dict]:
    """
    Scrape kết quả Google Search cho từ khóa liên quan đến thị trường.
    Actor: apify/google-search-scraper
    """
    run_input = {
        "queries": query,
        "maxPagesPerQuery": 1,
        "resultsPerPage": max_results,
        "languageCode": "vi",
        "countryCode": "vn",
    }
    run = client.actor("apify/google-search-scraper").call(run_input=run_input)
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def scrape_website_content(url: str) -> list[dict]:
    """
    Scrape nội dung trang web của đối thủ cạnh tranh.
    Actor: apify/website-content-crawler
    """
    run_input = {
        "startUrls": [{"url": url}],
        "maxCrawlPages": 10,
        "crawlerType": "playwright:firefox",
    }
    run = client.actor("apify/website-content-crawler").call(run_input=run_input)
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def scrape_tiktok_hashtag(hashtag: str, max_items: int = 30) -> list[dict]:
    """
    Scrape video TikTok theo hashtag để phân tích trend.
    Actor: clockworks/tiktok-scraper
    """
    run_input = {
        "hashtags": [hashtag],
        "resultsPerPage": max_items,
    }
    run = client.actor("clockworks/tiktok-scraper").call(run_input=run_input)
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


def find_photography_studios_vietnam(city: str = "Hà Nội", max_results: int = 50) -> list[dict]:
    """
    Tìm danh sách studio chụp ảnh tại Việt Nam qua Google Maps.
    Actor: compass/crawler-google-places
    """
    run_input = {
        "searchStringsArray": [f"studio chụp ảnh {city}", f"photography studio {city}"],
        "maxCrawledPlacesPerSearch": max_results,
        "language": "vi",
        "countryCode": "VN",
    }
    run = client.actor("compass/crawler-google-places").call(run_input=run_input)
    return list(client.dataset(run["defaultDatasetId"]).iterate_items())


# --- Competitor List cho Studio Flow ---
COMPETITORS = {
    "photostudio_vn": "https://www.facebook.com/photostudio.vn",
    "google_search_saas_photo": "phần mềm quản lý studio chụp ảnh việt nam",
}

PHOTOGRAPHY_HASHTAGS = [
    "studiochupanhhanoivn",
    "phimnhaptrang",
    "anhuongvietnam",
    "studioflow",
    "quanlykhachhang",
]

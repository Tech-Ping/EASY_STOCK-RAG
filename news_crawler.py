import requests
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import hashlib
from pinecone import Pinecone, ServerlessSpec
from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # ✅ 최신 라이브러리 사용
from langchain_core.documents import Document  # ✅ 요약 시 필요
from langchain.chains.summarize import load_summarize_chain
from urllib.parse import parse_qs, urlparse

load_dotenv()

PINECONE_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
INDEX_NAME = "easystock"

pc = Pinecone(api_key=PINECONE_KEY)
existing_indexes = pc.list_indexes().names()
if INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=INDEX_NAME,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    time.sleep(5)
    print(f"✅ '{INDEX_NAME}' 인덱스 생성 완료!")

TICKERS = {
    "삼성전자": "005930",
    "LG에너지솔루션": "373220",
    "SK하이닉스": "000660",
    "현대차": "005380",
    "비에이치아이": "083650"
}

BASE_URL = "https://finance.naver.com/item/news.naver?code={}"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Referer": "https://finance.naver.com/",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive"
}

def summarize_news(article_text):
    try:
        # ✅ OpenAI GPT-4 Turbo 모델 설정 (랜덤성 최소화)
        llm = ChatOpenAI(api_key=OPENAI_API_KEY, temperature=0)

        prompt = (
            "📰 다음 뉴스 기사를 반드시 한국어로 1문장으로 요약해 주세요.\n\n"
            "⚠️ **중요**: 영어가 아니라, 반드시 한국어로만 응답해야 합니다.\n"
            "💡 추가 설명 없이, 순수한 요약 문장만 출력하세요.\n\n"
            f"{article_text}"
        )
        response = llm.invoke(prompt)
        summary = response.content.strip()  # ✅ 응답에서 내용만 추출

        return summary  
    
    except Exception as e:
        print(f"🚨 요약 실패: {e}")
        return "요약 실패"


def get_news_article(url):
    """
    네이버 뉴스 기사 본문을 가져오는 함수
    """
    print(f"🔗 Fetching article from: {url}")

    try:
        response = requests.get(url, headers=HEADERS)
        response.encoding = "utf-8"

        if response.status_code != 200:
            print(f"🚨 기사 페이지 요청 실패! 상태 코드: {response.status_code}")
            return "기사 본문을 가져올 수 없습니다."

        article_soup = BeautifulSoup(response.text, "html.parser")

        # ✅ 최신 네이버 뉴스 본문 구조 반영
        article_body = article_soup.select_one("#dic_area")

        if article_body:
            return article_body.text.strip()
        else:
            print("🚨 기사 본문을 찾을 수 없음")
            return "기사 본문을 가져올 수 없습니다."

    except Exception as e:
        print(f"🔥 ERROR fetching article: {e}")
        return "기사 본문을 가져올 수 없습니다."


def get_news_iframe_url(ticker_code):
    url = BASE_URL.format(ticker_code)
    response = requests.get(url, headers=HEADERS)
    response.encoding = "euc-kr"

    if response.status_code != 200:
        print(f"🚨 {ticker_code} 페이지 요청 실패! 상태 코드: {response.status_code}")
        return None
    
    soup = BeautifulSoup(response.text, "html.parser")
    iframe_tag = soup.find("iframe", {"id": "news_frame"})
    if not iframe_tag:
        print(f"🫢 {ticker_code} iframe을 찾을 수 없음")
        return None
    
    return "https://finance.naver.com" + iframe_tag["src"]


def get_latest_stock_news(ticker_name, ticker_code):
    iframe_url = get_news_iframe_url(ticker_code)
    if not iframe_url:
        return None

    response = requests.get(iframe_url, headers=HEADERS)
    response.encoding = "euc-kr"

    if response.status_code != 200:
        print(f"🚨 iframe 요청 실패! 상태 코드: {response.status_code}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    news_table = soup.find("table", class_="type5")

    if not news_table:
        print(f"🫢 뉴스 테이블을 찾을 수 없음 ({ticker_code})")
        return None

    first_news = news_table.find("tr", class_="first")
    if not first_news:
        print("🚨 첫 번째 뉴스 기사를 찾을 수 없음")
        return None

    title_tag = first_news.find("a", class_="tit")
    if not title_tag:
        print("🚨 기사 제목을 찾을 수 없음")
        return None

    title = title_tag.text.strip()
    link = title_tag["href"]

    # ✅ 링크가 상대 경로일 경우, 네이버 뉴스(mnews.naver.com) URL로 변환
    if "/item/news_read.naver?" in link:
        parsed_url = urlparse(link)
        query_params = parse_qs(parsed_url.query)

        office_id = query_params.get("office_id", [""])[0]
        article_id = query_params.get("article_id", [""])[0]

        if office_id and article_id:
            link = f"https://n.news.naver.com/mnews/article/{office_id}/{article_id}"
        else:
            link = f"https://finance.naver.com{link}"  # 기존 방식 유지

    elif not link.startswith("http"):
        link = f"https://finance.naver.com{link}"

    date_tag = first_news.find("td", class_="date")
    news_date = date_tag.text.strip() if date_tag else "Unknown"

    # 기사 본문 가져오기
    article_text = get_news_article(link)
    summary = summarize_news(article_text)

    return {
        "title": title,
        "link": link,  # ✅ 정상적인 URL 변환
        "summary": summary,
        "date": news_date,
        "ticker": ticker_name
    }


def generate_ascii_id(ticker, title, date):
    """🔗 종목명 + 뉴스 제목 + 날짜 조합으로 벡터 ID 생성 (중복 방지)"""
    raw_text = f"{ticker}_{title}_{date}"
    return hashlib.sha256(raw_text.encode("utf-8")).hexdigest()[:16]

def store_latest_news(tickers_to_fetch):
    stored_news = []
    for name, code in tickers_to_fetch.items():
        print(f"📡 Fetching latest news for {name} ({code})...")
        latest_news = get_latest_stock_news(name, code)
        if latest_news:
            embeddings = OpenAIEmbeddings()
            index = pc.Index(INDEX_NAME)

            vector_id = generate_ascii_id(latest_news["ticker"], latest_news["title"], latest_news["date"])

            vector = embeddings.embed_query(str(latest_news["summary"]))  # 🔥 문자열 변환

            index.upsert([
                {
                    "id": vector_id,  
                    "values": vector,
                    "metadata": {
                        "title": latest_news["title"],
                        "url": latest_news["link"],
                        "date": latest_news["date"],
                        "summary": latest_news["summary"],  # ✅ 요약본 저장
                        "ticker": latest_news["ticker"]  
                    }
                }
            ])

            print(f"✅ Latest news stored in Pinecone: {latest_news['title']} (ID: {vector_id})")
            stored_news.append(latest_news)
    return stored_news
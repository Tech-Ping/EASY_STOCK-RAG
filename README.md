# 📰 TechPing-RAG

## 📌 개요
이 프로젝트는 이화캡스톤프로젝트 '이지-스톡'의 인앱 서비스형 챗봇 서버로,<br>
Flask 기반의 💸 **주식 뉴스 크롤링 및 AI 기반 금융 챗봇 💸**입니다.
- Yahoo Finance API로 tickers들의 2년간 주식 정보 접근
- OpenAI GPT-4 Turbo를 커스터마이징하여 사용자의 금융 질문에 친근하고 이해하기 쉬운 답변 제공
- Selenium과 BeautifulSoup을 이용한 네이버 금융 뉴스 크롤링
- Langchain 워크플로우로 금융 뉴스 요약 기능 제공
- Pinecone을 활용한 벡터 DB 구축

---

## 📌 기술 스택

| **구분**       | **기술 스택**                        |
|---------------|--------------------------------|
| **Backend**   | Flask                          |
| **AI Model**  | OpenAI GPT-4 Turbo            |
| **Database**  | Pinecone (Vector DB)          |
| **Web Scraping** | Selenium + BeautifulSoup    |
| **Summarization** | Langchain                  |
| **Stock Data** | Yahoo Finance API            |

---
## 📂 프로젝트 구조
```
📁 TechPing-AI-Server/
│── app.py                      # Flask API 서버
│── news_crawler.py             # 네이버 금융 뉴스 크롤러 (Selenium + BeautifulSoup)
│── openai_service.py           # OpenAI GPT-4 Turbo 챗봇 API
│── essential_package.txt       # 프로젝트 의존성 패키지 목록
│── .env                        # 환경 변수 (API 키 포함)
```

---
## 🚀 주요 기능
### 📈 1. 주식 정보 조회 API (`/stock-info`)
**요청 방식**: `POST`
```json
{
  "company_name": "삼성전자",
  "stock_field": "종가",
  "date": "2024-02-01"
}
```
**응답 예시**:
```json
{
  "message": "2024년 2월 1일, 삼성전자의 종가는 70,000원입니다."
}
```

### 💬 2. AI 기반 금융 질문 응답 API (`/ask`)
**요청 방식**: `POST`
```json
{
  "prompt": "PBR이란 무엇인가요?"
}
```
**응답 예시**:
```json
{
  "response": "PBR은 Price-to-Book Ratio의 약자로, 주가를 주당 장부가치로 나눈 값입니다."
}
```

### 📰 3. 주식 뉴스 크롤링 API (`/crawl-news`)
**요청 방식**: `GET`
- `ticker`를 Query Parameter로 전달하면 해당 종목 뉴스만 크롤링 가능
```bash
GET /crawl-news?ticker=삼성전자
```
**응답 예시**:
```json
{
  "message": "뉴스 크롤링 완료",
  "news": [
    {
      "title": "삼성전자, 반도체 시장에서의 도전",
      "link": "https://n.news.naver.com/mnews/article/015/0005088180",
      "summary": "삼성전자는 AI 반도체 기술 경쟁에서 새로운 도전에 직면하고 있습니다.",
      "date": "2024-02-01",
      "ticker": "삼성전자"
    }
  ]
}
```

---
## 🔧 환경 변수 설정 (`.env` 파일)
```
OPENAI_API_KEY=sk-xxxxx
PINECONE_API_KEY=xxxxxx
PINECONE_ENV=us-east-1
```

---
## 🛠️ 실행 방법
### 1️⃣ 필수 패키지 설치
```bash
pip install -r essential_package.txt
```

### 2️⃣ Flask 서버 실행
```bash
python app.py
```

### 3️⃣ Swagger UI 접속 (API 문서화)
서버 실행 후, 브라우저에서 `http://127.0.0.1:5000/apidocs/`에 접속

---
## ✨ TODO (추가 개발 계획)
- [ ] 월별 사용자 마이 투자 리포트 분석 기능 제공

---
## 📄 라이선스
이 프로젝트는 MIT 라이선스를 따릅니다.


from flask import Flask, request, jsonify
import yfinance as yf
from flasgger import Swagger
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from openai_service import get_response
from dateutil import parser
from news_crawler import store_latest_news
from news_crawler import fetch_latest_news
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",
            "https://easystogy.store",
            "https://easy-stock-techping.netlify.app"
        ]
    }
})


swagger = Swagger(app)

COMPANY_TICKERS = {
    "삼성전자": "005930.KS",
    "현대차": "005380.KS",
    "LG에너지솔루션": "373220.KQ"
}

STOCK_FIELDS = {
    "시가": "Open",
    "최고가": "High",
    "최저가": "Low",
    "종가": "Close",
    "거래량": "Volume"
}

NEWS_TICKERS = {
    "삼성전자": "005930",
    "LG에너지솔루션": "373220",
    "SK하이닉스": "000660",
    "현대차": "005380",
    "비에이치아이": "083650"
}

@app.route('/stock-info', methods=['POST'])
def get_stock_info():
    """
    주식 정보를 처리하는 API
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            company_name:
              type: string
              description: 회사명
              example: 삼성전자
            stock_field:
              type: string
              description: 주식 정보 필드 (시가, 종가 등)
              example: 종가
            date:
              type: string
              description: 날짜 (YYYY-MM-DD)
              example: "2023-12-01"
    responses:
      200:
        description: 주식 데이터
      400:
        description: 잘못된 요청
      404:
        description: 데이터 없음
    """
    try:
        data = request.json
        company_name = data.get("company_name")
        stock_field = data.get("stock_field")
        date = data.get("date")
        print(f"회사명: {company_name}, 주식 정보: {stock_field}, 날짜: {date}")

        if company_name not in COMPANY_TICKERS:
            return jsonify({"error": f"지원하지 않는 회사입니다: {company_name}"}), 400

        if stock_field not in STOCK_FIELDS:
            return jsonify({"error": f"지원하지 않는 정보입니다: {stock_field}"}), 400

        try:
            start_date = parser.parse(date).date()
            formatted_date = start_date.strftime("%Y년 %m월 %d일")
            end_date = start_date + timedelta(days=1)
            end_date_str = end_date.strftime("%Y-%m-%d")
        except Exception as e:
            return jsonify({"error": f"날짜 형식이 잘못되었습니다: {str(e)}"}), 400
        
        ticker = COMPANY_TICKERS[company_name]
        stock_data = yf.download(ticker, start=date, end=end_date_str)

        if stock_data.empty:
            return jsonify({"error": f"해당 날짜에 대한 주식 정보가 없습니다: {date}"}), 404

        field = STOCK_FIELDS[stock_field]
        value = stock_data.iloc[0][field]
        value = float(value)
        
        if stock_field == "거래량":
            return jsonify({"message": f"{formatted_date}, {company_name}의 {stock_field}은 {value:,.0f}주입니다."})
        else:
            return jsonify({"message": f"{formatted_date}, {company_name}의 {stock_field}는 {value:.0f}원입니다."})
    
    except Exception as e:
        return jsonify({"error": f"서버 에러: {str(e)}"}), 500


@app.route('/ask', methods=['POST'])
def ask():
    """
    사용자 질문을 처리하는 API
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            prompt:
              type: string
              description: 사용자 질문
              example: "PBR이란 무엇인가요?"
    responses:
      200:
        description: OpenAI 응답
      400:
        description: 잘못된 요청
      500:
        description: 서버 에러
    """
    try:
        data = request.json
        prompt = data.get("prompt", "")

        if not prompt:
            return jsonify({"error": "질문이 비어있습니다."}), 400

        response = get_response(prompt)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
from news_crawler import fetch_latest_news  # 이미 정의되어 있는 함수

@app.route('/latest-news', methods=['GET'])
def latest_news():
    """
    종목별 최신 뉴스 5개를 네이버 금융 뉴스 API에서 조회하는 API
    ---
    parameters:
      - name: ticker
        in: query
        type: string
        required: true
        enum: ["삼성전자", "LG에너지솔루션", "SK하이닉스", "현대차", "비에이치아이"]
        description: 종목 이름
        example: "삼성전자"
    responses:
      200:
        description: 뉴스 리스트 반환
      400:
        description: 유효하지 않은 ticker
      500:
        description: 서버 에러
    """
    try:
        ticker_name = request.args.get("ticker")
        if not ticker_name or ticker_name not in NEWS_TICKERS:
            return jsonify({"error": f"지원하지 않는 ticker입니다: {ticker_name}"}), 400

        ticker_code = NEWS_TICKERS[ticker_name]
        news_items = fetch_latest_news(ticker_code)

        return jsonify({"ticker": ticker_name, "news": news_items}), 200

    except Exception as e:
        return jsonify({"error": f"서버 에러: {str(e)}"}), 500

@app.route('/crawl-news', methods=['GET'])
def crawl_news():
    """
    최신 뉴스를 크롤링하고 특정 ticker별로 필터링하는 API
    ---
    parameters:
      - name: ticker
        in: query
        type: string
        required: false
        enum: ["삼성전자", "LG에너지솔루션", "SK하이닉스", "현대차", "비에이치아이"]
        description: "특정 종목의 뉴스만 가져오려면 선택하세요"
        example: "삼성전자"
    responses:
      200:
        description: 크롤링 완료 및 해당 ticker 뉴스 반환
      400:
        description: 유효하지 않은 ticker 값 입력
      500:
        description: 서버 에러 발생
    """
    try:
        ticker_name = request.args.get("ticker")

        if ticker_name and ticker_name not in NEWS_TICKERS:
            return jsonify({"error": f"Invalid ticker name: {ticker_name}"}), 400
        
        tickers_to_fetch = {ticker_name: NEWS_TICKERS[ticker_name]} if ticker_name else NEWS_TICKERS

        news_data = store_latest_news(tickers_to_fetch)

        return jsonify({"message": "뉴스 크롤링 완료", "news": news_data}), 200
    
    except Exception as e:
        print(f"🔥 ERROR: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)

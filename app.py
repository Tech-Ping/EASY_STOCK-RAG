from flask import Flask, request, jsonify
import yfinance as yf
from flasgger import Swagger
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from openai_service import get_response

app = Flask(__name__)
swagger = Swagger(app)

# 회사명과 티커 매핑
COMPANY_TICKERS = {
    "삼성전자": "005930.KS",
    "현대차": "005380.KS",
    "LG에너지솔루션": "373220.KQ"
}

# 주식 정보 Enum (시가, 최고가, 최저가, 종가, 거래량)
STOCK_FIELDS = {
    "시가": "Open",
    "최고가": "High",
    "최저가": "Low",
    "종가": "Close",
    "거래량": "Volume"
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
              example: 2023-12-01
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

        # 회사명 검증
        if company_name not in COMPANY_TICKERS:
            return jsonify({"error": f"지원하지 않는 회사입니다: {company_name}"}), 400

        # 주식 정보 검증
        if stock_field not in STOCK_FIELDS:
            return jsonify({"error": f"지원하지 않는 정보입니다: {stock_field}"}), 400

        # end 날짜 구하기
        start_date = datetime.strptime(date, "%Y-%m-%d")
        end_date = start_date + timedelta(days=1)
        end_date_str = end_date.strftime("%Y-%m-%d")
        formatted_date = start_date.strftime("%Y년 %m월 %d일")


        # 주식 데이터 가져오기
        ticker = COMPANY_TICKERS[company_name]
        stock_data = yf.download(ticker, start=date, end=end_date_str)

        print("주식데이터 출력:")
        print(stock_data)

        # 데이터가 비어있을 경우, 다른 날짜로 시도하거나 오류 메시지 반환
        if stock_data.empty:
            return jsonify({"error": f"해당 날짜에 대한 주식 정보가 없습니다: {date}"}), 404

        # 요청한 필드 값 가져오기
        field = STOCK_FIELDS[stock_field]
        value = stock_data.iloc[0][field]
        value = float(value)
        
        if stock_field == "거래량":
            return jsonify({"message": f"{formatted_date}, {company_name}의 {stock_field}은 {value:,.0f}주입니다."})
        else:
            return jsonify({"message": f"{formatted_date}, {company_name}의 {stock_field}는 {value:.0f}원입니다."})
    
    except Exception as e:
        return jsonify({"error": f"서버 에러: {str(e)}"}), 500


# 사용자 주식 질문을 처리하는 API(GPT 기본 성능)
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
        # 요청 데이터에서 질문 추출
        data = request.json
        prompt = data.get("prompt", "")

        if not prompt:
            return jsonify({"error": "질문이 비어있습니다."}), 400

        # OpenAI 응답 생성
        response = get_response(prompt)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)
    print("app.py 테스트 실행")
    response = get_response("PER이란 무엇인가요?")
    print(f"응답: {response}")
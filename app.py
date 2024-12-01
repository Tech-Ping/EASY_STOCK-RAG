from flask import Flask, request, jsonify
import yfinance as yf
from datetime import datetime, timedelta

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(debug=True)

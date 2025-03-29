import os
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")  
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

client = OpenAI(api_key=api_key)

def get_response1(prompt):
    return f"테스트 응답: {prompt}"

if __name__ == "__main__":
    print("openai_service.py 테스트 실행")
    response = get_response1("PBR이란 무엇인가요?")
    print(f"응답: {response}")

def get_response(prompt):
    """
    OpenAI API를 호출하여 사용자 프롬프트에 대한 응답 생성
    :param prompt: 사용자 질문
    :return: OpenAI 모델의 응답
    """
    try:
        full_prompt = f"""
        당신은 금융 및 주식 투자 전문가입니다. 귀여운 성격으로 친근하고 이해하기 쉬운 방식으로 질문에 답변하세요.

        아래는 주식 용어와 관련된 예제 답변입니다:

        Q: LG하이닉스 주가 정보 알려줄 수 있어?
        A: 현재 LG하이닉스(000660)의 주가는 177,000원이며, 이는 전일 대비 **300원 상승(+0.17%)**한 가격입니다. 오늘의 거래량은 약 4,244,333주이며, 시가는 174,500원, 고가는 179,500원, 저가는 173,900원으로 기록되었습니다.

        Q: PBR이란 무엇인가요?
        A: PBR은 'Price-to-Book Ratio'의 약자로, 주가를 주당 장부가치(BPS)로 나눈 값입니다. 주로 기업의 주식이 저평가되었는지 고평가되었는지 판단하는 데 사용됩니다.

        이제 사용자 질문에 답변해주세요:

        사용자 질문: {prompt}
        """
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly stock and finance expert named 스토기, you are task is to make appropriate answer with user's question."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=400,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

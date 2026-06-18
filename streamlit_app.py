
import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from datetime import datetime

def evaluate_url(url):
    score = 0

    response = requests.get(
        url,
        timeout=10,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    # 권위성
    domain = urlparse(url).netloc.lower()
    authority = 10
    authority_reason = "일반 웹사이트"

    if domain.endswith(".go.kr") or domain.endswith(".gov"):
        authority = 30
        authority_reason = "정부기관"
    elif domain.endswith(".ac.kr") or domain.endswith(".edu"):
        authority = 28
        authority_reason = "교육기관"
    elif domain.endswith(".org"):
        authority = 24
        authority_reason = "비영리기관"
    elif any(word in domain for word in ["news", "press", "journal"]):
        authority = 20
        authority_reason = "언론사"

    score += authority

    # 최신성
    currency = 5
    latest_year = None
    current_year = datetime.now().year

    date_keywords = [
        "published", "publish",
        "article:published_time",
        "date", "modified"
    ]

    for meta in soup.find_all("meta"):
        attrs = (meta.get("name", "") + " " +
                 meta.get("property", "")).lower()
        content = meta.get("content", "")

        if any(k in attrs for k in date_keywords):
            match = re.search(r"(20\d{2})", content)
            if match:
                latest_year = int(match.group(1))
                break

    if latest_year is None:
        years = re.findall(r"20\d{2}", text)

        if years:
            years = [
                int(y)
                for y in years
                if 2000 <= int(y) <= current_year
            ]

            if years:
                latest_year = max(years)

    if latest_year:
        if latest_year >= current_year - 1:
            currency = 20
        elif latest_year >= current_year - 3:
            currency = 15
        elif latest_year >= current_year - 6:
            currency = 10

    score += currency

    # 정확성
    accuracy = 5

    source_keywords = [
        "출처", "참고문헌",
        "references", "bibliography",
        "doi", "issn"
    ]

    source_count = sum(
        text.lower().count(word.lower())
        for word in source_keywords
    )

    if source_count >= 5:
        accuracy = 30
    elif source_count >= 3:
        accuracy = 25
    elif source_count >= 1:
        accuracy = 20

    if any(word in text for word in ["저자", "작성자", "기자"]):
        accuracy += 5

    accuracy = min(accuracy, 30)
    score += accuracy

    # 목적성
    purpose = 20

    sensational_words = [
        "충격", "경악", "대박", "소름",
        "긴급", "믿을 수 없는", "단독",
        "폭로", "논란", "역대급"
    ]

    count = sum(text.count(word) for word in sensational_words)
    purpose -= min(count * 2, 15)

    score += purpose

    if score >= 80:
        grade = "A (신뢰 가능)"
    elif score >= 60:
        grade = "B (추가 검증 필요)"
    else:
        grade = "C (신뢰도 낮음)"

    return {
        "authority": authority,
        "authority_reason": authority_reason,
        "currency": currency,
        "latest_year": latest_year,
        "accuracy": accuracy,
        "source_count": source_count,
        "purpose": purpose,
        "score": score,
        "grade": grade
    }

st.title("CRAAP 기반 정보 신뢰도 평가기")

url = st.text_input("평가할 URL 입력")

if st.button("평가") and url:
    try:
        result = evaluate_url(url)

        st.subheader("평가 결과")
        st.write(f"권위성: {result['authority']}/30")
        st.write(f"근거: {result['authority_reason']}")

        st.write(f"최신성: {result['currency']}/20")
        st.write(f"확인 연도: {result['latest_year']}")

        st.write(f"정확성: {result['accuracy']}/30")
        st.write(f"출처 키워드 수: {result['source_count']}")

        st.write(f"목적성: {result['purpose']}/20")

        st.metric("총점", f"{result['score']}/100")
        st.success(result['grade'])

    except Exception as e:
        st.error(f"오류 발생: {e}")

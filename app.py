# -*- coding: utf-8 -*-
import os
import io
from datetime import datetime, date

import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st


# -----------------------------
# 네이버 뉴스 1건 상세 가져오기
# -----------------------------
def get_news(n_url: str):
    """
    개별 네이버 뉴스 기사 페이지에서
    제목, 날짜, 본문, 언론사, 링크를 추출합니다.
    """
    news_detail = {
        "date": "",
        "company": "",
        "title": "",
        "content": "",
        "link": n_url,
    }

    try:
        breq = requests.get(n_url, timeout=5)
        breq.raise_for_status()
    except Exception as e:
        # 요청 실패 시 비어있는 데이터 반환
        print(f"요청 실패: {n_url} / {e}")
        return news_detail

    bsoup = BeautifulSoup(breq.content, "html.parser")

    # 제목 추출 (네이버 뉴스 구조 변경 대응)
    title_el = (
        bsoup.select_one("h2#title_area")  # 새 구조
        or bsoup.select_one("h3#articleTitle")  # 예전 구조
    )
    if title_el:
        news_detail["title"] = title_el.get_text(strip=True)

    # 날짜 추출
    # 새 구조: span.media_end_head_info_datestamp_time / 옛 구조: .t11
    pdate_el = (
        bsoup.select_one("span.media_end_head_info_datestamp_time")
        or bsoup.select_one(".t11")
    )
    if pdate_el:
        news_detail["date"] = pdate_el.get_text(strip=True)[:16]

    # 본문 추출
    body_el = (
        bsoup.select_one("article#dic_area")  # 새 구조
        or bsoup.select_one("#articleBodyContents")  # 옛 구조
    )
    if body_el:
        text = body_el.get_text(" ", strip=True)
        # 플래시 우회 문구 제거(예전 구조)
        text = text.replace(
            "// flash 오류를 우회하기 위한 함수 추가 function _flash_removeCallback() {}",
            "",
        )
        news_detail["content"] = text.strip()

    # 언론사 추출 (새/구조 혼합 대응)
    company_el = (
        bsoup.select_one("a.media_end_head_top_logo")  # 새 구조
        or bsoup.select_one("#footer address a")  # 예전 구조
    )
    if company_el:
        news_detail["company"] = company_el.get_text(strip=True)

    return news_detail


# -----------------------------
# 네이버 뉴스 검색 결과 크롤러
# -----------------------------
def crawler(max_page: int, query: str, s_date: str, e_date: str) -> pd.DataFrame:
    """
    max_page: 최대 검색 페이지 수 (1페이지당 10건, 네이버 기준)
    query   : 검색어
    s_date  : 시작일자 'YYYY.MM.DD'
    e_date  : 종료일자 'YYYY.MM.DD'
    """
    s_from = s_date.replace(".", "")
    e_to = e_date.replace(".", "")

    page = 1
    maxpage_t = (max_page - 1) * 10 + 1  # 1,11,21,...

    results = []

    while page <= maxpage_t:
        url = (
            "https://search.naver.com/search.naver"
            f"?where=news&query={query}"
            f"&sort=0&ds={s_date}&de={e_date}"
            f"&nso=so%3Ar%2Cp%3Afrom{s_from}to{e_to}%2Ca%3A&start={page}"
        )

        print("요청 URL:", url)
        try:
            req = requests.get(url, timeout=5)
            req.raise_for_status()
        except Exception as e:
            print("검색 페이지 요청 실패:", e)
            page += 10
            continue

        soup = BeautifulSoup(req.content, "html.parser")

        # 1) 새 구조: a.news_tit
        link_tags = soup.select("a.news_tit")
        # 2) 구 구조: a._sp_each_url (없을 수도 있음)
        if not link_tags:
            link_tags = soup.select("a._sp_each_url")

        if not link_tags:
            print("뉴스 링크를 찾지 못했습니다.")
            break

        for a_tag in link_tags:
            href = a_tag.get("href", "")
            if not href:
                continue
            # 네이버 뉴스 도메인만 크롤링
            if not href.startswith("https://news.naver.com"):
                continue

            news_detail = get_news(href)
            if news_detail["title"]:  # 제목 없는 경우는 스킵
                results.append(
                    {
                        "date": news_detail["date"],
                        "company": news_detail["company"],
                        "title": news_detail["title"],
                        "content": news_detail["content"],
                        "link": news_detail["link"],
                    }
                )

        page += 10

    if results:
        df = pd.DataFrame(results)
    else:
        df = pd.DataFrame(columns=["date", "company", "title", "content", "link"])

    return df


# -----------------------------
# Streamlit UI
# -----------------------------
def main():
    st.set_page_config(
        page_title="네이버 뉴스 크롤러",
        page_icon="📰",
        layout="wide",
    )

    st.title("📰 네이버 뉴스 크롤링 웹 앱")
    st.markdown(
        """
        네이버 뉴스에서 특정 **검색어 + 기간**으로 뉴스를 크롤링하고,<br>
        결과를 **화면에서 확인**하거나 **CSV/엑셀로 다운로드**할 수 있습니다.
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # 입력 폼
    with st.form(key="search_form"):
        col1, col2 = st.columns(2)

        with col1:
            query = st.text_input("검색어", value="파이썬", placeholder="예: 인공지능, 경제, 주식 등")
            max_page = st.number_input(
                "최대 검색 페이지 수 (1페이지당 약 10건)",
                min_value=1,
                max_value=50,
                value=3,
            )

        with col2:
            today = date.today()
            s_date = st.date_input("시작 날짜", value=today.replace(day=1))
            e_date = st.date_input("끝 날짜", value=today)

        submitted = st.form_submit_button("크롤링 시작하기 🕵️‍♂️")

    if submitted:
        if not query.strip():
            st.error("검색어를 입력해 주세요.")
            return

        if s_date > e_date:
            st.error("시작 날짜가 끝 날짜보다 클 수 없습니다.")
            return

        # 날짜 문자열 포맷 맞추기
        s_date_str = s_date.strftime("%Y.%m.%d")
        e_date_str = e_date.strftime("%Y.%m.%d")

        with st.spinner("네이버 뉴스를 크롤링하는 중입니다..."):
            df = crawler(
                max_page=int(max_page),
                query=query,
                s_date=s_date_str,
                e_date=e_date_str,
            )

        if df.empty:
            st.warning("검색 결과가 없습니다. 검색어 또는 기간을 변경해 보세요.")
            return

        st.success(f"총 {len(df)}개의 기사를 가져왔습니다.")

        # 데이터 미리보기
        st.subheader("📄 크롤링 결과 미리보기")
        st.dataframe(df, use_container_width=True)

        # 다운로드 버튼
        st.markdown("### 📥 데이터 다운로드")

        # CSV 다운로드
        csv_buffer = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="CSV 다운로드",
            data=csv_buffer,
            file_name=f"naver_news_{query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )

        # 엑셀 다운로드 (openpyxl 필요)
        try:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="news")
            excel_buffer.seek(0)

            st.download_button(
                label="엑셀(xlsx) 다운로드",
                data=excel_buffer,
                file_name=f"naver_news_{query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        except Exception as e:
            st.info(
                "엑셀 다운로드 중 문제가 발생했습니다. "
                "requirements.txt에 `openpyxl`을 추가했는지 확인해 주세요."
            )
            print("Excel export error:", e)


if __name__ == "__main__":
    main()

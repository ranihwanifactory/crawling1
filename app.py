import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 페이지 설정
st.set_page_config(
    page_title="성주 참외 경락시세 (No API)",
    page_icon="🍈",
    layout="wide"
)

# 헤더 UI
st.title("🍈 성주 참외 경락시세 모니터링")
st.markdown("API 없이 파이썬 크롤링을 통해 실시간 데이터를 가져옵니다.")

# 크롤링 함수
def get_chamoe_data():
    url = "http://xn--oj4bo0hg8bw0e.biz/index.php?pgurl=etc/701"
    
    try:
        # 1. 웹페이지 요청 (User-Agent 헤더 추가로 차단 방지)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.encoding = 'euc-kr' # 한글 깨짐 방지 (해당 사이트는 보통 euc-kr 또는 utf-8)

        if response.status_code != 200:
            st.error(f"사이트 접속 실패: {response.status_code}")
            return None

        # 2. HTML 파싱
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 3. 테이블 찾기 (해당 사이트 구조에 맞춰 테이블 선택)
        # 보통 데이터 테이블은 <table> 태그로 되어 있습니다.
        # 정확한 선택자가 필요하지만, pandas의 read_html을 쓰면 가장 큰 테이블을 자동으로 찾기 쉽습니다.
        dfs = pd.read_html(response.text)
        
        # 테이블 중 가장 데이터가 많은 것을 선택 (보통 본문 테이블)
        if len(dfs) > 0:
            # 데이터 정제 (필요없는 행 제거 등)
            df = dfs[0] 
            return df
        else:
            st.error("데이터 테이블을 찾을 수 없습니다.")
            return None

    except Exception as e:
        st.error(f"오류 발생: {e}")
        return None

# 새로고침 버튼
if st.button('데이터 새로고침', type="primary"):
    with st.spinner('성주 참외 홈페이지에서 데이터를 가져오는 중...'):
        df = get_chamoe_data()
        
        if df is not None:
            st.success("데이터 업데이트 완료!")
            
            # 데이터프레임 출력
            st.dataframe(
                df, 
                use_container_width=True,
                hide_index=True
            )
            
            # CSV 다운로드 버튼
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="CSV로 다운로드",
                data=csv,
                file_name='chamoe_price.csv',
                mime='text/csv',
            )

# 앱 실행 시 자동 로드
if 'init' not in st.session_state:
    st.session_state.init = True
    df = get_chamoe_data()
    if df is not None:
        st.dataframe(df, use_container_width=True, hide_index=True)
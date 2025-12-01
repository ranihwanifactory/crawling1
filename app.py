import streamlit as st
import requests
import pandas as pd
import lxml

# 페이지 기본 설정
st.set_page_config(
    page_title="참외 경락시세 모니터 (No API)",
    page_icon="🍈",
    layout="wide"
)

# 제목 및 설명
st.title("🍈 성주 참외 경락시세 (실시간)")
st.caption("API 없이 파이썬으로 직접 데이터를 수집합니다.")

# 데이터 수집 함수
@st.cache_data(ttl=600)  # 10분마다 캐시 갱신
def fetch_chamoe_data():
    url = "http://xn--oj4bo0hg8bw0e.biz/index.php?pgurl=etc/701"
    
    try:
        # 1. 웹페이지 요청
        # 차단을 방지하기 위해 User-Agent 헤더 추가
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        
        # 인코딩 설정 (한글 깨짐 방지)
        response.encoding = 'euc-kr' 
        
        if response.status_code != 200:
            return None, f"접속 실패 (Status Code: {response.status_code})"

        # 2. HTML 내의 테이블 찾기
        # pandas의 read_html은 페이지 내의 모든 <table>을 찾아 리스트로 반환합니다.
        dfs = pd.read_html(response.text)
        
        if not dfs:
            return None, "데이터 테이블을 찾을 수 없습니다."
            
        # 가장 데이터가 많은 테이블이 우리가 찾는 시세표일 확률이 높습니다.
        df = max(dfs, key=len)
        
        # 데이터 정제 (필요시)
        # 결측치 제거 등
        df = df.dropna(how='all')
        
        return df, None

    except Exception as e:
        return None, f"오류 발생: {str(e)}"

# 메인 로직
col1, col2 = st.columns([1, 4])

with col1:
    if st.button("🔄 시세 새로고침", use_container_width=True):
        st.cache_data.clear() # 캐시 초기화하여 강제 재수집

# 데이터 로드
with st.spinner('성주 참외 홈페이지에서 데이터를 가져오는 중...'):
    df, error_msg = fetch_chamoe_data()

if error_msg:
    st.error(error_msg)
elif df is not None:
    # 1. 요약 정보 표시 (상단)
    st.success(f"총 {len(df)}건의 거래 내역을 가져왔습니다.")
    
    # 2. 데이터 테이블 표시
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        height=600
    )
    
    # 3. CSV 다운로드 버튼
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 CSV로 다운로드",
        data=csv,
        file_name='chamoe_prices.csv',
        mime='text/csv',
    )

import streamlit as st
import pandas as pd
import requests
import time

# 페이지 설정
st.set_page_config(
    page_title="성주 참외 경락시세 모니터링",
    page_icon="🍈",
    layout="wide"
)

# 헤더 UI
st.title("🍈 성주 참외 경락시세 (성주군 농업기술센터)")
st.markdown("URL: https://www.sj.go.kr/sj-atc/page.do?mnu_uid=4185")

@st.cache_data(ttl=600)  # 10분마다 데이터 갱신
def get_chamoe_prices():
    target_url = "https://www.sj.go.kr/sj-atc/page.do?mnu_uid=4185"
    
    try:
        # 1. 웹사이트 접속 (봇 차단 방지용 헤더 추가)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(target_url, headers=headers)
        
        # 2. 인코딩 처리 (한글 깨짐 방지)
        # requests가 자동으로 추측하지만, 실패할 경우를 대비해 utf-8 강제 설정
        response.encoding = 'utf-8'

        if response.status_code != 200:
            return None, f"사이트 접속 실패 (코드: {response.status_code})"

        # 3. HTML에서 테이블 추출 (Pandas 사용)
        # read_html은 페이지 내의 모든 <table> 태그를 리스트로 반환합니다.
        dfs = pd.read_html(response.text)
        
        if not dfs:
            return None, "데이터 테이블을 찾을 수 없습니다."

        # 4. 가장 적절한 테이블 선택
        # 보통 데이터가 가장 많은 테이블이 우리가 찾는 시세표입니다.
        df = max(dfs, key=len)
        
        # 5. 데이터 정제 (선택 사항)
        # 결측치(NaN)가 있는 행을 제거하거나 정리합니다.
        df = df.dropna(how='all')
        
        return df, None

    except Exception as e:
        return None, f"오류 발생: {str(e)}"

# 새로고침 버튼
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("🔄 데이터 새로고침", type="primary"):
        st.cache_data.clear()

# 데이터 로딩 및 표시
with st.spinner('성주군 농업기술센터에서 데이터를 가져오는 중입니다...'):
    df, error_msg = get_chamoe_prices()

if error_msg:
    st.error(error_msg)
elif df is not None:
    # 요약 정보
    st.success(f"총 {len(df)}건의 데이터를 성공적으로 불러왔습니다.")
    
    # 데이터 테이블 표시
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=600
    )
    
    # 다운로드 버튼
    csv_data = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 CSV 파일로 다운로드",
        data=csv_data,
        file_name='sj_chamoe_prices.csv',
        mime='text/csv'
    )

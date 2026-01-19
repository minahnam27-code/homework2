import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="제약/의료기기 조달 리스크 대시보드", page_icon="💊", layout="wide")

# 2. 데이터 로드 및 전처리
@st.cache_data
def load_data():
    file_path = '품목 수출입 총괄 _ 국내통계 - K-stat 수출입 무역통계.xls - sheet1.csv'
    # 데이터 상단 빈칸 제외 및 로드
    df = pd.read_csv(file_path, skiprows=3)
    df.columns = ['순번', '코드', '품목명', '24_수출', '24_수출증감', '24_수입', '24_수입증감', '24_교역', 
                  '25_수출', '25_수출증감', '25_수입', '25_수입증감', '25_교역']
    
    # '총계'행 제외 및 데이터 정제
    df = df.dropna(subset=['코드'])
    
    # 구매 직무용 지표 추가: 수입 의존도 (수입액 / 총교역액)
    df['수입의존도'] = (df['25_수입'] / df['25_교역']) * 100
    return df

try:
    df = load_data()

    # --- 사이드바: 리스크 필터 ---
    st.sidebar.header("⚠️ 리스크 관리 설정")
    risk_threshold = st.sidebar.slider("수입 증감률 경고 기준 (%)", 0, 100, 20)
    
    # --- 메인 화면 ---
    st.title("💊 제약/의료기기 구매 전략 대시보드")
    st.markdown("전년 대비 **수입 원가 변화**와 **해외 조달 의존도**를 분석하여 공급망 리스크를 관리합니다.")

    # 1. 리스크 품목 자동 감지 (KPI 영역)
    risky_items = df[df['25_수입증감'] >= risk_threshold]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("총 분석 품목 수", f"{len(df)}개")
    c2.metric("수입 급증 품목", f"{len(risky_items)}개", delta="주의 요망", delta_color="inverse")
    c3.metric("최고 수입 의존도", f"{df['수입의존도'].max():.1f}%")

    st.divider()

    # 2. 품목별 상세 분석
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("📦 품목별 조달 구조 (수출 vs 수입)")
        # 수출과 수입 비중을 비교하는 차트
        fig_compare = px.bar(df, x='품목명', y=['25_수출', '25_수입'], 
                             title="품목별 외자 구매 vs 내자 공급 비중",
                             barmode='group', height=500)
        st.plotly_chart(fig_compare, use_container_width=True)

    with col_right:
        st.subheader("🚨 수입 리스크 매트릭스")
        # 수입 금액이 크고 증감률이 높은 품목을 한눈에 파악
        fig_scatter = px.scatter(df, x='25_수입', y='25_수입증감', 
                                 size='25_교역', color='수입의존도',
                                 hover_name='품목명', title="수입 규모 대비 증감률 분석",
                                 color_continuous_scale='Reds')
        st.plotly_chart(fig_scatter, use_container_width=True)

    # 3. 구매 담당자용 상세 데이터
    st.subheader("📑 전략적 구매 관리 리스트")
    # 수입 증감률 순으로 정렬하여 보여줌
    st.dataframe(df[['품목명', '코드', '25_수입', '25_수입증감', '수입의존도']].sort_values(by='25_수입증감', ascending=False), 
                 use_container_width=True)

    st.success("""
    **💡 제약 구매 직무용 데이터 해석 팁**
    - **수입증감률(↑) & 수입의존도(↑):** 해외 공급사의 가격 인상이나 수급 불안정에 가장 취약한 품목입니다. 우선적인 단가 협상 및 대체선 발굴이 필요합니다.
    - **수입규모(↑) & 수출규모(↓):** 순수 수입 품목으로, 환율 변동 리스크에 직접 노출되어 있으므로 환헷지 전략이 중요합니다.
    """)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다. 파일명과 형식을 확인해 주세요. 오류: {e}")
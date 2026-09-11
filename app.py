import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(
    page_title="카페24 주문 현황 대시보드",
    page_icon="📈",
    layout="wide"
)

st.title("📈 카페24 주문 현황 및 매출 분석 대시보드")
st.caption("카페24 주문 목록 엑셀을 업로드하여 기간별 매출, 인기 상품 TOP 10, 지역별/수량별 판매 추이를 한눈에 시각화합니다.")

uploaded_file = st.file_uploader("카페24 주문 목록 엑셀 파일 업로드 (.xlsx, .xls)", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        
        # 필드명 매핑 및 유연한 처리
        product_col = next((c for c in ['상품명', '상품명(필수)'] if c in df.columns), None)
        qty_col = next((c for c in ['수량', '주문수량', '구매수량'] if c in df.columns), None)
        price_col = next((c for c in ['총 결제금액', '결제금액', '상품구매금액', '주문금액', '공급가액'] if c in df.columns), None)
        date_col = next((c for c in ['주문일시', '주문일자', '결제일시', '주문일'] if c in df.columns), None)
        
        if not product_col or not qty_col:
            st.error("❌ 엑셀 파일에서 '상품명' 및 '수량' 열을 찾을 수 없습니다. 카페24 원본 엑셀인지 확인해주세요.")
            st.stop()
            
        # 데이터 전처리
        df[qty_col] = pd.to_numeric(df[qty_col], errors='coerce').fillna(0)
        
        if price_col:
            df[price_col] = pd.to_numeric(df[price_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        # 핵심 지표 계산
        total_orders = len(df)
        total_quantity = df[qty_col].sum()
        total_sales = df[price_col].sum() if price_col else 0

        st.divider()
        st.subheader("📌 핵심 성과 요약 (KPI)")
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("총 주문 건수", f"{total_orders:,} 건")
        kpi2.metric("총 판매 수량", f"{total_quantity:,} 개")
        if price_col:
            kpi3.metric("총 매출액", f"₩ {total_sales:,.0f}")
        else:
            kpi3.metric("총 매출액", "매출 열 미포함")

        st.divider()

        # 차트 시각화
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("🔥 인기 상품 TOP 10 (판매 수량 기준)")
            top_products = df.groupby(product_col)[qty_col].sum().reset_index()
            top_products = top_products.sort_values(by=qty_col, ascending=False).head(10)
            
            fig_top = px.bar(
                top_products,
                x=qty_col,
                y=product_col,
                orientation='h',
                text=qty_col,
                labels={qty_col: '판매 수량', product_col: '상품명'},
                color=qty_col,
                color_continuous_scale='Blues'
            )
            fig_top.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            st.plotly_chart(fig_top, use_container_width=True)

        with col_right:
            if price_col:
                st.subheader("💰 매출 상위 TOP 10 상품")
                top_sales = df.groupby(product_col)[price_col].sum().reset_index()
                top_sales = top_sales.sort_values(by=price_col, ascending=False).head(10)
                
                fig_sales = px.bar(
                    top_sales,
                    x=price_col,
                    y=product_col,
                    orientation='h',
                    text=price_col,
                    labels={price_col: '매출액 (원)', product_col: '상품명'},
                    color=price_col,
                    color_continuous_scale='Greens'
                )
                fig_sales.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
                st.plotly_chart(fig_sales, use_container_width=True)
            else:
                st.info("💡 엑셀에 결제금액 관련 열이 포함되면 매출 상위 상품 차트도 함께 표시됩니다.")

        # 날짜 데이터가 있는 경우 시계열 분석
        if date_col:
            st.divider()
            st.subheader("📅 일자별/시간별 주문 추이")
            df['Date'] = pd.to_datetime(df[date_col], errors='coerce')
            daily_trend = df.groupby(df['Date'].dt.date)[qty_col].sum().reset_index()
            daily_trend.columns = ['날짜', '주문수량']
            
            fig_line = px.line(daily_trend, x='날짜', y='주문수량', markers=True, title="일자별 주문 수량 추이")
            st.plotly_chart(fig_line, use_container_width=True)

        # 전체 데이터 표 및 다운로드
        st.divider()
        st.subheader("📋 전체 요약 데이터")
        summary_df = df.groupby(product_col).agg(
            총판매수량=(qty_col, 'sum'),
            주문건수=(qty_col, 'count')
        ).reset_index().sort_values(by='총판매수량', ascending=False)
        
        st.dataframe(summary_df, use_container_width=True)

    except Exception as e:
        st.error(f"엑셀 데이터를 처리하는 도중 오류가 발생했습니다: {e}")
else:
    st.info("👆 카페24 주문 목록 엑셀 파일을 업로드해 주세요.")
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from stock_logic import get_stock_data, analyze_dividend_stock, get_ai_insight

st.set_page_config(page_title="AI Dividend Stock Bot", layout="wide", page_icon="🧠")

st.title("🧠 AI Dividend Stock Analyst")
st.markdown("ผู้ช่วยวิเคราะห์หุ้นปันผลระดับสถาบันการเงิน ผสานพลัง Data Science (RSI, MACD) และ Google Gemini AI")
st.write("---")

st.sidebar.header("🔍 ค้นหาหุ้น")
ticker_input = st.sidebar.text_input("กรอกรหัสหุ้นต่างประเทศ (Ticker):", value="KO").strip().upper()
search_button = st.sidebar.button("เริ่มวิเคราะห์ข้อมูล")

if ticker_input:
    with st.spinner(f"⏳ บอทกำลังดึงข้อมูลและให้ AI วิเคราะห์หุ้น {ticker_input}..."):
        stock_data = get_stock_data(ticker_input)
        
        if stock_data and not stock_data.get("hist").empty:
            analysis = analyze_dividend_stock(stock_data)
            ai_summary = get_ai_insight(ticker_input, stock_data, analysis)
            
            # แสดงชื่อบริษัท
            st.header(f"🏢 {stock_data.get('company_name', ticker_input)} ({ticker_input})")
            
            # แสดงกล่องสรุปสถานะการลงทุนด่วน
            st.success(f"📌 **ผลการประเมินจากระบบ:** {analysis.get('status')} ({analysis.get('reason')})")
            
            # แสดง Dashboard ตัวเลขสำคัญ
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(label="ราคาปัจจุบัน", value=f"${stock_data.get('current_price', 0):.2f}")
            with col2:
                st.metric(label="Dividend Yield", value=f"{analysis.get('div_yield', 0):.2f}%")
            with col3:
                st.metric(label="RSI (14 Days)", value=f"{analysis.get('rsi', 0):.1f}")
            with col4:
                beta_val = stock_data.get('beta', 'N/A')
                if isinstance(beta_val, (int, float)):
                    beta_display = f"{beta_val:.2f}"
                else:
                    beta_display = str(beta_val)
                st.metric(label="Beta (ความผันผวน)", value=beta_display)
            
            st.write("---")
            
            # ส่วนแสดงบทวิเคราะห์ของ AI
            st.subheader("🤖 บทวิเคราะห์เชิงลึกจาก AI (Executive Summary)")
            st.info(ai_summary)
            
            st.write("---")
            
            # ส่วนแสดงกราฟเทคนิคเชิงลึก
            st.subheader("📈 กราฟราคาเทคนิค และ RSI Momentum")
            hist = stock_data["hist"]
            
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            
            # กราฟราคาหลัก + เส้น SMA 200
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='Close Price', line=dict(color='#2980B9', width=2)), row=1, col=1)
            if 'SMA200' in hist.columns:
                fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA200'], name='SMA 200', line=dict(color='#F39C12', width=1.5, dash='dash')), row=1, col=1)
            
            # กราฟ RSI
            if 'RSI' in hist.columns:
                fig.add_trace(go.Scatter(x=hist.index, y=hist['RSI'], name='RSI (14)', line=dict(color='#8E44AD', width=1.5)), row=2, col=1)
            
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1, annotation_text="Overbought")
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1, annotation_text="Oversold")
            
            fig.update_layout(height=500, hovermode="x unified", margin=dict(l=20, r=20, t=20, b=20))
            fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
            fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1)
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error(f"❌ ไม่พบข้อมูลสำหรับหุ้นรหัส '{ticker_input}' กรุณาตรวจสอบตัวย่อหุ้นอีกครั้ง")
import streamlit as st
import plotly.graph_objects as go
from stock_logic import get_stock_data, analyze_dividend_stock

# 1. ตั้งค่าหน้าเว็บให้เป็นแบบกว้าง (Wide Mode) เพื่อความสวยงามของแดชบอร์ด
st.set_page_config(page_title="Dividend Stock Bot", layout="wide", page_icon="🍫")

# หัวข้อหลักของหน้าเว็บ
st.title("🤖 Dividend Stock Analysis Bot")
st.markdown("บอทวิเคราะห์หุ้นปันผลอัจฉริยะ ผสมผสานกลยุทธ์เชิงเทคนิค (SMA 200) และเชิงพื้นฐาน (Dividend Yield)")
st.write("---")

# 2. ส่วนแถบด้านข้าง (Sidebar) สำหรับรับค่าจากผู้ใช้
st.sidebar.header("🔍 ค้นหาหุ้น")
# ช่องกรอกชื่อหุ้น (กำหนดค่าเริ่มต้นเป็น KO หรือ Coca-Cola)
ticker_input = st.sidebar.text_input("กรอกรหัสหุ้นต่างประเทศ (Ticker):", value="KO").strip().upper()

# ปุ่มกดสำหรับเริ่มคำนวณ
search_button = st.sidebar.button("เริ่มวิเคราะห์ข้อมูล")

# 3. ส่วนการประมวลผลหลักเมื่อผู้ใช้กดปุ่ม หรือเปิดหน้าเว็บครั้งแรก
if ticker_input:
    with st.spinner(f"🤖 บอทกำลังดึงข้อมูลและวิเคราะห์หุ้น {ticker_input} โปรดรอสักครู่..."):
        # เรียกใช้ฟังก์ชันดึงข้อมูลจากไฟล์ stock_logic.py
        stock_data = get_stock_data(ticker_input)
        
        if stock_data and not stock_data["hist"].empty:
            # สั่งให้สมองของบอทคำนวณคำแนะนำ
            analysis = analyze_dividend_stock(stock_data)
            
            # --- ส่วนแสดงผลบนเว็บ ---
            # แสดงชื่อบริษัทเด่นๆ
            st.header(f"🏢 {stock_data['company_name']} ({ticker_input})")
            
            # แบ่งหน้าจอเป็น 3 คอลัมน์สำหรับโชว์ตัวเลขสรุปสำคัญ (KPI Cards)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(label="ราคาปัจจุบัน (USD)", value=f"${stock_data['current_price']:.2f}")
            with col2:
                st.metric(label="อัตราปันผลปัจจุบัน (Dividend Yield)", value=f"{analysis['div_yield']:.2f}%")
            with col3:
                st.metric(label="เงินปันผลรวมรอบ 1 ปีล่าสุด", value=f"${analysis['latest_year_div']:.2f}")
            
            # แสดงกล่องคำแนะนำจากบอท (สรุปผลอัจฉริยะ)
            st.subheader("🤖 ผลการวิเคราะห์จากบอท")
            # ถ้าเป็นกลุ่มน่าสะสมให้ขึ้นแถบสีเขียว (Success) ถ้าให้หลีกเลี่ยงให้ขึ้นแถบสีแดง (Error) นอกนั้นสีฟ้า (Info)
            if "น่าสะสม" in analysis['status']:
                st.success(f"**สถานะ:** {analysis['status']}\n\n**เหตุผล:** {analysis['reason']}")
            elif "หลีกเลี่ยง" in analysis['status']:
                st.error(f"**สถานะ:** {analysis['status']}\n\n**เหตุผล:** {analysis['reason']}")
            else:
                st.info(f"**...สถานะ:** {analysis['status']}\n\n**เหตุผล:** {analysis['reason']}")
                
            st.write("---")
            
            # --- ส่วนการวาดกราฟเทคนิคด้วย Plotly ---
            st.subheader("📈 กราฟราคาหุ้นพร้อมเส้นค่าเฉลี่ย SMA 200 วัน")
            
            hist = stock_data["hist"]
            # สร้างกราฟราคาปิด (Line Chart)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Close'], name='ราคาปิด (Close)', line=dict(color='#8B5A2B', width=2)))
            # เพิ่มเส้น SMA 200 วันเข้าไปในกราฟเดียวกันเพื่อเปรียบเทียบเทรนด์
            fig.add_trace(go.Scatter(x=hist.index, y=hist['SMA200'], name='เส้น SMA 200 วัน', line=dict(color='#FF9900', width=1.5, dash='dash')))
            
            # ตกแต่งหน้าตากราฟ ซูมเข้าออกได้ มีปุ่มลากแถบเวลาด้านล่าง
            fig.update_layout(
                xaxis_title="วันที่",
                yaxis_title="ราคาหุ้น (USD)",
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=20, b=20)
            )
            # แสดงกราฟลงบนหน้าเว็บ Streamlit
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error(f"❌ ไม่พบข้อมูลสำหรับหุ้นรหัส '{ticker_input}' กรุณาตรวจสอบตัวย่อตัวอักษรอีกครั้งครับ")
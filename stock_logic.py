import yfinance as yf
import pandas as pd

def get_stock_data(ticker_name):
    """
    ฟังก์ชันสำหรับดึงข้อมูลราคาหุ้นและข้อมูลปันผลย้อนหลัง 5 ปี
    """
    try:
        # เชื่อมต่อกับ Yahoo Finance ดึงออบเจกต์หุ้น
        stock = yf.Ticker(ticker_name)
        
        # ดึงราคาย้อนหลัง 5 ปี (ช่วงเวลาที่กำลังดีสำหรับการดูแนวโน้ม)
        hist = stock.history(period="5y")
        
        # ดึงประวัติการจ่ายปันผลย้อนหลัง
        dividends = stock.dividends
        
        # ดึงข้อมูลพื้นฐานทั่วไป (เช่น ราคาปัจจุบัน, ชื่อบริษัท)
        info = stock.info
        current_price = info.get('currentPrice', None)
        # ถ้าหา currentPrice ไม่เจอ ให้ใช้ราคาปิดล่าสุดแทน
        if current_price is None and not hist.empty:
            current_price = hist['Close'].iloc[-1]
            
        return {
            "hist": hist,
            "dividends": dividends,
            "current_price": current_price,
            "company_name": info.get('longName', ticker_name)
        }
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการดึงข้อมูลหุ้น {ticker_name}: {e}")
        return None

def analyze_dividend_stock(stock_data):
    """
    สมองของบอท: วิเคราะห์ความน่าสนใจของหุ้นปันผล
    ด้วยเงื่อนไขเชิงเทคนิค (Moving Average) และเชิงพื้นฐาน (Dividend Yield)
    """
    hist = stock_data["hist"]
    dividends = stock_data["dividends"]
    current_price = stock_data["current_price"]
    
    if hist.empty or current_price is None:
        return {"status": "ไม่สามารถวิเคราะห์ได้", "reason": "ข้อมูลราคาไม่เพียงพอ"}
    
    # --- 1. วิเคราะห์เชิงเทคนิค (Technical Analysis) ---
    # คำนวณเส้นค่าเฉลี่ย 200 วัน (SMA 200) เพื่อดูแนวโน้มระยะยาว
    hist['SMA200'] = hist['Close'].rolling(window=200).mean()
    last_sma200 = hist['SMA200'].iloc[-1]
    
    # เช็คว่าราคาปัจจุบันอยู่เหนือเส้น 200 วันไหม (ขาขึ้น หรือ ขาลง)
    is_uptrend = current_price > last_sma200 if not pd.isna(last_sma200) else True

    # --- 2. วิเคราะห์เชิงพื้นฐานปันผล (Dividend Analysis) ---
    # หาผลรวมปันผลที่จ่ายในปีล่าสุด (ย้อนหลัง 365 วันล่าสุด)
    latest_year_div = dividends.last('365D').sum() if not dividends.empty else 0
    
    # คำนวณอัตราส่วนปันผลปัจจุบัน (Dividend Yield %)
    div_yield = (latest_year_div / current_price) * 100 if current_price > 0 else 0

    # --- 3. สรุปคำแนะนำด้วยเงื่อนไขบอท (Rule-based Recommendation) ---
    if div_yield >= 4.0 and is_uptrend:
        status = "🌟 น่าสะสมมาก (Strong Buy)"
        reason = f"ปันผลสูงเด่น ({div_yield:.2f}%) และราคาอยู่ในเทรนด์ขาขึ้นเหนือเส้น 200 วัน"
    elif div_yield >= 4.0 and not is_uptrend:
        status = "⏳ รอจังหวะ (Watchlist)"
        reason = f"ปันผลน่าสนใจ ({div_yield:.2f}%) แต่ราคายังเป็นเทรนด์ขาลงใต้เส้น 200 วัน ควรรอให้ราคานิ่งก่อน"
    elif 0 < div_yield < 4.0 and is_uptrend:
        status = "📈 ถือ/ซื้อเก็งกำไร (Hold/Buy)"
        reason = f"ราคาอยู่ในเทรนด์ขาขึ้น แต่ปันผลปานกลาง ({div_yield:.2f}%)"
    else:
        status = "❌ หลีกเลี่ยงก่อน (Avoid)"
        reason = "ไม่มีการจ่ายปันผล หรือมีความเสี่ยงสูงเกินไปในขณะนี้"
        
    return {
        "status": status,
        "reason": reason,
        "div_yield": div_yield,
        "latest_year_div": latest_year_div
    }
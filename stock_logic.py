import yfinance as yf
import pandas as pd
import numpy as np
import google.generativeai as genai

# ⚠️ ใส่ API Key ของคุณตรงนี้ครับ
GEMINI_API_KEY = "วาง_API_KEY_ของคุณตรงนี้"
genai.configure(api_key=GEMINI_API_KEY)

def get_stock_data(ticker_name):
    """ดึงข้อมูลราคา ปันผล ข้อมูลพื้นฐาน จาก Yahoo Finance"""
    try:
        stock = yf.Ticker(ticker_name)
        hist = stock.history(period="5y")
        dividends = stock.dividends
        info = stock.info
        
        current_price = info.get('currentPrice', None)
        if current_price is None and not hist.empty:
            current_price = hist['Close'].iloc[-1]
            
        return {
            "hist": hist,
            "dividends": dividends,
            "current_price": current_price,
            "company_name": info.get('longName', ticker_name),
            "beta": info.get('beta', None)
        }
    except Exception as e:
        print(f"Error getting data for {ticker_name}: {e}")
        return None

def analyze_dividend_stock(stock_data):
    """คำนวณอินดิเคเตอร์และเงื่อนไขหุ้นปันผลเชิงลึก"""
    hist = stock_data["hist"].copy()
    dividends = stock_data["dividends"]
    current_price = stock_data["current_price"]
    beta = stock_data.get("beta", None)
    
    if hist.empty or current_price is None:
        return {"status": "ไม่สามารถวิเคราะห์ได้", "reason": "ข้อมูลไม่เพียงพอ"}
    
    # 1. คำนวณเทรนด์ระยะยาว (SMA 200)
    hist['SMA200'] = hist['Close'].rolling(window=200).mean()
    last_sma200 = hist['SMA200'].iloc[-1]
    is_uptrend = current_price > last_sma200 if not pd.isna(last_sma200) else True

    # 2. คำนวณโมเมนตัม (RSI 14)
    delta = hist['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    hist['RSI'] = 100 - (100 / (1 + rs))
    last_rsi = hist['RSI'].iloc[-1]

    # 3. สัญญาณการกลับตัว (MACD)
    hist['EMA12'] = hist['Close'].ewm(span=12, adjust=False).mean()
    hist['EMA26'] = hist['Close'].ewm(span=26, adjust=False).mean()
    hist['MACD'] = hist['EMA12'] - hist['EMA26']
    hist['Signal_Line'] = hist['MACD'].ewm(span=9, adjust=False).mean()
    macd_bullish = hist['MACD'].iloc[-1] > hist['Signal_Line'].iloc[-1]

    stock_data["hist"] = hist

    # 4. คำนวณอัตราผลตอบแทนปันผล (Dividend Yield) ย้อนหลัง 1 ปี
    if not dividends.empty:
        cutoff_date = dividends.index[-1] - pd.Timedelta(days=365)
        latest_year_div = dividends[dividends.index >= cutoff_date].sum()
    else:
        latest_year_div = 0
    
    div_yield = (latest_year_div / current_price) * 100 if current_price > 0 else 0

    # 5. ประเมินความแข็งแกร่งทางเทคนิค
    rsi_status = "โซนปกติ (Sideways)"
    if not pd.isna(last_rsi):
        if last_rsi < 30: rsi_status = "Oversold (ราคาถูกมาก ขายมากเกินไป)"
        elif last_rsi > 70: rsi_status = "Overbought (ราคาแพง ซื้อมากเกินไป)"
            
    # สรุปสถานะหุ้น
    if div_yield >= 4.0 and last_rsi < 30:
        status, reason = "🔥 โอกาสเก็บของถูก (Strong Buy)", f"ปันผลคุ้มค่าสูง ({div_yield:.2f}%) และราคาเข้าโซน Oversold มีโอกาสดีดกลับสูง"
    elif div_yield >= 4.0 and is_uptrend and (last_rsi < 60 or macd_bullish):
        status, reason = "🌟 น่าสะสมมาก (Accumulate)", f"ปันผลสูง ({div_yield:.2f}%) และแนวโน้มราคาเป็นขาขึ้นชัดเจน"
    elif div_yield >= 4.0 and not is_uptrend:
        status, reason = "⏳ รอจังหวะ (Watchlist)", f"ปันผลดี ({div_yield:.2f}%) แต่โครงสร้างราคายังเป็นขาลง ควรสะสมเมื่อเริ่มสร้างฐานได้"
    elif 0 < div_yield < 4.0 and is_uptrend:
        status, reason = "📈 ถือ/ซื้อเก็งกำไร (Hold/Trade)", f"แนวโน้มแข็งแกร่ง แต่ปันผลระดับปานกลาง ({div_yield:.2f}%) เหมาะเน้นส่วนต่างราคาทุน"
    else:
        status, reason = "❌ หลีกเลี่ยงก่อน (Avoid)", "ไม่มีปันผล หรือความเสี่ยงทางเทคนิค (ขาลง/Overbought) อยู่ในระดับสูง"
        
    return {
        "status": status, "reason": reason, "div_yield": div_yield,
        "latest_year_div": latest_year_div, "rsi": last_rsi,
        "rsi_status": rsi_status, "macd_bullish": macd_bullish, "beta": beta,
        "is_uptrend": is_uptrend
    }

def get_ai_insight(ticker, stock_data, analysis_result):
    """ส่งข้อมูลตัวเลขทางเทคนิคทั้งหมดให้ AI ระดับวิเคราะห์เชิงลึก"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "วาง_API_KEY_ของคุณตรงนี้":
        return "⚠️ กรุณาใส่ API Key ในไฟล์ stock_logic.py ก่อนใช้งานครับ"
    
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # เพิ่มมิติข้อมูลให้ AI วิเคราะห์สภาวะตลาดและพฤติกรรมราคาจากตัวเลข
        prompt = f"""
        คุณคือนักวิเคราะห์หุ้นปันผลและผู้เชี่ยวชาญด้าน Quantitative Finance (ภาษาไทย)
        โปรดเขียนบทวิเคราะห์ระดับมืออาชีพสำหรับหุ้น {ticker} ({stock_data.get('company_name', ticker)}) โดยใช้ข้อมูลดิบทางสถิติต่อไปนี้:

        [ข้อมูลราคาและพื้นฐาน]
        - ราคาตลาดปัจจุบัน: ${stock_data.get('current_price', 0):.2f}
        - ค่า Beta (ความผันผวนเทียบตลาด): {analysis_result.get('beta', 'N/A')}

        [ข้อมูลเงินปันผล]
        - อัตราส่วนปันผล (Dividend Yield): {analysis_result.get('div_yield', 0):.2f}%
        - มูลค่าเงินปันผลที่จ่ายในรอบปีล่าสุด: ${analysis_result.get('latest_year_div', 0):.2f} ต่อหุ้น

        [ข้อมูลสัญญาณทางเทคนิค (Technical Indicators)]
        - ดัชนีโมเมนตัม RSI (14): {analysis_result.get('rsi', 0):.2f} ซึ่งอยู่ในสภาวะ {analysis_result.get('rsi_status', '')}
        - แนวโน้มระยะยาว (SMA 200): {'อยู่เหนือเส้น SMA 200 (แนวโน้มขาขึ้น)' if analysis_result.get('is_uptrend') else 'อยู่ใต้เส้น SMA 200 (แนวโน้มขาลง)'}
        - โมเมนตัมระยะสั้น MACD: {'เกิดสัญญาณ Bullish Crossover (แรงซื้อหนุน)' if analysis_result.get('macd_bullish') else 'เกิดสัญญาณ Bearish (แรงขายคุม)'}

        [ผลการคำนวณของระบบ]: {analysis_result.get('status')} -> เพราะ {analysis_result.get('reason')}

        คำสั่งในการเขียนบทวิเคราะห์:
        1. บทสรุปสภาวะปัจจุบัน: ตีความความสัมพันธ์ระหว่าง "ปันผล" กับ "แนวโน้มราคาทางเทคนิค" ว่ามีความปลอดภัยแค่ไหน
        2. การประเมินความเสี่ยง: ประเมินจากค่า Beta และความสุ่มเสี่ยงของราคา (เช่น เข้าโซนซื้อมาก/ขายมากเกินไปหรือไม่)
        3. คำแนะนำเชิงกลยุทธ์ที่ชัดเจน: ฟันธงว่าสำหรับนักลงทุนเน้นปันผล (Dividend Investor) ควร ซื้อสะสม, ถือ, หรือชะลอการลงทุน พร้อมระบุแผนการเข้าซื้อที่เหมาะสม
        """
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ AI เกิดข้อผิดพลาดในการวิเคราะห์: {e}"
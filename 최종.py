import sqlite3
import requests
import threading
import webbrowser
import time
from datetime import datetime
from collections import Counter
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, jsonify

# --- [설정 구간] ---
TARGET_URL = "https://gall.dcinside.com/mini/board/lists?id=vtubersnipe"
ISE_KEYWORDS = ["굴깨", "굴세돌", "굴계돌", "이계돌", "이파리", "굴짱개", "굴단", "65억", "아이네", "징버거", "버거", "주르르", "르르", "릴파", "비챤", "고세구", "세구", "포차", "굴"]

DB_NAME = "ise_monitor_final.db"
SCAN_INTERVAL = 3600 
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}

app = Flask(__name__)

# --- [데이터베이스 로직] ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs (timestamp TEXT, count INTEGER, keywords TEXT)''')
    conn.commit()
    conn.close()

def save_data(timestamp, count, keywords_str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO logs VALUES (?, ?, ?)", (timestamp, count, keywords_str))
    conn.commit()
    conn.close()

# --- [모니터링 엔진] ---
def monitoring_loop():
    is_first_scan = True
    while True:
        if not is_first_scan:
            time.sleep(SCAN_INTERVAL)
        now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            response = requests.get(TARGET_URL, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            posts = soup.select(".ub-content.us-post .gall_tit a")
            found_keywords = []
            ise_count = 0
            for p in posts:
                title = p.text.strip()
                for k in ISE_KEYWORDS:
                    if k in title:
                        found_keywords.append(k)
                        ise_count += 1
                        break
            save_data(now_time, ise_count, ",".join(found_keywords))
            if is_first_scan:
                # 서버 시작 후 브라우저 오픈 지연 실행
                threading.Timer(2.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
                is_first_scan = False
        except Exception as e:
            print(f"❌ 데이터 수집 오류: {e}")

# --- [웹 UI 코드 (HTML_TEMPLATE)] ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PROJECT : UTCK</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@900&family=Noto+Sans+KR:wght@400;700;900&display=swap');
        
        * { box-sizing: border-box; }
        html { scroll-behavior: smooth; scroll-snap-type: y mandatory; }
        
        body { 
            background-color: #000; 
            background-image: radial-gradient(#222 1.5px, transparent 1.5px);
            background-size: 40px 40px;
            color: #fff; 
            font-family: 'Noto Sans KR', sans-serif; 
            margin: 0; 
            overflow-x: hidden; 
        }

        nav {
            position: fixed; top: 0; width: 100%; height: 90px;
            background: rgba(0,0,0,0.9); backdrop-filter: blur(15px);
            display: flex; justify-content: space-between; align-items: center;
            padding: 0 60px; z-index: 1000; border-bottom: 5px solid #fff;
        }
        .logo { font-family: 'Montserrat', sans-serif; font-weight: 900; font-size: 2rem; letter-spacing: 2px; }
        .nav-links { display: flex; gap: 40px; }
        .nav-links a { color: #fff; text-decoration: none; font-size: 1rem; font-weight: 900; text-transform: uppercase; transition: 0.2s; }
        .nav-links a:hover { opacity: 0.6; }

        section {
            height: 100vh; width: 100%; display: flex; flex-direction: column;
            justify-content: center; align-items: center; padding: 0 10%;
            scroll-snap-align: start; position: relative;
        }

        #main-hero { text-align: center; }
        #main-hero h1 { 
            font-family: 'Montserrat', sans-serif; font-weight: 900; 
            font-size: 10vw; margin: 0; letter-spacing: -5px; line-height: 0.85;
        }
        #main-hero p { 
            font-weight: 900; font-size: 1.8rem; color: #fff; 
            margin-top: 40px; letter-spacing: 10px; border: 5px solid #fff;
            padding: 15px 40px; background: #000; display: inline-block;
        }

        .summary-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 30px; width: 100%; max-width: 1300px; }
        .summary-card { 
            background: #000; padding: 70px 30px; text-align: center; 
            border: 6px solid #fff; box-shadow: 20px 20px 0px #444;
        }
        .card-label { color: #fff; font-size: 1.2rem; margin-bottom: 25px; letter-spacing: 5px; font-weight: 900; }
        .card-value { font-size: 5rem; font-weight: 900; font-family: 'Montserrat', sans-serif; }

        .marquee-wrapper { width: 100vw; overflow: hidden; border-top: 6px solid #fff; border-bottom: 6px solid #fff; background: #000; padding: 60px 0; }
        .marquee-content { display: flex; white-space: nowrap; animation: scrolling 30s linear infinite; gap: 120px; }
        @keyframes scrolling { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
        .keyword-tag { 
            font-family: 'Montserrat', sans-serif; font-size: 7rem; font-weight: 900; 
            color: #000; -webkit-text-stroke: 3px #fff; transition: 0.3s; 
        }
        .keyword-tag:hover { color: #fff; -webkit-text-stroke: 0; }

        .chart-container { 
            width: 100%; max-width: 1300px; height: 550px; background: #000; 
            border: 6px solid #fff; padding: 50px; box-shadow: 25px 25px 0px #333;
        }
        
        .section-title { 
            position: absolute; top: 140px; left: 60px; font-size: 1.5rem; 
            color: #fff; background: #000; padding: 10px 20px; border: 4px solid #fff;
            letter-spacing: 8px; font-weight: 900; text-transform: uppercase; 
        }
    </style>
</head>
<body>

    <nav>
        <div class="logo">UTCK.PROJ</div>
        <div class="nav-links">
            <a href="#main-hero">HOME</a>
            <a href="#summary">SUMMARY</a>
            <a href="#keywords">KEYWORDS</a>
            <a href="#trend">TREND</a>
        </div>
    </nav>

    <section id="main-hero">
        <h1>PROJECT<br>UTCK</h1>
        <p>모든 버츄얼 아티스트를 위해 행동하겠습니다.</p>
    </section>

    <section id="summary">
        <div class="section-title">01 / Summary</div>
        <div class="summary-grid">
            <div class="summary-card">
                <div class="card-label">TOTAL</div>
                <div class="card-value" id="sum-total">0</div>
            </div>
            <div class="summary-card">
                <div class="card-label">PEAK</div>
                <div class="card-value" id="sum-peak" style="font-size: 2.5rem;">-</div>
            </div>
            <div class="summary-card">
                <div class="card-label">STATUS</div>
                <div class="card-value" style="color:#0f0">ACTIVE</div>
            </div>
        </div>
    </section>

    <section id="keywords">
        <div class="section-title">02 / Live Keywords</div>
        <div class="marquee-wrapper">
            <div class="marquee-content" id="keyword-marquee"></div>
        </div>
    </section>

    <section id="trend">
        <div class="section-title">03 / Trend Analysis</div>
        <div class="chart-container">
            <canvas id="iseChart"></canvas>
        </div>
    </section>

    <script>
        let myChart = null;
        async function refreshData() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                
                document.getElementById('sum-total').innerText = data.daily_total;
                document.getElementById('sum-peak').innerText = data.peak_time || "-";

                const marquee = document.getElementById('keyword-marquee');
                const words = Object.keys(data.keywords_count);
                if (words.length > 0) {
                    const content = words.map(w => `<span class="keyword-tag">${w}</span>`).join('');
                    marquee.innerHTML = content + content;
                } else {
                    marquee.innerHTML = '<span class="keyword-tag">SCANNING...</span>';
                }

                const ctx = document.getElementById('iseChart');
                if (ctx && data.labels.length > 0) {
                    if(myChart) myChart.destroy();
                    myChart = new Chart(ctx.getContext('2d'), {
                        type: 'line',
                        data: {
                            labels: data.labels,
                            datasets: [{
                                data: data.counts,
                                borderColor: '#fff',
                                borderWidth: 8,
                                pointRadius: 10,
                                pointBackgroundColor: '#fff',
                                pointBorderColor: '#000',
                                pointBorderWidth: 4,
                                tension: 0.3,
                                fill: false
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                x: { ticks: { color: '#fff', font: { size: 16, weight: '900' } }, grid: { display: false } },
                                y: { ticks: { color: '#fff', font: { size: 16, weight: '900' } }, grid: { color: '#444', lineWidth: 2 }, beginAtZero: true }
                            }
                        }
                    });
                }
            } catch (e) { console.error("Data update failed:", e); }
        }
        refreshData();
        setInterval(refreshData, 60000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/stats')
def get_stats():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT timestamp, count, keywords FROM logs ORDER BY timestamp DESC LIMIT 24")
    rows = c.fetchall()[::-1]
    conn.close()

    labels = [r[0].split(' ')[1][:5] for r in rows]
    full_labels = [r[0] for r in rows]
    counts = [r[1] for r in rows]
    
    all_k = []
    for r in rows:
        if r[2]: all_k.extend(r[2].split(','))
    k_counts = dict(Counter(all_k))

    daily_total = sum(counts)
    peak_time = full_labels[counts.index(max(counts))].split(' ')[1][:5] if counts else "-"

    return jsonify({
        "labels": labels,
        "counts": counts,
        "keywords_count": k_counts,
        "daily_total": daily_total,
        "peak_time": peak_time
    })

if __name__ == "__main__":
    init_db()
    # 모니터링 스레드 시작
    threading.Thread(target=monitoring_loop, daemon=True).start()
    # 서버 실행
    app.run(host='0.0.0.0', port=5000)
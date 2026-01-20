import logging
import random
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy

# Proje dosyaları
from config import Config
from tmdb_manager import get_manager
from engine import QuestionEngine

# --- 1. Uygulama Yapılandırması ---
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

# Loglama
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CineSaga.App")

# Veritabanı ve Motor
db = SQLAlchemy(app)
engine = QuestionEngine()

# --- 2. Modeller ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    current_level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    lives = db.Column(db.Integer, default=5) # Sonsuz modda kullanılmasa da DB yapısı bozulmasın diye tutuyoruz
    last_daily_played = db.Column(db.String(20), default="")
    total_correct = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id, 
            "username": self.username, 
            "level": self.current_level,
            "xp": self.xp, 
            "lives": "∞",  # Frontend'e her zaman Sonsuz gönderiyoruz
            "can_play_daily": self.last_daily_played != datetime.now().strftime('%Y-%m-%d')
        }

with app.app_context():
    db.create_all()

# --- 3. Yardımcılar ---
def get_current_user():
    if 'user_id' not in session:
        new_user = User(username=f"Sinefil_{random.randint(1000, 9999)}")
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return get_current_user()
    return user

# --- 4. Rotalar ---
@app.route('/')
def index():
    try:
        user = get_current_user()
        return render_template('index.html', user=user.to_dict())
    except Exception as e:
        logger.error(f"Sistem Hatası: {e}")
        return "Sistem şu an meşgul, lütfen daha sonra tekrar deneyin.", 500

@app.route('/api/game/start', methods=['POST'])
def start_level():
    user = get_current_user()
    
    # Can kontrolü devre dışı (Sonsuz Mod)
    
    # İnovatif Motoru Çağır
    is_daily = False
    questions = engine.generate_level_content(user, is_daily)
    
    return jsonify({
        "status": "success", 
        "questions": questions, 
        "level": user.current_level
    })

@app.route('/api/game/daily', methods=['POST'])
def daily_start():
    user = get_current_user()
    today = datetime.now().strftime('%Y-%m-%d')
    
    if user.last_daily_played == today:
        return jsonify({"status": "error", "error": "Bugünkü Premiere hakkını kullandın!"}), 400

    # Günlük Mod: True
    questions = engine.generate_level_content(user, is_daily=True)
    
    return jsonify({
        "status": "success", 
        "questions": questions
    })

@app.route('/api/game/submit', methods=['POST'])
def submit_answer():
    """
    Cevabı işler ve puanlama yapar.
    GÜNCELLEME: İpucu kullanıldıysa (hint_used) puan yarıya düşer.
    """
    data = request.json
    user = get_current_user()
    
    is_correct = data.get('correct')
    is_daily = data.get('is_daily')
    hint_used = data.get('hint_used', False) # Frontend'den gelen ipucu bilgisi

    if is_correct:
        # Temel Puan Hesaplama
        xp_gain = 100 if is_daily else 15
        
        # CEZA MANTIĞI: İpucu kullanıldıysa puanı yarıya düşür
        if hint_used:
            xp_gain = int(xp_gain / 2) # 15 -> 7, 100 -> 50
            logger.info(f"Kullanıcı {user.username} ipucu kullandı. Puan kırıldı: +{xp_gain} XP")
        else:
            logger.info(f"Kullanıcı {user.username} tam puan aldı: +{xp_gain} XP")

        user.xp += xp_gain
        user.total_correct += 1
        
        if is_daily:
            user.last_daily_played = datetime.now().strftime('%Y-%m-%d')
    else:
        # Yanlış cevapta sadece log tutuyoruz (Sonsuz can)
        logger.info(f"Kullanıcı {user.username} yanlış cevap verdi. Oyun devam ediyor.")
    
    db.session.commit()
    # Frontend'e her zaman sonsuz işareti dön
    return jsonify({"status": "success", "xp": user.xp, "lives": "∞"})

@app.route('/api/game/levelup', methods=['POST'])
def level_up():
    user = get_current_user()
    user.current_level += 1
    db.session.commit()
    return jsonify({"status": "success", "new_level": user.current_level})

if __name__ == '__main__':
    app.run(debug=True, port=8080)
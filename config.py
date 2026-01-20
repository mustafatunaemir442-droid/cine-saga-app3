import os
import secrets

class Config:
    """
    CineSaga Pro - Noir Edition 2026
    --------------------------------
    Uygulamanın tüm çevresel ayarlarını, oyun mekaniklerini, veritabanı 
    yollarını ve güvenlik protokollerini yöneten merkezi konfigürasyon sınıfı.
    
    Bu dosyadaki değişiklikler tüm oyun motorunu dinamik olarak etkiler.
    """

    # --- 1. Dizin ve Dosya Yapılandırması ---
    # Uygulamanın ana dizinini belirle (Dosya yollarının her sistemde çalışması için)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # TMDB Veri Önbelleği (JSON) yolu
    MOVIE_CACHE_FILE = os.path.join(BASE_DIR, "movies_cache.json")

    # --- 2. Flask ve Güvenlik Ayarları ---
    # CSRF ve Session güvenliği için gizli anahtar
    # Her başlatmada yeni bir anahtar üretmek oturumları sıfırlayabilir, 
    # sabit bir string kullanımı tercih edilir.
    SECRET_KEY = os.environ.get('SECRET_KEY') or "cine_saga_noir_vignette_secret_2026_x88"
    
    # JSON verilerinde Türkçe karakter desteği
    JSON_AS_ASCII = False

    # --- 3. Veritabanı (SQLAlchemy) Yapılandırması ---
    # Kullanıcı verilerini saklayan SQLite veritabanı yolu
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BASE_DIR, 'cinesaga_pro.db')
    
    # Performans için nesne takibini kapat
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- 4. TMDB API Entegrasyonu ---
    # Sinematik verileri çekmek için gerekli API anahtarı
    TMDB_API_KEY = "e5e05720a7328681bbc476b7c0eddb85"
    
    # Görsel Sunucu URL'leri (TMDB Standartları)
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p/"
    POSTER_SIZE = "w500"
    BACKDROP_SIZE = "w780"

    # --- 5. Oyun Mekanikleri ve Denge Ayarları ---
    # Başlangıç can sayısı
    STARTING_LIVES = 5
    
    # Doğru cevap başına kazanılan temel deneyim puanı (XP)
    BASE_XP_REWARD = 15
    
    # Günlük soru (Premiere) için ek XP ödülü
    DAILY_XP_BONUS = 50
    
    # Maksimum Seviye (Harita uzunluğu)
    TOTAL_LEVELS = 500
    
    # Seviye başına zorluk havuzunun büyüklüğü (Film sayısı)
    LEVEL_POOL_SIZE = 100
    
    # 'Deep Dive' (Odaklanmış bölüm) çıkma olasılığı (%30)
    DEEP_DIVE_PROBABILITY = 0.30

    # --- 6. UI / UX Stil Parametreleri (Frontend Referans) ---
    # Bu ayarlar frontend tarafında CSS değişkenlerine (CSS Variables) bağlanabilir
    THEME_COLORS = {
        "primary_gold": "#d4af37",
        "background_noir": "#050505",
        "card_shadow": "rgba(0, 0, 0, 0.8)",
        "accent_gray": "#222222"
    }

    # --- 7. Sunucu Çalıştırma Ayarları ---
    # Geliştirme modunda hata ayıklayıcıyı aç
    DEBUG = True
    
    # Uygulamanın çalışacağı port
    PORT = 8080
    
    # Yerel ağdan erişim (0.0.0.0 her yerden erişim sağlar)
    HOST = '127.0.0.1'

    # --- 8. Hata ve Loglama Yapılandırması ---
    # Log dosyası yolu
    LOG_FILE = os.path.join(BASE_DIR, "cinesaga_game.log")
    
    # Loglama seviyesi (INFO, WARNING, ERROR, CRITICAL)
    LOG_LEVEL = "INFO"

    @staticmethod
    def init_app(app):
        """Uygulama başlatılırken özel işlemler yapmak için kullanılır."""
        pass

# Profesyonel kullanım için farklı ortam sınıfları (Opsiyonel)
class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # Canlı ortamda DB URI farklı olabilir
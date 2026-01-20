import json
import os
import random
import logging
from typing import List, Dict, Any, Optional
from config import Config

class TMDBManager:
    """
    CineSaga Pro - Sinematik Veri ve Havuz Yönetim Sistemi
    ----------------------------------------------------
    Bu sınıf, 2000 filmlik arşivi yöneten ve oyun motoruna veri sunan merkezdir.
    """
    def __init__(self, cache_path: str = None):
        # Loglama konfigürasyonu
        self.logger = logging.getLogger("CineSaga.TMDBManager")
        self.logger.setLevel(logging.INFO)
        
        # Dosya yolları ve veri yapıları
        self.cache_path = cache_path or Config.MOVIE_CACHE_FILE
        self.all_movies: List[Dict[str, Any]] = []
        self.total_levels = Config.TOTAL_LEVELS
        self.window_size = Config.LEVEL_POOL_SIZE
        
        # Sistemi başlat
        self._initialize_system()

    def _initialize_system(self) -> None:
        """Sistemi ayağa kaldırır ve veriyi yükler."""
        if not self._check_file_integrity():
            return
        self._load_and_sanitize_data()
        self._sort_by_difficulty()

    def _check_file_integrity(self) -> bool:
        if not os.path.exists(self.cache_path):
            self.logger.critical(f"HATA: '{self.cache_path}' dosyası bulunamadı.")
            return False
        return True

    def _load_and_sanitize_data(self) -> None:
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Kritik veri kontrolü
            self.all_movies = [
                movie for movie in data
                if all(key in movie and movie[key] for key in ['id', 'title', 'overview'])
            ]
            self.logger.info(f"Yükleme Başarılı: {len(self.all_movies)} film hazır.")
        except Exception as e:
            self.logger.error(f"Veri yükleme hatası: {str(e)}")

    def _sort_by_difficulty(self) -> None:
        """Filmleri popülerliğe göre sıralar."""
        if self.all_movies:
            self.all_movies.sort(key=lambda x: x.get('popularity', 0), reverse=True)

    def get_pool_by_level(self, level: int, is_daily: bool = False) -> List[Dict[str, Any]]:
        if not self.all_movies: return []
        total_count = len(self.all_movies)
        
        if is_daily:
            return self.all_movies[int(total_count * 0.85):]

        safe_level = max(1, min(level, self.total_levels))
        max_shift = max(0, total_count - self.window_size)
        step_size = max_shift / (self.total_levels - 1) if self.total_levels > 1 else 0
        start_index = int((safe_level - 1) * step_size)
        return self.all_movies[start_index : start_index + self.window_size]

    def validate_content_readiness(self, movie: Dict[str, Any], q_type: str) -> bool:
        checks = {
            'poster': 'poster_path',
            'scene': 'backdrop_path',
            'riddle': 'overview',
            'year': 'release_date'
        }
        if q_type in checks:
            return bool(movie.get(checks[q_type]))
        return 'cast' in movie if q_type in ['actor', 'char'] else True

    def generate_distractors(self, correct_title: str, pool: List[Dict[str, Any]], count: int = 3) -> List[str]:
        potential_wrongs = [
            m['title'].strip() for m in pool 
            if m['title'].strip().lower() != correct_title.strip().lower()
        ]
        if len(potential_wrongs) < count:
            potential_wrongs = [m['title'] for m in self.all_movies if m['title'] != correct_title]
        return random.sample(list(set(potential_wrongs)), min(count, len(potential_wrongs)))

# --- Singleton Yapısı (Hata Giderildi) ---
_instance = None

def get_manager():
    global _instance
    if _instance is None:
        _instance = TMDBManager()
    return _instance
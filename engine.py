import random
import re
import logging
import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set

# ==============================================================================
# BÖLÜM 0: TİP TANIMLAMALARI VE SABİTLER
# ==============================================================================

MovieData = Dict[str, Any]
QuestionData = Dict[str, Any]

# Zorluk Katmanları
TIER_NOVICE = 1    
TIER_PRO = 2       
TIER_EXPERT = 3    
TIER_MASTER = 4    
TIER_LEGEND = 5    

class QuestionEngine:
    """
    CineSaga Pro - Logic Core v7.1 (Smart Hint Edition)
    --------------------------------------------------
    Bu motor, bir Sinema Ansiklopedisi gibi çalışır. Veriler arasındaki
    ilişkileri (Relational Data) analiz ederek bağlamsal sorular üretir.
    
    YENİLİK (v7.1):
    - Smart Oracle Hint: İpuçları artık jenerik değil, cevaba götüren
      spesifik bilgiler (Karakter adı, Yönetmen, Anahtar Kelime) içerir.
    """

    def __init__(self):
        from tmdb_manager import get_manager
        self.tmdb = get_manager()
        
        self.logger = logging.getLogger("CineSaga.Ensemble")
        self.logger.setLevel(logging.INFO)
        
        self.current_year = 2026
        
        # Emoji Kütüphanesi
        self.emoji_map = {
            28: ["💥", "🔫", "🏎️", "👊"], 12: ["🗺️", "🧭", "🎒", "🌋"],
            16: ["🎨", "👾", "🧚", "🦄"], 35: ["😂", "🤪", "🤡", "🎭"],
            80: ["🚓", "💰", "🕵️", "🩸"], 18: ["😢", "🎭", "🎻", "💔"],
            14: ["🧙‍♂️", "🐉", "🔮", "🧝"], 27: ["👻", "🪓", "🩸", "🧟"],
            10402: ["🎵", "🎹", "🎤", "🎸"], 9648: ["🔍", "🧩", "🕵️‍♂️", "❓"],
            10749: ["❤️", "💋", "💌", "🌹"], 878: ["👽", "🚀", "🤖", "🧬"],
            53: ["😰", "💣", "🔪", "👀"], 10752: ["🪖", "🎖️", "💣", "✈️"],
            37: ["🤠", "🌵", "🐎", "🔫"]
        }
        
        self.logger.info("Logic Core v7.1 (Smart Hint) başarıyla başlatıldı.")

    # =========================================================================
    # BÖLÜM 1: ANA ÜRETİM HATTI
    # =========================================================================

    def generate_level_content(self, user: Any, is_daily: bool = False) -> List[QuestionData]:
        level = user.current_level
        questions = []
        
        pool_mode_daily = is_daily or (level > 800)
        pool = self.tmdb.get_pool_by_level(level, pool_mode_daily)
        
        if not pool or len(pool) < 15:
            pool = self.tmdb.all_movies[-300:]

        current_tier = self._calculate_tier(level, is_daily)

        if is_daily: count = 1
        else:
            if level < 20: count = 1
            elif level < 100: count = 2
            elif level < 400: count = 3
            else: count = 4

        selected_movies = random.sample(pool, min(count, len(pool)))

        for movie in selected_movies:
            q = self._architect_question(movie, pool, current_tier, is_daily)
            if q: questions.append(q)
                
        if not questions:
            fallback_movie = random.choice(pool)
            questions.append(self._build_anagram_puzzle(fallback_movie, pool))

        return questions

    def _calculate_tier(self, level: int, is_daily: bool) -> int:
        if is_daily: return TIER_LEGEND
        if level <= 20: return TIER_NOVICE
        if level <= 100: return TIER_PRO
        if level <= 300: return TIER_EXPERT
        if level <= 600: return TIER_MASTER
        return TIER_LEGEND

    def _architect_question(self, movie: MovieData, pool: List[MovieData], tier: int, is_daily: bool) -> Optional[QuestionData]:
        possible_blueprints = []

        # TIER 1
        if self._has(movie, 'poster'): possible_blueprints.append("visual_poster_clean")
        if self._has(movie, 'scene'): possible_blueprints.append("visual_scene_clean")

        # TIER 2
        if tier >= TIER_PRO:
            if self._has(movie, 'date'): possible_blueprints.append("year_decade")
            if self._has(movie, 'cast'): possible_blueprints.append("actor_match_simple")
            if self._has(movie, 'tagline'): possible_blueprints.append("tagline_gap")
            if self._is_franchise(movie): possible_blueprints.append("franchise_trap_easy")

        # TIER 3
        if tier >= TIER_EXPERT:
            if self._has(movie, 'poster'): possible_blueprints.append("visual_poster_blur")
            if self._has(movie, 'cast_rich'): possible_blueprints.append("duo_who_is_in")
            if self._has(movie, 'cast_rich'): possible_blueprints.append("duo_which_movie")
            possible_blueprints.append("emoji_puzzle")
            possible_blueprints.append("anagram_simple")

        # TIER 4
        if tier >= TIER_MASTER:
            if self._has(movie, 'scene'): possible_blueprints.append("visual_scene_pixel")
            if self._has(movie, 'cast'): possible_blueprints.append("odd_one_out")
            if self._has(movie, 'overview'): possible_blueprints.append("riddle_redacted")
            if self._has(movie, 'cast'): possible_blueprints.append("actor_cross_ref")

        # TIER 5
        if tier >= TIER_LEGEND:
            possible_blueprints.append("hangman_keyboard")
            if self._has(movie, 'date'): possible_blueprints.append("logic_comparison")
            if self._is_franchise(movie): possible_blueprints.append("franchise_trap_hard")

        if is_daily:
            if "visual_poster_clean" in possible_blueprints: possible_blueprints.remove("visual_poster_clean")
            if "visual_scene_clean" in possible_blueprints: possible_blueprints.remove("visual_scene_clean")

        if not possible_blueprints: return self._build_anagram_puzzle(movie, pool)
        blueprint = random.choice(possible_blueprints)

        return self._execute_blueprint(blueprint, movie, pool)

    def _execute_blueprint(self, bp: str, m: MovieData, p: List[MovieData]) -> Optional[QuestionData]:
        # Görsel
        if bp == "visual_poster_clean": return self._build_visual(m, p, "poster", "")
        if bp == "visual_scene_clean": return self._build_visual(m, p, "scene", "")
        if bp == "visual_poster_blur": return self._build_visual(m, p, "poster", "blur")
        if bp == "visual_scene_pixel": return self._build_visual(m, p, "scene", "pixel")
        # Franchise
        if "franchise_trap" in bp: return self._build_franchise_trap(m, p)
        # Oyuncu
        if bp == "actor_match_simple": return self._build_actor_standard(m, p)
        if bp == "actor_cross_ref": return self._build_actor_cross(m, p)
        if bp == "odd_one_out": return self._build_odd_one_out(m, p)
        if bp == "duo_who_is_in": return self._build_dynamic_duo_reveal(m, p)
        if bp == "duo_which_movie": return self._build_co_star_lookup(m, p)
        # Mantık & Metin
        if bp == "year_decade": return self._build_year_logic(m)
        if bp == "tagline_gap": return self._build_tagline_gap(m, p)
        if bp == "riddle_redacted": return self._build_riddle(m, p)
        if bp == "logic_comparison": return self._build_ai_comparison(p)
        # Bulmaca
        if bp == "emoji_puzzle": return self._build_emoji(m, p)
        if "anagram" in bp: return self._build_anagram_puzzle(m, p)
        if bp == "hangman_keyboard": return self._build_hangman(m, p)
        return None

    # =========================================================================
    # BÖLÜM 2: YENİLENMİŞ AKILLI İPUCU (ORACLE HINT SYSTEM)
    # =========================================================================

    def _generate_smart_hint(self, movie: MovieData, q_type: str) -> str:
        """
        [GÜNCELLENDİ] Soru tipine göre EN FAYDALI ipucunu seçer.
        Oyuncuyu cevaba yaklaştırır ama cevabı direkt vermez.
        """
        title = movie['title']
        release_date = movie.get('release_date', '????')
        year = release_date[:4]
        
        # 1. HANGMAN / ANAGRAM İPUCU
        if q_type in ["hangman", "anagram"]:
            words = title.split()
            if len(words) > 1:
                return f"İpucu: Film {len(words)} kelimeden oluşuyor. İlk harfi: **{title[0]}**"
            else:
                return f"İpucu: Tek kelimelik bir başyapıt. İlk harfi: **{title[0]}**"

        # 2. YIL SORUSU İPUCU -> Oyuncu veya Tür ver
        if q_type == "year":
            if movie.get('cast'):
                main_actor = movie['cast'][0]['name']
                return f"İpucu: Bu dönemde **{main_actor}** kariyerinin zirvesindeydi."
            return f"İpucu: Bu bir **{self._get_genre_name(movie)}** filmi."

        # 3. OYUNCU SORUSU İPUCU -> Karakter Adı ver (En iyisi)
        if q_type == "actor":
            if movie.get('cast'):
                # Başrolün karakter adını bul
                char_name = movie['cast'][0].get('character', '')
                if char_name:
                    clean_char = char_name.split('/')[0].replace('(voice)', '').strip()
                    if clean_char:
                        return f"İpucu: Canlandırdığı karakterin adı: **{clean_char}**"
            
            # Karakter yoksa Yıl ver
            return f"İpucu: Film **{year}** yılında vizyona girdi."

        # 4. GÖRSEL SORU İPUCU -> Slogandan veya Özetten Kelime
        if q_type == "visual":
            if movie.get('tagline') and len(movie['tagline']) > 5:
                return f"Slogan: \"{movie['tagline']}\""
            
            keyword = self._extract_keyword(movie.get('overview', ''), title)
            if keyword:
                return f"Hikayenin anahtar kelimesi: **{keyword.upper()}**"
        
        # 5. CO-STAR / DUO İPUCU
        if q_type in ["duo", "co_star_lookup"]:
             return f"İpucu: Bu film **{year}** yılında çıkan bir **{self._get_genre_name(movie)}** efsanesidir."

        # GENEL YEDEK İPUÇLARI
        return f"Vizyon Tarihi: {release_date}"

    def _extract_keyword(self, text, title):
        """Özetten en ayırt edici uzun kelimeyi bulur."""
        if not text: return "Sinema"
        ignore = ["bir", "ve", "ile", "için", "olan", "çok", "ama", "film", "filmi"] + title.lower().split()
        words = [w for w in re.findall(r'\w+', text.lower()) if len(w) > 5 and w not in ignore]
        return random.choice(words) if words else "Klasik"

    # =========================================================================
    # BÖLÜM 3: GÜNCELLENMİŞ BUILDER FONKSİYONLARI (İPUCU ENTEGRASYONLU)
    # =========================================================================

    def _build_co_star_lookup(self, movie, pool):
        cast = movie.get('cast', [])
        if len(cast) < 2: return None
        a1, a2 = random.sample(cast[:4], 2)
        return {
            "movie_id": movie['id'], "type": "co_star_lookup", "input_mode": "select",
            "text": f"Sinema dünyasının bu iki ismi;\n\n🎭 **{a1['name']}** ve **{a2['name']}**\n\nHangi filmde BİRLİKTE rol almışlardır?",
            "image": None, "answer": movie['title'],
            "options": self._gen_options_movies(movie['title'], pool, 4),
            "hint": self._generate_smart_hint(movie, "co_star_lookup")
        }

    def _build_dynamic_duo_reveal(self, movie, pool):
        cast = movie.get('cast', [])
        if len(cast) < 2: return None
        a1, a2 = random.sample(cast[:3], 2)
        correct_pair = f"{a1['name']} & {a2['name']}"
        options = {correct_pair}
        while len(options) < 4:
            om = random.choice(pool)
            if om['id'] != movie['id'] and om.get('cast') and len(om['cast']) >= 2:
                oa1, oa2 = random.sample(om['cast'][:3], 2)
                options.add(f"{oa1['name']} & {oa2['name']}")
        return {
            "movie_id": movie['id'], "type": "dynamic_duo", "input_mode": "select",
            "text": f"**'{movie['title']}'** filminin kadrosunda hangi ikili yer alır?",
            "image": None, "answer": correct_pair, "options": list(options),
            "hint": self._generate_smart_hint(movie, "duo")
        }

    def _build_visual(self, movie, pool, img_type, effect):
        is_scene = (img_type == "scene")
        url = f"https://image.tmdb.org/t/p/w780{movie['backdrop_path']}" if is_scene else f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
        txt_map = {"normal": "Bu görsel hangi filme ait?", "blur": "Odaklan! Bu bulanık görüntü hangi filme ait?", "pixel": "Sinyal kaybı... Bu pikselleşmiş sahne hangi filmden?"}
        base_txt = txt_map.get(effect, txt_map["normal"])
        if is_scene: base_txt = base_txt.replace("görsel", "sahne").replace("görüntü", "kadraj")
        return {
            "movie_id": movie['id'], "type": "visual", "input_mode": "select",
            "text": base_txt, "image": url, "image_effect": effect,
            "answer": movie['title'], "options": self._gen_options_movies(movie['title'], pool, 4),
            "hint": self._generate_smart_hint(movie, "visual")
        }

    def _build_franchise_trap(self, movie, pool):
        title_parts = movie['title'].split()
        if len(title_parts) < 2: return self._build_visual(movie, pool, "poster", "")
        prefix = " ".join(title_parts[:2])
        siblings = [m['title'] for m in self.tmdb.all_movies if m['title'].startswith(prefix) and m['id'] != movie['id']]
        if len(siblings) < 3: return self._build_visual(movie, pool, "poster", "")
        options = random.sample(siblings, 3); options.append(movie['title']); random.shuffle(options)
        is_scene = self._has(movie, 'scene')
        url = f"https://image.tmdb.org/t/p/w780{movie['backdrop_path']}" if is_scene else f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
        return {
            "movie_id": movie['id'], "type": "franchise", "input_mode": "select",
            "text": f"DİKKAT! Bu {'sahne' if is_scene else 'afiş'} serinin HANGİ filmine ait?",
            "image": url, "image_effect": "", "answer": movie['title'], "options": options,
            "hint": f"Bu filmin vizyon yılı: **{movie['release_date'][:4]}**"
        }

    def _build_actor_cross(self, movie, pool):
        actor = movie['cast'][0]['name']
        other_movie = self._find_other_movie_for_actor(actor, movie['id'])
        if not other_movie: return self._build_actor_standard(movie, pool)
        return {
            "movie_id": movie['id'], "type": "knowledge", "input_mode": "select",
            "text": f"'{movie['title']}' filminin yıldızı **{actor}**, aşağıdaki başyapıtlardan hangisinde de rol almıştır?",
            "image": None, "answer": other_movie['title'],
            "options": self._gen_options_movies(other_movie['title'], pool, 4),
            "hint": self._generate_smart_hint(other_movie, "actor")
        }

    def _build_odd_one_out(self, movie, pool):
        cast_names = [c['name'] for c in movie['cast'][:6]]
        if len(cast_names) < 3: return self._build_anagram_puzzle(movie, pool)
        insiders = random.sample(cast_names, 3); outsider = self._get_random_outsider(movie, pool)
        opts = insiders + [outsider]; random.shuffle(opts)
        return {
            "movie_id": movie['id'], "type": "odd_one", "input_mode": "select",
            "text": f"Hangisi **'{movie['title']}'** kadrosunda YER ALMAZ?",
            "image": None, "answer": outsider, "options": opts,
            "hint": f"Filmdeki karakterlerden biri: **{movie['cast'][0]['character']}**"
        }

    def _build_tagline_gap(self, movie, pool):
        tagline = movie['tagline']
        censored = re.sub(re.escape(movie['title']), "...", tagline, flags=re.IGNORECASE)
        return {
            "movie_id": movie['id'], "type": "text", "input_mode": "select",
            "text": f"SLOGAN:\n\n\"{censored}\"\n\nBu söz hangi filme ait?",
            "image": None, "answer": movie['title'], "options": self._gen_options_movies(movie['title'], pool, 4),
            "hint": f"Başrolde **{movie['cast'][0]['name']}** var."
        }

    def _build_year_logic(self, movie):
        real_year = int(movie['release_date'][:4])
        options = {str(real_year)}
        while len(options) < 4:
            fake = real_year + random.randint(-8, 8)
            if fake <= self.current_year and fake != real_year: options.add(str(fake))
        return {
            "movie_id": movie['id'], "type": "year", "input_mode": "select",
            "text": f"'{movie['title']}' filmi hangi yıl vizyona girdi?",
            "image": None, "answer": str(real_year), "options": list(options),
            "hint": self._generate_smart_hint(movie, "year")
        }

    def _build_ai_comparison(self, pool):
        m1, m2 = random.sample(pool, 2)
        while m1['id'] == m2['id']: m2 = random.choice(pool)
        logic = random.choice(["oldest", "popular", "longest"])
        if logic == "oldest":
            ans = m1['title'] if m1.get('release_date') < m2.get('release_date') else m2['title']
            txt = "Hangi film daha ESKİDİR?"
        elif logic == "popular":
            ans = m1['title'] if m1.get('popularity') > m2.get('popularity') else m2['title']
            txt = "Hangi film daha POPÜLERDİR?"
        else:
            ans = m1['title'] if len(m1['title']) > len(m2['title']) else m2['title']
            txt = "Hangi filmin ismi daha UZUNDUR?"
        return {
            "movie_id": 0, "type": "logic", "input_mode": "select",
            "text": f"MANTIK SORUSU:\n\n{txt}",
            "image": None, "answer": ans, "options": [m1['title'], m2['title']],
            "hint": f"**{m1['title']}**: {m1['release_date'][:4]} | **{m2['title']}**: {m2['release_date'][:4]}"
        }

    def _build_emoji(self, movie, pool):
        genres = movie.get('genre_ids', [])
        emojis = []
        for g in genres: emojis.extend(self.emoji_map.get(g, []))
        if not emojis: emojis = ["🎬", "🍿", "🎥"]
        selection = random.sample(emojis, min(4, len(emojis)))
        return {
            "movie_id": movie['id'], "type": "emoji", "input_mode": "select",
            "text": f"Bu emojiler hangi filmi anlatıyor?\n\n# {' '.join(selection)}",
            "image": None, "answer": movie['title'], "options": self._gen_options_movies(movie['title'], pool, 4),
            "hint": self._generate_smart_hint(movie, "visual")
        }

    def _build_anagram_puzzle(self, movie, pool):
        title = movie['title'].upper()
        clean = [c for c in title if c.isalnum()]
        random.shuffle(clean)
        return {
            "movie_id": movie['id'], "type": "anagram", "input_mode": "select",
            "text": f"KARIŞIK HARFLER:\nBu hangi film olabilir?\n\n**{'  '.join(clean)}**",
            "image": None, "answer": movie['title'],
            "options": self._gen_options_movies(movie['title'], pool, 4),
            "hint": self._generate_smart_hint(movie, "anagram")
        }

    def _build_hangman(self, movie, pool):
        title = movie['title']
        masked = ""
        for char in title:
            if char == " ": masked += "  "
            elif not char.isalnum(): masked += char
            else: masked += "_ " if random.random() > 0.4 else f"{char} "
        return {
            "movie_id": movie['id'], "type": "hangman", "input_mode": "keyboard",
            "text": f"Eksik harfleri tamamla:\n\n{masked}",
            "image": None, "answer": title, "options": [],
            "hint": self._generate_smart_hint(movie, "hangman")
        }

    def _build_actor_standard(self, movie, pool):
        actor = movie['cast'][0]['name']
        return {
            "movie_id": movie['id'], "type": "actor", "input_mode": "select",
            "text": f"**{actor}** aşağıdaki filmlerden hangisinde rol almıştır?",
            "image": None, "answer": movie['title'], "options": self._gen_options_movies(movie['title'], pool, 4),
            "hint": self._generate_smart_hint(movie, "actor")
        }

    def _build_riddle(self, movie, pool):
        clean = re.sub(re.escape(movie['title']), "********", movie['overview'], flags=re.IGNORECASE)
        return {
            "movie_id": movie['id'], "type": "riddle", "input_mode": "select",
            "text": f"SİNEFİL BİLMECESİ:\n\n\"{clean[:180]}...\"",
            "image": None, "answer": movie['title'], "options": self._gen_options_movies(movie['title'], pool, 4),
            "hint": self._generate_smart_hint(movie, "visual")
        }

    # =========================================================================
    # BÖLÜM 4: GÜVENLİK VE YARDIMCILAR
    # =========================================================================

    def _gen_options_movies(self, correct: str, pool: List[MovieData], count: int) -> List[str]:
        opts = {correct}
        attempts = 0
        while len(opts) < count and attempts < 100:
            m = random.choice(pool)
            if m['title'] != correct: opts.add(m['title'])
            attempts += 1
        if len(opts) < count:
            while len(opts) < count:
                m = random.choice(self.tmdb.all_movies)
                if m['title'] != correct: opts.add(m['title'])
        l = list(opts); random.shuffle(l)
        return l

    def _get_random_outsider(self, movie: MovieData, pool: List[MovieData]) -> str:
        limit = 0
        while limit < 50:
            m = random.choice(pool)
            if not m.get('cast'): continue
            actor = m['cast'][0]['name']
            if not any(c['name'] == actor for c in movie['cast']): return actor
            limit += 1
        return "Nicolas Cage"

    def _find_other_movie_for_actor(self, actor, exclude_id):
        candidates = [m for m in self.tmdb.all_movies if m['id'] != exclude_id and m.get('cast') and any(c['name'] == actor for c in m['cast'])]
        return random.choice(candidates) if candidates else None

    def _has(self, m, k):
        if k == 'poster': return bool(m.get('poster_path'))
        if k == 'scene': return bool(m.get('backdrop_path'))
        if k == 'cast': return bool(m.get('cast'))
        if k == 'cast_rich': return bool(m.get('cast') and len(m['cast']) >= 2)
        if k == 'date': return bool(m.get('release_date'))
        if k == 'tagline': return bool(m.get('tagline'))
        if k == 'overview': return bool(m.get('overview'))
        return False

    def _is_franchise(self, movie):
        title_parts = movie['title'].split()
        if len(title_parts) < 2: return False
        prefix = " ".join(title_parts[:2])
        count = sum(1 for m in self.tmdb.all_movies if m['title'].startswith(prefix))
        return count >= 3

    def _get_genre_name(self, m):
        genre_map = {28: "Aksiyon", 12: "Macera", 16: "Animasyon", 35: "Komedi", 18: "Dram", 27: "Korku", 878: "Bilim Kurgu"}
        gid = m.get('genre_ids', [])
        return genre_map.get(gid[0], "Sinema") if gid else "Sinema"
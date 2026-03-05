import os
import json
import random
import requests
import anthropic

# ─────────────────────────────────────────────────────
#  TMDB CONFIGURATION
# ─────────────────────────────────────────────────────

TMDB_BASE = 'https://api.themoviedb.org/3'

# TMDB region/language codes per industry
INDUSTRY_TMDB = {
    'bolly': {'language': 'hi', 'region': 'IN', 'label': 'Bollywood'},
    'kolly': {'language': 'ta', 'region': 'IN', 'label': 'Kollywood'},
    'tolly': {'language': 'te', 'region': 'IN', 'label': 'Tollywood'},
}


def _tmdb_headers():
    token = os.environ.get('TMDB_API_KEY', '')
    return {
        'Authorization': f'Bearer {token}',
        'accept': 'application/json',
    }


def fetch_real_movies(industry, count=40):
    """
    Fetches real movie titles and director names from TMDB
    for the given industry. Returns list of dicts with
    title and director keys.
    """
    cfg = INDUSTRY_TMDB.get(industry, INDUSTRY_TMDB['bolly'])
    movies = []

    try:
        # Fetch popular movies in this language
        for page in range(1, 3):
            url = f"{TMDB_BASE}/discover/movie"
            params = {
                'with_original_language': cfg['language'],
                'sort_by': 'popularity.desc',
                'page': page,
            }
            resp = requests.get(url, headers=_tmdb_headers(),
                                params=params, timeout=8)
            if resp.status_code != 200:
                break
            data = resp.json()
            for m in data.get('results', []):
                movies.append({
                    'title':    m.get('title', ''),
                    'director': '',  # fetched separately if needed
                })
            if len(movies) >= count:
                break

    except Exception:
        # Fallback titles if TMDB is unavailable
        movies = [
            {'title': 'Dil Se', 'director': 'Mani Ratnam'},
            {'title': 'Lagaan', 'director': 'Ashutosh Gowariker'},
            {'title': 'Sholay', 'director': 'Ramesh Sippy'},
            {'title': 'Dilwale', 'director': 'Rohit Shetty'},
            {'title': 'Baahubali', 'director': 'S.S. Rajamouli'},
            {'title': 'Enthiran', 'director': 'Shankar'},
            {'title': 'Magadheera', 'director': 'S.S. Rajamouli'},
            {'title': 'Vikram', 'director': 'Lokesh Kanagaraj'},
        ]

    return movies[:count]


# ─────────────────────────────────────────────────────
#  MAIN GENERATION FUNCTION
# ─────────────────────────────────────────────────────

def generate_content_pool(actor):
    """
    Main entry point. Fetches TMDB data and calls Claude Haiku
    to generate a full content pool for this actor.
    Returns a dict with keys:
      movies, directors, controversies, onset_events, reviews
    """
    industry_cfg = INDUSTRY_TMDB.get(actor.industry, INDUSTRY_TMDB['bolly'])
    real_movies  = fetch_real_movies(actor.industry, count=40)
    real_titles  = [m['title'] for m in real_movies if m['title']][:30]

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        return _fallback_pool(actor)

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # ── BATCH 1: Movies + Directors ──
        movie_prompt = f"""
You are generating content for a fictional {industry_cfg['label']} career simulation game.

Here are some real {industry_cfg['label']} movie titles for inspiration only:
{', '.join(real_titles[:20])}

Generate fictional content inspired by this style but with CHANGED spellings and names so nothing is a real title.

Return ONLY valid JSON with this exact structure, no other text:
{{
  "movies": [
    {{
      "title": "fictional movie title",
      "genre": one of ["Action", "Romance", "Drama", "Comedy", "Thriller", "Biography", "Horror", "Masala"],
      "budget": one of ["Low", "Mid", "High", "Mega"],
      "tagline": "short punchy movie tagline"
    }}
  ],
  "directors": [
    {{
      "name": "fictional director name (Indian, sounds real but is not)",
      "stars": integer between 2 and 5,
      "known_for": "one genre they specialise in"
    }}
  ]
}}

Generate 30 movies and 15 directors.
Names must sound authentically Indian but must NOT be real people or real films.
Vary genres, budgets, and styles.
"""

        msg1 = client.messages.create(
            model='claude-haiku-4-5',
            max_tokens=2000,
            messages=[{'role': 'user', 'content': movie_prompt}],
        )
        batch1 = _safe_parse(msg1.content[0].text)

        # ── BATCH 2: Controversies ──
        controversy_prompt = f"""
You are generating controversy scenarios for a fictional {industry_cfg['label']} career game.

Return ONLY valid JSON with this exact structure, no other text:
{{
  "controversies": [
    {{
      "type": "short controversy type label",
      "severity": one of ["Low", "Medium", "High"],
      "headline": "tabloid-style headline (no real names)",
      "narrative": "2 sentence description of what happened",
      "tabloid_quote": "sensational quote a tabloid might print",
      "source_label": "fictional news source name",
      "immediate_fame": integer between -5 and 15,
      "credibility_hit": integer between 5 and 25,
      "public_mood": one of ["angry", "amused", "divided", "sympathetic"]
    }}
  ]
}}

Generate 12 controversies. Mix severity levels.
Set in {industry_cfg['label']}. No real celebrities or publications.
Make them feel authentic to Indian film industry culture.
"""

        msg2 = client.messages.create(
            model='claude-haiku-4-5',
            max_tokens=1500,
            messages=[{'role': 'user', 'content': controversy_prompt}],
        )
        batch2 = _safe_parse(msg2.content[0].text)

        # ── BATCH 3: On-Set Events + Review templates ──
        events_prompt = f"""
You are generating on-set events and critic review templates for a fictional {industry_cfg['label']} game.

Return ONLY valid JSON with this exact structure, no other text:
{{
  "onset_events": [
    {{
      "id": "unique_snake_case_id",
      "title": "short event title",
      "description": "2 sentence description of what happened on set",
      "choices": [
        {{
          "id": "choice_a",
          "label": "short action label",
          "preview": "brief outcome hint",
          "quality_change": integer between -5 and 10,
          "energy_change": integer between -15 and 5,
          "acting_change": integer between 0 and 3,
          "fame_change": integer between -3 and 5
        }},
        {{
          "id": "choice_b",
          "label": "short action label",
          "preview": "brief outcome hint",
          "quality_change": integer between -5 and 10,
          "energy_change": integer between -15 and 5,
          "acting_change": integer between 0 and 3,
          "fame_change": integer between -3 and 5
        }}
      ]
    }}
  ],
  "review_templates": {{
    "blockbuster": ["template 1", "template 2", "template 3"],
    "hit":         ["template 1", "template 2", "template 3"],
    "average":     ["template 1", "template 2", "template 3"],
    "flop":        ["template 1", "template 2", "template 3"],
    "disaster":    ["template 1", "template 2", "template 3"]
  }}
}}

Generate 10 on-set events and 3 review templates per result tier (15 total).
Events should feel like real film production situations.
Review templates use {{actor_name}} and {{movie_title}} as placeholders.
Set in {industry_cfg['label']} culture.
"""

        msg3 = client.messages.create(
            model='claude-haiku-4-5',
            max_tokens=2000,
            messages=[{'role': 'user', 'content': events_prompt}],
        )
        batch3 = _safe_parse(msg3.content[0].text)

        return {
            'movies':           batch1.get('movies', []),
            'directors':        batch1.get('directors', []),
            'controversies':    batch2.get('controversies', []),
            'onset_events':     batch3.get('onset_events', []),
            'review_templates': batch3.get('review_templates', {}),
        }

    except Exception as e:
        print(f"Content pool generation error: {e}")
        return _fallback_pool(actor)


def _safe_parse(text):
    """Safely parse JSON from Claude response, stripping markdown fences."""
    try:
        clean = text.strip()
        if clean.startswith('```'):
            clean = clean.split('\n', 1)[1]
        if clean.endswith('```'):
            clean = clean.rsplit('```', 1)[0]
        return json.loads(clean.strip())
    except Exception:
        return {}


# ─────────────────────────────────────────────────────
#  POOL ACCESSORS
#  These functions are called by job_board.py,
#  filming.py, and events.py to draw from the pool.
# ─────────────────────────────────────────────────────

def get_random_movie(pool_data):
    """Returns a random movie dict from the pool."""
    movies = pool_data.get('movies', [])
    return random.choice(movies) if movies else {
        'title': 'Ek Nayi Duniya', 'genre': 'Drama',
        'budget': 'Mid', 'tagline': 'A story untold.'
    }


def get_random_director(pool_data, min_stars=None):
    """Returns a random director dict, optionally filtered by min stars."""
    directors = pool_data.get('directors', [])
    if min_stars:
        filtered = [d for d in directors if d.get('stars', 3) >= min_stars]
        directors = filtered if filtered else directors
    return random.choice(directors) if directors else {
        'name': 'Rajan Mehta', 'stars': 3, 'known_for': 'Drama'
    }


def get_random_controversy(pool_data):
    """Returns a random controversy dict from the pool."""
    controversies = pool_data.get('controversies', [])
    return random.choice(controversies) if controversies else None


def get_random_onset_event(pool_data):
    """Returns a random on-set event dict from the pool."""
    events = pool_data.get('onset_events', [])
    if not events:
        return None
    return random.choice(events)


def get_review(pool_data, result_tier, actor_name, movie_title):
    """
    Returns a formatted critic review for the given result tier.
    Fills in actor_name and movie_title placeholders.
    """
    templates = pool_data.get('review_templates', {})
    tier_templates = templates.get(result_tier, [])
    if not tier_templates:
        return _fallback_review(result_tier, actor_name, movie_title)
    template = random.choice(tier_templates)
    return template.replace('{actor_name}', actor_name).replace('{movie_title}', movie_title)


# ─────────────────────────────────────────────────────
#  FALLBACK POOL
#  Used when API is unavailable. Keeps game playable.
# ─────────────────────────────────────────────────────

def _fallback_pool(actor):
    return {
        'movies': [
            {'title': 'Dil Ki Baat',     'genre': 'Romance',  'budget': 'Mid',  'tagline': 'Some stories never end.'},
            {'title': 'Toofan',          'genre': 'Action',   'budget': 'High', 'tagline': 'Rise above the storm.'},
            {'title': 'Khwaab',          'genre': 'Drama',    'budget': 'Low',  'tagline': 'Dreams cost everything.'},
            {'title': 'Ek Baar Phir',    'genre': 'Romance',  'budget': 'Mid',  'tagline': 'Love finds a way.'},
            {'title': 'Andhakar',        'genre': 'Thriller', 'budget': 'Mid',  'tagline': 'No one sees it coming.'},
            {'title': 'Junoon',          'genre': 'Masala',   'budget': 'High', 'tagline': 'Passion has no limits.'},
            {'title': 'Naya Savera',     'genre': 'Drama',    'budget': 'Low',  'tagline': 'Every dawn is a second chance.'},
            {'title': 'Sher Ka Dil',     'genre': 'Action',   'budget': 'Mega', 'tagline': 'The heart of a lion.'},
            {'title': 'Raaton Ki Rani',  'genre': 'Comedy',   'budget': 'Mid',  'tagline': 'She runs the night.'},
            {'title': 'Parchhaiyan',     'genre': 'Thriller', 'budget': 'Low',  'tagline': 'Shadows never lie.'},
            {'title': 'Mitti Ka Rang',   'genre': 'Drama',    'budget': 'Low',  'tagline': 'Roots run deep.'},
            {'title': 'Aakash',          'genre': 'Action',   'budget': 'High', 'tagline': 'The sky is not the limit.'},
            {'title': 'Pyaar Ka Safar',  'genre': 'Romance',  'budget': 'Mid',  'tagline': 'The journey of love.'},
            {'title': 'Badal Aur Bijli', 'genre': 'Masala',   'budget': 'High', 'tagline': 'Thunder and lightning.'},
            {'title': 'Khamoshi',        'genre': 'Drama',    'budget': 'Low',  'tagline': 'In silence, truth speaks.'},
        ],
        'directors': [
            {'name': 'Vikram Anand',    'stars': 5, 'known_for': 'Action'},
            {'name': 'Priya Nair',      'stars': 4, 'known_for': 'Drama'},
            {'name': 'Suresh Babu',     'stars': 3, 'known_for': 'Comedy'},
            {'name': 'Aditya Kapoor',   'stars': 4, 'known_for': 'Romance'},
            {'name': 'Lakshmi Devi',    'stars': 5, 'known_for': 'Thriller'},
            {'name': 'Rajan Mehta',     'stars': 3, 'known_for': 'Masala'},
            {'name': 'Kiran Rao',       'stars': 4, 'known_for': 'Biography'},
            {'name': 'Arjun Sinha',     'stars': 2, 'known_for': 'Horror'},
        ],
        'controversies': [
            {
                'type': 'On-Set Argument',
                'severity': 'Medium',
                'headline': 'Heated Confrontation Rocks Film Set',
                'narrative': 'Sources claim a heated argument broke out during a crucial shoot. The dispute reportedly delayed production by two days.',
                'tabloid_quote': 'It was chaos. Everyone was shouting.',
                'source_label': 'FilmiMasala Weekly',
                'immediate_fame': 5,
                'credibility_hit': 10,
                'public_mood': 'divided',
            },
            {
                'type': 'Award Snub',
                'severity': 'Low',
                'headline': 'Critics Overlook Breakout Performance',
                'narrative': 'Despite strong reviews, the actor was conspicuously absent from major award nominations this season.',
                'tabloid_quote': 'The industry clearly has a bias problem.',
                'source_label': 'CineScope India',
                'immediate_fame': 8,
                'credibility_hit': 5,
                'public_mood': 'sympathetic',
            },
        ],
        'onset_events': [
            {
                'id': 'costar_conflict',
                'title': 'Co-Star Tension',
                'description': 'Your co-star delivers a cutting remark in front of the entire crew. The director is watching.',
                'choices': [
                    {'id': 'choice_a', 'label': 'Stay Professional', 'preview': 'Keep the peace',
                     'quality_change': 3, 'energy_change': -5, 'acting_change': 0, 'fame_change': 0},
                    {'id': 'choice_b', 'label': 'Confront Them', 'preview': 'Risk the drama',
                     'quality_change': -2, 'energy_change': -10, 'acting_change': 1, 'fame_change': 3},
                ],
            },
        ],
        'review_templates': {
            'blockbuster': ['{actor_name} delivers a career-defining performance in {movie_title}. A triumph.'],
            'hit':         ['{movie_title} is a solid entertainer. {actor_name} shines throughout.'],
            'average':     ['{movie_title} has its moments but struggles to find its footing.'],
            'flop':        ['{movie_title} disappoints despite the talent involved.'],
            'disaster':    ['{movie_title} is a painful misfire. A forgettable chapter for everyone involved.'],
        },
    }


def _fallback_review(result_tier, actor_name, movie_title):
    reviews = {
        'blockbuster': f'{actor_name} is electric in {movie_title}. Pure cinema.',
        'hit':         f'{movie_title} delivers. {actor_name} carries it well.',
        'average':     f'{movie_title} is watchable but forgettable.',
        'flop':        f'{movie_title} never finds its rhythm. A wasted opportunity.',
        'disaster':    f'{movie_title} is a disaster from frame one.',
    }
    return reviews.get(result_tier, f'{movie_title} has released.')

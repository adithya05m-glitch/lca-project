import random

# ─────────────────────────────────────────────────────
#  ROLE POOLS — the raw ingredients for listings
#  All names are fictional and original
# ─────────────────────────────────────────────────────

MOVIE_TITLES = {
    'bolly': [
        'Dil Ka Safar', 'Roshni Ke Baad', 'Toofan', 'Ek Baar Phir',
        'Shehar Ki Raat', 'Waqt Badlega', 'Aakash Ke Neeche', 'Junoon',
        'Naya Sawera', 'Rangeen Zindagi', 'Dhadkan', 'Koi Nahin Roka',
        'Aandhi', 'Parwaz', 'Teri Meri Baat', 'Lakeer'
    ],
    'kolly': [
        'Vaanam Kizhindha', 'Oruvane', 'Kadhal Mazhai', 'Thalaivar',
        'Ninaivugal', 'Sorgam', 'Kaatru', 'Naan Illamal',
        'Porali', 'Manithan', 'Iravum Pagalum', 'Anbulla',
        'Thozhan', 'Kalai', 'Mazhai Payanam', 'Sooriyan'
    ],
    'tolly': [
        'Vayu', 'Naa Prema Katha', 'Vijayudu', 'Poratam',
        'Andaru Andhere', 'Prema Bandham', 'Neti Manishi', 'Tufan',
        'Yodhulu', 'Kalisi Unte', 'Aakasam Dati', 'Seethakoka Chilaka',
        'Ranarangam', 'Kshemanga', 'Jabilamma', 'Devudu Chesina Manishi'
    ]
}

GENRES = ['Action', 'Romance', 'Comedy', 'Thriller', 'Drama', 'Masala', 'Biographical']

ROLE_TYPES = [
    {'type': 'Lead Hero',       'tier': 'A'},
    {'type': 'Lead Heroine',    'tier': 'A'},
    {'type': 'Supporting Lead', 'tier': 'B'},
    {'type': 'Villain',         'tier': 'B'},
    {'type': 'Comedian',        'tier': 'C'},
    {'type': 'Item Number',     'tier': 'C'},
    {'type': 'Cameo',           'tier': 'D'},
    {'type': 'Background Role', 'tier': 'D'},
]

# Fictional directors — inspired by industry styles but entirely made up
DIRECTORS = {
    'bolly': [
        {'name': 'Kiran Johari',        'stars': 5},
        {'name': 'Sanjay Lal Bhansali', 'stars': 5},
        {'name': 'Raj Kumar Hiranand',  'stars': 5},
        {'name': 'Anurag Kapur',        'stars': 4},
        {'name': 'Rohit Shetti',        'stars': 4},
        {'name': 'Zoha Akhtaar',        'stars': 4},
        {'name': 'Imtiaz Alii',         'stars': 4},
        {'name': 'Kabir Khann',         'stars': 3},
    ],
    'kolly': [
        {'name': 'Kani Rathnam',        'stars': 5},
        {'name': 'Shankarra',            'stars': 5},
        {'name': 'Gokesh Janagaraaj',   'stars': 5},
        {'name': 'B.R. Murugadaas',     'stars': 4},
        {'name': 'Cutlee Kumaar',        'stars': 4},
        {'name': 'Kathrimaaran',         'stars': 4},
        {'name': 'Signesh Vivaan',     'stars': 3},
        {'name': 'S.K. Kavikumaar',     'stars': 3},
    ],
    'tolly': [
        {'name': 'S.S. Kajamoulee',     'stars': 5},
        {'name': 'Sukumaran',           'stars': 5},
        {'name': 'Trivikraman',         'stars': 4},
        {'name': 'Koratala Shiva',      'stars': 4},
        {'name': 'Gunashekhar',         'stars': 4},
        {'name': 'Puri Jaganath',       'stars': 3},
        {'name': 'Anil Ravipudi',       'stars': 3},
        {'name': 'Maruthi Dasari',      'stars': 2},
    ],
}

BUDGETS = ['Low', 'Mid', 'High', 'Mega']

# ─────────────────────────────────────────────────────
#  SALARY RANGES BY ROLE TIER
# ─────────────────────────────────────────────────────

SALARY_RANGE = {
    'A': (2000000, 10000000),   # 20L–1Cr — unchanged
    'B': (500000,  2000000),    # 5L–20L — unchanged
    'C': (40000,   200000),     # 40K–2L — reduced from 1L–5L
    'D': (5000,    30000),      # 5K–30K — reduced from 10K–1L
}

# ─────────────────────────────────────────────────────
#  MINIMUM REQUIREMENTS BY ROLE TIER
# ─────────────────────────────────────────────────────

def get_requirements(role_tier, genre):
    """Returns minimum attribute requirements for a role."""
    base = {
        'A': {'acting_skill': 45, 'screen_presence': 40, 'fame': 40, 'looks': 35},
        'B': {'acting_skill': 30, 'screen_presence': 25, 'fame': 20, 'looks': 20},
        'C': {'acting_skill': 15, 'screen_presence': 15, 'fame': 5,  'looks': 10},
        'D': {'acting_skill': 5,  'screen_presence': 5,  'fame': 0,  'looks': 5},
    }

    reqs = base[role_tier].copy()

    if genre == 'Action':
        reqs['fitness'] = {'A': 50, 'B': 35, 'C': 20, 'D': 10}[role_tier]
    if genre == 'Romance':
        reqs['looks'] = reqs.get('looks', 0) + 10
    if genre in ['Masala', 'Comedy']:
        reqs['dancing'] = {'A': 40, 'B': 25, 'C': 15, 'D': 5}[role_tier]
    if genre in ['Drama', 'Biographical']:
        reqs['acting_skill'] = reqs.get('acting_skill', 0) + 10
        reqs['dialogue'] = {'A': 45, 'B': 30, 'C': 15, 'D': 5}[role_tier]

    return reqs

# ─────────────────────────────────────────────────────
#  GENERATE A SINGLE LISTING
# ─────────────────────────────────────────────────────

def generate_listing(industry):
    """Creates one randomised job listing for the given industry."""
    role_info = random.choice(ROLE_TYPES)
    role_tier  = role_info['tier']
    genre      = random.choice(GENRES)
    budget     = random.choice(BUDGETS)

    # Pick directors from the right industry pool
    director_pool = DIRECTORS.get(industry, DIRECTORS['bolly'])

    # Lower tier roles get lower-rated directors more often
    if role_tier in ['C', 'D']:
        director_pool = [d for d in director_pool if d['stars'] <= 3] or director_pool

    director = random.choice(director_pool)

    salary_min, salary_max = SALARY_RANGE[role_tier]
    salary = random.randrange(salary_min, salary_max, 10000)

    shoot_days = {
        'A': random.randint(60, 120),
        'B': random.randint(30, 60),
        'C': random.randint(10, 30),
        'D': random.randint(1, 10),
    }[role_tier]

    title_pool  = MOVIE_TITLES.get(industry, MOVIE_TITLES['bolly'])
    movie_title = random.choice(title_pool)
    requirements = get_requirements(role_tier, genre)

    return {
        'movie_title':    movie_title,
        'genre':          genre,
        'role_type':      role_info['type'],
        'role_tier':      role_tier,
        'salary':         salary,
        'director_name':  director['name'],
        'director_stars': director['stars'],
        'budget':         budget,
        'shoot_days':     shoot_days,
        'requirements':   requirements,
        'industry':       industry,
    }

# ─────────────────────────────────────────────────────
#  GENERATE A FULL BOARD OF LISTINGS
# ─────────────────────────────────────────────────────

def generate_job_board(industry, count=10):
    """Returns a list of job listings for the board."""
    listings = []
    for _ in range(count):
        listings.append(generate_listing(industry))

    # Sort by salary descending so best roles appear first
    listings.sort(key=lambda x: x['salary'], reverse=True)
    return listings

# ─────────────────────────────────────────────────────
#  CHECK IF ACTOR MEETS REQUIREMENTS
# ─────────────────────────────────────────────────────

def check_eligibility(actor, requirements):
    """
    Returns a dict with:
      - eligible (bool): whether actor meets all requirements
      - missing (list): which requirements they fall short on
    """
    missing = []

    attr_map = {
        'acting_skill':    actor.acting_skill,
        'screen_presence': actor.screen_presence,
        'fame':            actor.fame,
        'looks':           actor.looks,
        'fitness':         actor.fitness,
        'dancing':         actor.dancing,
        'dialogue':        actor.dialogue,
    }

    for attr, min_val in requirements.items():
        actor_val = attr_map.get(attr, 0)
        if actor_val < min_val:
            missing.append({
                'attr':  attr.replace('_', ' ').title(),
                'have':  actor_val,
                'need':  min_val,
                'gap':   min_val - actor_val
            })

    return {
        'eligible': len(missing) == 0,
        'missing':  missing
    }
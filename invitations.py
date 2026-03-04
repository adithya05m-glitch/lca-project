import random

# ─────────────────────────────────────────────────────
#  INVITATION GENERATION
#  Called each End Day. Returns an Invitation object
#  or None depending on actor qualifications.
# ─────────────────────────────────────────────────────

INVITE_TITLES = [
    'Project Arjun', 'Nandanam 2', 'The Last Khan', 'Maalik',
    'Kaadhal', 'Phoenix Rising', 'Thirudan', 'Baadshah Returns',
    'Kalki Rises', 'Dil Aur Dhadkan', 'Raavanasura 2', 'Mizhiyoram',
]

INVITE_DIRECTORS = {
    'bolly': ['Kiran Johari', 'Raj Kumar Hiranand', 'Zoha Akhtaar', 'Anurag Kapur'],
    'kolly': ['Kani Rathnam', 'Gokesh Janagaraaj', 'B.R. Murugadaas', 'Cutlee Kumaar'],
    'tolly': ['S.S. Kajamoulee', 'Trivikraman', 'Koratala Shiva', 'Sukumaran'],
}

INVITE_REASONS = [
    'Your last film reached the right people. The director asked for you specifically.',
    'Your credibility in the industry has opened a door others don\'t even know exists.',
    'A producer who watched your work recommended you directly. No audition needed.',
    'Your connections score flagged you as the right person for this role.',
    'Your fame puts you on the shortlist for projects of this calibre.',
    'You worked with someone on this team before. They want you back.',
]


def maybe_generate_invitation(actor, db, Invitation_model):
    """
    Generates an Invitation object if the actor qualifies.
    Chance and tier scale with fame and connections.
    Returns an unsaved Invitation object or None.
    """
    # Qualification tiers
    if actor.fame >= 75:
        chance, tier, star_floor, salary_mult = 0.30, 'A', 4, 3.0
    elif actor.fame >= 50:
        chance, tier, star_floor, salary_mult = 0.20, 'A', 3, 2.0
    elif actor.fame >= 30:
        chance, tier, star_floor, salary_mult = 0.15, 'B', 3, 1.5
    elif actor.connections >= 40:
        chance, tier, star_floor, salary_mult = 0.12, 'B', 3, 1.3
    else:
        return None

    if random.random() > chance:
        return None

    # Pick director from actor's industry pool
    director_pool = INVITE_DIRECTORS.get(actor.industry, INVITE_DIRECTORS['bolly'])
    director_name = random.choice(director_pool)
    director_stars = random.randint(star_floor, 5)

    # Salary: scale from base ranges by tier and multiplier
    base_salaries = {'A': random.randint(1000000, 5000000), 'B': random.randint(300000, 1000000)}
    salary = int(base_salaries[tier] * salary_mult)

    shoot_days = {'A': random.randint(40, 90), 'B': random.randint(20, 50)}[tier]
    budget     = random.choice(['High', 'Mega'] if tier == 'A' else ['Mid', 'High'])
    role_type  = random.choice(['Lead Hero', 'Lead Heroine'] if tier == 'A' else ['Supporting Lead', 'Villain'])
    genre      = random.choice(['Action', 'Drama', 'Thriller', 'Biographical', 'Romance'])

    return Invitation_model(
        actor_id      = actor.id,
        movie_title   = random.choice(INVITE_TITLES),
        role_type     = role_type,
        role_tier     = tier,
        genre         = genre,
        director      = director_name,
        director_stars= director_stars,
        budget        = budget,
        salary        = salary,
        shoot_days    = shoot_days,
        invite_reason = random.choice(INVITE_REASONS),
        invite_type   = 'direct' if actor.fame >= 50 else 'connections',
        expires_day   = actor.game_day + 5,
        created_day   = actor.game_day,
        is_active     = True,
    )
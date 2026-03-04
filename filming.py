import random

# ─────────────────────────────────────────────────────
#  QUALITY SYSTEM CONSTANTS
#  Auto-advance can only push quality up to AUTO_QUALITY_CAP.
#  Only a voluntary set visit can push it beyond that, up to 100.
# ─────────────────────────────────────────────────────

AUTO_QUALITY_CAP = 60   # ceiling for passive quality gain per film
AUTO_QUALITY_GAIN = 3   # how many points auto-advance adds per day (up to cap)

# ─────────────────────────────────────────────────────
#  ON-SET RANDOM EVENTS
#  25% chance of appearing on any voluntary set visit.
#  Each event has two choices with different stat effects.
# ─────────────────────────────────────────────────────

ON_SET_EVENTS = [
    {
        'id': 'costar_conflict',
        'title': 'Co-Star Clash',
        'description': 'Your co-star confronts you between takes — they think you\'re overshadowing them. The whole crew is watching.',
        'choices': [
            {
                'id': 'defuse',
                'label': 'Defuse it calmly',
                'preview': '+2 Connections, small goodwill with director',
                'conn': 2, 'quality': 0, 'energy': 0, 'fame': 0, 'credibility': 2, 'acting': 0,
            },
            {
                'id': 'stand_ground',
                'label': 'Stand your ground',
                'preview': '+4 Film Quality (your intensity shines), -3 Connections',
                'conn': -3, 'quality': 4, 'energy': 0, 'fame': 0, 'credibility': 0, 'acting': 0,
            },
        ]
    },
    {
        'id': 'director_improv',
        'title': 'Director Goes Off-Script',
        'description': 'The director tears up the schedule and demands an intense improvised scene — right now, no preparation.',
        'choices': [
            {
                'id': 'commit',
                'label': 'Go all in',
                'preview': '+8 Film Quality, -10 Energy, +1 Connections',
                'conn': 1, 'quality': 8, 'energy': -10, 'fame': 0, 'credibility': 0, 'acting': 0,
            },
            {
                'id': 'request_time',
                'label': 'Ask for 5 minutes',
                'preview': '+4 Film Quality',
                'conn': 0, 'quality': 4, 'energy': 0, 'fame': 0, 'credibility': 0, 'acting': 0,
            },
        ]
    },
    {
        'id': 'production_delay',
        'title': 'Production Delay',
        'description': 'A key set piece collapsed. Today\'s shoot is cancelled. You have unexpected free time.',
        'choices': [
            {
                'id': 'rest',
                'label': 'Use it to rest',
                'preview': '+20 Energy',
                'conn': 0, 'quality': 0, 'energy': 20, 'fame': 0, 'credibility': 0, 'acting': 0,
            },
            {
                'id': 'rehearse',
                'label': 'Spend it rehearsing',
                'preview': '+3 Film Quality, +2 Acting Skill',
                'conn': 0, 'quality': 3, 'energy': 0, 'fame': 0, 'credibility': 0, 'acting': 2,
            },
        ]
    },
    {
        'id': 'viral_bts',
        'title': 'Behind-the-Scenes Leak',
        'description': 'A crew member\'s video of you doing a stunt goes viral. Millions of views overnight.',
        'choices': [
            {
                'id': 'embrace',
                'label': 'Embrace it publicly',
                'preview': '+5 Fame, -2 Credibility',
                'conn': 0, 'quality': 0, 'energy': 0, 'fame': 5, 'credibility': -2, 'acting': 0,
            },
            {
                'id': 'stay_professional',
                'label': 'Stay professional',
                'preview': '+3 Credibility, +1 Fame',
                'conn': 0, 'quality': 0, 'energy': 0, 'fame': 1, 'credibility': 3, 'acting': 0,
            },
        ]
    },
]


def get_todays_event():
    """25% chance of returning a random on-set event. Returns None otherwise."""
    if random.random() < 0.25:
        return random.choice(ON_SET_EVENTS)
    return None


def apply_event_choice(actor, film, event_id, choice_id):
    """
    Applies the stat effects of the chosen response to an on-set event.
    Returns a flash message string.
    """
    event  = next((e for e in ON_SET_EVENTS if e['id'] == event_id), None)
    if not event:
        return 'Something happened on set.'
    choice = next((c for c in event['choices'] if c['id'] == choice_id), None)
    if not choice:
        return 'Something happened on set.'

    if choice['conn']:
        actor.connections  = max(0, min(100, actor.connections  + choice['conn']))
    if choice['quality']:
        film.quality_score = max(0, min(100, film.quality_score + choice['quality']))
    if choice['energy']:
        actor.energy       = max(0, min(100, actor.energy       + choice['energy']))
    if choice['fame']:
        actor.fame         = max(0, min(100, actor.fame         + choice['fame']))
    if choice['credibility']:
        actor.credibility  = max(0, min(100, actor.credibility  + choice['credibility']))
    if choice['acting']:
        actor.acting_skill = max(0, min(100, actor.acting_skill + choice['acting']))

    return f'On-set choice made: {choice["label"]}. {choice["preview"]}'


# ─────────────────────────────────────────────────────
#  VOLUNTARY EFFORT — applies when player visits set
# ─────────────────────────────────────────────────────

EFFORT_CONFIG = {
    'minimum': {
        'energy_cost':  10,
        'quality_gain': (1, 4),
        'acting_gain':  0,
        'message': 'You hit your marks and kept things professional. The director seemed satisfied — barely.',
    },
    'standard': {
        'energy_cost':  20,
        'quality_gain': (4, 8),
        'acting_gain':  (0, 1),
        'message': 'A solid day\'s work. You brought the character to life and the crew respected your focus.',
    },
    'method': {
        'energy_cost':  35,
        'quality_gain': (8, 14),
        'acting_gain':  (3, 5),
        'message': 'Total immersion. You lost yourself in the role. The director called cut and just stared.',
    },
}


def apply_effort(actor, film, effort):
    """
    Applies a voluntary effort choice to the actor and film.
    Unlike auto-advance, this can push quality_score above AUTO_QUALITY_CAP.
    Returns a dict with outcome details for the flash message.
    """
    config = EFFORT_CONFIG.get(effort, EFFORT_CONFIG['standard'])

    energy_cost = config['energy_cost']

    # Burnout: if actor doesn't have enough energy, force-drain to 0 and set tired
    if actor.energy - energy_cost < 0:
        actor.is_tired        = True
        actor.tired_days_left = 3
        actual_energy_cost    = actor.energy
    else:
        actual_energy_cost = energy_cost

    actor.energy = max(0, actor.energy - actual_energy_cost)

    # Quality gain — no cap when visiting voluntarily
    q_range = config['quality_gain']
    quality_gain = random.randint(q_range[0], q_range[1]) if isinstance(q_range, tuple) else q_range
    film.quality_score = min(100, film.quality_score + quality_gain)

    # Acting skill gain
    a_range = config['acting_gain']
    if isinstance(a_range, tuple):
        acting_gain = random.randint(a_range[0], a_range[1])
    else:
        acting_gain = a_range
    if acting_gain:
        actor.acting_skill = min(100, actor.acting_skill + acting_gain)

    # Mark that the player visited today
    film.last_visit_day = actor.game_day

    return {
        'energy_cost':  actual_energy_cost,
        'quality_gain': quality_gain,
        'acting_gain':  acting_gain,
        'message':      config['message'],
        'burned_out':   actor.is_tired,
    }

def generate_review(film, actor, result):
    """
    Generates a short, unique-feeling critic review based on
    the box office result, genre, role tier, and director rating.
    """
    title  = film.movie_title
    role   = film.role_type
    genre  = film.genre
    tier   = film.role_tier
    dstars = film.director_stars

    # Opening lines by result
    openings = {
        'blockbuster': [
            f'"{title}" is nothing short of a phenomenon.',
            f'A masterpiece. "{title}" will be talked about for decades.',
            f'"{title}" redefines what Indian cinema can achieve.',
            f'Once in a generation, a film like "{title}" comes along.',
        ],
        'hit': [
            f'"{title}" delivers exactly what audiences came for.',
            f'A crowd-pleaser through and through — "{title}" earns its success.',
            f'"{title}" is the kind of solid, satisfying cinema the industry needs more of.',
            f'Audiences are loving "{title}", and the box office shows it.',
        ],
        'average': [
            f'"{title}" is a film of missed opportunities.',
            f'Neither disappointing nor memorable, "{title}" simply exists.',
            f'"{title}" has its moments, but struggles to sustain momentum.',
            f'A mixed bag — "{title}" tries hard but lands somewhere in the middle.',
        ],
        'flop': [
            f'"{title}" fails to find an audience, and it\'s easy to see why.',
            f'Despite some promise, "{title}" collapses under its own weight.',
            f'"{title}" is a forgettable addition to an otherwise promising career.',
            f'A disappointment — "{title}" squanders a decent premise.',
        ],
        'disaster': [
            f'"{title}" is a cinematic catastrophe that will haunt its cast.',
            f'One of the worst releases of the year — "{title}" fails on every level.',
            f'"{title}" is the kind of film you warn people about.',
            f'Critics are calling "{title}" a career setback. They\'re not wrong.',
        ],
    }

    # Actor lines by result and tier
    actor_lines = {
        'blockbuster': {
            'A': f'{actor.name}\'s performance as the {role} is career-defining.',
            'B': f'{actor.name} steals every scene as the {role} — a star-making turn.',
            'C': f'{actor.name} brings unexpected depth to the {role} role.',
            'D': f'Even in a small role, {actor.name} leaves a mark.',
        },
        'hit': {
            'A': f'{actor.name} commands the screen as the {role} with effortless charisma.',
            'B': f'{actor.name} holds their own as the {role} — a confident showing.',
            'C': f'{actor.name}\'s {role} turn is one of the film\'s highlights.',
            'D': f'{actor.name} makes the most of limited screen time.',
        },
        'average': {
            'A': f'{actor.name} has better films ahead — this {role} role doesn\'t showcase their range.',
            'B': f'{actor.name} is adequate as the {role}, though the script holds them back.',
            'C': f'{actor.name}\'s {role} performance won\'t be remembered.',
            'D': f'{actor.name} passes through the film without making an impression.',
        },
        'flop': {
            'A': f'{actor.name}\'s {role} portrayal feels flat — audiences expected more.',
            'B': f'{actor.name} looks lost as the {role}. Better material is needed.',
            'C': f'{actor.name} as the {role} is the film\'s weakest element.',
            'D': f'{actor.name} has a rough outing in this forgettable {role} role.',
        },
        'disaster': {
            'A': f'{actor.name}\'s career will need time to recover from this {role} performance.',
            'B': f'{actor.name} as the {role} is unconvincing — a miscast that sinks the film.',
            'C': f'{actor.name}\'s {role} appearance is a low point in an already troubled production.',
            'D': f'{actor.name} should be grateful the {role} is small in this disaster.',
        },
    }

    # Director lines based on star rating and result
    if dstars >= 5:
        director_line = (
            f'Director {film.director}\'s vision is unmistakable throughout.'
            if result in ('blockbuster', 'hit')
            else f'Even {film.director} can\'t rescue this one.'
        )
    elif dstars >= 4:
        director_line = (
            f'{film.director}\'s direction keeps the {genre} narrative tight and engaging.'
            if result in ('blockbuster', 'hit')
            else f'{film.director}\'s direction feels restrained compared to their best work.'
        )
    else:
        director_line = (
            f'The direction handles the {genre} material competently.'
            if result in ('blockbuster', 'hit')
            else f'The direction fails to elevate the weak {genre} script.'
        )

    # Closing verdict
    verdicts = {
        'blockbuster': 'A must-watch. Book your tickets now.',
        'hit': 'Worth your time and money. A solid theatrical experience.',
        'average': 'Wait for the OTT release.',
        'flop': 'Skip it. Life is short.',
        'disaster': 'An early frontrunner for the year\'s worst. Avoid.',
    }

    opening = random.choice(openings.get(result, openings['average']))
    actor_l = actor_lines.get(result, actor_lines['average']).get(tier, '')
    verdict = verdicts.get(result, '')

    return f'{opening} {actor_l} {director_line} {verdict}'

# ─────────────────────────────────────────────────────
#  POST-PRODUCTION DAYS BY BUDGET
#  Bigger productions take longer to edit and release
# ─────────────────────────────────────────────────────

POST_PRODUCTION_DAYS = {
    'Low':  2,
    'Mid':  3,
    'High': 5,
    'Mega': 7,
}

# ─────────────────────────────────────────────────────
#  BOX OFFICE SCORE CALCULATION
# ─────────────────────────────────────────────────────

def calculate_box_office(film, actor):
    """
    Calculates a box office score (0-100) based on:
      - Actor performance stats (40%)
      - Director star rating (25%)
      - Budget tier (20%)
      - Random audience/market factor (15%)

    Returns (score, result_label, fame_change)
    """
    # Actor performance score — weighted average of key attributes
    actor_score = (
        actor.acting_skill    * 0.30 +
        actor.screen_presence * 0.25 +
        actor.looks           * 0.15 +
        actor.dialogue        * 0.20 +
        actor.dancing         * 0.10
    )
    # Normalise to 0-100 (raw score is already 0-100 since attrs are capped at 100)
    actor_component = actor_score * 0.40

    # Director component — 5 stars maps to ~25 points
    director_component = (film.director_stars / 5) * 25

    # Budget component
    budget_scores = {'Low': 8, 'Mid': 13, 'High': 18, 'Mega': 20}
    budget_component = budget_scores.get(film.budget, 10)

    # Random audience factor (15 points max)
    audience_component = random.uniform(0, 15)

    raw_score = actor_component + director_component + budget_component + audience_component
    score = min(round(raw_score, 1), 100)

    # Determine result label and fame change
    if score >= 80:
        result   = 'blockbuster'
        fame_chg = random.randint(8, 15)
    elif score >= 60:
        result   = 'hit'
        fame_chg = random.randint(3, 7)
    elif score >= 40:
        result   = 'average'
        fame_chg = random.randint(0, 3)
    elif score >= 20:
        result   = 'flop'
        fame_chg = -random.randint(3, 8)
    else:
        result   = 'disaster'
        fame_chg = -random.randint(10, 20)

    return score, result, fame_chg

# ─────────────────────────────────────────────────────
#  PROCESS ACTIVE FILMS ON REST
#  Called every time the actor rests. Advances each film
#  by one day and triggers release when shooting is done.
# ─────────────────────────────────────────────────────

def process_filming(actor, active_films):
    """
    Advances each active film by 1 day.
    Handles transitions: filming → post_production → released.

    Returns a list of result dicts with messages to flash.
    Each dict has: message (str), category ('good'/'bad'/'neutral')
    """
    results = []

    for film in active_films:

        if film.status == 'filming':
            film.days_completed += 1

            # Passive quality gain — only up to AUTO_QUALITY_CAP (60)
            # Player must visit set voluntarily to push beyond this
            if film.quality_score < AUTO_QUALITY_CAP:
                gain = min(AUTO_QUALITY_GAIN, AUTO_QUALITY_CAP - film.quality_score)
                film.quality_score += gain
                
            remaining = film.total_shoot_days - film.days_completed

            if remaining <= 0:
                # Shooting wrapped — move to post-production
                film.status = 'post_production'
                post_days   = POST_PRODUCTION_DAYS.get(film.budget, 3)
                # Re-use days_completed to also track post-production countdown
                # We store total post days in total_shoot_days temporarily
                film.total_shoot_days = post_days
                film.days_completed   = 0
                results.append({
                    'message':  f'🎬 Shooting wrapped on "{film.movie_title}"! Now in post-production.',
                    'category': 'neutral',
                })
            else:
                results.append({
                    'message':  f'🎥 Filming "{film.movie_title}" — {remaining} shoot day(s) remaining.',
                    'category': 'neutral',
                })

        elif film.status == 'post_production':
            film.days_completed += 1
            remaining = film.total_shoot_days - film.days_completed

            if remaining <= 0:
                # Post-production done — release the film!
                score, result, fame_chg = calculate_box_office(film, actor)

                film.status           = 'released'
                film.box_office_result = result
                film.box_office_score  = score
                film.fame_change       = fame_chg
                film.release_day       = actor.game_day

                film.review            = generate_review(film, actor, result)

                # Apply fame change to actor (clamped 0–100)
                actor.fame = max(0, min(100, actor.fame + fame_chg))

                result_emoji = {
                    'blockbuster': '🏆',
                    'hit':         '✅',
                    'average':     '📊',
                    'flop':        '📉',
                    'disaster':    '💀',
                }.get(result, '🎬')

                fame_str = f'+{fame_chg}' if fame_chg >= 0 else str(fame_chg)
                category = 'good' if fame_chg > 0 else 'bad'

                results.append({
                    'message':  (
                        f'{result_emoji} "{film.movie_title}" has RELEASED! '
                        f'Box office: {result.upper()} (score: {score}). '
                        f'Fame: {fame_str}. '
                        f'Check your Filmography!'
                    ),
                    'category':         category,
                    'released_film_id': film.id,   # NEW — signals the rest route
                })
            else:
                results.append({
                    'message':  f'✂️ "{film.movie_title}" in post-production — {remaining} day(s) until release.',
                    'category': 'neutral',
                })

    return results

# ─────────────────────────────────────────────────────
#  MILESTONE DEFINITIONS
#  check(actor, stats) uses stats from game_state.get_career_stats()
#  stats keys: total_films, blockbusters, hits, flops,
#              total_earnings, total_apps, accepted, rejected,
#              game_days, peak_fame
# ─────────────────────────────────────────────────────

MILESTONES = [
    # ── First Steps ──
    {
        'key':         'first_audition',
        'category':    'First Steps',
        'name':        'First Audition',
        'icon':        '🎤',
        'rarity':      None,
        'description': 'Attended your very first audition.',
        'hint':        'Apply for any role on the Job Board.',
        'check':       lambda a, s: s['total_apps'] >= 1,
    },
    {
        'key':         'first_role',
        'category':    'First Steps',
        'name':        'First Role',
        'icon':        '📜',
        'rarity':      None,
        'description': 'Signed your first movie contract.',
        'hint':        'Accept an offer from your Inbox.',
        'check':       lambda a, s: s['accepted'] >= 1,
    },
    {
        'key':         'first_release',
        'category':    'First Steps',
        'name':        'Opening Night',
        'icon':        '🎞',
        'rarity':      None,
        'description': 'Had your first film released.',
        'hint':        'Complete filming and let a film release.',
        'check':       lambda a, s: s['total_films'] >= 1,
    },

    # ── Box Office ──
    {
        'key':         'first_hit',
        'category':    'Box Office',
        'name':        'Box Office Hit',
        'icon':        '🎯',
        'rarity':      None,
        'description': 'Had your first box office hit.',
        'hint':        'Get a Hit result or better on a released film.',
        'check':       lambda a, s: s['hits'] >= 1,
    },
    {
        'key':         'first_blockbuster',
        'category':    'Box Office',
        'name':        'Blockbuster!',
        'icon':        '🌟',
        'rarity':      'rare',
        'description': 'Starred in a Blockbuster film.',
        'hint':        'Achieve a Blockbuster result — score 80+.',
        'check':       lambda a, s: s['blockbusters'] >= 1,
    },
    {
        'key':         'three_blockbusters',
        'category':    'Box Office',
        'name':        'Hat-Trick',
        'icon':        '🏆',
        'rarity':      'epic',
        'description': 'Starred in three Blockbuster films.',
        'hint':        'Achieve three Blockbuster results.',
        'check':       lambda a, s: s['blockbusters'] >= 3,
    },

    # ── Earnings ──
    {
        'key':         'earn_500k',
        'category':    'Earnings',
        'name':        'In The Money',
        'icon':        '💰',
        'rarity':      None,
        'description': 'Earned Rs.5,00,000 across your career.',
        'hint':        'Accumulate Rs.5L in total salary from films.',
        'check':       lambda a, s: s['total_earnings'] >= 500000,
    },
    {
        'key':         'earn_1cr',
        'category':    'Earnings',
        'name':        'One Crore Club',
        'icon':        '💎',
        'rarity':      'rare',
        'description': 'Earned Rs.1 Crore across your career.',
        'hint':        'Take high-paying A and B tier roles.',
        'check':       lambda a, s: s['total_earnings'] >= 10000000,
    },

    # ── Fame ──
    {
        'key':         'fame_25',
        'category':    'Fame',
        'name':        'Recognised',
        'icon':        '⭐',
        'rarity':      None,
        'description': 'Reached 25 Fame.',
        'hint':        'Reach 25 Fame.',
        'check':       lambda a, s: a.fame >= 25,
    },
    {
        'key':         'fame_50',
        'category':    'Fame',
        'name':        'Known Face',
        'icon':        '🌟',
        'rarity':      None,
        'description': 'Reached 50 Fame — people recognise you on the street.',
        'hint':        'Reach 50 Fame.',
        'check':       lambda a, s: a.fame >= 50,
    },
    {
        'key':         'fame_75',
        'category':    'Fame',
        'name':        'Star',
        'icon':        '🔥',
        'rarity':      'rare',
        'description': 'Reached 75 Fame — a household name.',
        'hint':        'Reach 75 Fame.',
        'check':       lambda a, s: a.fame >= 75,
    },

    # ── Resilience ──
    {
        'key':         'comeback',
        'category':    'Resilience',
        'name':        'The Comeback',
        'icon':        '💪',
        'rarity':      'rare',
        'description': 'Had a Flop, then bounced back with a Blockbuster.',
        'hint':        'Get a Flop result and then a Blockbuster result.',
        'check':       lambda a, s: s['flops'] >= 1 and s['blockbusters'] >= 1,
    },
    {
        'key':         'survive_100_days',
        'category':    'Resilience',
        'name':        'Hundred Days',
        'icon':        '📅',
        'rarity':      None,
        'description': 'Survived 100 days in the industry.',
        'hint':        'Reach Day 100.',
        'check':       lambda a, s: a.game_day >= 100,
    },
]


def check_and_award(actor, stats, db, Milestone_model):
    """
    Checks all milestones against current actor state.
    Awards any newly-earned ones and returns a list of new names
    for flash messages.

    actor: Actor db object
    stats: dict from game_state.get_career_stats()
    db: the SQLAlchemy db instance from app.py
    Milestone_model: the Milestone class from app.py
    """
    new_awards = []

    earned_keys = {
        m.key for m in Milestone_model.query.filter_by(
            actor_id=actor.id, earned=True
        ).all()
    }

    for m_def in MILESTONES:
        if m_def['key'] in earned_keys:
            continue

        try:
            earned = m_def['check'](actor, stats)
        except Exception:
            earned = False

        if earned:
            row = Milestone_model.query.filter_by(
                actor_id=actor.id, key=m_def['key']
            ).first()
            if row:
                row.earned     = True
                row.earned_day = actor.game_day
            else:
                db.session.add(Milestone_model(
                    actor_id   = actor.id,
                    key        = m_def['key'],
                    earned     = True,
                    earned_day = actor.game_day,
                ))
            new_awards.append(m_def['name'])

    return new_awards


def get_milestone_context(actor_id, Milestone_model):
    """
    Returns the full category/tile structure for milestones.html.
    """
    earned_rows = {
        m.key: m for m in Milestone_model.query.filter_by(
            actor_id=actor_id, earned=True
        ).all()
    }

    categories = {}
    for m_def in MILESTONES:
        cat = m_def['category']
        if cat not in categories:
            categories[cat] = {'name': cat, 'milestones': [], 'earned_count': 0}

        row = earned_rows.get(m_def['key'])
        categories[cat]['milestones'].append({
            'icon':        m_def['icon'],
            'name':        m_def['name'],
            'description': m_def['description'],
            'hint':        m_def['hint'],
            'rarity':      m_def['rarity'],
            'earned':      bool(row),
            'earned_day':  row.earned_day if row else None,
        })
        if row:
            categories[cat]['earned_count'] += 1

    return {
        'milestone_categories': list(categories.values()),
        'earned_count':         sum(c['earned_count'] for c in categories.values()),
        'total_count':          len(MILESTONES),
    }
# ─────────────────────────────────────────────────────
#  PRESTIGE RANK SYSTEM
# ─────────────────────────────────────────────────────

def get_prestige(actor, released_films):
    """
    Calculates the actor's current prestige rank based on
    fame, number of released films, and quality of those films.

    Returns a dict with:
      - rank (str): internal key
      - label (str): display name
      - emoji (str): icon
      - next_rank (dict or None): what's needed to rank up
    """
    film_count    = len(released_films)
    blockbusters  = sum(1 for f in released_films if f.box_office_result == 'blockbuster')
    hits_or_above = sum(1 for f in released_films if f.box_office_result in ('blockbuster', 'hit'))

    # Check ranks from highest to lowest — return the first one that fits
    if actor.fame >= 100 and film_count >= 15 and blockbusters >= 5:
        return {
            'rank':      'legend',
            'label':     'LEGEND',
            'emoji':     '👑',
            'next_rank': None,   # Already won
        }

    if actor.fame >= 75 and film_count >= 10 and hits_or_above >= 3:
        return {
            'rank':      'superstar',
            'label':     'Superstar',
            'emoji':     '🔥',
            'next_rank': {
                'label':    'Legend',
                'needs': [
                    f'Fame to 100 (currently {actor.fame})',
                    f'15 released films (currently {film_count})',
                    f'5 Blockbusters (currently {blockbusters})',
                ],
            },
        }

    if actor.fame >= 50 and film_count >= 5 and hits_or_above >= 1:
        return {
            'rank':      'star',
            'label':     'Star',
            'emoji':     '🌟',
            'next_rank': {
                'label': 'Superstar',
                'needs': [
                    f'Fame to 75 (currently {actor.fame})',
                    f'10 released films (currently {film_count})',
                    f'3 Hits or Blockbusters (currently {hits_or_above})',
                ],
            },
        }

    if actor.fame >= 25 and film_count >= 2:
        return {
            'rank':      'rising',
            'label':     'Rising Star',
            'emoji':     '⭐',
            'next_rank': {
                'label': 'Star',
                'needs': [
                    f'Fame to 50 (currently {actor.fame})',
                    f'5 released films (currently {film_count})',
                    f'1 Hit or Blockbuster (currently {hits_or_above})',
                ],
            },
        }

    if actor.fame >= 10 or film_count >= 1:
        return {
            'rank':      'struggling',
            'label':     'Struggling Actor',
            'emoji':     '🌱',
            'next_rank': {
                'label': 'Rising Star',
                'needs': [
                    f'Fame to 25 (currently {actor.fame})',
                    f'2 released films (currently {film_count})',
                ],
            },
        }

    return {
        'rank':      'extra',
        'label':     'Extra',
        'emoji':     '🎭',
        'next_rank': {
            'label': 'Struggling Actor',
            'needs': [
                f'Fame to 10 (currently {actor.fame})',
                'OR release your first film',
            ],
        },
    }

# ─────────────────────────────────────────────────────
#  WIN CONDITION CHECK
# ─────────────────────────────────────────────────────

def check_win(actor, released_films):
    """
    Returns True if the actor has reached Legend status.
    """
    prestige = get_prestige(actor, released_films)
    return prestige['rank'] == 'legend'

# ─────────────────────────────────────────────────────
#  LOSE CONDITION CHECK
# ─────────────────────────────────────────────────────

def check_lose(actor, active_films):
    """
    Returns True if the actor is broke with no active income.
    Broke = funds below zero AND no films currently being shot
    (active films represent contractual income that's coming).
    """
    return actor.funds < 0 and len(active_films) == 0

# ─────────────────────────────────────────────────────
#  CAREER SUMMARY STATS
#  Used on both the dashboard and the end screens
# ─────────────────────────────────────────────────────

def get_career_stats(actor, released_films, all_applications):
    """
    Returns a dict of summary stats for display.
    """
    total_earnings = sum(f.salary for f in released_films)
    blockbusters   = sum(1 for f in released_films if f.box_office_result == 'blockbuster')
    hits           = sum(1 for f in released_films if f.box_office_result == 'hit')
    flops          = sum(1 for f in released_films if f.box_office_result in ('flop', 'disaster'))
    total_apps     = len(all_applications)
    accepted       = sum(1 for a in all_applications if a.status == 'accepted')
    rejected       = sum(1 for a in all_applications if a.status == 'rejected')

    return {
        'total_films':    len(released_films),
        'blockbusters':   blockbusters,
        'hits':           hits,
        'flops':          flops,
        'total_earnings': total_earnings,
        'total_apps':     total_apps,
        'accepted':       accepted,
        'rejected':       rejected,
        'game_days':      actor.game_day,
        'peak_fame':      actor.fame,    # current (we don't track peak separately yet)
    }

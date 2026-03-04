import random

# ─────────────────────────────────────────────────────
#  CONTROVERSY LIBRARY
#  Each entry defines the text, severity, and numeric
#  effects for each of the four possible responses.
# ─────────────────────────────────────────────────────

CONTROVERSIES = [
    {
        'type':              'On-Set Argument',
        'severity':          'Medium',
        'headline':          'Explosive Meltdown Rocks Film Set',
        'tabloid_quote':     'Sources say the argument was audible three floors away. Production was halted for two hours.',
        'source_label':      'SpotboyE Exclusive',
        'narrative':         'An anonymous crew member posted a blurry video. The comments section is already on fire. Studios are watching.',
        'immediate_fame':    3,
        'credibility_hit':   12,
        'public_mood':       '😤',
        'responses': {
            'apologise': {'fame': -2,  'credibility': -8,  'msg': 'Your public apology was received. Short-term cost, cleaner path forward.'},
            'deny':      {'fame':  0,  'credibility':  0,  'msg': 'You said nothing. The story will die on its own timeline — or it won\'t.'},
            'lean':      {'fame': 10,  'credibility': -18, 'msg': 'You owned it. Fame spiked. Something else quietly took a lasting hit.'},
            'pr':        {'fame':  0,  'credibility':  5,  'cost': 50000, 'msg': 'The PR team earned their fee. Story gone in 24 hours.'},
        },
        'precedents': [
            ('Established star who apologised', 'Back on A-list within 3 months'),
            ('Newcomer who leaned in',          'Fame spiked, credibility never recovered'),
        ],
    },
    {
        'type':              'Award Show Snub',
        'severity':          'Low',
        'headline':          'Critics Slam Surprise Snub at Filmfare',
        'tabloid_quote':     'The committee overlooked what many called the performance of the year. Fans are furious.',
        'source_label':      'Filmfare Insider',
        'narrative':         'You were the favourite going into nominations. The snub feels calculated. Social media is siding with you — for now.',
        'immediate_fame':    5,
        'credibility_hit':   0,
        'public_mood':       '😮',
        'responses': {
            'apologise': {'fame':  0,  'credibility': 0,  'msg': 'A graceful, measured response. The industry respected it.'},
            'deny':      {'fame':  0,  'credibility': 0,  'msg': 'You let the work speak. The conversation moved on quickly.'},
            'lean':      {'fame':  8,  'credibility': -5, 'msg': 'You made it a moment. Fans loved it. Industry insiders, less so.'},
            'pr':        {'fame':  0,  'credibility': 3,  'cost': 20000, 'msg': 'Narrative shaped. You came out looking like the bigger person.'},
        },
        'precedents': [
            ('Graceful response', 'Goodwill boost — won next year'),
            ('Public grievance',  'Made enemies in the committee'),
        ],
    },
    {
        'type':              'Social Media Controversy',
        'severity':          'High',
        'headline':          'Old Post Resurfaces — Internet Divided',
        'tabloid_quote':     'A 6-year-old post has been screenshotted and shared 40,000 times. Brands are watching.',
        'source_label':      'Twitter/X Trending',
        'narrative':         'You barely remember writing it. But the internet never forgets. One wrong move here and your brand deals vanish.',
        'immediate_fame':    -2,
        'credibility_hit':   20,
        'public_mood':       '😡',
        'responses': {
            'apologise': {'fame': -3,  'credibility': -10, 'msg': 'Immediate apology. Brands stayed. Audience moved on in a week.'},
            'deny':      {'fame':  0,  'credibility':   0, 'msg': 'You stayed silent. Risky. Time will tell if that was wise.'},
            'lean':      {'fame':  6,  'credibility': -25, 'msg': 'Defiant. Polarised your fanbase. Lost 3 brand deals. Worth it?'},
            'pr':        {'fame':  0,  'credibility':   5, 'cost': 100000, 'msg': 'The narrative was buried. Expensive, but effective.'},
        },
        'precedents': [
            ('Immediate apology', 'Brands stayed. Audience moved on in a week.'),
            ('Defiant response',  'Lost 3 brand deals. Fanbase permanently split.'),
        ],
    },
    {
        'type':              'Co-Star Feud Rumour',
        'severity':          'Medium',
        'headline':          'Feud Allegations Threaten Film Release',
        'tabloid_quote':     'Neither actor will share a frame in the promotional material. The producer denies everything — unconvincingly.',
        'source_label':      'Bollywood Hungama',
        'narrative':         'What started as creative differences became a tabloid war. The studio needs both of you to cooperate for promotions.',
        'immediate_fame':    4,
        'credibility_hit':   8,
        'public_mood':       '🍿',
        'responses': {
            'apologise': {'fame': -1,  'credibility': -5, 'msg': 'You reached out privately. Co-star responded. Promotions saved.'},
            'deny':      {'fame':  0,  'credibility':  0, 'msg': 'No comment from either side. Rumours died in two weeks.'},
            'lean':      {'fame': 12,  'credibility': -12,'msg': 'You made it a saga. Massive press. Film releases into a storm of attention.'},
            'pr':        {'fame':  0,  'credibility':  5, 'cost': 75000, 'msg': 'Joint statement issued. Co-star played along. Crisis managed.'},
        },
        'precedents': [
            ('Reconciled publicly', 'Film released to huge hype'),
            ('Stayed silent',       'Rumours died in two weeks'),
        ],
    },
]


def maybe_trigger_controversy(actor):
    """
    Called when the player advances the day (End Day).
    10% base chance. Rises to 20% if fame > 60.
    Won't trigger if there's already an unresolved controversy.
    Returns a template dict (not a DB object) or None.
    """
    # Check for existing unresolved controversy (passed in from the route)
    # The route itself checks the DB — this function only handles chance rolling.
    chance = 0.20 if actor.fame > 60 else 0.10
    if random.random() > chance:
        return None
    return random.choice(CONTROVERSIES)


def resolve_controversy(controversy, actor, response):
    """
    Applies response effects to actor.
    controversy: a Controversy DB object
    response: 'apologise' | 'deny' | 'lean' | 'pr'
    Returns a flash message string.
    """
    template = next((c for c in CONTROVERSIES if c['type'] == controversy.type), None)
    if not template:
        controversy.resolved        = True
        controversy.response_chosen = response
        return 'Controversy resolved.'

    effects = template['responses'].get(response, {})

    actor.fame        = max(0, min(100, actor.fame        + effects.get('fame', 0)))
    actor.credibility = max(0, min(100, actor.credibility + effects.get('credibility', 0)))

    # PR option costs money
    if response == 'pr' and 'cost' in effects:
        actor.funds -= effects['cost']

    controversy.resolved        = True
    controversy.response_chosen = response

    return effects.get('msg', 'Controversy resolved.')
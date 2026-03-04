import random

# ─────────────────────────────────────────────────────
#  ACTIVITY DEFINITIONS
#  Each activity is a dict with everything the system needs
# ─────────────────────────────────────────────────────

ACTIVITIES = {
    'acting_class': {
        'name':        'Acting Class',
        'emoji':       '🎭',
        'description': 'Work with a coach on technique, emotional range, and dialogue delivery.',
        'energy_cost': 30,
        'money_cost':  8000,
        'days':        1,
        'gains': {
            'acting_skill': (2, 5),
            'dialogue':     (1, 4),
        },
    },
    'gym': {
        'name':        'Gym Session',
        'emoji':       '💪',
        'description': 'Build strength, stamina, and the physique that the camera loves.',
        'energy_cost': 25,
        'money_cost':  3500,
        'days':        1,
        'gains': {
            'fitness': (2, 5),
            'looks':   (1, 3),
        },
    },
    'dance_workshop': {
        'name':        'Dance Workshop',
        'emoji':       '💃',
        'description': 'Learn choreography, stage movement, and screen presence through dance.',
        'energy_cost': 30,
        'money_cost':  7000,
        'days':        1,
        'gains': {
            'dancing':         (2, 5),
            'screen_presence': (1, 3),
        },
    },
    'networking': {
        'name':        'Networking Event',
        'emoji':       '🤝',
        'description': 'Attend an industry party or premiere. Be seen, make contacts.',
        'energy_cost': 20,
        'money_cost':  5000,
        'days':        1,
        'gains': {
            'connections': (2, 6),
            'fame':        (1, 3),
        },
    },
    'script_reading': {
        'name':        'Script Reading',
        'emoji':       '📖',
        'description': 'Study scripts at home. Free but builds dialogue and mental toughness.',
        'energy_cost': 10,
        'money_cost':  0,
        'days':        1,
        'gains': {
            'dialogue':   (1, 3),
            'resilience': (1, 3),
        },
    },
}

# ─────────────────────────────────────────────────────
#  CHECK IF ACTOR CAN DO AN ACTIVITY
# ─────────────────────────────────────────────────────

def can_do_activity(actor, activity_key):
    """
    Returns a dict:
      - can_do (bool): whether the actor has enough energy AND money
      - reason (str): explanation if they can't
    """
    activity = ACTIVITIES.get(activity_key)
    if not activity:
        return {'can_do': False, 'reason': 'Unknown activity.'}

    if actor.energy < activity['energy_cost']:
        return {
            'can_do': False,
            'reason': f"Not enough energy. Need {activity['energy_cost']} ⚡, have {actor.energy} ⚡."
        }

    if actor.funds < activity['money_cost']:
        return {
            'can_do': False,
            'reason': f"Not enough money. Need Rs.{activity['money_cost']:,}, have Rs.{actor.funds:,}."
        }

    return {'can_do': True, 'reason': ''}

# ─────────────────────────────────────────────────────
#  APPLY AN ACTIVITY TO AN ACTOR
# ─────────────────────────────────────────────────────

def do_activity(actor, activity_key):
    """
    Applies the activity to the actor:
      - Deducts energy and money
      - Rolls random stat gains and applies them (capped at 100)
      - Returns a result dict with what happened
    """
    check = can_do_activity(actor, activity_key)
    if not check['can_do']:
        return {'success': False, 'message': check['reason'], 'gains': {}}

    activity = ACTIVITIES[activity_key]

    # Deduct costs
    actor.energy -= activity['energy_cost']
    actor.funds  -= activity['money_cost']

    # Burnout debuff: -20% gains if actor is tired
    debuff = 0.8 if getattr(actor, 'is_tired', False) else 1.0

    # Roll and apply gains
    actual_gains = {}
    for attr, (min_gain, max_gain) in activity['gains'].items():
        gain = int(random.randint(min_gain, max_gain) * debuff)
        
        current = getattr(actor, attr, 0)
        new_val  = min(current + gain, 100)   # cap at 100
        setattr(actor, attr, new_val)
        actual_gains[attr] = gain

    # Build a readable gains string for the flash message
    gain_parts = []
    for attr, gain in actual_gains.items():
        label = attr.replace('_', ' ').title()
        gain_parts.append(f'+{gain} {label}')
    gains_str = ', '.join(gain_parts)

    message = (
        f"{activity['emoji']} {activity['name']} complete! "
        f"Gained: {gains_str}. "
        f"Energy left: {actor.energy} ⚡"
    )

    return {
        'success': True,
        'message': message,
        'gains':   actual_gains,
    }

# ─────────────────────────────────────────────────────
#  REST — restores energy, advances the day
# ─────────────────────────────────────────────────────

def do_rest(actor):
    """
    Resets energy to 100 and advances the game day by 1.
    Returns a result message.
    """
    actor.energy   = 100
    actor.game_day += 1

    return {
        'success': True,
        'message': (
            f"😴 Rested and recharged. "
            f"Welcome to Day {actor.game_day}! Energy fully restored to 100 ⚡."
        ),
    }

# ─────────────────────────────────────────────────────
#  GET ACTIVITIES WITH AVAILABILITY STATUS
#  Used by the template to show what's available vs locked
# ─────────────────────────────────────────────────────

def get_activities_with_status(actor):
    """
    Returns the full activities list, each tagged with
    whether the actor can currently do it and why not if not.
    """
    result = []
    for key, activity in ACTIVITIES.items():
        check = can_do_activity(actor, key)
        result.append({
            'key':         key,
            'name':        activity['name'],
            'emoji':       activity['emoji'],
            'description': activity['description'],
            'energy_cost': activity['energy_cost'],
            'money_cost':  activity['money_cost'],
            'gains':       activity['gains'],
            'can_do':      check['can_do'],
            'reason':      check['reason'],
        })
    return result

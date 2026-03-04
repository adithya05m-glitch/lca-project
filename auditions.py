import random

# ─────────────────────────────────────────────────────
#  CALLBACK CHANCES BY ROLE TIER
#  Probability (0.0 to 1.0) of getting a callback each day
# ─────────────────────────────────────────────────────

CALLBACK_CHANCE = {
    'A': 0.15,   # 15% — lead roles are competitive
    'B': 0.30,   # 30%
    'C': 0.55,   # 55%
    'D': 0.80,   # 80% — background work is easy to get called for
}

REJECTION_CHANCE = {
    'A': 0.25,   # 25% chance of outright rejection per day
    'B': 0.20,
    'C': 0.15,
    'D': 0.10,
}

# ─────────────────────────────────────────────────────
#  AUDITION SUCCESS FORMULA
#  Calculates how likely the actor is to pass the audition
# ─────────────────────────────────────────────────────

def audition_score(actor, role_tier):
    """
    Combines the actor's most relevant attributes into a score.
    Score is compared against the role tier threshold.
    Returns (score, threshold, passed)
    """
    # Weighted average of the key performance attributes
    score = (
        actor.acting_skill    * 0.30 +
        actor.screen_presence * 0.20 +
        actor.looks           * 0.15 +
        actor.dialogue        * 0.20 +
        actor.dancing         * 0.10 +
        actor.fame            * 0.05
    )

    # Add a random performance factor — even great actors have off days
    performance = random.uniform(0.8, 1.2)
    score = score * performance

    # Thresholds — what score you need to pass
    thresholds = {
        'A': 55,
        'B': 38,
        'C': 22,
        'D': 10,
    }
    threshold = thresholds[role_tier]

    return round(score, 1), threshold, score >= threshold

# ─────────────────────────────────────────────────────
#  PROCESS ALL PENDING APPLICATIONS FOR AN ACTOR
#  Called every time the actor rests (day advances)
# ─────────────────────────────────────────────────────

def process_applications(actor, applications):
    """
    Loops through all 'applied' and 'invited' applications,
    rolls for outcomes, updates statuses, and returns
    a list of result messages to show the player.

    Each result dict has:
      - message (str): what to show the player
      - category (str): 'good', 'bad', or 'neutral'
      - application: the updated application object
    """
    results = []

    for app in applications:

        # ── STAGE 1: applied → callback or rejection ──
        if app.status == 'applied':

            roll = random.random()

            # Outright rejection
            if roll < REJECTION_CHANCE.get(app.role_tier, 0.15):
                app.status = 'rejected'
                results.append({
                    'message':  f'❌ Rejected for {app.role_type} in "{app.movie_title}". They went with someone else.',
                    'category': 'bad',
                    'app':      app,
                })

            # Callback to audition
            elif roll < REJECTION_CHANCE.get(app.role_tier, 0.15) + CALLBACK_CHANCE.get(app.role_tier, 0.30):
                # Immediately run the audition
                score, threshold, passed = audition_score(actor, app.role_tier)

                if passed:
                    app.status = 'offered'
                    results.append({
                        'message':  (
                            f'🎉 OFFER! You auditioned for {app.role_type} in "{app.movie_title}" '
                            f'and got the role! Check your inbox to accept.'
                        ),
                        'category': 'good',
                        'app':      app,
                    })
                else:
                    app.status = 'rejected'
                    results.append({
                        'message':  (
                            f'📞 Callback for "{app.movie_title}" — but the audition didn\'t go well. '
                            f'Score: {score} (needed {threshold}). Keep training.'
                        ),
                        'category': 'bad',
                        'app':      app,
                    })

            # Still pending — no news yet
            else:
                results.append({
                    'message':  f'⏳ Still waiting to hear back about {app.role_type} in "{app.movie_title}".',
                    'category': 'neutral',
                    'app':      app,
                })

    return results

# ─────────────────────────────────────────────────────
#  ACCEPT A ROLE OFFER
#  Pays salary, boosts fame, marks as accepted
# ─────────────────────────────────────────────────────

def accept_offer(actor, application):
    """
    Applies the benefits of accepting a role:
      - Pays the salary into actor's funds
      - Boosts fame based on role tier
      - Returns a result message
    """
    fame_gain = {
        'A': random.randint(12, 20),
        'B': random.randint(6, 12),
        'C': random.randint(2, 6),
        'D': random.randint(1, 3),
    }.get(application.role_tier, 2)

    actor.funds += application.salary
    actor.fame   = min(actor.fame + fame_gain, 100)
    application.status = 'accepted'

    return {
        'message': (
            f'✅ You accepted the role of {application.role_type} in '
            f'"{application.movie_title}"! '
            f'Rs.{application.salary:,} paid. '
            f'+{fame_gain} Fame. Lights, camera, action!'
        ),
        'category': 'good',
    }

# ─────────────────────────────────────────────────────
#  DECLINE A ROLE OFFER
# ─────────────────────────────────────────────────────

def decline_offer(actor, application):
    """Marks the application as declined. No penalties."""
    application.status = 'declined'
    return {
        'message': f'🚫 You passed on the {application.role_type} role in "{application.movie_title}".',
        'category': 'neutral',
    }

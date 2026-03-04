import os
import json
import anthropic

# ─────────────────────────────────────────────────────
#  PERSONA VOICES
#  Defines the narrative tone for each persona.
#  Used in every prompt so Claude stays consistent.
# ─────────────────────────────────────────────────────

PERSONA_VOICES = {
    'newcomer': {
        'tone':  'raw, hungry, slightly overwhelmed. Short punchy sentences. This person has nothing to lose and everything to prove.',
        'style': 'gritty and urgent. No polish. Real.',
    },
    'nepo': {
        'tone':  'breezy, entitled, and faintly self-aware. Longer sentences. The world has always bent for this person and they half-expect it to keep doing so.',
        'style': 'casual and confident, with occasional flashes of insecurity underneath.',
    },
    'theatre': {
        'tone':  'cerebral, observational, slightly world-weary. This person has craft but is learning that craft alone does not make a star.',
        'style': 'literary and considered. Rich vocabulary but never showy.',
    },
    'model': {
        'tone':  'image-conscious and ambitious. Aware of how they look in every room. Used to being watched but not yet respected.',
        'style': 'sleek and self-possessed, with an edge of wanting to be taken seriously.',
    },
    'background': {
        'tone':  'quietly desperate but resilient. Has seen the industry from the bottom. Knows exactly how hard this is.',
        'style': 'understated and earned. Every small win feels enormous.',
    },
}

# ─────────────────────────────────────────────────────
#  STORY BEAT DEFINITIONS
#  Each beat has:
#    - key: unique identifier stored in DB
#    - title: shown on the cinematic card
#    - emoji: decorative
#    - prompt_fn: function(actor, context) → prompt string
# ─────────────────────────────────────────────────────

INDUSTRY_CITY = {
    'bolly': 'Mumbai',
    'kolly': 'Chennai',
    'tolly': 'Hyderabad',
}

INDUSTRY_NAME = {
    'bolly': 'Bollywood',
    'kolly': 'Kollywood',
    'tolly': 'Tollywood',
}


def _voice(actor):
    v = PERSONA_VOICES.get(actor.persona, PERSONA_VOICES['newcomer'])
    return f"Tone: {v['tone']}\nStyle: {v['style']}"


def _base(actor):
    city    = INDUSTRY_CITY.get(actor.industry, 'Mumbai')
    industry = INDUSTRY_NAME.get(actor.industry, 'Bollywood')
    return f"Actor name: {actor.name}\nIndustry: {industry}\nCity: {city}\nPersona: {actor.persona}\nCurrent Fame: {actor.fame}/100\nCurrent Funds: ₹{actor.funds:,}\nGame Day: {actor.game_day}"


BEAT_DEFINITIONS = {

    'arrival': {
        'title': 'Day One',
        'emoji': '🎬',
        'prompt_fn': lambda actor, ctx: f"""
You are writing the opening scene of a career story set in the Indian film industry.

{_base(actor)}
{_voice(actor)}

Write exactly 2 short paragraphs in the first person ("You...") describing {actor.name}'s arrival in {INDUSTRY_CITY.get(actor.industry, 'Mumbai')} on their first day. 
Capture the city, the ambition, and the specific fear of someone with this persona standing at the start of everything.
Do not mention any real film titles or real celebrities.
Do not use quotation marks around the output.
Write only the 2 paragraphs. Nothing else.
""",
    },

    'first_audition': {
        'title': 'First Audition',
        'emoji': '🎤',
        'prompt_fn': lambda actor, ctx: f"""
You are writing a story beat for a career simulation game set in the Indian film industry.

{_base(actor)}
{_voice(actor)}

Context: {actor.name} just submitted their very first audition application for a role.

Write exactly 2 short paragraphs in the first person ("You...") capturing the moment after clicking submit — the mix of hope and terror, what this first step means for someone with this persona.
Do not mention any real film titles or real celebrities.
Write only the 2 paragraphs. Nothing else.
""",
    },

    'first_role': {
        'title': 'First Role',
        'emoji': '📜',
        'prompt_fn': lambda actor, ctx: f"""
You are writing a story beat for a career simulation game set in the Indian film industry.

{_base(actor)}
{_voice(actor)}

Context: {actor.name} just accepted their first film role.
Role: {ctx.get('role_type', 'Supporting Role')} in "{ctx.get('movie_title', 'a film')}"
Director: {ctx.get('director', 'a director')}
Salary: ₹{ctx.get('salary', 0):,}

Write exactly 2 short paragraphs in the first person ("You...") about signing this contract — what it feels like to finally have a role, what this specific role means for someone of this persona, the weight of it becoming real.
Do not mention any real film titles or real celebrities.
Write only the 2 paragraphs. Nothing else.
""",
    },

    'first_release': {
        'title': 'Opening Night',
        'emoji': '🎞️',
        'prompt_fn': lambda actor, ctx: f"""
You are writing a story beat for a career simulation game set in the Indian film industry.

{_base(actor)}
{_voice(actor)}

Context: {actor.name}'s first film just released in cinemas.
Film: "{ctx.get('movie_title', 'the film')}"
Result: {ctx.get('result', 'average').upper()}
Fame change: {'+' if ctx.get('fame_change', 0) >= 0 else ''}{ctx.get('fame_change', 0)}

Write exactly 2 short paragraphs in the first person ("You...") about the feeling of your first film being out in the world — the vulnerability of being judged, the surreal reality of seeing your name on a poster, and what the result means emotionally for this persona.
Do not mention any real film titles or real celebrities.
Write only the 2 paragraphs. Nothing else.
""",
    },

    'first_blockbuster': {
        'title': 'Blockbuster',
        'emoji': '🏆',
        'prompt_fn': lambda actor, ctx: f"""
You are writing a story beat for a career simulation game set in the Indian film industry.

{_base(actor)}
{_voice(actor)}

Context: {actor.name} just had their first BLOCKBUSTER hit.
Film: "{ctx.get('movie_title', 'the film')}"
Box office score: {ctx.get('score', 80)}/100
Fame is now: {actor.fame}/100

Write exactly 2 short paragraphs in the first person ("You...") about what a blockbuster feels like — the morning after, the phone calls, the industry suddenly treating you differently, what this moment means for someone of this persona who has worked for it.
Do not mention any real film titles or real celebrities.
Write only the 2 paragraphs. Nothing else.
""",
    },

    'first_flop': {
        'title': 'The Flop',
        'emoji': '📉',
        'prompt_fn': lambda actor, ctx: f"""
You are writing a story beat for a career simulation game set in the Indian film industry.

{_base(actor)}
{_voice(actor)}

Context: {actor.name} just had their first flop or disaster at the box office.
Film: "{ctx.get('movie_title', 'the film')}"
Result: {ctx.get('result', 'flop').upper()}
Fame change: {ctx.get('fame_change', -5)}

Write exactly 2 short paragraphs in the first person ("You...") about what a public failure feels like in this industry — the silence from people who were calling, reading the reviews, what this does to someone of this persona. End on a note of defiance or resolve, not despair.
Do not mention any real film titles or real celebrities.
Write only the 2 paragraphs. Nothing else.
""",
    },

    'first_controversy': {
        'title': 'Crisis',
        'emoji': '🚨',
        'prompt_fn': lambda actor, ctx: f"""
You are writing a story beat for a career simulation game set in the Indian film industry.

{_base(actor)}
{_voice(actor)}

Context: {actor.name} is facing their first public controversy.
Headline: "{ctx.get('headline', 'A controversy has broken out')}"
Type: {ctx.get('type', 'On-Set Argument')}

Write exactly 2 short paragraphs in the first person ("You...") about the moment you see the headline — the stomach drop, the notifications flooding in, how someone of this persona instinctively reacts when the industry turns its scrutiny on them.
Do not mention any real celebrities.
Write only the 2 paragraphs. Nothing else.
""",
    },

    'prestige_rank': {
        'title': 'Rising Star',
        'emoji': '⭐',
        'prompt_fn': lambda actor, ctx: f"""
You are writing a story beat for a career simulation game set in the Indian film industry.

{_base(actor)}
{_voice(actor)}

Context: {actor.name} just reached a new prestige rank.
New rank: {ctx.get('rank_label', 'Rising Star')}
Fame: {actor.fame}/100
Day: {actor.game_day}

Write exactly 2 short paragraphs in the first person ("You...") about the moment you realise the industry sees you differently now — a specific interaction, a phone call, a moment in the mirror, something concrete that marks this transition for someone of this persona.
Do not mention any real celebrities.
Write only the 2 paragraphs. Nothing else.
""",
    },

    'first_invitation': {
        'title': 'The Call',
        'emoji': '✦',
        'prompt_fn': lambda actor, ctx: f"""
You are writing a story beat for a career simulation game set in the Indian film industry.

{_base(actor)}
{_voice(actor)}

Context: {actor.name} just received their first exclusive private invitation — a director approached them directly, no audition required.
Film: "{ctx.get('movie_title', 'a prestigious project')}"
Director: {ctx.get('director', 'a renowned director')}
Role: {ctx.get('role_type', 'Lead Role')}

Write exactly 2 short paragraphs in the first person ("You...") about receiving this call — what it means to be chosen rather than having to chase, how it feels different from every audition, what this moment means for someone of this persona.
Do not mention any real celebrities.
Write only the 2 paragraphs. Nothing else.
""",
    },

    'game_over': {
        'title': 'The End of the Road',
        'emoji': '💀',
        'prompt_fn': lambda actor, ctx: f"""
You are writing the ending scene of a career story set in the Indian film industry.

{_base(actor)}
{_voice(actor)}

Context: {actor.name}'s career is over. They ran out of money with no films in production.
Days survived: {actor.game_day}
Films released: {ctx.get('total_films', 0)}
Final fame: {actor.fame}

Write exactly 2 short paragraphs in the first person ("You...") about this ending — not melodramatic, but honest. What does it feel like to pack up and leave? What will this person carry with them? For this persona, what does failure mean? End with something that acknowledges the attempt was real, even if the dream didn't land.
Do not mention any real celebrities.
Write only the 2 paragraphs. Nothing else.
""",
    },

    'winner': {
        'title': 'Legend',
        'emoji': '👑',
        'prompt_fn': lambda actor, ctx: f"""
You are writing the final scene of a career story set in the Indian film industry.

{_base(actor)}
{_voice(actor)}

Context: {actor.name} has reached Legend status — the highest rank in the industry.
Days played: {actor.game_day}
Films released: {ctx.get('total_films', 0)}
Blockbusters: {ctx.get('blockbusters', 0)}
Final fame: {actor.fame}/100

Write exactly 2 short paragraphs in the first person ("You...") about this moment of arrival — what it feels like to have made it all the way, what you see when you look back at where you started, and what Legend actually means for someone of this persona. Make it earned, not triumphant.
Do not mention any real celebrities.
Write only the 2 paragraphs. Nothing else.
""",
    },
}


# ─────────────────────────────────────────────────────
#  GENERATION FUNCTION
# ─────────────────────────────────────────────────────

def generate_beat(beat_key, actor, context=None):
    """
    Calls Claude Haiku to generate narrative text for a story beat.
    Returns the generated text string, or a fallback if the API fails.
    """
    if context is None:
        context = {}

    beat = BEAT_DEFINITIONS.get(beat_key)
    if not beat:
        return None

    prompt = beat['prompt_fn'](actor, context)

    try:
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            return _fallback(beat_key, actor, context)

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model='claude-haiku-4-5',
            max_tokens=400,
            messages=[{'role': 'user', 'content': prompt}],
        )
        return message.content[0].text.strip()

    except Exception:
        return _fallback(beat_key, actor, context)


def _fallback(beat_key, actor, context):
    """
    Hardcoded fallback text if the API is unavailable.
    Keeps the game playable even without an API key.
    """
    city = INDUSTRY_CITY.get(actor.industry, 'Mumbai')
    fallbacks = {
        'arrival':           f"You arrive in {city} with nothing but a name and a reason. The city doesn't notice. It never does, at first.\n\nBut you're here. That already puts you ahead of everyone who stayed home.",
        'first_audition':    f"You hit submit and immediately want to take it back. That's how you know it mattered.\n\nNow you wait. The industry runs on waiting.",
        'first_role':        f"The contract is two pages. You read it four times. It's real.\n\nYou have a role. Everything before this was prologue.",
        'first_release':     f"Your name is on a poster in a cinema. Strangers will sit in the dark and watch you today.\n\nYou don't know how to feel about that yet. You just know you want to do it again.",
        'first_blockbuster': f"The numbers come in and for a moment you just sit with them. This is what it feels like.\n\nThe phone hasn't stopped. The industry has a short memory — but right now, it remembers you.",
        'first_flop':        f"The reviews are not kind. You read them anyway, every word.\n\nOne film doesn't end a career. You know this. You just need to remember it.",
        'first_controversy': f"You see the headline and the room gets very quiet very fast.\n\nThis is the part they don't prepare you for. How you handle the next 72 hours will say more about you than any performance.",
        'prestige_rank':     f"Something shifted and you felt it before you saw it. The way people look at you in a room. The calls you get now versus six months ago.\n\nYou earned this. That matters.",
        'first_invitation':  f"They came to you. No audition, no waiting — they called and asked.\n\nThis is different from everything before. This is what it means to be wanted.",
        'game_over':         f"You give it everything and sometimes that still isn't enough. {city} takes more than it gives.\n\nBut you were here. You were really here. Not everyone can say that.",
        'winner':            f"You made it all the way. From nothing to this.\n\nLegend is just a word until you live it. Now you know what it costs.",
    }
    return fallbacks.get(beat_key, "The story continues.")


# ─────────────────────────────────────────────────────
#  HELPER — check if a beat has already been triggered
# ─────────────────────────────────────────────────────

def beat_triggered(beat_key, actor_id, StoryBeat_model):
    return StoryBeat_model.query.filter_by(
        actor_id=actor_id, beat_key=beat_key
    ).first() is not None


def get_or_create_beat(beat_key, actor, context, db, StoryBeat_model):
    """
    Checks DB for existing beat. If found, returns it.
    If not, generates via AI, stores, and returns it.
    Returns a StoryBeat object.
    """
    existing = StoryBeat_model.query.filter_by(
        actor_id=actor.id, beat_key=beat_key
    ).first()
    if existing:
        return existing

    text = generate_beat(beat_key, actor, context)
    beat_def = BEAT_DEFINITIONS.get(beat_key, {})

    new_beat = StoryBeat_model(
        actor_id  = actor.id,
        beat_key  = beat_key,
        title     = beat_def.get('title', 'A Moment'),
        emoji     = beat_def.get('emoji', '🎬'),
        narrative = text,
        game_day  = actor.game_day,
    )
    db.session.add(new_beat)
    db.session.flush()  # get the ID without full commit
    return new_beat

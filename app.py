from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from job_board import generate_job_board, check_eligibility
from training import do_activity, do_rest, get_activities_with_status
from auditions import process_applications, accept_offer, decline_offer
from filming import process_filming, apply_effort, get_todays_event, apply_event_choice
from game_state import get_prestige, check_win, check_lose, get_career_stats
from events import maybe_trigger_controversy, resolve_controversy, CONTROVERSIES
from milestones  import check_and_award, get_milestone_context
from invitations import maybe_generate_invitation
import random
import os
from story import get_or_create_beat, beat_triggered, BEAT_DEFINITIONS

app = Flask(__name__)
database_url = os.environ.get('DATABASE_URL', 'sqlite:///game.db')
database_url = database_url.replace('postgres://', 'postgresql+pg8000://')
database_url = database_url.replace('postgresql://', 'postgresql+pg8000://')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'lca-game-secret-2024'
db = SQLAlchemy(app)


# ─────────────────────────────────────────────────────
#  DATABASE MODEL
# ─────────────────────────────────────────────────────

class Actor(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(80), nullable=False)
    industry        = db.Column(db.String(20))
    persona         = db.Column(db.String(30))
    funds           = db.Column(db.Integer, default=50000)
    energy          = db.Column(db.Integer, default=100)
    fame            = db.Column(db.Integer, default=5)
    game_day        = db.Column(db.Integer, default=1)
    acting_skill    = db.Column(db.Integer, default=10)
    screen_presence = db.Column(db.Integer, default=10)
    looks           = db.Column(db.Integer, default=10)
    dialogue        = db.Column(db.Integer, default=10)
    dancing         = db.Column(db.Integer, default=10)
    connections     = db.Column(db.Integer, default=0)
    fitness         = db.Column(db.Integer, default=10)
    resilience      = db.Column(db.Integer, default=10)
    credibility     = db.Column(db.Integer, default=80)
    is_tired        = db.Column(db.Boolean, default=False)
    tired_days_left = db.Column(db.Integer, default=0)

class JobApplication(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    actor_id     = db.Column(db.Integer, db.ForeignKey('actor.id'), nullable=False)
    movie_title  = db.Column(db.String(100))
    role_type    = db.Column(db.String(50))
    genre        = db.Column(db.String(30))
    salary       = db.Column(db.Integer)
    director     = db.Column(db.String(80))
    role_tier    = db.Column(db.String(2))
    shoot_days   = db.Column(db.Integer)
    status       = db.Column(db.String(20), default='applied')
    # status values: applied, invited, rejected, offered, declined

class Film(db.Model):
    id                  = db.Column(db.Integer, primary_key=True)
    actor_id            = db.Column(db.Integer, db.ForeignKey('actor.id'), nullable=False)
    application_id      = db.Column(db.Integer, db.ForeignKey('job_application.id'))

    # Film details (copied from the application when accepted)
    movie_title         = db.Column(db.String(100))
    role_type           = db.Column(db.String(50))
    role_tier           = db.Column(db.String(2))
    genre               = db.Column(db.String(30))
    director            = db.Column(db.String(80))
    director_stars      = db.Column(db.Integer, default=3)
    budget              = db.Column(db.String(10))
    salary              = db.Column(db.Integer, default=0)

    # Filming progress
    total_shoot_days    = db.Column(db.Integer, default=10)
    days_completed      = db.Column(db.Integer, default=0)

    # Status: filming / post_production / released
    status              = db.Column(db.String(20), default='filming')

    # Box office result (set when released)
    box_office_result   = db.Column(db.String(20))   # blockbuster/hit/average/flop/disaster
    box_office_score    = db.Column(db.Float)
    fame_change         = db.Column(db.Integer, default=0)
    release_day         = db.Column(db.Integer)       # game_day when released
    review              = db.Column(db.Text)

    quality_score   = db.Column(db.Integer, default=50)
    last_visit_day  = db.Column(db.Integer, default=0)


class Controversy(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    actor_id        = db.Column(db.Integer, db.ForeignKey('actor.id'), nullable=False)
    type            = db.Column(db.String(60))
    severity        = db.Column(db.String(20))    # 'Low', 'Medium', 'High'
    headline        = db.Column(db.String(200))
    narrative       = db.Column(db.Text)
    tabloid_quote   = db.Column(db.String(300))
    source_label    = db.Column(db.String(80))
    deadline_day    = db.Column(db.Integer)       # game_day by which to respond
    created_day     = db.Column(db.Integer)
    immediate_fame  = db.Column(db.Integer, default=0)
    credibility_hit = db.Column(db.Integer, default=10)
    resolved        = db.Column(db.Boolean, default=False)
    response_chosen = db.Column(db.String(20))    # 'apologise', 'deny', 'lean', 'pr'

class Milestone(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    actor_id   = db.Column(db.Integer, db.ForeignKey('actor.id'), nullable=False)
    key        = db.Column(db.String(60))        # e.g. 'first_blockbuster'
    earned     = db.Column(db.Boolean, default=False)
    earned_day = db.Column(db.Integer)

class Invitation(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    actor_id     = db.Column(db.Integer, db.ForeignKey('actor.id'), nullable=False)
    movie_title  = db.Column(db.String(100))
    role_type    = db.Column(db.String(50))
    role_tier    = db.Column(db.String(2))
    genre        = db.Column(db.String(30))
    director     = db.Column(db.String(80))
    director_stars = db.Column(db.Integer, default=4)
    budget       = db.Column(db.String(10))
    salary       = db.Column(db.Integer)
    shoot_days   = db.Column(db.Integer)
    invite_reason = db.Column(db.String(300))
    invite_type  = db.Column(db.String(30))      # 'direct' or 'fame_threshold'
    expires_day  = db.Column(db.Integer)
    created_day  = db.Column(db.Integer)
    is_active    = db.Column(db.Boolean, default=True)

class StoryBeat(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    actor_id  = db.Column(db.Integer, db.ForeignKey('actor.id'), nullable=False)
    beat_key  = db.Column(db.String(40))       # e.g. 'first_blockbuster'
    title     = db.Column(db.String(80))
    emoji     = db.Column(db.String(10))
    narrative = db.Column(db.Text)
    game_day  = db.Column(db.Integer)

# ─────────────────────────────────────────────────────
#  PERSONA STARTING STATS
# ─────────────────────────────────────────────────────

def get_starting_stats(persona):
    if persona == 'newcomer':
        return {
            'funds': 15000, 'fame': 0,
            'acting_skill': random.randint(15, 25),
            'screen_presence': random.randint(10, 20),
            'looks': random.randint(10, 30),
            'dialogue': random.randint(10, 20),
            'dancing': random.randint(5, 15),
            'connections': 0,
            'fitness': random.randint(10, 20),
            'resilience': random.randint(20, 35),
        }
    elif persona == 'nepo':
        return {
            'funds': 500000, 'fame': random.randint(1,10),
            'acting_skill': random.randint(0, 10),
            'screen_presence': random.randint(20, 30),
            'looks': random.randint(25, 40),
            'dialogue': random.randint(0, 10),
            'dancing': random.randint(0, 15),
            'connections': random.randint(25, 40),
            'fitness': random.randint(15, 25),
            'resilience': random.randint(5, 15),
        }
    elif persona == 'theatre':
        return {
            'funds': 100000, 'fame': random.randint(5, 10),
            'acting_skill': random.randint(30, 45),
            'screen_presence': random.randint(8, 18),
            'looks': random.randint(10, 25),
            'dialogue': random.randint(30, 45),
            'dancing': random.randint(5, 15),
            'connections': random.randint(5, 15),
            'fitness': random.randint(10, 20),
            'resilience': random.randint(20, 35),
        }
    elif persona == 'model':
        return {
            'funds': 300000, 'fame': random.randint(5, 10),
            'acting_skill': random.randint(5, 15),
            'screen_presence': random.randint(25, 38),
            'looks': random.randint(35, 55),
            'dialogue': random.randint(8, 18),
            'dancing': random.randint(15, 30),
            'connections': random.randint(15, 25),
            'fitness': random.randint(25, 40),
            'resilience': random.randint(10, 20),
        }
    else:  # background actor
        return {
            'funds': 30000, 'fame': random.randint(0, 5),
            'acting_skill': random.randint(10, 20),
            'screen_presence': random.randint(8, 18),
            'looks': random.randint(8, 25),
            'dialogue': random.randint(8, 18),
            'dancing': random.randint(5, 15),
            'connections': random.randint(10, 20),
            'fitness': random.randint(10, 20),
            'resilience': random.randint(25, 40),
        }

# Used by the filming template to display effort card details
EFFORT_OPTIONS = [
    {
        'key':         'minimum',
        'label':       'Minimum Effort',
        'emoji':       '😐',
        'energy_cost': 10,
        'quality':     '+1 to +4 quality',
        'acting':      'No skill gain',
        'note':        'Safe. Won\'t hurt the film but won\'t elevate it either.',
        'color':       'green',
    },
    {
        'key':         'standard',
        'label':       'Standard',
        'emoji':       '💪',
        'energy_cost': 20,
        'quality':     '+4 to +8 quality',
        'acting':      '+0 to +1 Acting Skill',
        'note':        'The professional default. Respect from the director.',
        'color':       'blue',
    },
    {
        'key':         'method',
        'label':       'Method Acting',
        'emoji':       '🔥',
        'energy_cost': 35,
        'quality':     '+8 to +14 quality',
        'acting':      '+3 to +5 Acting Skill',
        'note':        'Maximum quality gain. Burnout risk if energy is low.',
        'color':       'gold',
    },
]

# ─────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────

# Home page redirects straight to new game
@app.route('/')
def home():
    return redirect(url_for('new_game'))

# Show the New Game form (GET = just display the page)
@app.route('/new-game', methods=['GET'])
def new_game():
    return render_template('new_game.html')

# Handle form submission (POST = process the data)
@app.route('/create-actor', methods=['POST'])
def create_actor():
    name     = request.form.get('name')
    industry = request.form.get('industry')
    persona  = request.form.get('persona')

    stats = get_starting_stats(persona)

    actor = Actor(
        name=name,
        industry=industry,
        persona=persona,
        funds=stats['funds'],
        fame=stats['fame'],
        acting_skill=stats['acting_skill'],
        screen_presence=stats['screen_presence'],
        looks=stats['looks'],
        dialogue=stats['dialogue'],
        dancing=stats['dancing'],
        connections=stats['connections'],
        fitness=stats['fitness'],
        resilience=stats['resilience'],
    )

    db.session.add(actor)
    db.session.commit()


    beat = get_or_create_beat('arrival', actor, {}, db, StoryBeat)
    db.session.commit()
    return redirect(url_for('dashboard', actor_id=actor.id, story_beat_id=beat.id))

    return redirect(url_for('dashboard', actor_id=actor.id))

# Dashboard — loads actor from DB and passes to HTML
@app.route('/dashboard/<int:actor_id>')
def dashboard(actor_id):
    actor = db.get_or_404(Actor, actor_id)
    story_beat_id = request.args.get('story_beat_id', type=int)
    story_beat    = StoryBeat.query.get(story_beat_id) if story_beat_id else None

    offer_count = JobApplication.query.filter_by(
        actor_id=actor_id, status='offered'
    ).count()

    active_film_count = Film.query.filter(
        Film.actor_id == actor_id,
        Film.status.in_(['filming', 'post_production'])
    ).count()

    released_films   = Film.query.filter_by(actor_id=actor_id, status='released').all()
    all_applications = JobApplication.query.filter_by(actor_id=actor_id).all()

    prestige = get_prestige(actor, released_films)
    stats    = get_career_stats(actor, released_films, all_applications)

    active_controversy = Controversy.query.filter_by(
        actor_id=actor_id, resolved=False
    ).first()

    return render_template(
        'dashboard.html',
        actor=actor,
        offer_count=offer_count,
        active_film_count=active_film_count,
        prestige=prestige,
        stats=stats,
        story_beat=story_beat,
        active_controversy=active_controversy,
    )

# Job Board — generates listings and shows them
@app.route('/job-board/<int:actor_id>')
def job_board(actor_id):
    actor = Actor.query.get_or_404(actor_id)
    story_beat_id = request.args.get('story_beat_id', type=int)
    story_beat    = StoryBeat.query.get(story_beat_id) if story_beat_id else None

    # Generate fresh listings for the actor's industry
    listings = generate_job_board(actor.industry, count=10)

    # Check eligibility for each listing and attach the result
    for listing in listings:
        result = check_eligibility(actor, listing['requirements'])
        listing['eligible'] = result['eligible']
        listing['missing']  = result['missing']

    # Split into eligible and ineligible for the template
    eligible_listings   = [l for l in listings if l['eligible']]
    ineligible_listings = [l for l in listings if not l['eligible']]

    invite_count = Invitation.query.filter_by(
        actor_id=actor_id, is_active=True
    ).filter(Invitation.expires_day >= actor.game_day).count()

    return render_template(
        'job_board.html',
        actor=actor,
        eligible_listings=eligible_listings,
        invite_count=invite_count,
        story_beat=story_beat,
        ineligible_listings=ineligible_listings
    )

# Apply for a role — receives form data, saves application
@app.route('/apply/<int:actor_id>', methods=['POST'])
def apply_role(actor_id):
    actor = Actor.query.get_or_404(actor_id)

    # Read the hidden form fields sent from the job board page
    movie_title = request.form.get('movie_title')
    role_type   = request.form.get('role_type')
    genre       = request.form.get('genre')
    salary      = int(request.form.get('salary', 0))
    director    = request.form.get('director')
    role_tier   = request.form.get('role_tier')
    shoot_days  = int(request.form.get('shoot_days', 0))

    # Save the application to the database
    application = JobApplication(
        actor_id=actor_id,
        movie_title=movie_title,
        role_type=role_type,
        genre=genre,
        salary=salary,
        director=director,
        role_tier=role_tier,
        shoot_days=shoot_days,
        status='applied'
    )
    db.session.add(application)
    db.session.commit()

    story_beat_id = None
    if not beat_triggered('first_audition', actor_id, StoryBeat):
        beat = get_or_create_beat('first_audition', actor, {}, db, StoryBeat)
        db.session.commit()
        story_beat_id = beat.id

    flash(f'Application submitted for {role_type} in "{movie_title}". Check back in a few days!', 'success')
    return redirect(url_for('job_board', actor_id=actor_id, story_beat_id=story_beat_id))

    flash(f'Application submitted for {role_type} in "{movie_title}". Check back in a few days!', 'success')
    return redirect(url_for('job_board', actor_id=actor_id))

# Training page — shows all activities with availability status
@app.route('/training/<int:actor_id>')
def training(actor_id):
    actor      = db.get_or_404(Actor, actor_id)
    activities = get_activities_with_status(actor)
    
    invite_count = Invitation.query.filter_by(
        actor_id=actor_id, is_active=True
    ).filter(Invitation.expires_day >= actor.game_day).count()

    return render_template('training.html', actor=actor, invite_count=invite_count, activities=activities)

# Do an activity — POST from training page
@app.route('/do-activity/<int:actor_id>', methods=['POST'])
def do_activity_route(actor_id):
    actor        = db.get_or_404(Actor, actor_id)
    activity_key = request.form.get('activity_key')

    result = do_activity(actor, activity_key)

    if result['success']:
        db.session.commit()
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'error')

    return redirect(url_for('training', actor_id=actor_id))

# Rest — restores energy and advances the day
@app.route('/rest/<int:actor_id>', methods=['POST'])
def rest(actor_id):
    actor = db.get_or_404(Actor, actor_id)
    pending_story_beat_id = None

    # 1. Process pending job applications
    pending_apps = JobApplication.query.filter(
        JobApplication.actor_id == actor_id,
        JobApplication.status   == 'applied'
    ).all()
    if pending_apps:
        app_results = process_applications(actor, pending_apps)
        for r in app_results:
            cat = 'success' if r['category'] == 'good' else 'error' if r['category'] == 'bad' else 'info'
            flash(r['message'], cat)

    # 2. Advance active films
    active_films = Film.query.filter(
        Film.actor_id == actor_id,
        Film.status.in_(['filming', 'post_production'])
    ).all()
    
    released_film_id = None
    if active_films:
        film_results = process_filming(actor, active_films)
        for r in film_results:
            cat = 'success' if r['category'] == 'good' else 'error' if r['category'] == 'bad' else 'info'
            flash(r['message'], cat)
            # Capture the first film that released this End Day
            if r.get('released_film_id') and released_film_id is None:
                released_film_id = r['released_film_id']
                released_film    = Film.query.get(released_film_id)
                if released_film:
                    ctx = {
                        'movie_title': released_film.movie_title,
                        'result':      released_film.box_office_result,
                        'fame_change': released_film.fame_change,
                        'score':       released_film.box_office_score,
                    }
                    # First release ever
                    if not beat_triggered('first_release', actor_id, StoryBeat):
                        release_beat = get_or_create_beat('first_release', actor, ctx, db, StoryBeat)
                        pending_story_beat_id = release_beat.id
                    # First blockbuster
                    elif released_film.box_office_result == 'blockbuster' and not beat_triggered('first_blockbuster', actor_id, StoryBeat):
                        block_beat = get_or_create_beat('first_blockbuster', actor, ctx, db, StoryBeat)
                        pending_story_beat_id = block_beat.id
                    # First flop or disaster
                    elif released_film.box_office_result in ('flop', 'disaster') and not beat_triggered('first_flop', actor_id, StoryBeat):
                        flop_beat = get_or_create_beat('first_flop', actor, ctx, db, StoryBeat)
                        pending_story_beat_id = flop_beat.id

    old_prestige_label = get_prestige(actor, Film.query.filter_by(actor_id=actor_id, status='released').all()).get('label')

    # 3. Advance the day and restore energy
    rest_result = do_rest(actor)

    # Count down the tired debuff
    if actor.is_tired:
        actor.tired_days_left -= 1
        if actor.tired_days_left <= 0:
            actor.is_tired        = False
            actor.tired_days_left = 0
            flash('✅ You\'ve recovered from exhaustion. Training gains back to normal.', 'success')
    
    # Maybe trigger a controversy (only if no active one exists)
    existing_controversy = Controversy.query.filter_by(
        actor_id=actor_id, resolved=False
    ).first()
    if not existing_controversy:
        controversy_template = maybe_trigger_controversy(actor)
        if controversy_template:
            new_c = Controversy(
                actor_id        = actor_id,
                type            = controversy_template['type'],
                severity        = controversy_template['severity'],
                headline        = controversy_template['headline'],
                narrative       = controversy_template['narrative'],
                tabloid_quote   = controversy_template['tabloid_quote'],
                source_label    = controversy_template['source_label'],
                deadline_day    = actor.game_day + 3,
                created_day     = actor.game_day,
                immediate_fame  = controversy_template['immediate_fame'],
                credibility_hit = controversy_template['credibility_hit'],
                resolved        = False,
            )
            # Apply immediate effects
            actor.fame        = max(0, min(100, actor.fame        + controversy_template['immediate_fame']))
            actor.credibility = max(0, actor.credibility - controversy_template['credibility_hit'])
            db.session.add(new_c)
            flash('🚨 A controversy has broken out. Check your Dashboard to handle it.', 'error')

            if not beat_triggered('first_controversy', actor_id, StoryBeat):
                        ctx = {
                            'headline': controversy_template['headline'],
                            'type':     controversy_template['type'],
                        }
                        c_beat = get_or_create_beat('first_controversy', actor, ctx, db, StoryBeat)
                        pending_story_beat_id = c_beat.id

        # Check and award milestones
    released_films_for_stats = Film.query.filter_by(actor_id=actor_id, status='released').all()
    all_apps_for_stats       = JobApplication.query.filter_by(actor_id=actor_id).all()
    career_stats             = get_career_stats(actor, released_films_for_stats, all_apps_for_stats)
    new_awards = check_and_award(actor, career_stats, db, Milestone)
    for award_name in new_awards:
        flash(f'🏆 Achievement Unlocked: {award_name}!', 'success')

    # Maybe generate an exclusive invitation
    new_invitation = maybe_generate_invitation(actor, db, Invitation)
    if new_invitation:
        db.session.add(new_invitation)
        flash('✦ A private invitation has arrived. Check Invitations.', 'success')
        if not beat_triggered('first_invitation', actor_id, StoryBeat):
            inv_ctx = {
                'movie_title': new_invitation.movie_title,
                'director':    new_invitation.director,
                'role_type':   new_invitation.role_type,
            }
            inv_beat = get_or_create_beat('first_invitation', actor, inv_ctx, db, StoryBeat)
            pending_story_beat_id = inv_beat.id

    new_prestige = get_prestige(actor, Film.query.filter_by(actor_id=actor_id, status='released').all())
    if new_prestige.get('label') != old_prestige_label:
        prestige_beat_key = f"prestige_{new_prestige.get('label','').lower().replace(' ','_')}"
        if not beat_triggered(prestige_beat_key, actor_id, StoryBeat):
            p_beat = get_or_create_beat('prestige_rank', actor,
                {'rank_label': new_prestige.get('label')}, db, StoryBeat)
            p_beat.beat_key = prestige_beat_key  # unique key per rank
            pending_story_beat_id = p_beat.id

    db.session.commit()
    flash(rest_result['message'], 'success')

    # 4. Check lose condition
    remaining_active = Film.query.filter(
        Film.actor_id == actor_id,
        Film.status.in_(['filming', 'post_production'])
    ).all()
    if check_lose(actor, remaining_active):
        return redirect(url_for('game_over', actor_id=actor_id))

    # 5. Check win condition
    released = Film.query.filter_by(actor_id=actor_id, status='released').all()
    if check_win(actor, released):
        return redirect(url_for('winner', actor_id=actor_id))

    # If a film released today, go to the reveal screen instead of inbox
    if released_film_id:
        return redirect(url_for('box_office_reveal', actor_id=actor_id, film_id=released_film_id))

    return redirect(url_for('applications', actor_id=actor_id,
                            story_beat_id=pending_story_beat_id))

# Applications inbox
@app.route('/applications/<int:actor_id>')
def applications(actor_id):
    actor = db.get_or_404(Actor, actor_id)
    story_beat_id = request.args.get('story_beat_id', type=int)
    story_beat    = StoryBeat.query.get(story_beat_id) if story_beat_id else None

    # Offers are shown prominently at the top
    offers = JobApplication.query.filter_by(
        actor_id=actor_id, status='offered'
    ).all()

    # Full history in reverse order (newest first)
    all_applications = JobApplication.query.filter_by(
        actor_id=actor_id
    ).order_by(JobApplication.id.desc()).all()

    invite_count = Invitation.query.filter_by(
        actor_id=actor_id, is_active=True
    ).filter(Invitation.expires_day >= actor.game_day).count()

    return render_template(
        'applications.html',
        actor=actor,
        offers=offers,
        invite_count=invite_count,
        story_beat=story_beat,
        all_applications=all_applications
    )

# Accept a role offer
@app.route('/accept/<int:actor_id>/<int:app_id>', methods=['POST'])
def accept(actor_id, app_id):
    actor       = db.get_or_404(Actor, actor_id)
    application = db.get_or_404(JobApplication, app_id)
    result      = accept_offer(actor, application)

    # Create a Film record for this accepted role
    film = Film(
        actor_id       = actor_id,
        application_id = app_id,
        movie_title    = application.movie_title,
        role_type      = application.role_type,
        role_tier      = application.role_tier,
        genre          = application.genre,
        director       = application.director,
        director_stars = 3,         # default — we'll improve this in a future phase
        budget         = 'Mid',     # default — same reason
        salary         = application.salary,
        total_shoot_days = application.shoot_days,
        days_completed = 0,
        status         = 'filming',
    )
    db.session.add(film)
    db.session.commit()

    story_beat_id = None
    if not beat_triggered('first_role', actor_id, StoryBeat):
        context = {
            'role_type':   application.role_type,
            'movie_title': application.movie_title,
            'director':    application.director,
            'salary':      application.salary,
        }
        beat = get_or_create_beat('first_role', actor, context, db, StoryBeat)
        db.session.commit()
        story_beat_id = beat.id

    return redirect(url_for('applications', actor_id=actor_id, story_beat_id=story_beat_id))


    flash(result['message'], 'success')
    flash(f'🎬 You are now filming "{application.movie_title}"! It will release after {application.shoot_days} shoot days.', 'info')
    return redirect(url_for('applications', actor_id=actor_id))

# Decline a role offer
@app.route('/decline/<int:actor_id>/<int:app_id>', methods=['POST'])
def decline(actor_id, app_id):
    actor       = db.get_or_404(Actor, actor_id)
    application = db.get_or_404(JobApplication, app_id)
    result      = decline_offer(actor, application)
    db.session.commit()
    flash(result['message'], 'info')
    return redirect(url_for('applications', actor_id=actor_id))

# Filmography page
@app.route('/films/<int:actor_id>')
def films(actor_id):
    actor = db.get_or_404(Actor, actor_id)

    active_films = Film.query.filter(
        Film.actor_id == actor_id,
        Film.status.in_(['filming', 'post_production'])
    ).all()

    released_films = Film.query.filter_by(
        actor_id=actor_id, status='released'
    ).order_by(Film.release_day.desc()).all()

    return render_template(
        'films.html',
        actor=actor,
        active_films=active_films,
        released_films=released_films
    )

# ── Filming set screen — shows effort options for a specific active film ──
@app.route('/filming/<int:actor_id>/<int:film_id>')
def filming_set(actor_id, film_id):
    actor = db.get_or_404(Actor, actor_id)
    film  = db.get_or_404(Film, film_id)

    offer_count = JobApplication.query.filter_by(
        actor_id=actor_id, status='offered'
    ).count()

    invite_count = Invitation.query.filter_by(
        actor_id=actor_id, is_active=True
    ).filter(Invitation.expires_day >= actor.game_day).count()

    already_visited = (film.last_visit_day == actor.game_day)
    on_set_event    = None if already_visited else get_todays_event()

    released_films = Film.query.filter_by(actor_id=actor_id, status='released').all()
    prestige = get_prestige(actor, released_films)

    return render_template(
        'filming.html',
        actor=actor,
        film=film,
        prestige=prestige,
        offer_count=offer_count,
        invite_count=invite_count,
        already_visited=already_visited,
        on_set_event=on_set_event,
        effort_options=EFFORT_OPTIONS,
        auto_quality_cap=60,
    )


# ── Submit effort choice for the day ──
@app.route('/filming/<int:actor_id>/<int:film_id>/work', methods=['POST'])
def filming_work(actor_id, film_id):
    actor  = db.get_or_404(Actor, actor_id)
    film   = db.get_or_404(Film, film_id)

    if film.last_visit_day == actor.game_day:
        flash('You\'ve already visited the set today. End the day to visit again.', 'info')
        return redirect(url_for('filming_set', actor_id=actor_id, film_id=film_id))

    effort = request.form.get('effort', 'standard')
    result = apply_effort(actor, film, effort)
    db.session.commit()

    flash(result['message'], 'success')
    if result['acting_gain']:
        flash(f'+{result["acting_gain"]} Acting Skill from method work.', 'success')
    if result['burned_out']:
        flash('⚠️ You pushed past your limit. Burnout debuff active for 3 days: -20% training gains.', 'error')

    return redirect(url_for('filming_set', actor_id=actor_id, film_id=film_id))


# ── Resolve an on-set event choice ──
@app.route('/filming/<int:actor_id>/<int:film_id>/event/<event_id>/choice/<choice_id>')
def filming_event_choice(actor_id, film_id, event_id, choice_id):
    actor = db.get_or_404(Actor, actor_id)
    film  = db.get_or_404(Film, film_id)
    msg   = apply_event_choice(actor, film, event_id, choice_id)
    db.session.commit()
    flash(msg, 'info')
    return redirect(url_for('filming_set', actor_id=actor_id, film_id=film_id))

# ── Box office reveal — shows the cinematic result screen ──
@app.route('/box-office/<int:actor_id>/<int:film_id>')
def box_office_reveal(actor_id, film_id):
    actor = db.get_or_404(Actor, actor_id)
    film  = db.get_or_404(Film, film_id)
    story_beat_id = request.args.get('story_beat_id', type=int)
    story_beat    = StoryBeat.query.get(story_beat_id) if story_beat_id else None

    offer_count = JobApplication.query.filter_by(
        actor_id=actor_id, status='offered'
    ).count()

    invite_count = Invitation.query.filter_by(
        actor_id=actor_id, is_active=True
    ).filter(Invitation.expires_day >= actor.game_day).count()

    released_films = Film.query.filter_by(actor_id=actor_id, status='released').all()
    prestige       = get_prestige(actor, released_films)

    # Determine result colours/theming for the template
    result_theme = {
        'blockbuster': {'color': 'gold',  'emoji': '🏆'},
        'hit':         {'color': 'green', 'emoji': '✅'},
        'average':     {'color': 'blue',  'emoji': '📊'},
        'flop':        {'color': 'red',   'emoji': '📉'},
        'disaster':    {'color': 'red',   'emoji': '💀'},
    }.get(film.box_office_result, {'color': 'gold', 'emoji': '🎬'})

    return render_template(
        'box_office.html',
        actor=actor,
        film=film,
        prestige=prestige,
        offer_count=offer_count,
        invite_count=invite_count,
        story_beat=story_beat,
        result_theme=result_theme,
    )

# ── View active controversy ──
@app.route('/controversy/<int:actor_id>/<int:controversy_id>')
def controversy_view(actor_id, controversy_id):
    actor       = db.get_or_404(Actor, actor_id)
    controversy = db.get_or_404(Controversy, controversy_id)

    offer_count  = JobApplication.query.filter_by(actor_id=actor_id, status='offered').count()
    invite_count = Invitation.query.filter_by(actor_id=actor_id, is_active=True).filter(
        Invitation.expires_day >= actor.game_day
    ).count()

    # Merge template data (response costs, recovery times, precedents) from the library
    template = next((c for c in CONTROVERSIES if c['type'] == controversy.type), CONTROVERSIES[0])

    released_films = Film.query.filter_by(actor_id=actor_id, status='released').all()
    prestige = get_prestige(actor, released_films)

    return render_template(
        'controversy.html',
        actor=actor,
        controversy=controversy,
        template=template,
        prestige=prestige,
        offer_count=offer_count,
        invite_count=invite_count,
    )


# ── Submit controversy response ──

@app.route('/controversy/<int:actor_id>/<int:controversy_id>/respond', methods=['POST'])
def controversy_respond(actor_id, controversy_id):
    actor       = db.get_or_404(Actor, actor_id)
    controversy = db.get_or_404(Controversy, controversy_id)
    response    = request.form.get('response')

    # Block PR if actor can't afford it
    if response == 'pr':
        from events import CONTROVERSIES
        template = next((c for c in CONTROVERSIES if c['type'] == controversy.type), None)
        cost = template['responses']['pr'].get('cost', 0) if template else 0
        if actor.funds < cost:
            flash(f'❌ You can\'t afford the PR team. You need ₹{cost:,} but only have ₹{actor.funds:,}.', 'error')
            return redirect(url_for('controversy_view', actor_id=actor_id, controversy_id=controversy_id))

    msg = resolve_controversy(controversy, actor, response)
    db.session.commit()
    flash(msg, 'success')
    return redirect(url_for('dashboard', actor_id=actor_id))

# ── Trophy Wall ──
@app.route('/milestones/<int:actor_id>')
def milestones_view(actor_id):
    actor = db.get_or_404(Actor, actor_id)

    offer_count  = JobApplication.query.filter_by(actor_id=actor_id, status='offered').count()
    invite_count = Invitation.query.filter_by(actor_id=actor_id, is_active=True).filter(
        Invitation.expires_day >= actor.game_day
    ).count()

    released_films = Film.query.filter_by(actor_id=actor_id, status='released').all()
    prestige = get_prestige(actor, released_films)

    context = get_milestone_context(actor_id, Milestone)

    return render_template(
        'milestones.html',
        actor=actor,
        prestige=prestige,
        offer_count=offer_count,
        invite_count=invite_count,
        **context,
    )


# ── Invitations panel ──
@app.route('/invitations/<int:actor_id>')
def invitations_view(actor_id):
    actor = db.get_or_404(Actor, actor_id)

    # Expire any invitations whose deadline has passed
    expired = Invitation.query.filter_by(
        actor_id=actor_id, is_active=True
    ).filter(Invitation.expires_day < actor.game_day).all()
    for inv in expired:
        inv.is_active = False
    if expired:
        db.session.commit()

    active_invitations = Invitation.query.filter_by(
        actor_id=actor_id, is_active=True
    ).order_by(Invitation.created_day.desc()).all()

    offer_count  = JobApplication.query.filter_by(actor_id=actor_id, status='offered').count()
    released_films = Film.query.filter_by(actor_id=actor_id, status='released').all()
    prestige = get_prestige(actor, released_films)

    return render_template(
        'invitations.html',
        actor=actor,
        prestige=prestige,
        offer_count=offer_count,
        invite_count=len(active_invitations),
        invitations=active_invitations,
    )


# ── Accept an invitation ──
@app.route('/invitations/<int:actor_id>/<int:inv_id>/accept', methods=['POST'])
def invitation_accept(actor_id, inv_id):
    actor = db.get_or_404(Actor, actor_id)
    inv   = db.get_or_404(Invitation, inv_id)

    # Create a Film record (same as normal offer acceptance)
    film = Film(
        actor_id         = actor_id,
        application_id   = None,
        movie_title      = inv.movie_title,
        role_type        = inv.role_type,
        role_tier        = inv.role_tier,
        genre            = inv.genre,
        director         = inv.director,
        director_stars   = inv.director_stars,
        budget           = inv.budget,
        salary           = inv.salary,
        total_shoot_days = inv.shoot_days,
        days_completed   = 0,
        status           = 'filming',
    )
    db.session.add(film)

    # Pay the full salary (same as accept_offer in auditions.py)
    actor.funds  += inv.salary
    fame_gain     = random.randint(12, 22) if inv.role_tier == 'A' else random.randint(6, 12)
    actor.fame    = min(100, actor.fame + fame_gain)

    inv.is_active = False
    db.session.commit()

    flash(f'✅ You accepted the invitation for {inv.movie_title}! Rs.{inv.salary:,} paid. +{fame_gain} Fame. Filming begins.', 'success')
    return redirect(url_for('dashboard', actor_id=actor_id))


# ── Decline an invitation ──
@app.route('/invitations/<int:actor_id>/<int:inv_id>/decline', methods=['POST'])
def invitation_decline(actor_id, inv_id):
    inv = db.get_or_404(Invitation, inv_id)
    inv.is_active = False
    db.session.commit()
    flash('Invitation declined. They may not offer again.', 'info')
    return redirect(url_for('invitations_view', actor_id=inv.actor_id))

# Game Over screen
@app.route('/game-over/<int:actor_id>')
def game_over(actor_id):
    actor = db.get_or_404(Actor, actor_id)
    released_films  = Film.query.filter_by(actor_id=actor_id, status='released').all()
    all_applications = JobApplication.query.filter_by(actor_id=actor_id).all()
    prestige = get_prestige(actor, released_films)
    stats    = get_career_stats(actor, released_films, all_applications)
    story_beat = None
    if not beat_triggered('game_over', actor_id, StoryBeat):
        ctx = {
            'total_films': stats.get('total_films', 0),
        }
        story_beat = get_or_create_beat('game_over', actor, ctx, db, StoryBeat)
        db.session.commit()

    return render_template('game_over.html', actor=actor, prestige=prestige,
                           stats=stats, story_beat=story_beat)
    return render_template('game_over.html', actor=actor, prestige=prestige, stats=stats)

# Winner screen
@app.route('/winner/<int:actor_id>')
def winner(actor_id):
    actor = db.get_or_404(Actor, actor_id)
    released_films   = Film.query.filter_by(actor_id=actor_id, status='released').all()
    all_applications = JobApplication.query.filter_by(actor_id=actor_id).all()
    stats = get_career_stats(actor, released_films, all_applications)
    story_beat = None
    if not beat_triggered('winner', actor_id, StoryBeat):
        ctx = {
            'total_films':  stats.get('total_films', 0),
            'blockbusters': stats.get('blockbusters', 0),
        }
        story_beat = get_or_create_beat('winner', actor, ctx, db, StoryBeat)
        db.session.commit()

    return render_template('winner.html', actor=actor, stats=stats,
                           story_beat=story_beat)
    return render_template('winner.html', actor=actor, stats=stats)

# ─────────────────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
from traceback import print_exception
import os, requests, datetime, json, sys

from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from forms import UserAddForm, LoginForm, UserUpdateForm, CompleteQuest
from models import db, connect_db, User, Quest
from random_quest import fetch_quest
from werkzeug.middleware.proxy_fix import ProxyFix

import data_url

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# App is behind one proxy that sets the -For and -Host headers.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///seren'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4MB max-limit.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")

#toolbar = DebugToolbarExtension(app)


with app.app_context():
    connect_db(app)


@app.context_processor
def handle_context():
    '''Inject object into jinja2 templates.'''
    return dict(json=json)

##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    if CURR_USER_KEY in session:
        session.pop(CURR_USER_KEY)
        flash(f"Goodbye, {g.user.username}!", "danger")
        g.user = None
        
    
    return redirect('/')


##############################################################################
# General user routes:

@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    quests = (Quest
                .query
                .filter(Quest.user_id == user_id)
                .order_by(Quest.timestamp.desc())
                .all())
    return render_template('users/show.html', user=user, quests=quests)


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = UserUpdateForm()

    if form.validate_on_submit():
        user = User.authenticate(g.user.username, form.password.data)
        if not user:
            flash("Incorrect Password", "danger")
            return redirect('/users/profile')
        
        username = form.username.data
        email = form.email.data
        image_url = data_url.construct_data_url(mime_type='image/png', base64_encode=True, data=form.image.data.read())

        if g.user.username != username and len(User.query.filter(User.username == username).all()) > 0:
            flash("Username already Taken", "danger")
            return redirect('/users/profile')
        if g.user.email != email and len(User.query.filter(User.email == email).all()) > 0:
            flash("Email already Taken", "danger")
            return redirect('/users/profile')
        
        user.username = username
        user.email = email
        user.image_url = image_url

        db.session.commit()
        
        return redirect("/")
    else:
        form.username.data = g.user.username
        form.email.data = g.user.email

    return render_template('users/update.html', form=form)


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Quest Routes

@app.route('/quest/new', methods=['GET','POST'])
def new_quest():
    """Generate a new quest based on user's IP"""
    
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    try:
        quest = fetch_quest(request.access_route[0])
        qst = Quest(
            name=quest["name"], 
            address=" ".join(quest['location']['display_address']), 
            image=quest['image_url'], 
            points=quest['points'],
            timestamp=datetime.datetime.now(datetime.timezone.utc))
    except Exception as e:
        flash("ERROR fetching Quest Try Again")
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print_exception(exc_obj)
        return redirect("/")
        
    g.user.quests.append(qst)
    db.session.commit()
    g.user.last_quest = qst.timestamp
    db.session.commit()

    return render_template('new-quest.html', quest = qst)
    


@app.route('/quest/<int:quest_id>', methods=['GET','POST'])
def complete_quest(quest_id):
    """Show form to complete quest or submit form to complete quest"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = CompleteQuest()
    quest = Quest.query.get_or_404(quest_id)

    if form.validate_on_submit():
        
        image = form.image.data.read()
        reflection = form.reflection.data

        quest.complete_image = data_url.construct_data_url(mime_type='image/png', base64_encode=True, data=image)

        quest.reflection = reflection

        quest.status = "Complete"
        
        g.user.score += quest.points

        db.session.commit()
        
        return redirect("/")

    return render_template('complete-quest.html', form = form, quest = quest)

##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: login and signup
    - logged in: active and completed Quests page, check active Quests for expiration
    """

    if g.user:

        active_quests = (Quest
                .query
                .filter(Quest.user_id == g.user.id, Quest.status == "In-progress")
                .order_by(Quest.timestamp.asc())
                .all())
        
        for quest in active_quests:
            if (datetime.datetime.now(datetime.timezone.utc) - 
                quest.timestamp.replace(tzinfo=datetime.timezone.utc)).days >= 2:

                quest.status = "Expired"
        
        db.session.commit()

        quests = (Quest
                .query
                .filter(Quest.user_id == g.user.id)
                .order_by(Quest.timestamp.desc())
                .all())
        
        return render_template('home.html', quests=quests)

    else:

        return render_template('home-anon.html')



from flask import Blueprint, render_template, request, url_for, redirect, flash, session, g
# from flask_session import Session
from .models import Usuario
from werkzeug.security import generate_password_hash, check_password_hash
from mrp import db

bp = Blueprint('auth',__name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nombre = request.form['nombre']

        user = Usuario(username=username, password=generate_password_hash(password), nombre=nombre)

        user_name = Usuario.query.filter_by(username=username).first()

        error = None

        if user_name == None:
            db.session.add(user)
            db.session.commit()

            return redirect(url_for('auth.login'))
        else:
            error = f'User with that username {username} already exists.'

        flash(error)
    return render_template('auth/register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']


        error = None

        user = Usuario.query.filter_by(username=username).first()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'

        # iniciar sesión
        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('index'))

        flash(error)
    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = Usuario.query.get_or_404(user_id)
        #return redirect(url_for('auth.login'))

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

import functools
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view
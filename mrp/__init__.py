from flask import Flask, request, render_template, session, url_for, redirect
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def page_not_found(e):
  return render_template('error/404.html'), 404

def create_app():
    app = Flask(__name__)

    app.config.from_mapping(
        DEBUG=True,
        SECRET_KEY='8fdf56a9-340e-4850-a60d-f6015b459efb',
        SQLALCHEMY_DATABASE_URI = 'sqlite:///productos.db'
    )
    db.init_app(app)

    app.register_error_handler(404, page_not_found)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import tipo_unidad
    app.register_blueprint(tipo_unidad.bp)

    from . import unidad
    app.register_blueprint(unidad.bp)

    from . import categoria_producto
    app.register_blueprint(categoria_producto.bp)

    from . import producto
    app.register_blueprint(producto.bp)

    from . import proveedor
    app.register_blueprint(proveedor.bp)

    from . import lugar
    app.register_blueprint(lugar.bp)

    from . import bodega
    app.register_blueprint(bodega.bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    with app.app_context():
        db.create_all()

    return app
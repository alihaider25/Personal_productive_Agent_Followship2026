from flask import Flask
from config import Config
from models.db_models import db
from routes.logs_routes import logs_bp
from routes.tasks_routes import tasks_bp
from routes.plans_routes import plans_bp
def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()

    import tools

    from routes.agent_routes import agent_bp
    from routes.approval_routes import approval_bp
    app.register_blueprint(agent_bp)
    app.register_blueprint(approval_bp)
    app.register_blueprint(logs_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(plans_bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
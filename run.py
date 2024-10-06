from unwrap import app, db  # Import the app and db instance
from unwrap.models import User  # Import your User model if needed

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create all tables in the new database
    app.run(debug=True)

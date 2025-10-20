from app import create_app

# This is the entry point for the application.
# It creates the Flask app instance using the function from our app package.
app = create_app()

if __name__ == '__main__':
    # This condition ensures that the app runs only when this script is executed directly.
    # 'debug=True' allows for hot-reloading when you save changes.
    app.run(debug=True)
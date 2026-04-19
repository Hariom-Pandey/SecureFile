import os

from project.main import create_app


if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', '5000'))

    app = create_app()
    print("\n=== Secure File Management System ===")
    print(f"Server running at http://{host}:{port}")
    app.run(debug=False, host=host, port=port)

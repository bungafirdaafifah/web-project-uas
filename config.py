import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Flask Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret_key_kas_mahasiswa_12345')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'kas_management.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Configurations
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Limit uploads to 5MB
    
    # Ensure upload directories exist
    @staticmethod
    def init_app(app):
        profile_upload_dir = os.path.join(Config.UPLOAD_FOLDER, 'profile')
        logo_upload_dir = os.path.join(Config.UPLOAD_FOLDER)
        
        os.makedirs(profile_upload_dir, exist_ok=True)
        os.makedirs(logo_upload_dir, exist_ok=True)

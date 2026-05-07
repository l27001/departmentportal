from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
jwt = JWTManager()


def allowed_file(filename, config=None):
    if config is None:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config['ALLOWED_EXTENSIONS']


def allowed_image_file(filename, config=None):
    if config is None:
        return False
    image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'tiff'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in image_extensions
from extensions import db
from datetime import datetime

class GalleryAlbum(db.Model):
    __tablename__ = "gallery_albums"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    photos = db.relationship("GalleryPhoto", backref="album", lazy="dynamic", cascade="all, delete-orphan", order_by="GalleryPhoto.sort_order")

    def photo_count(self):
        return self.photos.count()


class GalleryPhoto(db.Model):
    __tablename__ = "gallery_photos"

    id = db.Column(db.Integer, primary_key=True)
    album_id = db.Column(db.Integer, db.ForeignKey("gallery_albums.id"), nullable=False)
    image = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(500))
    sort_order = db.Column(db.Integer, default=0)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

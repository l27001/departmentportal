import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from extensions import db
from models.user import User
from models.about import GalleryAlbum, GalleryPhoto
from datetime import datetime

about_bp = Blueprint("about", __name__, url_prefix="/about")


def allowed_image(filename):
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    return ext in {"png", "jpg", "jpeg", "gif", "webp"}


def save_image(file):
    upload_dir = os.path.join(current_app.root_path, "static", "uploads", "gallery")
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    name, ext = os.path.splitext(filename)
    unique = f"{name}_{timestamp}{ext}"
    file.save(os.path.join(upload_dir, unique))
    return unique


# ─── Главная ───
@about_bp.route("/")
def index():
    return redirect(url_for("about.employees"))


# ─── Сотрудники (из users, только не уволенные) ───
@about_bp.route("/employees")
def employees():
    all_employees = User.query.filter(User.dismissal_date.is_(None)).order_by(User.name).all()
    return render_template("about/about.html", active_tab="employees", employees=all_employees)


# ─── Редактировать день рождения ───
@about_bp.route("/employees/<int:user_id>/edit_birthday", methods=["POST"])
def edit_birthday(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("Сотрудник не найден", "danger")
        return redirect(url_for("about.employees"))
    birthday = request.form.get("birthday")
    user.birthday = datetime.strptime(birthday, "%Y-%m-%d").date() if birthday else None
    db.session.commit()
    flash("День рождения обновлён", "success")
    return redirect(url_for("about.employees"))


# ─── Галерея ───
@about_bp.route("/gallery")
def gallery():
    albums = GalleryAlbum.query.order_by(GalleryAlbum.sort_order, GalleryAlbum.name).all()
    return render_template("about/about.html", active_tab="gallery", albums=albums)


@about_bp.route("/gallery/album/<int:album_id>")
def view_album(album_id):
    album = db.session.get(GalleryAlbum, album_id)
    if not album:
        flash("Альбом не найден", "danger")
        return redirect(url_for("about.gallery"))
    photos = album.photos.order_by(GalleryPhoto.sort_order).all()
    albums = GalleryAlbum.query.order_by(GalleryAlbum.sort_order, GalleryAlbum.name).all()
    return render_template("about/about.html", active_tab="gallery", albums=albums, current_album=album, photos=photos)


@about_bp.route("/gallery/album/add", methods=["POST"])
def add_album():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Название альбома обязательно", "danger")
        return redirect(url_for("about.gallery"))
    album = GalleryAlbum(name=name, description=request.form.get("description"))
    db.session.add(album)
    db.session.commit()
    flash("Альбом создан", "success")
    return redirect(url_for("about.gallery"))


@about_bp.route("/gallery/album/<int:album_id>/edit", methods=["POST"])
def edit_album(album_id):
    album = db.session.get(GalleryAlbum, album_id)
    if not album:
        flash("Альбом не найден", "danger")
        return redirect(url_for("about.gallery"))
    album.name = request.form.get("name", album.name).strip()
    album.description = request.form.get("description")
    db.session.commit()
    flash("Альбом обновлён", "success")
    return redirect(url_for("about.gallery"))


@about_bp.route("/gallery/album/<int:album_id>/delete", methods=["POST"])
def delete_album(album_id):
    album = db.session.get(GalleryAlbum, album_id)
    if album:
        db.session.delete(album)
        db.session.commit()
        flash("Альбом удалён", "success")
    return redirect(url_for("about.gallery"))


@about_bp.route("/gallery/album/<int:album_id>/upload", methods=["POST"])
def upload_photos(album_id):
    album = db.session.get(GalleryAlbum, album_id)
    if not album:
        flash("Альбом не найден", "danger")
        return redirect(url_for("about.gallery"))

    files = request.files.getlist("photos")
    count = 0
    for file in files:
        if file and file.filename and allowed_image(file.filename):
            filename = save_image(file)
            photo = GalleryPhoto(album_id=album.id, image=filename, caption=request.form.get("caption", ""))
            db.session.add(photo)
            count += 1

    if count:
        db.session.commit()
        flash(f"Загружено {count} фото", "success")
    else:
        flash("Нет файлов для загрузки", "warning")
    return redirect(url_for("about.view_album", album_id=album.id))


@about_bp.route("/gallery/photo/<int:photo_id>/download")
def download_photo(photo_id):
    from flask import send_from_directory
    photo = db.session.get(GalleryPhoto, photo_id)
    if not photo:
        flash("Фото не найдено", "danger")
        return redirect(url_for("about.gallery"))
    return send_from_directory(
        os.path.join(current_app.root_path, "static", "uploads", "gallery"),
        photo.image,
        as_attachment=True,
        download_name=photo.image
    )


@about_bp.route("/gallery/photo/<int:photo_id>/delete", methods=["POST"])
def delete_photo(photo_id):
    photo = db.session.get(GalleryPhoto, photo_id)
    if photo:
        album_id = photo.album_id
        filepath = os.path.join(current_app.root_path, "static", "uploads", "gallery", photo.image)
        if os.path.exists(filepath):
            os.remove(filepath)
        db.session.delete(photo)
        db.session.commit()
        flash("Фото удалено", "success")
        return redirect(url_for("about.view_album", album_id=album_id))
    return redirect(url_for("about.gallery"))

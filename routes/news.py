import os
import uuid
from flask import Blueprint, request, render_template, flash, redirect, url_for, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from extensions import db, allowed_image_file
from models.news import News
from models.attachment import Attachment
from models.role import Role

news_bp = Blueprint("web_news", __name__, url_prefix="/news")


@news_bp.route("/", methods=["GET"])
@jwt_required()
def list_news():
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    page = request.args.get("page", 1, type=int)
    per_page = 10
    pagination = News.query.filter_by(is_deleted=False).order_by(News.is_pinned.desc(), News.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("news/list.html", news=pagination.items, page=page, total=pagination.total, per_page=per_page, total_pages=pagination.pages, role=role)


@news_bp.route("/create", methods=["GET", "POST"])
@jwt_required()
def create_news():
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    if role.name not in ("Руководитель", "Документовед", "Ответственный"):
        flash("Доступ запрещён", "danger")
        return redirect(url_for("web_news.list_news"))

    if request.method == "POST":
        title = request.form.get("title")
        text = request.form.get("text")
        is_pinned = request.form.get("is_pinned") == "on"
        files = request.files.getlist("files")

        if not title or not text:
            flash("Заполните заголовок и текст", "danger")
            return render_template("news/create.html", role=role)

        for f in files:
            if f.filename and not allowed_image_file(f.filename, current_app.config):
                flash(f"Недопустимый формат файла: {f.filename}", "danger")
                return render_template("news/create.html", role=role)

        news = News(title=title, text=text, is_pinned=is_pinned)
        db.session.add(news)
        db.session.flush()

        if files:
            upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "attachments", "news", str(news.id))
            os.makedirs(upload_dir, exist_ok=True)

            for f in files:
                if f.filename:
                    original_name = f.filename
                    ext = os.path.splitext(original_name)[1].lower()
                    safe_name = str(uuid.uuid4()) + ext
                    save_path = os.path.join(upload_dir, safe_name)
                    f.save(save_path)
                    file_size = os.path.getsize(save_path)

                    attachment = Attachment(
                        news_id=news.id,
                        file_name=original_name,
                        file_path=save_path,
                        mime_type=f.content_type or "application/octet-stream",
                        size=file_size,
                    )
                    db.session.add(attachment)

        db.session.commit()
        flash("Новость успешно создана", "success")
        return redirect(url_for("web_news.list_news"))

    return render_template("news/create.html", role=role)


@news_bp.route("/<int:news_id>", methods=["GET"])
@jwt_required()
def news_details(news_id):
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    news = News.query.filter_by(id=news_id, is_deleted=False).first_or_404()
    return render_template("news/details.html", news=news, role=role)


@news_bp.route("/<int:news_id>/edit", methods=["GET", "POST"])
@jwt_required()
def edit_news(news_id):
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    if role.name not in ("Руководитель", "Документовед", "Ответственный"):
        flash("Доступ запрещён", "danger")
        return redirect(url_for("web_news.list_news"))

    news = News.query.filter_by(id=news_id, is_deleted=False).first_or_404()

    if request.method == "POST":
        title = request.form.get("title")
        text = request.form.get("text")
        is_pinned = request.form.get("is_pinned") == "on"
        delete_attachments = request.form.getlist("delete_attachments")
        new_files = request.files.getlist("files")

        if not title or not text:
            flash("Заполните заголовок и текст", "danger")
            return render_template("news/edit.html", news=news, role=role)

        for att_id in delete_attachments:
            att = Attachment.query.get(int(att_id))
            if att and att.news_id == news.id:
                if os.path.exists(att.file_path):
                    os.remove(att.file_path)
                db.session.delete(att)

        for f in new_files:
            if f.filename and allowed_image_file(f.filename, current_app.config):
                upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "attachments", "news", str(news.id))
                os.makedirs(upload_dir, exist_ok=True)
                original_name = f.filename
                ext = os.path.splitext(original_name)[1].lower()
                safe_name = str(uuid.uuid4()) + ext
                save_path = os.path.join(upload_dir, safe_name)
                f.save(save_path)
                file_size = os.path.getsize(save_path)
                attachment = Attachment(
                    news_id=news.id,
                    file_name=original_name,
                    file_path=save_path,
                    mime_type=f.content_type or "application/octet-stream",
                    size=file_size,
                )
                db.session.add(attachment)

        news.title = title
        news.text = text
        news.is_pinned = is_pinned
        db.session.commit()
        flash("Новость успешно обновлена", "success")
        return redirect(url_for("web_news.news_details", news_id=news.id))

    return render_template("news/edit.html", news=news, role=role)


@news_bp.route("/<int:news_id>/delete", methods=["POST"])
@jwt_required()
def delete_news(news_id):
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    if role.name not in ("Руководитель", "Документовед", "Ответственный"):
        flash("Доступ запрещён", "danger")
        return redirect(url_for("web_news.list_news"))

    news = News.query.filter_by(id=news_id, is_deleted=False).first_or_404()
    news.is_deleted = True
    db.session.commit()
    flash("Новость удалена", "success")
    return redirect(url_for("web_news.list_news"))


@news_bp.route("/image/<int:attachment_id>")
@jwt_required()
def serve_news_image(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    if not attachment.news_id:
        return "Not found", 404
    directory = os.path.dirname(attachment.file_path)
    filename = os.path.basename(attachment.file_path)
    return send_from_directory(directory, filename, mimetype=attachment.mime_type)

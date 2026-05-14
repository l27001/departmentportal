import os
import uuid
import math
from flask import Blueprint, request, jsonify, render_template, flash, send_file, redirect, url_for, current_app
from models.document import Document, DocumentLink
from models.attachment import Attachment
from models.role import Role
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from extensions import db, allowed_file
from decorators.roles import roles_required

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

CATEGORIES = ['нормативный', 'учебный', 'методический', 'прочее']


def get_combined_items(category=None, page=1, per_page=10):
    query_docs = Document.query
    query_links = DocumentLink.query
    if category:
        query_docs = query_docs.filter_by(category=category)
        query_links = query_links.filter_by(category=category)

    docs = query_docs.all()
    links = query_links.all()

    combined = []
    for d in docs:
        combined.append({
            'type': 'file',
            'id': d.id,
            'title': d.title,
            'category': d.category,
            'creator_id': d.creator_id,
            'created_at': d.created_at,
            'creator': d.creator,
            'attachments': d.attachments,
            'url': None,
        })
    for l in links:
        combined.append({
            'type': 'link',
            'id': l.id,
            'title': l.title,
            'category': l.category,
            'creator_id': l.creator_id,
            'created_at': l.created_at,
            'creator': l.creator,
            'attachments': [],
            'url': l.url,
        })

    combined.sort(key=lambda x: x['created_at'], reverse=True)
    total = len(combined)
    start = (page - 1) * per_page
    end = start + per_page
    items = combined[start:end]
    total_pages = max(1, math.ceil(total / per_page))
    return items, total, total_pages


@documents_bp.route('/', methods=['POST'])
@jwt_required()
@roles_required('Документовед', 'Руководитель')
def upload_document():
    user_id = get_jwt_identity()
    title = request.form.get("title")
    doc_type = request.form.get("doc_type").lower()
    files = request.files.getlist("file")

    files = [f for f in files if f.filename]
    if not files:
        flash("Файлы не выбраны", "danger")
        return redirect(url_for("documents.documents"))

    for file in files:
        if not allowed_file(file.filename, current_app.config):
            flash(f"Недопустимый формат файла: {file.filename}", "danger")
            return redirect(url_for("documents.documents"))

    if doc_type not in CATEGORIES:
        flash("Выберите категорию файла", "danger")
        return redirect(url_for("documents.documents"))

    document = Document(
        title=title,
        category=doc_type,
        creator_id=user_id
    )
    db.session.add(document)
    db.session.flush()

    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "attachments", "documents", str(document.id))
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        original_filename = file.filename
        ext = os.path.splitext(original_filename)[1] if '.' in original_filename else ''
        safe_name = str(uuid.uuid4()) + ext
        save_path = os.path.join(upload_dir, safe_name)

        file.save(save_path)
        file_size = os.path.getsize(save_path)

        attachment = Attachment(
            document_id=document.id,
            file_name=original_filename,
            file_path=save_path,
            mime_type=file.content_type or 'application/octet-stream',
            size=file_size
        )
        db.session.add(attachment)

    db.session.commit()

    flash("Документ успешно загружен", "success")
    return redirect(url_for("documents.documents"))


@documents_bp.route('/add_link', methods=['POST'])
@jwt_required()
@roles_required('Документовед', 'Руководитель')
def add_link():
    user_id = get_jwt_identity()
    title = request.form.get("title", "").strip()
    url = request.form.get("url", "").strip()
    category = request.form.get("category", "").strip().lower()

    if not title:
        flash("Название обязательно", "danger")
        return redirect(url_for("documents.documents"))
    if not url:
        flash("Ссылка обязательна", "danger")
        return redirect(url_for("documents.documents"))
    if not url.startswith(("http://", "https://")):
        flash("Ссылка должна начинаться с http:// или https://", "danger")
        return redirect(url_for("documents.documents"))
    if category not in CATEGORIES:
        flash("Выберите категорию", "danger")
        return redirect(url_for("documents.documents"))

    link = DocumentLink(
        title=title,
        url=url,
        category=category,
        creator_id=user_id
    )
    db.session.add(link)
    db.session.commit()
    flash("Ссылка добавлена", "success")
    return redirect(url_for("documents.documents"))


@documents_bp.route("/")
@documents_bp.route("/list")
@jwt_required()
def documents():
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    page = request.args.get("page", 1, type=int)
    per_page = 10
    category = request.args.get("category")

    items, total, total_pages = get_combined_items(category=category, page=page, per_page=per_page)
    return render_template(
        "documents/list.html",
        documents=items,
        role=role,
        page=page,
        total=total,
        per_page=per_page,
        total_pages=total_pages,
        current_category=category
    )


@documents_bp.route("/<int:document_id>/<int:attachment_id>")
@jwt_required()
def download_document(document_id, attachment_id):
    document = Document.query.get_or_404(document_id)
    attachment = Attachment.query.filter_by(id=attachment_id, document_id=document_id).first_or_404()
    return send_file(
        attachment.file_path,
        as_attachment=True,
        download_name=attachment.file_name
    )


@documents_bp.route('/<int:document_id>/edit', methods=['POST'])
@jwt_required()
@roles_required('Документовед', 'Руководитель')
def edit_document(document_id):
    document = Document.query.get_or_404(document_id)

    title = request.form.get("title", "").strip()
    if title:
        document.title = title

    db.session.commit()
    flash("Документ обновлён", "success")
    return redirect(url_for("documents.documents"))


@documents_bp.route('/link/<int:link_id>/edit', methods=['POST'])
@jwt_required()
@roles_required('Документовед', 'Руководитель')
def edit_link(link_id):
    link = DocumentLink.query.get_or_404(link_id)

    title = request.form.get("title", "").strip()
    if title:
        link.title = title

    url = request.form.get("url", "").strip()
    if url:
        if not url.startswith(("http://", "https://")):
            flash("Ссылка должна начинаться с http:// или https://", "danger")
            return redirect(url_for("documents.documents"))
        link.url = url

    db.session.commit()
    flash("Ссылка обновлена", "success")
    return redirect(url_for("documents.documents"))


@documents_bp.route('/<int:document_id>', methods=['DELETE'])
@jwt_required()
@roles_required('Документовед', 'Руководитель')
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)
    user_id = get_jwt_identity()
    if document.creator_id != user_id and get_jwt()["role"] != 1:
        return jsonify({"msg": "Access denied"}), 403

    for attachment in document.attachments:
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)

    db.session.delete(document)
    db.session.commit()

    return jsonify({"msg": "Document deleted successfully"}), 200


@documents_bp.route('/link/<int:link_id>', methods=['DELETE'])
@jwt_required()
@roles_required('Документовед', 'Руководитель')
def delete_link(link_id):
    link = DocumentLink.query.get_or_404(link_id)
    user_id = get_jwt_identity()
    if link.creator_id != user_id and get_jwt()["role"] != 1:
        return jsonify({"msg": "Access denied"}), 403

    db.session.delete(link)
    db.session.commit()

    return jsonify({"msg": "Link deleted successfully"}), 200


@documents_bp.route('/filter', methods=['GET'])
@jwt_required()
def filter_documents():
    category = request.args.get('category')
    query = Document.query

    if category:
        query = query.filter_by(category=category)

    docs = query.all()

    return jsonify([doc.to_dict() for doc in docs])

import os
import uuid
from flask import Blueprint, request, jsonify, render_template, flash, send_file, redirect, url_for, current_app
from models.document import Document
from models.attachment import Attachment
from models.role import Role
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from extensions import db, allowed_file
from decorators.auth import roles_required

documents_bp = Blueprint('documents', __name__, url_prefix='/documents')

@documents_bp.route('/', methods=['POST'])
@jwt_required()
def upload_document():
    categories = ['нормативный', 'учебный', 'методический', 'прочее']
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
    
    if doc_type not in categories:
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

@documents_bp.route("/")
@documents_bp.route("/list")
@jwt_required()
def documents():
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    page = request.args.get("page", 1, type=int)
    per_page = 10
    pagination = Document.query.order_by(Document.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template("documents/list.html", documents=pagination.items, role=role, page=page, total=pagination.total, per_page=per_page, total_pages=pagination.pages)

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

@documents_bp.route('/filter', methods=['GET'])
@jwt_required()
def filter_documents():
    category = request.args.get('category')
    query = Document.query
    
    if category:
        query = query.filter_by(category=category)
    
    docs = query.all()

    return jsonify([doc.to_dict() for doc in docs])

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
# @roles_required('Документовед', 'Руководитель')
@jwt_required()
def upload_document():
    if request.method == "POST":
        categories = ['нормативный', 'учебный', 'методический', 'прочее']
        user_id = get_jwt_identity()
        title = request.form.get("title")
        doc_type = request.form.get("doc_type").lower()
        file = request.files.get("file")

        if not file or file.filename == "":
            flash("Файл не выбран", "danger")
            return redirect(url_for("documents.documents"))

        if not allowed_file(file.filename, current_app.config):
            flash("Недопустимый формат файла", "danger")
            return redirect(url_for("documents.documents"))
        
        if(doc_type not in categories):
            flash("Выберите категорию файла", "danger")
            return redirect(url_for("documents.documents"))

        original_filename = file.filename
        ext = os.path.splitext(original_filename)[1] if '.' in original_filename else ''
        safe_name = str(uuid.uuid4()) + ext
        upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "attachments")
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, safe_name)

        file.save(save_path)
        file.seek(0, 2)
        file_size = file.tell()

        attachment = Attachment(
            task_id=None,
            file_name=original_filename,
            file_path=save_path,
            mime_type=file.content_type or 'application/octet-stream',
            size=file_size
        )
        db.session.add(attachment)
        db.session.flush()

        document = Document(
            title=title,
            category=doc_type,
            attachment_id=attachment.id,
            creator_id=user_id
        )

        db.session.add(document)
        db.session.commit()

        flash("Документ успешно загружен", "success")
        return redirect(url_for("documents.documents"))

    documents = Document.query.order_by(Document.created_at.desc()).all()
    return render_template("documents/list.html", documents=documents)

@documents_bp.route("/")
@documents_bp.route("/list")
@jwt_required()
def documents():
    role = Role.query.filter_by(id=get_jwt()["role"]).first()
    documents = Document.query.order_by(Document.created_at.desc()).all()
    return render_template("documents/list.html", documents=documents, role=role)

@documents_bp.route("/<int:document_id>")
@jwt_required()
def download_document(document_id):
    document = Document.query.get_or_404(document_id)
    attachment = document.attachment
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

    attachment = document.attachment
    if attachment and os.path.exists(attachment.file_path):
        os.remove(attachment.file_path)
        db.session.delete(attachment)

    db.session.delete(document)
    db.session.commit()

    return jsonify({"msg": "Document deleted successfully"}), 200

@documents_bp.route('/filter', methods=['GET'])
@jwt_required()  # Требует авторизации
def filter_documents():
    category = request.args.get('category')
    documents = Document.query
    
    if category:
        documents = documents.filter_by(category=category)
    
    documents = documents.all()

    return jsonify([doc.to_dict() for doc in documents])

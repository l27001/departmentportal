"""add missing indexes

Revision ID: c3daab576447
Revises: c5dff54a4e56
Create Date: 2026-05-16 17:27:25.911807

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3daab576447'
down_revision: Union[str, Sequence[str], None] = 'c5dff54a4e56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # announcements
    op.create_index("ix_announcements_is_deleted", "announcements", ["is_deleted"])
    op.create_index("ix_announcements_created_at", "announcements", ["created_at"])
    op.create_index(
        "ix_announcements_is_deleted_created_at",
        "announcements",
        ["is_deleted", sa.text("created_at DESC")],
    )

    # announcement_views
    op.create_index("ix_announcement_views_user_id", "announcement_views", ["user_id"])
    op.create_index(
        "ix_announcement_views_announcement_id",
        "announcement_views",
        ["announcement_id"],
    )

    # announcement_rsvps
    op.create_index(
        "ix_announcement_rsvps_announcement_id",
        "announcement_rsvps",
        ["announcement_id"],
    )

    # news
    op.create_index("ix_news_is_deleted", "news", ["is_deleted"])
    op.create_index("ix_news_created_at", "news", ["created_at"])
    op.create_index(
        "ix_news_list",
        "news",
        ["is_deleted", sa.text("is_pinned DESC"), sa.text("created_at DESC")],
    )

    # tasks
    op.create_index("ix_tasks_deadline_at", "tasks", ["deadline_at"])
    op.create_index("ix_tasks_creator_id", "tasks", ["creator_id"])

    # task_comments
    op.create_index("ix_task_comments_task_id", "task_comments", ["task_id"])
    op.create_index(
        "ix_task_comments_recipient_id", "task_comments", ["recipient_id"]
    )

    # attachments
    op.create_index("ix_attachments_task_id", "attachments", ["task_id"])
    op.create_index("ix_attachments_news_id", "attachments", ["news_id"])
    op.create_index(
        "ix_attachments_announcement_id", "attachments", ["announcement_id"]
    )
    op.create_index("ix_attachments_document_id", "attachments", ["document_id"])
    op.create_index("ix_attachments_meeting_id", "attachments", ["meeting_id"])
    op.create_index(
        "ix_attachments_chat_message_id", "attachments", ["chat_message_id"]
    )

    # general_chat
    op.create_index("ix_general_chat_created_at", "general_chat", ["created_at"])

    # documents
    op.create_index("ix_documents_category", "documents", ["category"])
    op.create_index("ix_documents_created_at", "documents", ["created_at"])

    # department_meetings
    op.create_index("ix_department_meetings_date", "department_meetings", ["date"])

    # users
    op.create_index("ix_users_is_active", "users", ["is_active"])
    op.create_index("ix_users_dismissal_date", "users", ["dismissal_date"])
    op.create_index("ix_users_role_id", "users", ["role_id"])
    op.create_index("ix_users_name", "users", ["name"])

    # user_groups — PK is (user_id, group_id), doesn't cover group_id-only lookups
    op.create_index("ix_user_groups_group_id", "user_groups", ["group_id"])

    # meeting_tasks — unique on (meeting_id, task_id), doesn't cover task_id-only
    op.create_index("ix_meeting_tasks_task_id", "meeting_tasks", ["task_id"])

    # entity_coauthors / entity_supervisors — unique on (type, entity_id, user_id)
    op.create_index(
        "ix_entity_coauthors_type_user_id",
        "entity_coauthors",
        ["entity_type", "user_id"],
    )
    op.create_index(
        "ix_entity_supervisors_type_user_id",
        "entity_supervisors",
        ["entity_type", "user_id"],
    )

    # rating status filters
    op.create_index("ix_awards_status", "awards", ["status"])
    op.create_index("ix_conferences_status", "conferences", ["status"])
    op.create_index("ix_trainings_status", "trainings", ["status"])


def downgrade() -> None:
    # announcements
    op.drop_index("ix_announcements_is_deleted_created_at")
    op.drop_index("ix_announcements_created_at")
    op.drop_index("ix_announcements_is_deleted")

    # announcement_views
    op.drop_index("ix_announcement_views_announcement_id")
    op.drop_index("ix_announcement_views_user_id")

    # announcement_rsvps
    op.drop_index("ix_announcement_rsvps_announcement_id")

    # news
    op.drop_index("ix_news_list")
    op.drop_index("ix_news_created_at")
    op.drop_index("ix_news_is_deleted")

    # tasks
    op.drop_index("ix_tasks_creator_id")
    op.drop_index("ix_tasks_deadline_at")

    # task_comments
    op.drop_index("ix_task_comments_recipient_id")
    op.drop_index("ix_task_comments_task_id")

    # attachments
    op.drop_index("ix_attachments_chat_message_id")
    op.drop_index("ix_attachments_meeting_id")
    op.drop_index("ix_attachments_document_id")
    op.drop_index("ix_attachments_announcement_id")
    op.drop_index("ix_attachments_news_id")
    op.drop_index("ix_attachments_task_id")

    # general_chat
    op.drop_index("ix_general_chat_created_at")

    # documents
    op.drop_index("ix_documents_created_at")
    op.drop_index("ix_documents_category")

    # department_meetings
    op.drop_index("ix_department_meetings_date")

    # users
    op.drop_index("ix_users_name")
    op.drop_index("ix_users_role_id")
    op.drop_index("ix_users_dismissal_date")
    op.drop_index("ix_users_is_active")

    # user_groups
    op.drop_index("ix_user_groups_group_id")

    # meeting_tasks
    op.drop_index("ix_meeting_tasks_task_id")

    # entity_coauthors / entity_supervisors
    op.drop_index("ix_entity_coauthors_type_user_id")
    op.drop_index("ix_entity_supervisors_type_user_id")

    # rating status
    op.drop_index("ix_awards_status")
    op.drop_index("ix_conferences_status")
    op.drop_index("ix_trainings_status")

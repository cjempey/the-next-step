"""add_user_auth_and_multi_user_support

Revision ID: 47f5d4737325
Revises: f79d82ec6267
Create Date: 2026-01-01 15:50:14.000982

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "47f5d4737325"
down_revision: Union[str, None] = "f79d82ec6267"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # Add user_id to tasks table
    op.add_column("tasks", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_tasks_user_id"), "tasks", ["user_id"], unique=False)
    op.create_foreign_key("fk_tasks_user_id", "tasks", "users", ["user_id"], ["id"])

    # Add user_id to values table
    op.add_column("values", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_values_user_id"), "values", ["user_id"], unique=False)
    op.create_foreign_key("fk_values_user_id", "values", "users", ["user_id"], ["id"])

    # Add user_id to rejection_dampening table
    op.add_column(
        "rejection_dampening", sa.Column("user_id", sa.Integer(), nullable=True)
    )
    op.create_index(
        op.f("ix_rejection_dampening_user_id"),
        "rejection_dampening",
        ["user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_rejection_dampening_user_id",
        "rejection_dampening",
        "users",
        ["user_id"],
        ["id"],
    )

    # Add user_id to daily_priorities table
    op.add_column("daily_priorities", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_daily_priorities_user_id"),
        "daily_priorities",
        ["user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_daily_priorities_user_id", "daily_priorities", "users", ["user_id"], ["id"]
    )

    # Add user_id to review_history table
    op.add_column("review_history", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_review_history_user_id"), "review_history", ["user_id"], unique=False
    )
    op.create_foreign_key(
        "fk_review_history_user_id", "review_history", "users", ["user_id"], ["id"]
    )

    # Add user_id to review_cards table
    op.add_column("review_cards", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_review_cards_user_id"), "review_cards", ["user_id"], unique=False
    )
    op.create_foreign_key(
        "fk_review_cards_user_id", "review_cards", "users", ["user_id"], ["id"]
    )

    # Make user_id NOT NULL after foreign keys are added
    # (In production with data, you'd first populate user_id, then make it NOT NULL)
    op.alter_column("tasks", "user_id", nullable=False)
    op.alter_column("values", "user_id", nullable=False)
    op.alter_column("rejection_dampening", "user_id", nullable=False)
    op.alter_column("daily_priorities", "user_id", nullable=False)
    op.alter_column("review_history", "user_id", nullable=False)
    op.alter_column("review_cards", "user_id", nullable=False)


def downgrade() -> None:
    # Remove user_id columns
    op.drop_constraint("fk_review_cards_user_id", "review_cards", type_="foreignkey")
    op.drop_index(op.f("ix_review_cards_user_id"), table_name="review_cards")
    op.drop_column("review_cards", "user_id")

    op.drop_constraint(
        "fk_review_history_user_id", "review_history", type_="foreignkey"
    )
    op.drop_index(op.f("ix_review_history_user_id"), table_name="review_history")
    op.drop_column("review_history", "user_id")

    op.drop_constraint(
        "fk_daily_priorities_user_id", "daily_priorities", type_="foreignkey"
    )
    op.drop_index(op.f("ix_daily_priorities_user_id"), table_name="daily_priorities")
    op.drop_column("daily_priorities", "user_id")

    op.drop_constraint(
        "fk_rejection_dampening_user_id", "rejection_dampening", type_="foreignkey"
    )
    op.drop_index(
        op.f("ix_rejection_dampening_user_id"), table_name="rejection_dampening"
    )
    op.drop_column("rejection_dampening", "user_id")

    op.drop_constraint("fk_values_user_id", "values", type_="foreignkey")
    op.drop_index(op.f("ix_values_user_id"), table_name="values")
    op.drop_column("values", "user_id")

    op.drop_constraint("fk_tasks_user_id", "tasks", type_="foreignkey")
    op.drop_index(op.f("ix_tasks_user_id"), table_name="tasks")
    op.drop_column("tasks", "user_id")

    # Drop users table
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")

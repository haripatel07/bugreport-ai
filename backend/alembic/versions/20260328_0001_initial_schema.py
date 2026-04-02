"""initial_schema

Revision ID: 20260328_0001
Revises:
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260328_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
        op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    if "analysis_records" not in existing_tables:
        op.create_table(
            "analysis_records",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("input_type", sa.String(length=32), nullable=False),
            sa.Column("environment", sa.JSON(), nullable=True),
            sa.Column("processed_input", sa.JSON(), nullable=True),
            sa.Column("bug_report", sa.JSON(), nullable=True),
            sa.Column("root_cause_analysis", sa.JSON(), nullable=True),
            sa.Column("recommendations", sa.JSON(), nullable=True),
            sa.Column("similar_bugs", sa.JSON(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_analysis_records_id"), "analysis_records", ["id"], unique=False)
        op.create_index(op.f("ix_analysis_records_user_id"), "analysis_records", ["user_id"], unique=False)
    else:
        columns = {column["name"] for column in inspector.get_columns("analysis_records")}
        if "user_id" not in columns:
            op.execute(
                "INSERT INTO users (id, email, hashed_password, is_active, created_at) "
                "VALUES (1, 'legacy@local', 'legacy_migration_placeholder', true, CURRENT_TIMESTAMP) "
                "ON CONFLICT (id) DO NOTHING"
            )
            op.add_column(
                "analysis_records",
                sa.Column("user_id", sa.Integer(), nullable=True),
            )
            op.execute("UPDATE analysis_records SET user_id = 1 WHERE user_id IS NULL")


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_records_user_id"), table_name="analysis_records")
    op.drop_index(op.f("ix_analysis_records_id"), table_name="analysis_records")
    op.drop_table("analysis_records")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

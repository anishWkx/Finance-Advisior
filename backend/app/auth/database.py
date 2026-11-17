import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv


# Load project-root and backend environment variables.
BACKEND_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BACKEND_DIR.parent

load_dotenv(ROOT_DIR / ".env")
load_dotenv(BACKEND_DIR / ".env", override=False)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured.")


def get_connection():
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row,
        connect_timeout=15,
        sslmode="require",
    )


def initialize_database():
    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text)
            )
        """)

        connection.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_lower
            ON users (LOWER(email))
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
                FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                transaction_date TEXT,
                description TEXT NOT NULL,
                debit TEXT,
                credit TEXT,
                balance TEXT,
                source_page INTEGER,
                source_sheet TEXT,
                raw_text TEXT,
                created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
                FOREIGN KEY (document_id) REFERENCES documents(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_user
            ON documents(user_id)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_user
            ON transactions(user_id)
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_document
            ON transactions(document_id)
        """)


# -------------------------
# USER FUNCTIONS
# -------------------------

def create_user(user_id, name, email, password_hash):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO users (id, name, email, password_hash)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, name, email.strip().lower(), password_hash),
        )


def get_user_by_email(email):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM users
            WHERE LOWER(email) = LOWER(%s)
            """,
            (email.strip(),),
        ).fetchone()

        return dict(row) if row else None


def get_user_by_id(user_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, email, created_at
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        ).fetchone()

        return dict(row) if row else None


# -------------------------
# DOCUMENT FUNCTIONS
# -------------------------

def save_document(
    document_id,
    user_id,
    original_filename,
    stored_filename,
    file_type,
    file_size_bytes=0,
    chunk_count=0,
):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO documents (
                id,
                user_id,
                original_filename,
                stored_filename,
                file_type,
                file_size_bytes,
                chunk_count
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                document_id,
                user_id,
                original_filename,
                stored_filename,
                file_type,
                file_size_bytes,
                chunk_count,
            ),
        )


def get_user_documents(user_id):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM documents
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()

        return [dict(row) for row in rows]


# -------------------------
# TRANSACTION FUNCTIONS
# -------------------------

def save_transactions(transactions):
    if not transactions:
        return 0

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO transactions (
                    id,
                    document_id,
                    user_id,
                    transaction_date,
                    description,
                    debit,
                    credit,
                    balance,
                    source_page,
                    source_sheet,
                    raw_text
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        transaction["id"],
                        transaction["document_id"],
                        transaction["user_id"],
                        transaction.get("transaction_date"),
                        transaction["description"],
                        transaction.get("debit"),
                        transaction.get("credit"),
                        transaction.get("balance"),
                        transaction.get("source_page"),
                        transaction.get("source_sheet"),
                        transaction.get("raw_text"),
                    )
                    for transaction in transactions
                ],
            )

    return len(transactions)


def get_user_transactions(user_id, document_id=None):
    with get_connection() as connection:

        if document_id:
            rows = connection.execute(
                """
                SELECT *
                FROM transactions
                WHERE user_id = %s AND document_id = %s
                ORDER BY transaction_date
                """,
                (user_id, document_id),
            ).fetchall()

        else:
            rows = connection.execute(
                """
                SELECT *
                FROM transactions
                WHERE user_id = %s
                ORDER BY transaction_date
                """,
                (user_id,),
            ).fetchall()

        return [dict(row) for row in rows]

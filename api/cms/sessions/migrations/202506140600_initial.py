# List of dependencies (migration that must be applied before this one)
dependencies = ["users.202506121032_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE UNLOGGED TABLE IF NOT EXISTS sessions (
        session_id UUID DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL,
        ip_addr CHAR(64) NOT NULL,
        expires_at TIMESTAMP(0) WITH TIME ZONE DEFAULT (now() + INTERVAL '15 minutes'),
        is_terminated BOOLEAN DEFAULT FALSE,
        CONSTRAINT pk_sessions PRIMARY KEY (session_id),
        CONSTRAINT fk_sessions_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """,
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP TABLE IF EXISTS sessions;
    """,
]

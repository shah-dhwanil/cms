# List of dependencies (migration that must be applied before this one)
dependencies = ["users.202505311458_initial"]

# SQL to apply the migration
apply = [
    """
    CREATE UNLOGGED TABLE IF NOT EXISTS sessions(
        id UUID DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL,
        created_at TIMESTAMP DEFAULT now(),
        expires_at TIMESTAMP DEFAULT (now() + INTERVAL '15 minutes'),
        terminated boolean DEFAULT false,
        CONSTRAINT pk_sessions PRIMARY KEY (id),
        CONSTRAINT fk_sessions_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
]

# SQL to rollback the migration
rollback = [
    """
    DROP TABLE IF EXISTS sessions;
    """
]

# List of dependencies (migration that must be applied before this one)
dependencies = ["users.202506121032_initial", "permissions.202506131242_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS user_permissions (
        user_id UUID NOT NULL,
        permission VARCHAR(64) NOT NULL,
        CONSTRAINT pk_user_permissions PRIMARY KEY (user_id, permission),
        CONSTRAINT fk_user_permissions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        CONSTRAINT fk_user_permissions_permissions FOREIGN KEY (permission) REFERENCES permissions(slug) ON DELETE NO ACTION
    );
    """,
    """--sql
    CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id);
    """
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP INDEX IF EXISTS idx_user_permissions_user_id;
    """,
    """--sql
    DROP TABLE IF EXISTS user_permissions;
    """
]

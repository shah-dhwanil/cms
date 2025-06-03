# List of dependencies (migration that must be applied before this one)
dependencies = ["users.202505311458_initial", "permissions.202506021436_initial"]

# SQL to apply the migration
apply = [
    """
    CREATE TABLE user_permissions(
        user_id UUID NOT NULL,
        permission_name VARCHAR(64) NOT NULL,
        CONSTRAINT pk_user_permissions PRIMARY KEY (user_id, permission_name),
        CONSTRAINT fk_user_permissions_users FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        CONSTRAINT fk_user_permissions_permissions FOREIGN KEY (permission_name) REFERENCES permissions(name) ON DELETE RESTRICT
    );
    """
    """
    CREATE INDEX idx_user_permissions_user_id ON user_permissions(user_id);
    """
]

# SQL to rollback the migration
rollback = [
    """
    DROP INDEX idx_user_permissions_user_id;
    """
    """
    DROP TABLE user_permissions;
    """
]

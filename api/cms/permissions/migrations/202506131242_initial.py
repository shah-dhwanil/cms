# List of dependencies (migration that must be applied before this one)
dependencies = []

# SQL to apply the migration
apply = [
    """
    CREATE TABLE IF NOT EXISTS permissions (
        slug VARCHAR(64),
        description VARCHAR(255),
        CONSTRAINT pk_permissions PRIMARY KEY (slug)
    );
    """
]

# SQL to rollback the migration
rollback = [
    """
    DROP TABLE IF EXISTS permissions;
    """
]

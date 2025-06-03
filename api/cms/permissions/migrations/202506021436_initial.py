# List of dependencies (migration that must be applied before this one)
dependencies = []

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS permissions(
        name VARCHAR(64) NOT NULL,
        description VARCHAR(255) NOT NULL,
        CONSTRAINT pk_permissions PRIMARY KEY (name)
    );
    """,
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP TABLE IF EXISTS permissions;
    """,
]

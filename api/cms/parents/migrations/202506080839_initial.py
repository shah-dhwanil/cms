# List of dependencies (migration that must be applied before this one)
dependencies = ["users.202505311458_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS parents(
        id UUID,
        father_name VARCHAR(64) NOT NULL,
        mother_name VARCHAR(64) NOT NULL,
        address TEXT NOT NULL,
        active BOOLEAN DEFAULT TRUE,
        CONSTRAINT pk_parents PRIMARY KEY (id),
        CONSTRAINT fk_parents_users FOREIGN KEY (id) REFERENCES users(id)
    )
    """
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP TABLE IF EXISTS parents
    """
]

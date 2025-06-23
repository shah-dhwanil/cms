
# List of dependencies (migration that must be applied before this one)
dependencies = ["staff.202506200509_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS school (
        id uuid,
        name VARCHAR(128) NOT NULL,
        dean_id uuid NOT NULL,
        extra_info JSON,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        CONSTRAINT pk_school PRIMARY KEY (id),
        CONSTRAINT fk_school_dean FOREIGN KEY (dean_id) REFERENCES staff(id) ON DELETE NO ACTION ON UPDATE CASCADE
    );
    """,
    """--sql
    CREATE UNIQUE INDEX IF NOT EXISTS uniq_school_name ON school(name) WHERE is_active;
    """,
    """--sql
    CREATE UNIQUE INDEX IF NOT EXISTS uniq_school_dean_id ON school(dean_id) WHERE is_active;
    """,
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP INDEX IF EXISTS uniq_school_dean_id;
    """,
    """--sql
    DROP INDEX IF EXISTS uniq_school_name;
    """,
    """--sql
    DROP TABLE IF EXISTS school;
    """,
]

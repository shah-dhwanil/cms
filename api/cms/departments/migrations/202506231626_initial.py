
# List of dependencies (migration that must be applied before this one)
dependencies = ["schools.202506231302_initial","staff.202506200509_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TABLE IF NOT EXISTS departments (
        id UUID,
        name VARCHAR(128) NOT NULL,
        school_id UUID NOT NULL,
        head_id UUID NOT NULL,
        extra_info JSON,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        CONSTRAINT pk_departments PRIMARY KEY (id),
        CONSTRAINT fk_departments_school_id FOREIGN KEY (school_id) REFERENCES school (id) ON DELETE CASCADE ON UPDATE CASCADE,
        CONSTRAINT fk_departments_head_id FOREIGN KEY (head_id) REFERENCES staff (id) ON DELETE NO ACTION ON UPDATE CASCADE
    );
    """,
    """--sql
    CREATE UNIQUE INDEX IF NOT EXISTS uniq_departments_name ON departments (name) WHERE is_active;
    """,
    """--sql
    CREATE UNIQUE INDEX IF NOT EXISTS uniq_departments_head_id ON departments (head_id) WHERE is_active;
    """,
    """--sql
    CREATE INDEX IF NOT EXISTS idx_departments_school_id ON departments (school_id);
    """,
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP INDEX IF EXISTS uniq_departments_name;
    """,
    """--sql
    DROP INDEX IF EXISTS uniq_departments_head_id;
    """,
    """--sql
    DROP INDEX IF EXISTS idx_departments_school_id;
    """,
    """--sql
    DROP TABLE IF EXISTS departments;
    """
]

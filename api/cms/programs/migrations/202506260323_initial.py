# List of dependencies (migration that must be applied before this one)
dependencies = ["departments.202506231626_initial"]

# SQL to apply the migration
apply = [
    """--sql
    CREATE TYPE DegreeType AS ENUM (
        'DIPLOMA',
        'MINOR',
        'BECHELORS',
        'MASTERS',
        'PHD',
        'OTHERS'
    );
    """,
    """--sql
    CREATE TABLE IF NOT EXISTS programs (
        id UUID,
        name VARCHAR(128) NOT NULL,
        degree_name VARCHAR(128) NOT NULL,
        degree_type DegreeType NOT NULL,
        offered_by UUID NOT NULL,
        extra_info JSON,
        is_active BOOLEAN DEFAULT TRUE,
        CONSTRAINT pk_programs PRIMARY KEY (id),
        CONSTRAINT fk_programs_departments FOREIGN KEY (offered_by) REFERENCES departments (id) ON DELETE NO ACTION ON UPDATE CASCADE
    );
    """,
    """--sql
    CREATE UNIQUE INDEX IF NOT EXISTS uniq_programs_name ON programs (name) WHERE is_active;
    """,
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP INDEX IF EXISTS uniq_programs_name;
    """,
    """--sql
    DROP TABLE IF EXISTS programs;
    """,
    """--sql
    DROP TYPE IF EXISTS DegreeType;
    """,
]

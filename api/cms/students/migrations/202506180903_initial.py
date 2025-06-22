# List of dependencies (migration that must be applied before this one)
dependencies = ["users.202506121032_initial"]

# SQL to apply the migration
apply = [
    """--sql    
    CREATE TABLE IF NOT EXISTS students(
        id UUID,
        first_name VARCHAR(32) NOT NULL,
        middle_name VARCHAR(32) NOT NULL,
        last_name VARCHAR(32) NOT NULL,
        date_of_birth DATE NOT NULL,
        gender CHAR(1) NOT NULL,
        address TEXT NOT NULL,
        aadhaar_no CHAR(12) NOT NULL,
        apaar_id CHAR(12) NOT NULL,
        extra_info JSON,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        CONSTRAINT pk_students PRIMARY KEY (id),
        CONSTRAINT fk_students_user FOREIGN KEY (id,is_active) REFERENCES users(id,is_active) ON DELETE CASCADE ON UPDATE CASCADE
    );
    """,
    """--sql
    CREATE UNIQUE INDEX uniq_students_aadhaar_no ON students(aadhaar_no,is_active) WHERE is_active;
    """,
    """--sql
    CREATE UNIQUE INDEX uniq_students_apaar_id ON students(apaar_id,is_active) WHERE is_active;
    """,
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP INDEX IF EXISTS uniq_students_aadhaar_no;
    """,
    """--sql
    DROP INDEX IF EXISTS uniq_students_apaar_id;
    """,
    """--sql
    DROP TABLE IF EXISTS students;
    """,
]

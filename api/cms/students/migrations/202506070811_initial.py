# List of dependencies (migration that must be applied before this one)
dependencies = ["users.202505311458_initial"]

# SQL to apply the migration
apply = [
    """
    CREATE TABLE IF NOT EXISTS students(
        id UUID,
        first_name VARCHAR(16) NOT NULL,
        last_name VARCHAR(16) NOT NULL,
        gender CHAR(1) NOT NULL,
        aadhaar_no CHAR(12) NOT NULL,
        apaar_id CHAR(12) NOT NULL,
        active BOOLEAN NOT NULL DEFAULT TRUE,
        CONSTRAINT pk_students PRIMARY KEY (id),
        CONSTRAINT uniq_students_aadhaar_no UNIQUE (aadhaar_no),
        CONSTRAINT uniq_students_apaar_id UNIQUE (apaar_id),
        CONSTRAINT fk_students_user FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
]

# SQL to rollback the migration
rollback = [
    """
    DROP TABLE IF EXISTS students;
    """
]

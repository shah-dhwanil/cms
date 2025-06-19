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
        CONSTRAINT pk_students PRIMARY KEY (id,is_active),
        CONSTRAINT uniq_students_aadhaar_no UNIQUE (aadhaar_no,is_active),
        CONSTRAINT uniq_students_apaar_id UNIQUE (apaar_id,is_active),
        CONSTRAINT fk_students_user FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
    );
    """
]

# SQL to rollback the migration
rollback = [
    """--sql
    DROP TABLE IF EXISTS students;
    """
]

-- Runs automatically the first time the postgres container initializes its data volume

CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    credits INT DEFAULT 3
);

CREATE TABLE IF NOT EXISTS enrollments (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    course_id INT NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (student_id, course_id)
);

-- Seed a few sample courses
INSERT INTO courses (course_code, title, description, credits) VALUES
    ('CS101', 'Introduction to Computer Science', 'Basics of programming and computational thinking', 4),
    ('MATH201', 'Calculus II', 'Integration techniques, series, and applications', 4),
    ('ENG150', 'Academic Writing', 'Writing clear, structured academic essays', 3),
    ('DB301', 'Database Systems', 'Relational databases, SQL, and design theory', 3),
    ('AI401', 'Introduction to Artificial Intelligence', 'Search, knowledge representation, and ML basics', 4)
ON CONFLICT (course_code) DO NOTHING;

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL
import jwt
from datetime import datetime, timedelta
import bcrypt

app = Flask(__name__)
CORS(app)

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Chocolatemilk'
app.config['MYSQL_DB'] = 'elearning'
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Change in production

mysql = MySQL(app)

# Database initialization
def init_db():
    cur = mysql.connection.cursor()
    
    # Users table with varied privileges
    cur.execute(''' 
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            role ENUM('student', 'instructor', 'admin') NOT NULL
        )
    ''')
    
    # Courses table
    cur.execute(''' 
        CREATE TABLE IF NOT EXISTS courses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            instructor_id INT,
            FOREIGN KEY (instructor_id) REFERENCES users(id)
        )
    ''')
    
    # New modules table
    cur.execute(''' 
        CREATE TABLE IF NOT EXISTS modules (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_id INT,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            content TEXT,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
        )
    ''')
    
    # Enrollments table
    cur.execute(''' 
        CREATE TABLE IF NOT EXISTS enrollments (
            user_id INT,
            course_id INT,
            enrollment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, course_id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (course_id) REFERENCES courses(id)
        )
    ''')
    
    mysql.connection.commit()
    cur.close()

@app.route('/')
def index():
    return "Welcome to the eLearning API!"

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    cur = mysql.connection.cursor()
    
    # Hash the password
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    
    try:
        # Insert the user into the users table
        cur.execute(
            "INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)",
            (data['username'], hashed_password, data['email'], data['role'])
        )
        user_id = cur.lastrowid  # Get the user ID of the newly inserted user
        mysql.connection.commit()
        
        # Insert additional data based on role (student or instructor)
        if data['role'] == 'student':
            cur.execute(
                "INSERT INTO students (user_id, username, password, email) VALUES (%s, %s, %s, %s)",
                (user_id, data['username'], hashed_password, data['email'])
            )
        elif data['role'] == 'instructor':
            cur.execute(
                "INSERT INTO instructors (user_id, username, password, email) VALUES (%s, %s, %s, %s)",
                (user_id, data['username'], hashed_password, data['email'])
            )
        mysql.connection.commit()
        
        return jsonify({"message": "User registered successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()

@app.route('/course-stats', methods=['GET'])
def course_stats():
    """
    Aggregate query: Get enrollment statistics for each course
    """
    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            SELECT courses.title, COUNT(enrollments.user_id) AS student_count
            FROM courses
            LEFT JOIN enrollments ON courses.id = enrollments.course_id
            GROUP BY courses.title
        ''')
        rows = cur.fetchall()
        result = [
            {
                "course_title": row[0],
                "student_count": row[1]
            }
            for row in rows
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

@app.route('/instructor-courses', methods=['GET'])
def instructor_courses():
    """
    Join query: Get courses with their instructor names
    """
    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            SELECT courses.title, users.username
            FROM courses
            INNER JOIN users ON courses.instructor_id = users.id
            WHERE users.role = 'instructor'
        ''')
        rows = cur.fetchall()
        result = [
            {
                "course_title": row[0],
                "instructor_name": row[1]
            }
            for row in rows
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

@app.route('/student-enrollments', methods=['GET'])
def student_enrollments():
    """
    Join query: Get all enrolled courses for students
    """
    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            SELECT users.username AS student, courses.title
            FROM enrollments
            INNER JOIN users ON enrollments.user_id = users.id
            INNER JOIN courses ON enrollments.course_id = courses.id
            WHERE users.role = 'student'
        ''')
        rows = cur.fetchall()
        result = [
            {
                "student": row[0],
                "course_title": row[1]
            }
            for row in rows
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

@app.route('/popular-course', methods=['GET'])
def popular_course():
    """
    Nested query: Get the course with the most enrollments
    """
    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            SELECT title
            FROM courses
            WHERE id = (
                SELECT course_id
                FROM enrollments
                GROUP BY course_id
                ORDER BY COUNT(user_id) DESC
                LIMIT 1
            )
        ''')
        row = cur.fetchone()
        if row:
            return jsonify({"most_popular_course": row[0]})
        return jsonify({"message": "No enrollments found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

# Optional: Combined stats endpoint
@app.route('/dashboard-stats', methods=['GET'])
def dashboard_stats():
    """
    Combined endpoint that returns all statistics
    """
    cur = mysql.connection.cursor()
    try:
        # Course enrollment stats
        cur.execute('''
            SELECT courses.title, COUNT(enrollments.user_id) AS student_count
            FROM courses
            LEFT JOIN enrollments ON courses.id = enrollments.course_id
            GROUP BY courses.title
        ''')
        enrollment_stats = [
            {"course_title": row[0], "student_count": row[1]}
            for row in cur.fetchall()
        ]

        # Instructor courses
        cur.execute('''
            SELECT courses.title, users.username
            FROM courses
            INNER JOIN users ON courses.instructor_id = users.id
            WHERE users.role = 'instructor'
        ''')
        instructor_data = [
            {"course_title": row[0], "instructor_name": row[1]}
            for row in cur.fetchall()
        ]

        # Most popular course
        cur.execute('''
            SELECT title
            FROM courses
            WHERE id = (
                SELECT course_id
                FROM enrollments
                GROUP BY course_id
                ORDER BY COUNT(user_id) DESC
                LIMIT 1
            )
        ''')
        popular_course = cur.fetchone()

        return jsonify({
            "enrollment_statistics": enrollment_stats,
            "instructor_courses": instructor_data,
            "most_popular_course": popular_course[0] if popular_course else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    cur = mysql.connection.cursor()
    
    try:
        cur.execute("SELECT * FROM users WHERE username = %s", (data['username'],))
        user = cur.fetchone()
        
        if user and bcrypt.checkpw(data['password'].encode('utf-8'), user[2].encode('utf-8')): 
            token = jwt.encode({
                'user_id': user[0],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['JWT_SECRET_KEY'])
            
            return jsonify({
                "token": token,
                "user_id": user[0],
                "role": user[4]
            })
        return jsonify({"error": "Invalid credentials"}), 401
    finally:
        cur.close()

@app.route('/courses', methods=['GET', 'POST'])
def courses():
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, title, description, instructor_id FROM courses")
        courses = cur.fetchall()
        cur.close()
        
        # Convert to JSON objects
        courses_list = [
            {"id": course[0], "title": course[1], "description": course[2], "instructor_id": course[3]}
            for course in courses
        ]
        return jsonify(courses_list)
    
    if request.method == 'POST':
        data = request.json
        cur = mysql.connection.cursor()
        
        try:
            cur.execute(
                "INSERT INTO courses (title, description, instructor_id) VALUES (%s, %s, %s)",
                (data['title'], data['description'], data['instructor_id'])
            )
            mysql.connection.commit()
            return jsonify({"message": "Course created successfully"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        finally:
            cur.close()

@app.route('/modules', methods=['GET', 'POST'])
def modules():
    if request.method == 'GET':
        course_id = request.args.get('course_id')
        cur = mysql.connection.cursor()
        
        if course_id:
            cur.execute("SELECT id, title, description, content FROM modules WHERE course_id = %s", (course_id,))
        else:
            cur.execute("SELECT id, course_id, title, description, content FROM modules")
        
        modules = cur.fetchall()
        cur.close()
        
        # Convert to JSON objects
        modules_list = [
            {
                "id": module[0], 
                "course_id": module[1] if len(module) > 1 else None,
                "title": module[1] if len(module) > 1 else module[0],
                "description": module[2],
                "content": module[3]
            } for module in modules
        ]
        return jsonify(modules_list)
    
    if request.method == 'POST':
        data = request.json
        cur = mysql.connection.cursor()
        
        try:
            cur.execute(
                "INSERT INTO modules (course_id, title, description, content) VALUES (%s, %s, %s, %s)",
                (data['course_id'], data['title'], data['description'], data.get('content', ''))
            )
            mysql.connection.commit()
            return jsonify({"message": "Module created successfully"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        finally:
            cur.close()

@app.route('/enrollments', methods=['POST'])
def enroll():
    data = request.json
    course_id = data['course_id']
    student_id = data['student_id']
    
    cur = mysql.connection.cursor()
    
    # Check if the student is already enrolled in the course
    cur.execute("SELECT * FROM enrollments WHERE user_id = %s AND course_id = %s", (student_id, course_id))
    existing_enrollment = cur.fetchone()
    
    if existing_enrollment:
        return jsonify({"error": "You are already enrolled in this course."}), 400
    
    try:
        # Insert the enrollment record
        cur.execute(
            "INSERT INTO enrollments (user_id, course_id) VALUES (%s, %s)",
            (student_id, course_id)
        )
        mysql.connection.commit()
        return jsonify({"message": "Enrollment successful!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cur.close()

if __name__ == '__main__':
    with app.app_context():  # Wrap init_db in app context
        init_db()
    app.run(debug=True)
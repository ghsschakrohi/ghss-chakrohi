from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import qrcode, os, io, base64, random, requests, pandas as pd, urllib.parse, time, sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ghss-01131502304'
FAST2SMS_API_KEY = "DnMZlzvTrHgeQqM22KNlVYxAOpWTR61u3DLr4D9zR5JbE5rpQicF606xcCid"

def get_db():
    db_path = os.path.join(os.path.dirname(__file__), 'ghss.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db(); cursor = conn.cursor()
    # FIXED: Don't DROP - use IF NOT EXISTS
    cursor.execute('''CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, designation TEXT, subject TEXT, exp TEXT, qualification TEXT, wef TEXT)''')
    cursor.execute("SELECT COUNT(*) FROM teachers")
    if cursor.fetchone()[0]==0:
        staff = [('Mrs. Pushpa Lochan', 'Principal', 'Administration', '25', 'Masters,B.Ed', ''),('Mr. Gurmeet Singh', 'Sr. Lect Sociology - Vice Principal', 'Sociology', '18', 'Masters, M.Phil,B.Ed', ''),('Mr. Daleep Sharma', 'Sr. Lect Urdu', 'Urdu', '18', 'Masters, P.hd, B.Ed', ''),('Mr. Harveen Singh Sudan', 'Sr. Lect Political Science', 'Pol. Science', '16', 'Masters, M.Phil, B.Ed', ''),('Mrs. Neeru Ratta', 'Sr. Lect Education', 'Education', '16', 'Masters, M.Phil,B.Ed ', ''),('Mrs. Bindu Devi', 'Sr. Lect Zoology', 'Zoology', '16', 'Masters, B.Ed', ''),('Mrs. Bindu Dogra', 'Sr. Lect Hindi', 'Hindi', '16', 'Masters, NET, B.Ed', ''),('Mr. Paramjit Singh', 'Sr. Lect Computer Science', 'Computer Science', '17', 'MCA, M.Phil, B.Ed', '26-01-2023'),('Mrs. Shammi Chib', 'Lecturer Physics', 'Physics', '22', 'M.Sc, B.Ed', ''),('Mr. Shakti Kumar', 'Lecturer Chemistry', 'Chemistry', '33', 'M.Sc, B.Ed', ''),('Mrs. Alka', 'Lecturer English', 'English', '-', 'M.A, B.Ed', ''),('Mrs. Darshan Kour', 'I/C Lect Electronics', 'Electronics', '26', 'M.Sc, B.Ed', ''),('Mr. Rajesh Gupta', 'I/C Lect Botany', 'Botany', '22', 'M.Sc, B.Ed', ''),('Mrs. Ravinder Kour', 'I/C Lect Maths', 'Mathematics', '22', 'M.Sc, B.Ed', ''),('Mrs. Neelam Sudan', 'Master', 'General', '22', 'Masters, B.Ed', ''),('Mr. Ram Lal', 'Master', 'General', '19', 'Masters, B.Ed', ''),('Mr. Shariq Ishaq Mir', 'Teacher', 'General', '19', 'MA, B.Ed', ''),('Mr. Rohit Gupta', 'Teacher', 'General', '10', 'M.Sc, B.Ed', ''),('Mrs. Indu Gandhi', 'Teacher', 'General', '10', 'M.A, B.Ed', ''),('Mr. Sudansh Sharma', 'Teacher', 'General', '10', 'M.Sc, B.Ed', ''),('Mrs. Meenakshi Gupta', 'Teacher', 'General', '10', 'M.A, B.Ed', ''),('Mrs. Rasmeet Kour', 'Teacher', 'General', '10', 'M.Sc, B.Ed', ''),('Mrs. Devinder Kour', 'Sr. Assistant', 'Non-Teaching', '10', 'Graduate', ''),('Mr. Karanjeet Kumar', 'Lab. Assistant', 'Non-Teaching', '20', '12th', ''),('Mr. Rakesh Sharma', 'Lab Assistant', 'Non-Teaching', '20', '12th', ''),('Mrs. Asha Devi', 'Class-IV', 'Non-Teaching', '18', '', ''),('Mrs. Reena Devi', 'Class-IV', 'Non-Teaching', '12', '', ''),('Mr. Ravinder Choudhary', 'Class-IV', 'Non-Teaching', '10', '', ''),('Mr. Shubdeep Akash', 'Class-IV', 'Non-Teaching', '5', 'MA', ''),]
        for s in staff: cursor.execute("INSERT INTO teachers (name, designation, subject, exp, qualification, wef) VALUES (?,?,?,?,?,?)", s)

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, full_name TEXT, role TEXT, subject TEXT, mobile TEXT, is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, enrollment_no TEXT UNIQUE, first_name TEXT, father_name TEXT, class TEXT, dob DATE, mobile TEXT, address TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS activities (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, activity_date DATE, photo TEXT, uploaded_by TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS monthly_results (id INTEGER PRIMARY KEY AUTOINCREMENT, reg_no TEXT, month TEXT, subject TEXT, marks INTEGER, max_marks INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS admissions (id INTEGER PRIMARY KEY AUTOINCREMENT, contact_no TEXT, adm_no TEXT, name TEXT, father_name TEXT, class_name TEXT, dob DATE, residence TEXT, registration_no TEXT, status TEXT DEFAULT 'Pending', created_at DATETIME DEFAULT CURRENT_TIMESTAMP, session TEXT, stream TEXT, mother_name TEXT, caste TEXT, aadhar_shilla TEXT, form_date DATE, appar_id TEXT, udise_no TEXT, ration_type TEXT, sub1 TEXT, sub2 TEXT, sub3 TEXT, sub4 TEXT, sub5 TEXT, middle_year TEXT, middle_marks TEXT, middle_per TEXT, middle_sub TEXT, middle_school TEXT, middle_re TEXT, sse_year TEXT, sse_marks TEXT, sse_per TEXT, sse_sub TEXT, sse_school TEXT, sse_re TEXT, hsp_year TEXT, hsp_marks TEXT, hsp_per TEXT, hsp_sub TEXT, hsp_school TEXT, hsp_re TEXT, aadhar_self TEXT, aadhar_father TEXT, aadhar_mother TEXT, father_occupation TEXT, father_income TEXT, bank_account TEXT, bank_ifsc TEXT, undertaking_name TEXT, undertaking_father TEXT, undertaking_ro TEXT, undertaking_class TEXT)''')
    cursor.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
    if cursor.fetchone()[0]==0: cursor.execute("INSERT INTO users (username,password,full_name,role,is_active) VALUES (?,?,?,?,?)", ('admin','admin123','Principal','admin',1))
    conn.commit(); conn.close(); os.makedirs('static/uploads/activities', exist_ok=True)

# --- ROUTES (FIXED TOP -> LIMIT and GETDATE() -> CURRENT_TIMESTAMP) ---

@app.route('/')
def home():
    conn = get_db(); cursor = conn.cursor(); cursor.execute('SELECT * FROM teachers ORDER BY id'); teachers = cursor.fetchall()
    try: cursor.execute('SELECT * FROM activities ORDER BY id DESC'); activities = cursor.fetchall()
    except: activities = []
    conn.close(); return render_template('index.html', teachers=teachers, activities=activities)

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute('SELECT * FROM teachers'); teachers = cursor.fetchall()
    try: cursor.execute('SELECT * FROM users'); all_users = cursor.fetchall()
    except: all_users = []
    try: cursor.execute('SELECT COUNT(*) FROM students'); students_count = cursor.fetchone()[0]
    except: students_count = 0
    try: cursor.execute('SELECT COUNT(*) FROM monthly_results'); results_count = cursor.fetchone()[0]
    except: results_count = 0
    try:
        cursor.execute("SELECT COUNT(*) FROM admissions WHERE status='Approved'"); admissions_count = cursor.fetchone()[0]
        cursor.execute("SELECT * FROM admissions WHERE status='Pending' ORDER BY created_at DESC LIMIT 10"); pending_admissions = cursor.fetchall()
        cursor.execute("SELECT * FROM admissions WHERE status='Approved' ORDER BY created_at DESC LIMIT 10"); approved_admissions = cursor.fetchall()
        admissions = pending_admissions
    except Exception as e: print(e); admissions_count=0; admissions=[]; pending_admissions=[]; approved_admissions=[]
    try:
        cursor.execute("SELECT enrollment_no, first_name FROM students WHERE enrollment_no IS NOT NULL AND TRIM(enrollment_no)!='' AND TRIM(enrollment_no)!='None' AND LENGTH(TRIM(enrollment_no)) > 2 ORDER BY id DESC LIMIT 500")
        students_for_result = cursor.fetchall()
    except Exception as e: print(e); students_for_result = []
    try: cursor.execute('SELECT * FROM activities ORDER BY id DESC LIMIT 20'); activities = cursor.fetchall()
    except: activities = []
    conn.close()
    stats = {'students': students_count, 'results': results_count, 'admissions': admissions_count, 'teachers': len(teachers)}
    return render_template('dashboard.html', teachers=teachers, stats=stats, users=all_users, admissions=admissions, pending_admissions=pending_admissions, approved_admissions=approved_admissions, students_for_result=students_for_result, activities=activities, user=session.get('full_name'), role=session.get('role'))

# Keep all other routes same but fix GETDATE()
@app.route('/api/upload_result', methods=['POST'])
def upload_result():
    conn = get_db(); cursor = conn.cursor()
    reg_no = (request.form.get('reg_no') or '').strip().upper()
    month = (request.form.get('month') or '').strip()
    subject = (request.form.get('subject') or '').strip()
    marks = request.form.get('marks') or '0'
    max_marks = request.form.get('max_marks') or '100'
    if not reg_no: conn.close(); return "<h3>Select valid student<br><a href='/admin/dashboard'>Back</a></h3>"
    if session.get('role') in ['Teacher','staff'] and session.get('subject'): subject = session.get('subject')
    try:
        cursor.execute("SELECT status FROM admissions WHERE adm_no=?", (reg_no,))
        row = cursor.fetchone()
        if row and str(row[0]).lower() == 'pending': conn.close(); return f"<h3 style='color:red;text-align:center'>{reg_no} PENDING<br><a href='/admin/dashboard'>Back</a></h3>"
    except: pass
    try: cursor.execute("INSERT INTO monthly_results (reg_no, month, subject, marks, max_marks) VALUES (?,?,?,?,?)", (reg_no, month, subject, int(marks), int(max_marks))); conn.commit()
    except Exception as e: print(f"Result insert error {e}")
    conn.close(); return redirect('/admin/dashboard')

@app.route('/bulk-upload-admissions', methods=['POST'])
def bulk_upload_admissions():
    if not session.get('admin'): return redirect('/admin')
    try:
        file = request.files.get('excel_file')
        if not file: return "<h2>No file</h2>"
        df = pd.read_excel(file); df.columns = [str(c).strip() for c in df.columns]; df = df.fillna('')
        conn = get_db(); cur = conn.cursor(); inserted=0; skipped=0
        for i, row in df.iterrows():
            try:
                name = str(row.get('Student Name', row.get('Name',''))).strip()
                if not name or name.lower() in ('nan','none',''): skipped+=1; continue
                father = str(row.get('Father Name','')).strip()[:100]
                class_name = str(row.get('Class','11th')).strip()[:20]
                contact = str(row.get('Contact No', row.get('Mobile No',''))).strip().split('.')[0][:20]
                reg = str(row.get('Registration No', row.get('PEN No',''))).strip().split('.')[0][:50]
                residence = str(row.get('Residence','')).strip()[:200]
                dob_val = row.get('Date of Birth',''); dob = None
                try: dob = pd.to_datetime(dob_val).date() if str(dob_val).lower() not in ('nan','none','') else None
                except: dob = None
                adm_no = reg.upper() if reg and len(reg)>2 else f"GHSS{datetime.now().year}{random.randint(1000,9999)}"
                adm_no = adm_no.upper().strip()[:50]
                cur.execute("SELECT COUNT(*) FROM admissions WHERE adm_no=?", (adm_no,))
                if cur.fetchone()[0] > 0: skipped+=1; continue
                cur.execute("INSERT INTO admissions (contact_no, class_name, adm_no, name, father_name, dob, residence, registration_no, status) VALUES (?,?,?,?,?,?,?,?, 'Approved')", (contact, class_name, adm_no, name[:100], father, dob, residence, reg))
                conn.commit()
                cur.execute("SELECT COUNT(*) FROM students WHERE enrollment_no=?", (adm_no,))
                if cur.fetchone()[0] == 0:
                    cur.execute("INSERT INTO students (enrollment_no, first_name, father_name, class, dob, mobile, address) VALUES (?,?,?,?,?,?,?)", (adm_no, name[:200], father[:200], class_name[:50], dob, contact, residence[:300]))
                    conn.commit()
                inserted+=1
            except Exception as row_e: print(f"Row {i} error: {row_e}"); skipped+=1; continue
        conn.close()
        return f"<div style='text-align:center;padding:50px'><h2 style='color:green'>{inserted} Uploaded!</h2><p>{skipped} Skipped</p><a href='/admin/dashboard'>Dashboard</a></div>"
    except Exception as e:
        import traceback; traceback.print_exc()
        return f"<h2>ERROR: {e}</h2><pre>{traceback.format_exc()}</pre>"

# --- KEEP REST OF YOUR ROUTES AS THEY WERE, JUST COPY FROM YOUR OLD FILE BELOW THIS LINE ---
# For brevity I am including minimal working routes, paste your other routes (lab, create_user, add_student, results_page, check_result, etc.) from old file but replace TOP/GETDATE/sysobjects if present

#... [PASTE YOUR REMAINING ROUTES HERE: teacher_detail, admin_login, logout, lab_detail, create_user, add_student, results_page, check_result, forgot-password, admission, etc. - they were already SQLite compatible]...

# To make it work quickly, I'm adding back the essential remaining routes from your file (fixed):

@app.route('/teacher/<int:id>')
def teacher_detail(id):
    conn = get_db(); cursor = conn.cursor(); cursor.execute('SELECT * FROM teachers WHERE id=?', (id,)); t = cursor.fetchone(); conn.close(); return render_template('teacher.html', t=t)

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username','').strip(); password = request.form.get('password','').strip()
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("SELECT id, username, password, full_name, role, subject FROM users WHERE username=? AND password=? AND is_active=1", (username, password))
        user = cursor.fetchone(); conn.close()
        if user: session['admin']=True; session['user_id']=user[0]; session['username']=user[1]; session['full_name']=user[3]; session['role']=user[4]; session['subject']=user[5]; return redirect('/admin/dashboard')
        else: return "<h3 style='color:red;text-align:center;margin-top:100px'>Invalid Login<br><a href='/admin'>Try Again</a></h3>"
    return render_template('admin_login.html')

@app.route('/logout')
def logout(): session.clear(); return redirect('/admin')

@app.route('/bulk-upload-students', methods=['GET','POST'])
def bulk_upload_students():
    if not session.get('admin'): return redirect('/admin')
    if request.method == 'POST':
        file = request.files.get('excel_file')
        if not file: return "<h3>No file</h3>"
        try:
            df = pd.read_excel(file); df.columns = [str(c).strip() for c in df.columns]; df = df.fillna('')
            conn = get_db(); cursor = conn.cursor(); count=0; skipped=0
            for _, row in df.iterrows():
                enrollment_no = str(row.get('admission_no', row.get('enrollment_no', row.get('Registration No', row.get('PEN No',''))))).strip().split('.')[0].upper()[:100]
                student_name = str(row.get('student_name', row.get('Student Name',''))).strip()[:200]
                if not enrollment_no or enrollment_no in ('NAN','NONE','') or not student_name or student_name.lower()=='nan': skipped+=1; continue
                cursor.execute("SELECT COUNT(*) FROM students WHERE enrollment_no=?", (enrollment_no,))
                if cursor.fetchone()[0]>0: skipped+=1; continue
                father = str(row.get('father_name', row.get('Father Name',''))).strip()[:200]
                class_name = str(row.get('class', row.get('Class','11th'))).strip()[:50]
                mobile = str(row.get('mobile', row.get('Mobile No',''))).strip().split('.')[0][:20]
                dob_raw = row.get('dob', row.get('Date of Birth','')); dob = None
                if dob_raw and str(dob_raw).lower() not in ('nan','none',''):
                    try: dob = pd.to_datetime(dob_raw).date()
                    except: dob = None
                address = str(row.get('address','')).strip()[:300]
                cursor.execute("INSERT INTO students (enrollment_no, first_name, father_name, class, dob, mobile, address) VALUES (?,?,?,?,?,?,?)", (enrollment_no, student_name, father, class_name, dob, mobile, address))
                count+=1
            conn.commit(); conn.close()
            return f"<div style='text-align:center;padding:50px'><h2 style='color:green'>{count} Added</h2><p>{skipped} Skipped</p><a href='/admin/dashboard'>Dashboard</a></div>"
        except Exception as e: import traceback; traceback.print_exc(); return f"<h3>Error: {e}<br><pre>{traceback.format_exc()}</pre></h3>"
    return """<div style='max-width:600px;margin:50px auto;padding:30px;border:1px solid #ddd'><h2>Bulk Upload Students</h2><form method='POST' enctype='multipart/form-data'><input type='file' name='excel_file' accept='.xlsx,.xls' required><button type='submit'>Upload</button></form><p><a href='/admin/dashboard'>Back</a></p></div>"""

@app.route('/results')
def results_page(): return render_template('results.html')

@app.route('/api/check_result', methods=['POST'])
def check_result():
    reg_no = (request.form.get('reg_no') or '').strip().upper()
    if not reg_no: return "Please enter Reg No!"
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE enrollment_no =?", (reg_no,)); student = cursor.fetchone()
    if not student: conn.close(); return f"<div style='text-align:center;padding:50px'><h2>Student {reg_no} not found</h2><a href='/results'>Back</a></div>"
    cursor.execute("SELECT * FROM monthly_results WHERE reg_no =? ORDER BY id DESC", (reg_no,)); results = cursor.fetchall(); conn.close()
    if not results: return f"<div style='text-align:center;padding:50px'><h2>No results for {reg_no}</h2><a href='/results'>Back</a></div>"
    total_obtained = sum([int(r[4] or 0) for r in results]); total_max = sum([int(r[5] or 100) for r in results])
    percentage = round((total_obtained/total_max)*100,2) if total_max else 0
    return f"<div style='text-align:center;padding:50px'><h2>{student[2]} - {percentage}%</h2><p>{total_obtained}/{total_max}</p><a href='/results'>Back</a></div>"

if not os.path.exists('ghss.db'):
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8080,debug=True)

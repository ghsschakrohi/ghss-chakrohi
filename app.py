from flask import Flask, render_template, request, redirect, session, jsonify, send_file, g
import sqlite3
import os
import io
import base64
import random
import requests
try:
    import pandas as pd
except:
    pd = None
try:
    import qrcode
except:
    qrcode = None
import urllib.parse
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ghss-01131502304'
FAST2SMS_API_KEY = "DnMZlzvTrHgeQqM22KNlVYxAOpWTR61u3DLr4D9zR5JbE5rpQicF606xcCid"
DATABASE = 'school.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        full_name TEXT,
        role TEXT,
        subject TEXT,
        mobile TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        enrollment_no TEXT UNIQUE,
        first_name TEXT,
        last_name TEXT,
        father_name TEXT,
        class_name TEXT,
        section TEXT,
        dob TEXT,
        contact TEXT,
        address TEXT,
        class TEXT,
        mobile TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        designation TEXT,
        subject TEXT,
        exp TEXT,
        qualification TEXT,
        wef TEXT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        activity_date DATE,
        photo TEXT,
        uploaded_by TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS monthly_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reg_no TEXT,
        month TEXT,
        subject TEXT,
        marks INTEGER,
        max_marks INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS admissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contact_no TEXT, aadhar_shilla TEXT, form_date DATE, session TEXT, class_name TEXT,
        adm_no TEXT, stream TEXT, appar_id TEXT, udise_no TEXT, name TEXT, father_name TEXT,
        mother_name TEXT, dob DATE, residence TEXT, caste TEXT, registration_no TEXT,
        ration_type TEXT, sub1 TEXT, sub2 TEXT, sub3 TEXT, sub4 TEXT, sub5 TEXT,
        middle_year TEXT, middle_marks TEXT, middle_per TEXT, middle_sub TEXT, middle_school TEXT, middle_re TEXT,
        sse_year TEXT, sse_marks TEXT, sse_per TEXT, sse_sub TEXT, sse_school TEXT, sse_re TEXT,
        hsp_year TEXT, hsp_marks TEXT, hsp_per TEXT, hsp_sub TEXT, hsp_school TEXT, hsp_re TEXT,
        aadhar_self TEXT, aadhar_father TEXT, aadhar_mother TEXT, father_occupation TEXT,
        father_income TEXT, bank_account TEXT, bank_ifsc TEXT, undertaking_name TEXT,
        undertaking_father TEXT, undertaking_ro TEXT, undertaking_class TEXT,
        status TEXT DEFAULT 'Pending', created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("SELECT * FROM users WHERE username='principal'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password, full_name, role, is_active) VALUES (?,?,?,?,?)",
                    ('principal', 'admin123', 'Principal', 'admin', 1))
        print("Admin user principal created!")

    cur.execute("SELECT COUNT(*) FROM teachers")
    if cur.fetchone()[0] == 0:
        staff = [
            ('Mrs. Pushpa Lochan', 'Principal', 'Administration', '25', 'Masters,B.Ed', ''),
            ('Mr. Gurmeet Singh', 'Sr. Lect Sociology - Vice Principal', 'Sociology', '18', 'Masters, M.Phil,B.Ed', ''),
            ('Mr. Daleep Sharma', 'Sr. Lect Urdu', 'Urdu', '18', 'Masters, P.hd, B.Ed', ''),
            ('Mr. Harveen Singh Sudan', 'Sr. Lect Political Science', 'Pol. Science', '16', 'Masters, M.Phil, B.Ed', ''),
            ('Mrs. Neeru Ratta', 'Sr. Lect Education', 'Education', '16', 'Masters, M.Phil,B.Ed ', ''),
            ('Mrs. Bindu Devi', 'Sr. Lect Zoology', 'Zoology', '16', 'Masters, B.Ed', ''),
            ('Mrs. Bindu Dogra', 'Sr. Lect Hindi', 'Hindi', '16', 'Masters, NET, B.Ed', ''),
            ('Mr. Paramjit Singh', 'Sr. Lect Computer Science', 'Computer Science', '17', 'MCA, M.Phil, B.Ed', '26-01-2023'),
            ('Mrs. Shammi Chib', 'Lecturer Physics', 'Physics', '22', 'M.Sc, B.Ed', ''),
            ('Mr. Shakti Kumar', 'Lecturer Chemistry', 'Chemistry', '33', 'M.Sc, B.Ed', ''),
            ('Mrs. Alka', 'Lecturer English', 'English', '-', 'M.A, B.Ed', ''),
            ('Mrs. Darshan Kour', 'I/C Lect Electronics', 'Electronics', '26', 'M.Sc, B.Ed', ''),
            ('Mr. Rajesh Gupta', 'I/C Lect Botany', 'Botany', '22', 'M.Sc, B.Ed', ''),
            ('Mrs. Ravinder Kour', 'I/C Lect Maths', 'Mathematics', '22', 'M.Sc, B.Ed', ''),
            ('Mrs. Neelam Sudan', 'Master', 'General', '22', 'Masters, B.Ed', ''),
            ('Mr. Ram Lal', 'Master', 'General', '19', 'Masters, B.Ed', ''),
            ('Mr. Shariq Ishaq Mir', 'Teacher', 'General', '19', 'MA, B.Ed', ''),
            ('Mr. Rohit Gupta', 'Teacher', 'General', '10', 'M.Sc, B.Ed', ''),
            ('Mrs. Indu Gandhi', 'Teacher', 'General', '10', 'M.A, B.Ed', ''),
            ('Mr. Sudansh Sharma', 'Teacher', 'General', '10', 'M.Sc, B.Ed', ''),
            ('Mrs. Meenakshi Gupta', 'Teacher', 'General', '10', 'M.A, B.Ed', ''),
            ('Mrs. Rasmeet Kour', 'Teacher', 'General', '10', 'M.Sc, B.Ed', ''),
            ('Mrs. Devinder Kour', 'Sr. Assistant', 'Non-Teaching', '10', 'Graduate', ''),
            ('Mr. Karanjeet Kumar', 'Lab. Assistant', 'Non-Teaching', '20', '12th', ''),
            ('Mr. Rakesh Sharma', 'Lab Assistant', 'Non-Teaching', '20', '12th', ''),
            ('Mrs. Asha Devi', 'Class-IV', 'Non-Teaching', '18', '', ''),
            ('Mrs. Reena Devi', 'Class-IV', 'Non-Teaching', '12', '', ''),
            ('Mr. Ravinder Choudhary', 'Class-IV', 'Non-Teaching', '10', '', ''),
            ('Mr. Shubdeep Akash', 'Class-IV', 'Non-Teaching', '5', 'MA', ''),
        ]
        for s in staff:
            cur.execute("INSERT INTO teachers (name, designation, subject, exp, qualification, wef) VALUES (?,?,?,?,?,?)", s)
        print(f"{len(staff)} teachers inserted")

    conn.commit()
    conn.close()
    os.makedirs('static/uploads/activities', exist_ok=True)
    print("DB init done")

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def home():
    conn = get_db(); cursor = conn.cursor(); cursor.execute('SELECT * FROM teachers ORDER BY id'); teachers = cursor.fetchall()
    try: cursor.execute('SELECT * FROM activities ORDER BY id DESC'); activities = cursor.fetchall()
    except: activities = []
    return render_template('index.html', teachers=teachers, activities=activities)

@app.route('/teacher/<int:id>')
def teacher_detail(id):
    conn = get_db(); cursor = conn.cursor(); cursor.execute('SELECT * FROM teachers WHERE id=?', (id,)); t = cursor.fetchone(); return render_template('teacher.html', t=t)

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username','').strip(); password = request.form.get('password','').strip()
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("SELECT id, username, password, full_name, role, subject FROM users WHERE username=? AND password=? AND is_active=1", (username, password))
        user = cursor.fetchone()
        if user: session['admin']=True; session['user_id']=user[0]; session['username']=user[1]; session['full_name']=user[3]; session['role']=user[4]; session['subject']=user[5]; return redirect('/admin/dashboard')
        else: return "<h3 style='color:red;text-align:center;margin-top:100px'>Invalid Login<br><a href='/admin'>Try Again</a></h3>"
    return render_template('admin_login.html')

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
    except: admissions_count=0; admissions=[]; pending_admissions=[]; approved_admissions=[]
    try:
        cursor.execute("SELECT enrollment_no, first_name FROM students WHERE enrollment_no IS NOT NULL AND TRIM(enrollment_no)!= '' AND TRIM(enrollment_no)!= 'None' AND LENGTH(TRIM(enrollment_no)) > 2 ORDER BY id DESC LIMIT 500")
        students_for_result = cursor.fetchall()
    except: students_for_result = []
    try: cursor.execute('SELECT * FROM activities ORDER BY id DESC LIMIT 20'); activities = cursor.fetchall()
    except: activities = []
    stats = {'students': students_count, 'results': results_count, 'admissions': admissions_count, 'teachers': len(teachers)}
    return render_template('dashboard.html', teachers=teachers, stats=stats, users=all_users, admissions=admissions, pending_admissions=pending_admissions, approved_admissions=approved_admissions, students_for_result=students_for_result, activities=activities, user=session.get('full_name'), role=session.get('role'))

@app.route('/logout')
def logout(): session.clear(); return redirect('/admin')

@app.route('/lab/<lab_name>')
def lab_detail(lab_name):
    labs_data = {'physics': {'name': 'Physics Lab', 'description': 'Physics Lab', 'photo': '/static/physics.jpg'},'chemistry': {'name': 'Chemistry Lab', 'description': 'Chemistry Lab', 'photo': '/static/chemistry.jpg'},'biology': {'name': 'Biology Lab', 'description': 'Biology Lab', 'photo': '/static/biology.jpg'},'computer': {'name': 'Computer Lab', 'description': 'Computer Lab', 'photo': '/static/computer.jpg'}}
    lab = labs_data.get(lab_name.lower(), {'name': lab_name.title()+' Lab', 'description': 'Well equipped lab', 'photo': '/static/naps_2.jpg'})
    return render_template('lab.html', lab=lab)

@app.route('/api/create_user', methods=['POST'])
def create_user():
    if not session.get('admin'): return redirect('/admin')
    if session.get('role','').lower()!= 'admin': return jsonify({"status":"error","msg":"Only Admin"}), 403
    conn = get_db(); cursor = conn.cursor()
    if request.is_json: data = request.get_json(); username=data.get('username'); password=data.get('password'); role=data.get('role'); subject=data.get('subject'); full_name=data.get('full_name') or username; mobile=data.get('mobile')
    else: username=request.form.get('username'); password=request.form.get('password'); role=request.form.get('role'); subject=request.form.get('subject'); full_name=request.form.get('full_name') or username; mobile=request.form.get('mobile')
    try: cursor.execute("INSERT INTO users (username, password, full_name, role, subject, mobile) VALUES (?,?,?,?,?,?)", (username, password, full_name, role, subject, mobile)); conn.commit()
    except Exception as e: print(e)
    if request.is_json: return jsonify({"status":"ok"});
    else: return redirect('/admin/dashboard')

@app.route('/api/add_student', methods=['POST'])
def add_student():
    conn = get_db(); cursor = conn.cursor()
    reg_no = (request.form.get('reg_no') or '').strip().upper()[:100]
    student_name = (request.form.get('name') or '').strip()[:200]
    father_name = (request.form.get('father_name') or '').strip()[:200]
    class_name = (request.form.get('class') or '').strip()[:50]
    dob = request.form.get('dob') or None
    mobile = (request.form.get('mobile') or '').strip()[:20]
    address = (request.form.get('address') or '').strip()[:300]
    try: cursor.execute("INSERT INTO students (enrollment_no, first_name, father_name, class, dob, mobile, address) VALUES (?,?,?,?,?,?,?)", (reg_no, student_name, father_name, class_name, dob, mobile, address)); conn.commit()
    except Exception as e: print(e)
    return redirect('/admin/dashboard')

@app.route('/api/upload_result', methods=['POST'])
def upload_result():
    conn = get_db(); cursor = conn.cursor()
    reg_no = (request.form.get('reg_no') or '').strip().upper()
    month = (request.form.get('month') or '').strip()
    subject = (request.form.get('subject') or '').strip()
    marks = request.form.get('marks') or '0'
    max_marks = request.form.get('max_marks') or '100'
    if not reg_no or reg_no in ('','NONE','NULL','None'): return "<h3 style='text-align:center;color:red'>Select valid student<br><a href='/admin/dashboard'>Back</a></h3>"
    if session.get('role') in ['Teacher','staff'] and session.get('subject'): subject = session.get('subject')
    try:
        cursor.execute("SELECT status FROM admissions WHERE adm_no=?", (reg_no,))
        row = cursor.fetchone()
        if row and str(row[0]).lower() == 'pending': return f"<h3 style='color:red;text-align:center;margin-top:50px'>{reg_no} is PENDING - Approve first<br><a href='/admin/dashboard'>Back</a></h3>"
    except: pass
    try: cursor.execute("INSERT INTO monthly_results (reg_no, month, subject, marks, max_marks) VALUES (?,?,?,?,?)", (reg_no, month, subject, int(marks), int(max_marks))); conn.commit()
    except Exception as e: print(f"Result insert error {e}")
    return redirect('/admin/dashboard')

@app.route('/results')
def results_page(): return render_template('results.html')

@app.route('/api/check_result', methods=['POST'])
def check_result():
    try:
        reg_no = request.form.get('reg_no','').strip().upper()
        if not reg_no:
            return "Please enter Reg No <a href='/results'>Back</a>"

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE enrollment_no =?", (reg_no,))
        student = cursor.fetchone()

        if not student:
            return f"<center style='font-family:Arial;padding:50px'><h2>Student {reg_no} Not Found</h2><a href='/results'>Try Again</a></center>"

        # SAFE - use indexes, print len to debug
        # Table: 0:id,1:enrollment_no,2:first_name,3:last_name,4:father_name,5:class_name,6:section,7:dob,8:contact,9:address,10:class,11:mobile
        try:
            stu_name = student[2] if student[2] else "N/A"
            father_name = student[4] if len(student)>4 and student[4] else (student[3] if len(student)>3 else "N/A")
            class_name = student[10] if len(student)>10 and student[10] else (student[5] if len(student)>5 else "N/A")
            dob = student[7] if len(student)>7 and student[7] else "N/A"
            contact = student[11] if len(student)>11 and student[11] else (student[8] if len(student)>8 else "")
        except:
            stu_name = str(student[2])
            father_name = str(student[3])
            class_name = str(student[4])
            dob = "N/A"
            contact = ""

        cursor.execute("SELECT * FROM monthly_results WHERE reg_no =? ORDER BY month", (reg_no,))
        results = cursor.fetchall()

        if not results:
            return f"<center style='font-family:Arial;padding:50px'><h2>No Results for {reg_no}</h2><p>Upload results first</p><a href='/results'>Back</a></center>"

        total_obt = 0
        total_max = 0
        for r in results:
            try:
                total_obt += int(r[4] or 0)
                total_max += int(r[5] or 0)
            except:
                pass
        perc = round(total_obt*100/total_max, 1) if total_max else 0
        status = "PASS" if perc>=33 else "FAIL"
        grade = "A+" if perc>=90 else "A" if perc>=75 else "B+" if perc>=60 else "B" if perc>=50 else "C" if perc>=33 else "F"

        # QR
        import qrcode, base64, io
        qr = qrcode.make(f"GHSS CHAKROHI | {reg_no} | {stu_name} | {total_obt}/{total_max} {perc}% {status}")
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        qr_b64 = base64.b64encode(buf.getvalue()).decode()

        rows=""
        for i,r in enumerate(results,1):
            rows+=f"<tr><td>{i}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[5]}</td><td><b>{r[4]}</b></td><td>{round((int(r[4] or 0)*100)/(int(r[5] or 10)),0)}%</td></tr>"

        return f"""
        <html><head><title>{reg_no} Result</title><meta name="viewport" content="width=device-width,initial-scale=1">
        <style>
        body{{font-family:Arial;background:#eef2ff;padding:10px}}
       .sheet{{max-width:800px;margin:auto;background:#fff;border:3px solid #0b3d91}}
       .head{{background:#0b3d91;color:#fff;padding:15px;text-align:center}}
       .info{{display:grid;grid-template-columns:1fr 1fr 1fr;padding:15px;gap:10px;background:#f8fafc;border-bottom:2px solid #0b3d91;font-size:13px}}
        table{{width:100%;border-collapse:collapse}} th{{background:#0b3d91;color:#fff;padding:8px;font-size:12px}} td{{padding:8px;border-bottom:1px solid #ddd;font-size:13px;text-align:center}}
       .sum{{display:flex;justify-content:space-between;padding:15px;background:#f1f5f9}}
        @media print{{.btns{{display:none}}}}
        </style></head><body>
        <div class="sheet">
        <div class="head"><h2 style="margin:0">GOVT. HR. SEC. SCHOOL CHAKROHI</h2><div style="font-size:11px">UDISE: 01131502304 | BLOCK - R.S. PURA | JAMMU (J&K) - 181201<br>Academic Session 2026-27 | STATEMENT OF MARKS</div></div>
        <div class="info">
        <div><b>Student:</b> {stu_name}</div><div><b>Father:</b> {father_name}</div><div><b>Reg No:</b> {reg_no}</div>
        <div><b>Class:</b> {class_name}</div><div><b>DOB:</b> {dob}</div><div><b>Contact:</b> {contact}</div>
        </div>
        <table><tr><th>#</th><th>Month</th><th>Subject</th><th>Max</th><th>Obtained</th><th>%</th></tr>{rows}</table>
        <div class="sum">
        <div><b>Total: {total_obt}/{total_max} | {perc}% | Grade: {grade}</b><br><span style="background:{'#dcfce7' if status=='PASS' else '#fee2e2'};color:{'#16a34a' if status=='PASS' else '#dc2626'};padding:3px 10px;border-radius:20px;font-weight:bold">{status} - {grade}</span></div>
        <div style="text-align:center"><img src="data:image/png;base64,{qr_b64}" style="width:80px;border:1px solid #000;padding:2px"><br><span style="font-size:9px">{reg_no}</span></div>
        </div>
        <div style="display:flex;justify-content:space-between;padding:20px;font-size:11px;border-top:2px solid #0b3d91"><div>Class Teacher</div><div>Generated: {__import__('datetime').datetime.now().strftime('%d-%m-%Y')}<br>ghss-chakrohi.onrender.com</div><div>Principal</div></div>
        </div>
        <center class="btns" style="margin:20px"><button onclick="window.print()" style="padding:10px 20px;background:#0b3d91;color:#fff;border:none;border-radius:5px;cursor:pointer">Print</button> <a href="/results" style="padding:10px 20px;background:#fff;border:1px solid #0b3d91;border-radius:5px;text-decoration:none">Back</a></center>
        </body></html>
        """
    except Exception as e:
        import traceback
        return f"<h2>Error: {str(e)}</h2><pre>{traceback.format_exc()}</pre><a href='/results'>Back</a>"    return html@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        conn = get_db(); cursor = conn.cursor(); cursor.execute("SELECT mobile FROM users WHERE username=? AND is_active=1", (username,)); row = cursor.fetchone()
        if row and row[0]:
            mobile=row[0]; otp=str(random.randint(100000,999999)); session['reset_otp']=otp; session['reset_user']=username
            try: msg=f"OTP {otp}"; url=f"https://www.fast2sms.com/dev/bulkV2?authorization={FAST2SMS_API_KEY}&route=q&message={urllib.parse.quote(msg)}&numbers={mobile}&flash=0"; requests.get(url, timeout=10)
            except: pass
            return f"<div style='text-align:center;padding:50px'><h2 style='color:green'>OTP Sent to {mobile[:2]}****</h2><a href='/verify-otp'>Verify</a></div>"
        else: return "<h3 style='color:red;text-align:center'>User not found</h3>"
    return render_template('forgot_password.html')

@app.route('/verify-otp', methods=['GET','POST'])
def verify_otp():
    if request.method == 'POST':
        entered=request.form.get('otp','').strip(); new_pass=request.form.get('new_password','').strip(); confirm=request.form.get('confirm_password','').strip()
        if new_pass!=confirm: return "<h3>Passwords mismatch</h3>"
        if entered==session.get('reset_otp'): conn=get_db(); cursor=conn.cursor(); cursor.execute("UPDATE users SET password=? WHERE username=?", (new_pass, session.get('reset_user'))); conn.commit(); return "<h2 style='text-align:center;color:green'>Password Reset Done <a href='/admin'>Login</a></h2>"
        else: return "<h3>Invalid OTP</h3>"
    return """<div style='max-width:400px;margin:80px auto;padding:20px;border:1px solid #ccc'><h2>Verify OTP</h2><form method='POST'><input name='otp' placeholder='OTP' required style='width:100%;padding:10px'><br><input type='password' name='new_password' placeholder='New Password' required style='width:100%;padding:10px;margin-top:10px'><br><input type='password' name='confirm_password' placeholder='Confirm' required style='width:100%;padding:10px;margin-top:10px'><br><button style='width:100%;padding:10px;background:#0b3d91;color:white;margin-top:10px'>Reset</button></form></div>"""

@app.route('/admission')
def admission_form(): return render_template('admission.html')

@app.route('/api/submit_admission', methods=['POST'])
def submit_admission():
    conn = get_db(); cursor = conn.cursor()
    data = request.form; adm_no = data.get('adm_no') or f"GHSS{datetime.now().year}{random.randint(1000,9999)}"
    adm_no = adm_no.upper().strip()[:50]
    cursor.execute("""INSERT INTO admissions (contact_no, aadhar_shilla, form_date, session, class_name, adm_no, stream, appar_id, udise_no, name, father_name, mother_name, dob, residence, caste, registration_no, ration_type, sub1, sub2, sub3, sub4, sub5, middle_year, middle_marks, middle_per, middle_sub, middle_school, middle_re, sse_year, sse_marks, sse_per, sse_sub, sse_school, sse_re, hsp_year, hsp_marks, hsp_per, hsp_sub, hsp_school, hsp_re, aadhar_self, aadhar_father, aadhar_mother, father_occupation, father_income, bank_account, bank_ifsc, undertaking_name, undertaking_father, undertaking_ro, undertaking_class) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (data.get('contact_no'), data.get('aadhar_shilla'), data.get('form_date') or datetime.now().date(), data.get('session'), data.get('class_name'), adm_no, data.get('stream'), data.get('appar_id'), data.get('udise_no') or '01131502304', data.get('name'), data.get('father_name'), data.get('mother_name'), data.get('dob') or None, data.get('residence'), data.get('caste'), data.get('registration_no'), data.get('ration_type'), data.get('sub1'), data.get('sub2'), data.get('sub3'), data.get('sub4'), data.get('sub5'), data.get('middle_year'), data.get('middle_marks'), data.get('middle_per'), data.get('middle_sub'), data.get('middle_school'), data.get('middle_re'), data.get('sse_year'), data.get('sse_marks'), data.get('sse_per'), data.get('sse_sub'), data.get('sse_school'), data.get('sse_re'), data.get('hsp_year'), data.get('hsp_marks'), data.get('hsp_per'), data.get('hsp_sub'), data.get('hsp_school'), data.get('hsp_re'), data.get('aadhar_self'), data.get('aadhar_father'), data.get('aadhar_mother'), data.get('father_occupation'), data.get('father_income'), data.get('bank_account'), data.get('bank_ifsc'), data.get('undertaking_name'), data.get('undertaking_father'), data.get('undertaking_ro'), data.get('undertaking_class')))
    conn.commit()
    return f"<h2>Admission {adm_no} Submitted - Pending</h2><a href='/admin/dashboard'>Back</a>"

@app.route('/admin/admissions')
def admissions_list():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    try: cursor.execute('SELECT * FROM admissions ORDER BY created_at DESC'); admissions = cursor.fetchall()
    except: admissions = []
    return render_template('admissions_list.html', admissions=admissions, user=session.get('full_name'))

@app.route('/api/delete_admission/<int:id>')
def delete_admission(id):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor(); cursor.execute('DELETE FROM admissions WHERE id=?', (id,)); conn.commit(); return redirect('/admin/admissions')

@app.route('/admin/approve/<adm_no>')
def approve_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("UPDATE admissions SET status='Approved' WHERE adm_no=?", (adm_no,)); conn.commit()
    try:
        cursor.execute("INSERT INTO students (enrollment_no, first_name, father_name, class) SELECT adm_no, name, father_name, class_name FROM admissions WHERE adm_no=? AND adm_no NOT IN (SELECT enrollment_no FROM students)", (adm_no,))
        conn.commit()
    except: pass
    return redirect('/admin/admissions')

@app.route('/admin/reject/<adm_no>')
def reject_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("UPDATE admissions SET status='Rejected' WHERE adm_no=?", (adm_no,)); conn.commit()
    return redirect('/admin/admissions')

@app.route('/api/submit_admission_view/<int:id>')
def view_admission_by_id(id):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute('SELECT * FROM admissions WHERE id=?', (id,))
    row = cursor.fetchone()
    if not row: return "Record not found"
    cols = [d[0] for d in cursor.description]
    data = dict(zip(cols, row))
    return render_template('admission_view.html', data=data, adm_no=data.get('adm_no'), user=session.get('full_name'))

@app.route('/admin/view/<adm_no>')
def view_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM admissions WHERE adm_no=?", (adm_no,))
    row = cursor.fetchone()
    if not row: return "Record not found"
    cols = [d[0] for d in cursor.description]
    data = dict(zip(cols, row))
    return render_template('admission_view.html', data=data, adm_no=adm_no, user=session.get('full_name'))

@app.route('/api/update_user_mobile', methods=['POST'])
def update_user_mobile():
    if session.get('role','').lower()!= 'admin': return jsonify({"status":"error"}), 403
    data = request.get_json(); conn=get_db(); cur=conn.cursor(); cur.execute("UPDATE users SET mobile=? WHERE username=?", (data.get('mobile'), data.get('username'))); conn.commit(); return jsonify({"status":"ok"})

@app.route('/activities')
def activities_page():
    conn=get_db(); cursor=conn.cursor()
    try: cursor.execute("SELECT * FROM activities ORDER BY id DESC"); acts = cursor.fetchall()
    except: acts = []
    return render_template('activities.html', activities=acts)

@app.route('/api/upload_activity', methods=['POST'])
def upload_activity():
    if not session.get('admin'): return redirect('/admin')
    title = request.form.get('title','').strip(); desc = request.form.get('description','').strip(); date = request.form.get('activity_date')
    if not title: return "<h3>Title required</h3>"
    photo_path = ""
    if 'photo' in request.files:
        f = request.files['photo']
        if f.filename:
            os.makedirs('static/uploads/activities', exist_ok=True)
            filename = f"act_{int(time.time())}_{f.filename.replace(' ', '_')}"
            save_path = os.path.join('static/uploads/activities', filename)
            f.save(save_path); photo_path = f"/static/uploads/activities/{filename}"
    conn=get_db(); cursor=conn.cursor()
    try: cursor.execute("INSERT INTO activities (title, description, activity_date, photo, uploaded_by) VALUES (?,?,?,?,?)", (title, desc, date or datetime.now().date(), photo_path, session.get('username'))); conn.commit()
    except Exception as e: return f"DB Error {e}"
    return redirect('/admin/dashboard')

@app.route('/api/delete_activity/<int:id>')
def delete_activity(id):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor(); cursor.execute('DELETE FROM activities WHERE id=?', (id,)); conn.commit(); return redirect('/admin/dashboard')

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
                student_name = str(row.get('student_name', row.get('Student Name', row.get('Student_Name','')))).strip()[:200]
                if not enrollment_no or enrollment_no in ('NAN','NONE','') or not student_name or student_name.lower()=='nan': skipped+=1; continue
                cursor.execute("SELECT COUNT(*) FROM students WHERE enrollment_no=?", (enrollment_no,))
                if cursor.fetchone()[0]>0: skipped+=1; continue
                father = str(row.get('father_name', row.get('Father Name',''))).strip()[:200]
                class_name = str(row.get('class', row.get('Class','11th'))).strip()[:50]
                mobile = str(row.get('mobile', row.get('Mobile No', row.get('Contact No','')))).strip().split('.')[0][:20]
                dob_raw = row.get('dob', row.get('Date of Birth',''))
                dob = None
                if dob_raw and str(dob_raw).lower() not in ('nan','none',''):
                    try: dob = pd.to_datetime(dob_raw).date()
                    except: dob = None
                address = str(row.get('address', row.get('Residence',''))).strip()[:300]
                cursor.execute("INSERT INTO students (enrollment_no, first_name, father_name, class, dob, mobile, address) VALUES (?,?,?,?,?,?,?)", (enrollment_no, student_name, father, class_name, dob, mobile, address))
                count+=1
            conn.commit()
            return f"<div style='text-align:center;padding:50px'><h2 style='color:green'>{count} Added</h2><p>{skipped} Skipped</p><a href='/admin/dashboard'>Dashboard</a></div>"
        except Exception as e: import traceback; traceback.print_exc(); return f"<h3>Error: {e}<br><pre>{traceback.format_exc()}</pre></h3>"
    return """<div style='max-width:600px;margin:50px auto;padding:30px;border:1px solid #ddd;border-radius:10px;font-family:Arial'><h2 style='text-align:center;color:#0b3d91'>Bulk Upload Students</h2><form method='POST' enctype='multipart/form-data'><input type='file' name='excel_file' accept='.xlsx,.xls' required style='width:100%;padding:12px;border:2px dashed #0b3d91;margin:15px 0'><button type='submit' style='width:100%;padding:14px;background:#0b3d91;color:white;border:none;border-radius:6px'>Upload</button></form><p style='text-align:center'><a href='/admin/dashboard'>Back</a></p></div>"""

@app.route('/download-template')
def download_template():
    cols = ['S.No','PEN No','Form Date','Session','Class','Stream / Option','UDISE No','Contact No','Aadhar Shilla','APPAR ID','Student Name','Father Name','Mother Name','Date of Birth','Residence','Caste','Registration No','Ration Card Type','Subjects','Exam Passed','Year of Passing','Marks Obtained','Percentage','School Passed From','Aadhar Number (Self)','Aadhar Number (Father)','Aadhar Number (Mother)','Father Occupation','Father Monthly Income','Bank A/C No','Mobile No']
    df = pd.DataFrame(columns=cols); path = "GHSS_Template.xlsx"; df.to_excel(path, index=False); return send_file(path, as_attachment=True)

@app.route('/bulk-upload-admissions', methods=['POST'])
def bulk_upload_admissions():
    if not session.get('admin'): return redirect('/admin')
    try:
        file = request.files.get('excel_file')
        if not file: return "<h2>No file</h2><a href='/admin/dashboard'>Back</a>"
        df = pd.read_excel(file); df.columns = [str(c).strip() for c in df.columns]; df = df.fillna('')
        conn = get_db(); cur = conn.cursor(); inserted=0; skipped=0
        for i, row in df.iterrows():
            try:
                name = str(row.get('Student Name', row.get('Student_Name', row.get('Name','')))).strip()
                if not name or name.lower() in ('nan','none',''): skipped+=1; continue
                father = str(row.get('Father Name', row.get('Father_Name',''))).strip()[:100]
                class_name = str(row.get('Class','11th')).strip()[:20]
                contact = str(row.get('Contact No', row.get('Mobile No', row.get('Mobile_No','')))).strip().split('.')[0][:20]
                reg = str(row.get('Registration No', row.get('PEN No', row.get('Registration_No','')))).strip().split('.')[0][:50]
                residence = str(row.get('Residence','')).strip()[:200]
                dob_val = row.get('Date of Birth', row.get('DOB',''))
                dob = None
                if dob_val and str(dob_val).lower() not in ('nan','none',''):
                    try: dob = pd.to_datetime(dob_val).date()
                    except: dob = None
                adm_no = reg.upper() if reg and reg.lower() not in ('nan','none','') else f"GHSS{datetime.now().year}{random.randint(1000,9999)}"
                adm_no = adm_no.upper().strip()[:50]
                if len(adm_no) < 3: adm_no = f"GHSS{datetime.now().year}{random.randint(1000,9999)}"
                cur.execute("SELECT COUNT(*) FROM admissions WHERE adm_no=?", (adm_no,))
                if cur.fetchone()[0] > 0: skipped+=1; continue
                cur.execute("INSERT INTO admissions (contact_no, class_name, adm_no, name, father_name, dob, residence, registration_no, status, created_at) VALUES (?,?,?,?,?,?,?,?, 'Approved', CURRENT_TIMESTAMP)", (contact, class_name, adm_no, name[:100], father, dob, residence, reg))
                conn.commit()
                cur.execute("SELECT COUNT(*) FROM students WHERE enrollment_no=?", (adm_no,))
                if cur.fetchone()[0] == 0:
                    cur.execute("INSERT INTO students (enrollment_no, first_name, father_name, class, dob, mobile, address) VALUES (?,?,?,?,?,?,?)", (adm_no, name[:200], father[:200], class_name[:50], dob, contact, residence[:300]))
                    conn.commit()
                inserted+=1
            except Exception as row_e: print(f"Row {i} error: {row_e}"); skipped+=1; continue
        return f"<div style='text-align:center;padding:50px;font-family:Arial'><h2 style='color:green'>{inserted} Students Uploaded!</h2><p>{skipped} Skipped</p><a href='/admin/dashboard'>Go to Dashboard</a></div>"
    except Exception as e:
        import traceback; traceback.print_exc()
        return f"<h2>ERROR: {e}</h2><pre>{traceback.format_exc()}</pre><a href='/admin/dashboard'>Back</a>"

@app.route('/admin/student_report')
def student_report():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT name, father_name, class_name, contact_no, stream, dob, registration_no, adm_no, caste FROM admissions WHERE status='Approved' ORDER BY class_name, name")
    rows = cursor.fetchall()
    return render_template('student_report.html', rows=rows, user=session.get('full_name'), role=session.get('role'))

@app.route('/admin/student_report/excel')
def student_report_excel():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT name as [Student Name], father_name as [Father Name], class_name as [Class], contact_no as [Contact], stream as [Stream], dob as [DOB], registration_no as [Reg No], adm_no as [Adm No], caste as [Category] FROM admissions WHERE status='Approved' ORDER BY class_name, name")
    rows = cursor.fetchall(); cols = [d[0] for d in cursor.description]
    df = pd.DataFrame([tuple(r) for r in rows], columns=cols)
    os.makedirs('static', exist_ok=True)
    path = "static/Student_Report.xlsx"; df.to_excel(path, index=False)
    return send_file(path, as_attachment=True)

@app.route('/admin/edit/<adm_no>')
def edit_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM admissions WHERE adm_no=?", (adm_no,))
    row = cursor.fetchone()
    if not row: return "Record not found"
    cols = [d[0] for d in cursor.description]
    data = dict(zip(cols, row))
    return render_template('admission_edit.html', data=data, adm_no=adm_no, user=session.get('full_name'))

@app.route('/api/update_admission/<adm_no>', methods=['POST'])
def update_admission_route(adm_no):
    if not session.get('admin'): return redirect('/admin')
    data = request.form
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE admissions SET
            contact_no=?, aadhar_shilla=?, form_date=?, session=?, class_name=?, stream=?, appar_id=?, udise_no=?,
            name=?, father_name=?, mother_name=?, dob=?, residence=?, caste=?, registration_no=?, ration_type=?,
            sub1=?, sub2=?, sub3=?, sub4=?, sub5=?,
            middle_year=?, middle_marks=?, middle_per=?, middle_sub=?, middle_school=?, middle_re=?,
            sse_year=?, sse_marks=?, sse_per=?, sse_sub=?, sse_school=?, sse_re=?,
            hsp_year=?, hsp_marks=?, hsp_per=?, hsp_sub=?, hsp_school=?, hsp_re=?,
            aadhar_self=?, aadhar_father=?, aadhar_mother=?, father_occupation=?, father_income=?, bank_account=?, bank_ifsc=?
            WHERE adm_no=?
        """, (
            data.get('contact_no'), data.get('aadhar_shilla'), data.get('form_date') or None, data.get('session'), data.get('class_name'), data.get('stream'), data.get('appar_id'), data.get('udise_no'),
            data.get('name'), data.get('father_name'), data.get('mother_name'), data.get('dob') or None, data.get('residence'), data.get('caste'), data.get('registration_no'), data.get('ration_type'),
            data.get('sub1'), data.get('sub2'), data.get('sub3'), data.get('sub4'), data.get('sub5'),
            data.get('middle_year'), data.get('middle_marks'), data.get('middle_per'), data.get('middle_sub'), data.get('middle_school'), data.get('middle_re'),
            data.get('sse_year'), data.get('sse_marks'), data.get('sse_per'), data.get('sse_sub'), data.get('sse_school'), data.get('sse_re'),
            data.get('hsp_year'), data.get('hsp_marks'), data.get('hsp_per'), data.get('hsp_sub'), data.get('hsp_school'), data.get('hsp_re'),
            data.get('aadhar_self'), data.get('aadhar_father'), data.get('aadhar_mother'), data.get('father_occupation'), data.get('father_income'), data.get('bank_account'), data.get('bank_ifsc'),
            adm_no
        ))
        conn.commit()
        try:
            cursor.execute("UPDATE students SET first_name=?, father_name=?, class=?, mobile=?, address=? WHERE enrollment_no=?",
                (data.get('name'), data.get('father_name'), data.get('class_name'), data.get('contact_no'), data.get('residence'), adm_no))
            conn.commit()
        except: pass
    except Exception as e: print(f"Update error {e}")
    return redirect(f'/admin/view/{adm_no}')

# Startup - Create DB if missing
print("Checking DB...")
if not os.path.exists(DATABASE):
    print("Creating school.db first time...")
    init_db()
else:
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

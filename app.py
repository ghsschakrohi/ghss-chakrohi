from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import pyodbc
import qrcode
import os
import io
import base64
import random
import requests
import pandas as pd
import urllib.parse
import time
import pymssql
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ghss-01131502304'
FAST2SMS_API_KEY = "DnMZlzvTrHgeQqM22KNlVYxAOpWTR61u3DLr4D9zR5JbE5rpQicF606xcCid"

def get_db():
    import pymssql
    # TEMP - Change these to your Azure SQL details later
    conn = pymssql.connect(
        server='your_server.database.windows.net',
        user='your_username',
        password='your_password',
        database='GHSS_Chakrohi_DB'
    )
    return conn
    
def init_db():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("IF OBJECT_ID('teachers', 'U') IS NOT NULL DROP TABLE teachers")
    cursor.execute('''CREATE TABLE teachers (id INT IDENTITY(1,1) PRIMARY KEY, name NVARCHAR(200), designation NVARCHAR(200), subject NVARCHAR(100), exp int, qualification NVARCHAR(100), wef NVARCHAR(100))''')
    staff = [('Mrs. Pushpa Lochan', 'Principal', 'Administration', '25', 'Masters,B.Ed', ''),('Mr. Gurmeet Singh', 'Sr. Lect Sociology - Vice Principal', 'Sociology', '18', 'Masters, M.Phil,B.Ed', ''),('Mr. Daleep Sharma', 'Sr. Lect Urdu', 'Urdu', '18', 'Masters, P.hd, B.Ed', ''),('Mr. Harveen Singh Sudan', 'Sr. Lect Political Science', 'Pol. Science', '16', 'Masters, M.Phil, B.Ed', ''),('Mrs. Neeru Ratta', 'Sr. Lect Education', 'Education', '16', 'Masters, M.Phil,B.Ed ', ''),('Mrs. Bindu Devi', 'Sr. Lect Zoology', 'Zoology', '16', 'Masters, B.Ed', ''),('Mrs. Bindu Dogra', 'Sr. Lect Hindi', 'Hindi', '16', 'Masters, NET, B.Ed', ''),('Mr. Paramjit Singh', 'Sr. Lect Computer Science', 'Computer Science', '17', 'MCA, M.Phil, B.Ed', '26-01-2023'),('Mrs. Shammi Chib', 'Lecturer Physics', 'Physics', '22', 'M.Sc, B.Ed', ''),('Mr. Shakti Kumar', 'Lecturer Chemistry', 'Chemistry', '33', 'M.Sc, B.Ed', ''),('Mrs. Alka', 'Lecturer English', 'English', '-', 'M.A, B.Ed', ''),('Mrs. Darshan Kour', 'I/C Lect Electronics', 'Electronics', '26', 'M.Sc, B.Ed', ''),('Mr. Rajesh Gupta', 'I/C Lect Botany', 'Botany', '22', 'M.Sc, B.Ed', ''),('Mrs. Ravinder Kour', 'I/C Lect Maths', 'Mathematics', '22', 'M.Sc, B.Ed', ''),('Mrs. Neelam Sudan', 'Master', 'General', '22', 'Masters, B.Ed', ''),('Mr. Ram Lal', 'Master', 'General', '19', 'Masters, B.Ed', ''),('Mr. Shariq Ishaq Mir', 'Teacher', 'General', '19', 'MA, B.Ed', ''),('Mr. Rohit Gupta', 'Teacher', 'General', '10', 'M.Sc, B.Ed', ''),('Mrs. Indu Gandhi', 'Teacher', 'General', '10', 'M.A, B.Ed', ''),('Mr. Sudansh Sharma', 'Teacher', 'General', '10', 'M.Sc, B.Ed', ''),('Mrs. Meenakshi Gupta', 'Teacher', 'General', '10', 'M.A, B.Ed', ''),('Mrs. Rasmeet Kour', 'Teacher', 'General', '10', 'M.Sc, B.Ed', ''),('Mrs. Devinder Kour', 'Sr. Assistant', 'Non-Teaching', '10', 'Graduate', ''),('Mr. Karanjeet Kumar', 'Lab. Assistant', 'Non-Teaching', '20', '12th', ''),('Mr. Rakesh Sharma', 'Lab Assistant', 'Non-Teaching', '20', '12th', ''),('Mrs. Asha Devi', 'Class-IV', 'Non-Teaching', '18', '', ''),('Mrs. Reena Devi', 'Class-IV', 'Non-Teaching', '12', '', ''),('Mr. Ravinder Choudhary', 'Class-IV', 'Non-Teaching', '10', '', ''),('Mr. Shubdeep Akash', 'Class-IV', 'Non-Teaching', '5', 'MA', ''),]
    for s in staff: cursor.execute("INSERT INTO teachers (name, designation, subject, exp, qualification, wef) VALUES (?,?,?,?,?,?)", s[0], s[1], s[2], s[3], s[4], s[5])
    cursor.execute("""IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U') CREATE TABLE users (id INT IDENTITY(1,1) PRIMARY KEY, username NVARCHAR(100) UNIQUE, password NVARCHAR(100), full_name NVARCHAR(200), role NVARCHAR(50), subject NVARCHAR(100), mobile NVARCHAR(20), is_active INT DEFAULT 1, created_at DATETIME DEFAULT GETDATE())""")
    cursor.execute("""IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='students' AND xtype='U') CREATE TABLE students (id INT IDENTITY(1,1) PRIMARY KEY, enrollment_no NVARCHAR(100) UNIQUE, first_name NVARCHAR(200), father_name NVARCHAR(200), class NVARCHAR(50), dob DATE, mobile NVARCHAR(20), address NVARCHAR(300), created_at DATETIME DEFAULT GETDATE())""")
    cursor.execute("""IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='activities' AND xtype='U') CREATE TABLE activities (id INT IDENTITY(1,1) PRIMARY KEY, title NVARCHAR(300) NOT NULL, description NVARCHAR(MAX), activity_date DATE, photo NVARCHAR(500), uploaded_by NVARCHAR(100), created_at DATETIME DEFAULT GETDATE())""")
    conn.commit(); conn.close(); os.makedirs('static/uploads/activities', exist_ok=True)

@app.route('/')
def home():
    conn = get_db(); cursor = conn.cursor(); cursor.execute('SELECT * FROM teachers ORDER BY id'); teachers = cursor.fetchall()
    try: cursor.execute('SELECT * FROM activities ORDER BY id DESC'); activities = cursor.fetchall()
    except: activities = []
    conn.close(); return render_template('index.html', teachers=teachers, activities=activities)

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
        cursor.execute("SELECT TOP 10 * FROM admissions WHERE status='Pending' ORDER BY created_at DESC"); pending_admissions = cursor.fetchall()
        cursor.execute("SELECT TOP 10 * FROM admissions WHERE status='Approved' ORDER BY created_at DESC"); approved_admissions = cursor.fetchall()
        admissions = pending_admissions
    except: admissions_count=0; admissions=[]; pending_admissions=[]; approved_admissions=[]
    try:
        cursor.execute("SELECT TOP 500 enrollment_no, first_name FROM students WHERE enrollment_no IS NOT NULL AND LTRIM(RTRIM(enrollment_no))!= '' AND LTRIM(RTRIM(enrollment_no))!= 'None' AND LEN(LTRIM(RTRIM(enrollment_no))) > 2 ORDER BY id DESC")
        students_for_result = cursor.fetchall()
    except: students_for_result = []
    try: cursor.execute('SELECT TOP 20 * FROM activities ORDER BY id DESC'); activities = cursor.fetchall()
    except: activities = []
    conn.close()
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
    conn.close()
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
    conn.close(); return redirect('/admin/dashboard')

@app.route('/api/upload_result', methods=['POST'])
def upload_result():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("""IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='monthly_results' AND xtype='U') CREATE TABLE monthly_results (id INT IDENTITY(1,1) PRIMARY KEY, reg_no NVARCHAR(50), month NVARCHAR(50), subject NVARCHAR(100), marks INT, max_marks INT, created_at DATETIME DEFAULT GETDATE())"""); conn.commit()
    reg_no = (request.form.get('reg_no') or '').strip().upper()
    month = (request.form.get('month') or '').strip()
    subject = (request.form.get('subject') or '').strip()
    marks = request.form.get('marks') or '0'
    max_marks = request.form.get('max_marks') or '100'
    if not reg_no or reg_no in ('','NONE','NULL','None'): conn.close(); return "<h3 style='text-align:center;color:red'>Select valid student<br><a href='/admin/dashboard'>Back</a></h3>"
    if session.get('role') in ['Teacher','staff'] and session.get('subject'): subject = session.get('subject')
    try:
        cursor.execute("SELECT status FROM admissions WHERE adm_no=?", (reg_no,))
        row = cursor.fetchone()
        if row and str(row[0]).lower() == 'pending': conn.close(); return f"<h3 style='color:red;text-align:center;margin-top:50px'>{reg_no} is PENDING - Approve first<br><a href='/admin/dashboard'>Back</a></h3>"
    except: pass
    try: cursor.execute("INSERT INTO monthly_results (reg_no, month, subject, marks, max_marks) VALUES (?,?,?,?,?)", (reg_no, month, subject, int(marks), int(max_marks))); conn.commit()
    except Exception as e: print(f"Result insert error {e}")
    conn.close(); return redirect('/admin/dashboard')

@app.route('/results')
def results_page(): return render_template('results.html')

@app.route('/api/check_result', methods=['POST'])
def check_result():
    if not request.form.get('reg_no'): return "Please enter Reg No!"
    reg_no = request.form.get('reg_no').strip().upper()
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE enrollment_no =?", (reg_no,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return f"<div style='text-align:center;padding:50px'><h2 style='color:red'>Student {reg_no} not found</h2><a href='/results'>Back</a></div>"
    cursor.execute("SELECT * FROM monthly_results WHERE reg_no =? ORDER BY id DESC", (reg_no,))
    results = cursor.fetchall(); conn.close()
    if not results:
        return f"<div style='text-align:center;padding:50px'><h2>No results for {reg_no}</h2><a href='/results'>Back</a></div>"
    total_obtained = sum([int(r.marks or 0) for r in results])
    total_max = sum([int(r.max_marks or 100) for r in results])
    percentage = round((total_obtained/total_max)*100, 2) if total_max else 0
    status = "PASS" if percentage >= 33 else "FAIL"
    grade = "A+" if percentage>=90 else "A" if percentage>=75 else "B+" if percentage>=60 else "B" if percentage>=50 else "C" if percentage>=33 else "F"
    badge_color = "#16a34a" if status == "PASS" else "#dc2626"
    qr_data = f"GHSS CHAKROHI VERIFIED\nReg: {reg_no}\nName: {student.first_name}\nMarks: {total_obtained}/{total_max} {percentage}% {status}"
    qr = qrcode.QRCode(version=1, box_size=4, border=1); qr.add_data(qr_data); qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white"); buffered = io.BytesIO(); img.save(buffered, format="PNG")
    qr_b64 = base64.b64encode(buffered.getvalue()).decode()
    rows_html = "".join([f"<tr><td>{i}</td><td>{r.month}</td><td><b>{r.subject}</b></td><td>{r.max_marks}</td><td><b>{r.marks}</b></td></tr>" for i,r in enumerate(results,1)])
    html = f"""
    <html><head><title>Marksheet {reg_no}</title><meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        *{{box-sizing:border-box;margin:0;padding:0}}
        body{{font-family:'Segoe UI',Arial,sans-serif;background:#f1f5f9;padding:20px}}
      .sheet{{background:#fff;max-width:750px;margin:0 auto;border:1px solid #0b3d91;border-radius:8px;overflow:hidden;box-shadow:0 4px 15px rgba(0,0,0,0.1)}}
      .header{{background:#0b3d91;color:#fff;padding:18px 22px;text-align:center}}
      .header h1{{font-size:20px}}.header p{{font-size:12px;opacity:0.9;margin-top:4px}}
      .student-box{{display:flex;justify-content:space-between;padding:16px 22px;background:#f8fafc;border-bottom:1px solid #e2e8f0;flex-wrap:wrap;gap:10px}}
      .student-box div{{font-size:13px;line-height:20px}}.student-box b{{color:#0b3d91}}
        table{{width:100%;border-collapse:collapse}} th{{background:#0b3d91;color:#fff;padding:10px 12px;font-size:12px;text-align:left}} td{{padding:10px 12px;font-size:13px;border-bottom:1px solid #e2e8f0}}
      .total-bar{{display:flex;justify-content:space-between;align-items:center;padding:14px 22px;background:#f8fafc;border-top:2px solid #0b3d91;flex-wrap:wrap;gap:12px}}
      .badge{{padding:6px 14px;border-radius:20px;font-weight:bold;font-size:12px;color:#fff;background:{badge_color}}}
      .qr-area{{display:flex;align-items:center;gap:18px}}.qr-area img{{width:85px;height:85px;border:1px solid #ddd;padding:3px;background:#fff}}
      .btns{{max-width:750px;margin:18px auto;text-align:center}}.btn{{padding:10px 20px;border:none;border-radius:6px;font-weight:bold;cursor:pointer;margin:5px;text-decoration:none;display:inline-block;font-size:13px}}
        @media print{{.btns{{display:none}}}}
    </style></head><body>
    <div class="sheet" id="marksheet">
        <div class="header"><h1>GOVT. HR. SEC. SCHOOL CHAKROHI</h1><p>UDISe: 01131502304 | Monthly Test Result - 2026</p></div>
        <div class="student-box">
            <div><b>Student:</b> {student.first_name}<br><b>Father:</b> {student.father_name}<br><b>Class:</b> {student[4]}</div>
            <div><b>Reg No:</b> {reg_no}<br><b>DOB:</b> {student.dob}<br><b>Grade:</b> {grade} ({percentage}%)</div>
            <div><b>Session:</b> 2026-27<br><b>Status:</b> <span class="badge">{status}</span><br><b>Total:</b> {total_obtained}/{total_max}</div>
        </div>
        <table><tr><th>#</th><th>Month</th><th>Subject</th><th>Max</th><th>Obt</th></tr>{rows_html}</table>
        <div class="total-bar">
            <div><b>Total: {total_obtained} / {total_max}</b> | <b>{percentage}%</b> <span class="badge">{status} - {grade}</span></div>
            <div class="qr-area"><div style="text-align:center"><img src="data:image/png;base64,{qr_b64}"><div style="font-size:9px;margin-top:2px">Scan to Verify</div></div></div>
        </div>
    </div>
    <div class="btns">
        <button onclick="window.print()" class="btn" style="background:#0b3d91;color:#fff">Print</button>
        <button onclick="downloadPDF()" class="btn" style="background:#16a34a;color:#fff">Download PDF</button>
        <a href="/results" class="btn" style="background:#e2e8f0;color:#111">Check Another</a>
    </div>
    <script>
    function downloadPDF(){{
        var el=document.getElementById('marksheet');
        var opt={{margin:5, filename:'GHSS_{reg_no}_Result.pdf', image:{{type:'jpeg',quality:0.98}}, html2canvas:{{scale:2, useCORS:true}}, jsPDF:{{unit:'mm',format:'a4',orientation:'portrait'}}}};
        html2pdf().set(opt).from(el).save();
    }}
    </script>
    </body></html>
    """
    return html

@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        conn = get_db(); cursor = conn.cursor(); cursor.execute("SELECT mobile FROM users WHERE username=? AND is_active=1", (username,)); row = cursor.fetchone(); conn.close()
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
        if entered==session.get('reset_otp'): conn=get_db(); cursor=conn.cursor(); cursor.execute("UPDATE users SET password=? WHERE username=?", (new_pass, session.get('reset_user'))); conn.commit(); conn.close(); session.clear(); return "<h2 style='text-align:center;color:green'>Password Reset Done <a href='/admin'>Login</a></h2>"
        else: return "<h3>Invalid OTP</h3>"
    return """<div style='max-width:400px;margin:80px auto;padding:20px;border:1px solid #ccc'><h2>Verify OTP</h2><form method='POST'><input name='otp' placeholder='OTP' required style='width:100%;padding:10px'><br><input type='password' name='new_password' placeholder='New Password' required style='width:100%;padding:10px;margin-top:10px'><br><input type='password' name='confirm_password' placeholder='Confirm' required style='width:100%;padding:10px;margin-top:10px'><br><button style='width:100%;padding:10px;background:#0b3d91;color:white;margin-top:10px'>Reset</button></form></div>"""

@app.route('/admission')
def admission_form(): return render_template('admission.html')

@app.route('/api/submit_admission', methods=['POST'])
def submit_admission():
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("""IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='admissions' AND xtype='U') CREATE TABLE admissions (id INT IDENTITY(1,1) PRIMARY KEY, contact_no NVARCHAR(20), aadhar_shilla NVARCHAR(50), form_date DATE, session NVARCHAR(20), class_name NVARCHAR(20), adm_no NVARCHAR(50), stream NVARCHAR(20), appar_id NVARCHAR(50), udise_no NVARCHAR(50), name NVARCHAR(100), father_name NVARCHAR(100), mother_name NVARCHAR(100), dob DATE, residence NVARCHAR(200), caste NVARCHAR(50), registration_no NVARCHAR(50), ration_type NVARCHAR(20), sub1 NVARCHAR(100), sub2 NVARCHAR(100), sub3 NVARCHAR(100), sub4 NVARCHAR(100), sub5 NVARCHAR(100), middle_year NVARCHAR(20), middle_marks NVARCHAR(20), middle_per NVARCHAR(20), middle_sub NVARCHAR(100), middle_school NVARCHAR(100), middle_re NVARCHAR(50), sse_year NVARCHAR(20), sse_marks NVARCHAR(20), sse_per NVARCHAR(20), sse_sub NVARCHAR(100), sse_school NVARCHAR(100), sse_re NVARCHAR(50), hsp_year NVARCHAR(20), hsp_marks NVARCHAR(20), hsp_per NVARCHAR(20), hsp_sub NVARCHAR(100), hsp_school NVARCHAR(100), hsp_re NVARCHAR(50), aadhar_self NVARCHAR(20), aadhar_father NVARCHAR(20), aadhar_mother NVARCHAR(20), father_occupation NVARCHAR(100), father_income NVARCHAR(50), bank_account NVARCHAR(50), bank_ifsc NVARCHAR(50), undertaking_name NVARCHAR(100), undertaking_father NVARCHAR(100), undertaking_ro NVARCHAR(200), undertaking_class NVARCHAR(20), status NVARCHAR(20) DEFAULT 'Pending', created_at DATETIME DEFAULT GETDATE())"""); conn.commit()
    data = request.form; adm_no = data.get('adm_no') or f"GHSS{datetime.now().year}{random.randint(1000,9999)}"
    adm_no = adm_no.upper().strip()[:50]
    cursor.execute("""INSERT INTO admissions (contact_no, aadhar_shilla, form_date, session, class_name, adm_no, stream, appar_id, udise_no, name, father_name, mother_name, dob, residence, caste, registration_no, ration_type, sub1, sub2, sub3, sub4, sub5, middle_year, middle_marks, middle_per, middle_sub, middle_school, middle_re, sse_year, sse_marks, sse_per, sse_sub, sse_school, sse_re, hsp_year, hsp_marks, hsp_per, hsp_sub, hsp_school, hsp_re, aadhar_self, aadhar_father, aadhar_mother, father_occupation, father_income, bank_account, bank_ifsc, undertaking_name, undertaking_father, undertaking_ro, undertaking_class) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (data.get('contact_no'), data.get('aadhar_shilla'), data.get('form_date') or datetime.now().date(), data.get('session'), data.get('class_name'), adm_no, data.get('stream'), data.get('appar_id'), data.get('udise_no') or '01131502304', data.get('name'), data.get('father_name'), data.get('mother_name'), data.get('dob') or None, data.get('residence'), data.get('caste'), data.get('registration_no'), data.get('ration_type'), data.get('sub1'), data.get('sub2'), data.get('sub3'), data.get('sub4'), data.get('sub5'), data.get('middle_year'), data.get('middle_marks'), data.get('middle_per'), data.get('middle_sub'), data.get('middle_school'), data.get('middle_re'), data.get('sse_year'), data.get('sse_marks'), data.get('sse_per'), data.get('sse_sub'), data.get('sse_school'), data.get('sse_re'), data.get('hsp_year'), data.get('hsp_marks'), data.get('hsp_per'), data.get('hsp_sub'), data.get('hsp_school'), data.get('hsp_re'), data.get('aadhar_self'), data.get('aadhar_father'), data.get('aadhar_mother'), data.get('father_occupation'), data.get('father_income'), data.get('bank_account'), data.get('bank_ifsc'), data.get('undertaking_name'), data.get('undertaking_father'), data.get('undertaking_ro'), data.get('undertaking_class')))
    conn.commit(); conn.close()
    return f"<h2>Admission {adm_no} Submitted - Pending</h2><a href='/admin/dashboard'>Back</a>"

@app.route('/admin/admissions')
def admissions_list():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    try: cursor.execute('SELECT * FROM admissions ORDER BY created_at DESC'); admissions = cursor.fetchall()
    except: admissions = []
    conn.close(); return render_template('admissions_list.html', admissions=admissions, user=session.get('full_name'))

@app.route('/api/delete_admission/<int:id>')
def delete_admission(id):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor(); cursor.execute('DELETE FROM admissions WHERE id=?', (id,)); conn.commit(); conn.close(); return redirect('/admin/admissions')

@app.route('/admin/approve/<adm_no>')
def approve_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    try:
        cursor.execute("UPDATE admissions SET status='Approved' WHERE adm_no=?", (adm_no,))
        conn.commit()
        try:
            cursor.execute("INSERT INTO students (enrollment_no, first_name, father_name, class) SELECT adm_no, name, father_name, class_name FROM admissions WHERE adm_no=? AND adm_no NOT IN (SELECT enrollment_no FROM students)", (adm_no,))
            conn.commit()
        except Exception as e: print(f"Student insert skip: {e}")
    except Exception as e: print(f"Approve error: {e}")
    conn.close()
    return redirect('/admin/admissions')

@app.route('/admin/reject/<adm_no>')
def reject_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("UPDATE admissions SET status='Rejected' WHERE adm_no=?", (adm_no,))
    conn.commit(); conn.close()
    return redirect('/admin/admissions')

# SINGLE VIEW FUNCTION - FIXED DUPLICATE
@app.route('/api/submit_admission_view/<int:id>')
def view_admission_by_id(id):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute('SELECT * FROM admissions WHERE id=?', (id,))
    row = cursor.fetchone()
    if not row: conn.close(); return "Record not found"
    cols = [d[0] for d in cursor.description]
    data = dict(zip(cols, row))
    adm_no = data.get('adm_no')
    conn.close()
    return render_template('admission_view.html', data=data, adm_no=adm_no, user=session.get('full_name'))

@app.route('/admin/view/<adm_no>')
def view_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT * FROM admissions WHERE adm_no=?", (adm_no,))
    row = cursor.fetchone()
    if not row: conn.close(); return "Record not found"
    cols = [d[0] for d in cursor.description]
    data = dict(zip(cols, row))
    conn.close()
    return render_template('admission_view.html', data=data, adm_no=adm_no, user=session.get('full_name'))

@app.route('/api/update_user_mobile', methods=['POST'])
def update_user_mobile():
    if session.get('role','').lower()!= 'admin': return jsonify({"status":"error"}), 403
    data = request.get_json(); conn=get_db(); cur=conn.cursor(); cur.execute("UPDATE users SET mobile=? WHERE username=?", (data.get('mobile'), data.get('username'))); conn.commit(); conn.close(); return jsonify({"status":"ok"})

@app.route('/activities')
def activities_page():
    conn=get_db(); cursor=conn.cursor()
    try: cursor.execute("SELECT * FROM activities ORDER BY id DESC"); acts = cursor.fetchall()
    except: acts = []
    conn.close(); return render_template('activities.html', activities=acts)

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
    finally: conn.close()
    return redirect('/admin/dashboard')

@app.route('/api/delete_activity/<int:id>')
def delete_activity(id):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor(); cursor.execute('DELETE FROM activities WHERE id=?', (id,)); conn.commit(); conn.close(); return redirect('/admin/dashboard')

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
            conn.commit(); conn.close()
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
                cur.execute("INSERT INTO admissions (contact_no, class_name, adm_no, name, father_name, dob, residence, registration_no, status, created_at) VALUES (?,?,?,?,?,?,?,?, 'Approved', GETDATE())", (contact, class_name, adm_no, name[:100], father, dob, residence, reg))
                conn.commit()
                cur.execute("SELECT COUNT(*) FROM students WHERE enrollment_no=?", (adm_no,))
                if cur.fetchone()[0] == 0:
                    cur.execute("INSERT INTO students (enrollment_no, first_name, father_name, class, dob, mobile, address) VALUES (?,?,?,?,?,?,?)", (adm_no, name[:200], father[:200], class_name[:50], dob, contact, residence[:300]))
                    conn.commit()
                inserted+=1
            except Exception as row_e: print(f"Row {i} error: {row_e}"); skipped+=1; continue
        conn.close()
        return f"<div style='text-align:center;padding:50px;font-family:Arial'><h2 style='color:green'>{inserted} Students Uploaded!</h2><p>{skipped} Skipped</p><a href='/admin/dashboard'>Go to Dashboard</a></div>"
    except Exception as e:
        import traceback; traceback.print_exc()
        return f"<h2>ERROR: {e}</h2><pre>{traceback.format_exc()}</pre><a href='/admin/dashboard'>Back</a>"

@app.route('/admin/student_report')
def student_report():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT name, father_name, class_name, contact_no, stream, dob, registration_no, adm_no, caste FROM admissions WHERE status='Approved' ORDER BY class_name, name")
    rows = cursor.fetchall(); conn.close()
    return render_template('student_report.html', rows=rows, user=session.get('full_name'), role=session.get('role'))

@app.route('/admin/student_report/excel')
def student_report_excel():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor()
    cursor.execute("SELECT name as [Student Name], father_name as [Father Name], class_name as [Class], contact_no as [Contact], stream as [Stream], dob as [DOB], registration_no as [Reg No], adm_no as [Adm No], caste as [Category] FROM admissions WHERE status='Approved' ORDER BY class_name, name")
    rows = cursor.fetchall(); cols = [d[0] for d in cursor.description]; conn.close()
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
    if not row: conn.close(); return "Record not found"
    cols = [d[0] for d in cursor.description]
    data = dict(zip(cols, row))
    conn.close()
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
        # also update students table
        try:
            cursor.execute("UPDATE students SET first_name=?, father_name=?, class=?, mobile=?, address=? WHERE enrollment_no=?",
                (data.get('name'), data.get('father_name'), data.get('class_name'), data.get('contact_no'), data.get('residence'), adm_no))
            conn.commit()
        except: pass
    except Exception as e: print(f"Update error {e}")
    finally: conn.close()
    return redirect(f'/admin/view/{adm_no}')

if __name__ == '__main__':
    print("GHSS Chakrohi Server - FINAL FIXED - Running on 127.0.0.1:8080")
    app.run(host='0.0.0.0',port=8080,debug=True)

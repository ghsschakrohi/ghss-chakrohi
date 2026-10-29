from flask import Flask, render_template, request, redirect, session, jsonify, send_file, g
import sqlite3
import os
import io
import base64
import random
import requests
import urllib.parse
import time
from dotenv import load_dotenv
load_dotenv()
try:
    import pandas as pd
except:
    pd = None
try:
    import qrcode
except:
    qrcode = None
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", 'ghss-01131502304')
FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY")
DATABASE = 'school.db'

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

def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, full_name TEXT, role TEXT, subject TEXT, mobile TEXT, is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, enrollment_no TEXT UNIQUE, first_name TEXT, father_name TEXT, class TEXT, dob TEXT, mobile TEXT, address TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, designation TEXT, subject TEXT, exp TEXT, qualification TEXT, wef TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS activities (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, activity_date DATE, photo TEXT, uploaded_by TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS monthly_results (id INTEGER PRIMARY KEY AUTOINCREMENT, reg_no TEXT, class_name TEXT, month TEXT, subject TEXT, marks INTEGER, max_marks INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS admissions (id INTEGER PRIMARY KEY AUTOINCREMENT, contact_no TEXT, aadhar_shilla TEXT, form_date DATE, session TEXT, class_name TEXT, adm_no TEXT, stream TEXT, appar_id TEXT, udise_no TEXT, name TEXT, father_name TEXT, mother_name TEXT, dob DATE, residence TEXT, caste TEXT, registration_no TEXT, ration_type TEXT, sub1 TEXT, sub2 TEXT, sub3 TEXT, sub4 TEXT, sub5 TEXT, middle_year TEXT, middle_marks TEXT, middle_per TEXT, middle_sub TEXT, middle_school TEXT, middle_re TEXT, sse_year TEXT, sse_marks TEXT, sse_per TEXT, sse_sub TEXT, sse_school TEXT, sse_re TEXT, hsp_year TEXT, hsp_marks TEXT, hsp_per TEXT, hsp_sub TEXT, hsp_school TEXT, hsp_re TEXT, aadhar_self TEXT, aadhar_father TEXT, aadhar_mother TEXT, father_occupation TEXT, father_income TEXT, bank_account TEXT, bank_ifsc TEXT, undertaking_name TEXT, undertaking_father TEXT, undertaking_ro TEXT, undertaking_class TEXT, gender TEXT, status TEXT DEFAULT 'Pending', created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("SELECT * FROM users WHERE username='principal'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password, full_name, role, is_active) VALUES (?,?,?,?,?)", ('principal', 'admin123', 'Principal', 'admin', 1))
    cur.execute("SELECT COUNT(*) FROM teachers")
    if cur.fetchone()[0] == 0:
        staff = [('Mrs. Pushpa Lochan', 'Principal', 'Administration', '25', 'Masters,B.Ed', ''),('Mr. Gurmeet Singh', 'Sr. Lect Sociology - Vice Principal', 'Sociology', '18', 'Masters, M.Phil,B.Ed', ''),('Mr. Daleep Sharma', 'Sr. Lect Urdu', 'Urdu', '18', 'Masters, P.hd, B.Ed', ''),('Mr. Harveen Singh Sudan', 'Sr. Lect Political Science', 'Pol. Science', '16', 'Masters, M.Phil, B.Ed', ''),('Mrs. Neeru Ratta', 'Sr. Lect Education', 'Education', '16', 'Masters, M.Phil,B.Ed ', ''),('Mrs. Bindu Devi', 'Sr. Lect Zoology', 'Zoology', '16', 'Masters, B.Ed', ''),('Mrs. Bindu Dogra', 'Sr. Lect Hindi', 'Hindi', '16', 'Masters, NET, B.Ed', ''),('Mr. Paramjit Singh', 'Sr. Lect Computer Science', 'Computer Science', '17', 'MCA, M.Phil, B.Ed', '26-01-2023'),('Mrs. Shammi Chib', 'Lecturer Physics', 'Physics', '22', 'M.Sc, B.Ed', ''),('Mr. Shakti Kumar', 'Lecturer Chemistry', 'Chemistry', '33', 'M.Sc, B.Ed', ''),('Mrs. Alka', 'Lecturer English', 'English', '-', 'M.A, B.Ed', ''),('Mrs. Darshan Kour', 'I/C Lect Electronics', 'Electronics', '26', 'M.Sc, B.Ed', ''),('Mr. Rajesh Gupta', 'I/C Lect Botany', 'Botany', '22', 'M.Sc, B.Ed', ''),('Mrs. Ravinder Kour', 'I/C Lect Maths', 'Mathematics', '22', 'M.Sc, B.Ed', ''),('Mrs. Neelam Sudan', 'Master', 'General', '22', 'Masters, B.Ed', ''),('Mr. Ram Lal', 'Master', 'General', '19', 'Masters, B.Ed', ''),('Mr. Shariq Ishaq Mir', 'Teacher', 'General', '19', 'MA, B.Ed', ''),('Mr. Rohit Gupta', 'Teacher', 'General', '10', 'M.Sc, B.Ed', ''),('Mrs. Indu Gandhi', 'Teacher', 'General', '10', 'M.A, B.Ed', ''),('Mr. Sudansh Sharma', 'Teacher', 'General', '10', 'M.Sc, B.Ed', ''),('Mrs. Meenakshi Gupta', 'Teacher', 'General', '10', 'M.A, B.Ed', ''),('Mrs. Rasmeet Kour', 'Teacher', 'General', '10', 'M.Sc, B.Ed', ''),('Mrs. Devinder Kour', 'Sr. Assistant', 'Non-Teaching', '10', 'Graduate', ''),('Mr. Karanjeet Kumar', 'Lab. Assistant', 'Non-Teaching', '20', '12th', ''),('Mr. Rakesh Sharma', 'Lab Assistant', 'Non-Teaching', '20', '12th', ''),('Mrs. Asha Devi', 'Class-IV', 'Non-Teaching', '18', '', ''),('Mrs. Reena Devi', 'Class-IV', 'Non-Teaching', '12', '', ''),('Mr. Ravinder Choudhary', 'Class-IV', 'Non-Teaching', '10', '', ''),('Mr. Shubdeep Akash', 'Class-IV', 'Non-Teaching', '5', 'MA', ''),]
        for s in staff:
            cur.execute("INSERT INTO teachers (name, designation, subject, exp, qualification, wef) VALUES (?,?,?,?,?,?)", s)
    conn.commit(); conn.close()
    os.makedirs('static/uploads/activities', exist_ok=True)

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
        if user:
            session['admin']=True; session['user_id']=user[0]; session['username']=user[1]; session['full_name']=user[3]; session['role']=user[4]
            subj = (user[5] or '').strip()
            uname = str(user[1]).lower(); fname = str(user[3]).lower()
            if 'paramjit' in uname or 'paramjit' in fname: subj='Computer Science'
            elif 'shakti' in uname or 'shakti' in fname: subj='Chemistry'
            elif 'shammi' in fname: subj='Physics'
            elif not subj or subj.lower() in ['general','']: subj='Computer Science'
            session['subject']=subj
            return redirect('/admin/dashboard')
        else:
            return "<h3 style='color:red;text-align:center;margin-top:100px'>Invalid Login<br><a href='/admin'>Try Again</a></h3>"
    return render_template('admin_login.html')

# ============ FORGOT PASSWORD - RENDER FIXED ============
@app.route('/forgot-password', methods=['GET','POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        conn = get_db(); cursor = conn.cursor()
        cursor.execute("SELECT mobile FROM users WHERE username=? AND is_active=1", (username,))
        row = cursor.fetchone()
        if row and row[0]:
            mobile = str(row[0]).strip().replace("+91","").replace(" ","")[-10:]
            otp = str(random.randint(100000,999999))
            session['reset_otp'] = otp
            session['reset_user'] = username
            try:
                msg = f"Your GHSS Chakrohi ERP OTP is {otp}. Valid for 5 mins. Do not share."
                url = "https://www.fast2sms.com/dev/bulkV2"
                params = {"authorization": FAST2SMS_API_KEY, "route": "q", "message": msg, "language": "english", "flash": 0, "numbers": mobile}
                resp = requests.get(url, params=params, timeout=15)
                print(f"SMS to {mobile}: {resp.text}")
            except Exception as e:
                print(f"SMS Error: {e}")
                return "<div style='text-align:center;padding:50px'><h3 style='color:red'>SMS service temporarily unavailable. Try later.</h3><a href='/forgot-password'>Back</a></div>"
            masked = f"{mobile[:2]}****{mobile[-2:]}"
            return f"<div style='text-align:center;padding:50px'><h2 style='color:green'>OTP Sent Successfully</h2><p>OTP sent to your registered mobile {masked}</p><a href='/verify-otp'><button style='padding:10px 20px;background:#0b3d91;color:white;border:none;border-radius:5px'>Verify OTP</button></a></div>"
        else:
            return "<h3 style='color:red;text-align:center'>User not found or mobile not registered<br><a href='/forgot-password'>Back</a></h3>"
    return render_template('forgot_password.html')

@app.route('/verify-otp', methods=['GET','POST'])
def verify_otp():
    if request.method == 'POST':
        entered = request.form.get('otp','').strip()
        new_pass = request.form.get('new_password','').strip()
        confirm = request.form.get('confirm_password','').strip()
        if new_pass != confirm:
            return "<h3 style='text-align:center'>Passwords do not match<br><a href='/verify-otp'>Back</a></h3>"
        if not session.get('reset_otp'):
            return "<h3 style='text-align:center'>Session expired<br><a href='/forgot-password'>Start Again</a></h3>"
        if entered == session.get('reset_otp'):
            conn = get_db(); cursor = conn.cursor()
            cursor.execute("UPDATE users SET password=? WHERE username=?", (new_pass, session.get('reset_user')))
            conn.commit()
            session.clear()
            return "<h2 style='text-align:center;color:green;padding:50px'>Password Reset Successful!<br><br><a href='/admin'>Login Now</a></h2>"
        else:
            return "<h3 style='text-align:center;color:red'>Invalid OTP<br><a href='/verify-otp'>Try Again</a></h3>"
    html = "<div style='max-width:400px;margin:80px auto;padding:20px;border:1px solid #ccc;border-radius:8px'>"
    html += "<h2 style='text-align:center;color:#0b3d91'>Verify OTP</h2>"
    html += "<form method='POST'>"
    html += "<input name='otp' placeholder='Enter OTP from SMS' required style='width:100%;padding:12px;margin-top:15px'><br>"
    html += "<input type='password' name='new_password' placeholder='New Password' required style='width:100%;padding:12px;margin-top:10px'><br>"
    html += "<input type='password' name='confirm_password' placeholder='Confirm Password' required style='width:100%;padding:12px;margin-top:10px'><br>"
    html += "<button style='width:100%;padding:12px;background:#0b3d91;color:white;margin-top:15px;border:none;border-radius:4px'>Reset Password</button>"
    html += "</form></div>"
    return html

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
    try: cursor.execute("SELECT enrollment_no, first_name FROM students WHERE enrollment_no IS NOT NULL AND TRIM(enrollment_no)!='' LIMIT 500"); students_for_result = cursor.fetchall()
    except: students_for_result = []
    try: cursor.execute('SELECT * FROM activities ORDER BY id DESC LIMIT 20'); activities = cursor.fetchall()
    except: activities = []
    stats = {'students': students_count, 'results': results_count, 'admissions': admissions_count, 'teachers': len(teachers)}
    return render_template('dashboard.html', teachers=teachers, stats=stats, users=all_users, admissions=admissions, pending_admissions=pending_admissions, approved_admissions=approved_admissions, students_for_result=students_for_result, activities=activities, user=session.get('full_name'), role=session.get('role'))

@app.route('/logout')
def logout(): session.clear(); return redirect('/admin')

@app.route('/lab/<lab_name>')
def lab_detail(lab_name):
    labs_data = {'physics': {'name': 'Physics Lab', 'description': 'Well equipped Physics Lab', 'photo': '/static/physics.jpg'},'chemistry': {'name': 'Chemistry Lab', 'description': 'Chemistry Lab', 'photo': '/static/chemistry.jpg'},'biology': {'name': 'Biology Lab', 'description': 'Biology Lab', 'photo': '/static/biology.jpg'},'computer': {'name': 'Computer Lab', 'description': 'Computer Lab', 'photo': '/static/computer.jpg'}}
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
    except: pass
    if request.is_json: return jsonify({"status":"ok"});
    else: return redirect('/admin/dashboard')

@app.route('/results')
def results_page(): return render_template('results.html')

@app.route('/api/check_result', methods=['POST'])
def check_result():
    reg_no=request.form.get('reg_no','').strip().upper()
    conn=get_db(); cursor=conn.cursor(); cursor.execute("SELECT * FROM students WHERE enrollment_no=?",(reg_no,)); student=cursor.fetchone()
    if not student: return f"<div style='text-align:center;padding:50px'><h2 style='color:red'>Student {reg_no} not found</h2><a href='/results'>Back</a></div>"
    cursor.execute("SELECT * FROM monthly_results WHERE reg_no=?",(reg_no,)); results=cursor.fetchall()
    if not results: return f"<div style='text-align:center;padding:50px'><h2>No results for {reg_no}</h2><a href='/results'>Back</a></div>"
    total=sum([r[4] for r in results]); max_t=sum([r[5] for r in results]); per=round(total/max_t*100,2) if max_t else 0
    rows="".join([f"<tr><td>{i}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[5]}</td><td>{r[4]}</td></tr>" for i,r in enumerate(results,1)])
    return f"<h2>{student[2]} - {total}/{max_t} {per}%</h2><table border=1>{rows}</table>"

@app.route('/admin/admissions')
def admissions_list():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor(); cursor.execute('SELECT * FROM admissions ORDER BY created_at DESC'); admissions = cursor.fetchall()
    return render_template('admissions_list.html', admissions=admissions, user=session.get('full_name'))

@app.route('/admin/approve/<adm_no>')
def approve_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor(); cursor.execute("UPDATE admissions SET status='Approved' WHERE adm_no=?", (adm_no,)); conn.commit()
    return redirect('/admin/admissions')

@app.route('/admin/reject/<adm_no>')
def reject_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor(); cursor.execute("UPDATE admissions SET status='Rejected' WHERE adm_no=?", (adm_no,)); conn.commit()
    return redirect('/admin/admissions')

@app.route('/admin/view/<adm_no>')
def view_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor(); cursor.execute("SELECT * FROM admissions WHERE adm_no=?", (adm_no,)); row = cursor.fetchone()
    if not row: return "Record not found"
    cols = [d[0] for d in cursor.description]; data = dict(zip(cols, row))
    return render_template('admission_view.html', data=data, adm_no=adm_no, user=session.get('full_name'))

@app.route('/activities')
def activities_page():
    conn=get_db(); cursor=conn.cursor(); cursor.execute("SELECT * FROM activities ORDER BY id DESC"); acts = cursor.fetchall()
    return render_template('activities.html', activities=acts)

@app.route('/api/upload_activity', methods=['POST'])
def upload_activity():
    if not session.get('admin'): return redirect('/admin')
    title = request.form.get('title','').strip(); desc = request.form.get('description','').strip(); date = request.form.get('activity_date')
    photo_path = ""
    if 'photo' in request.files:
        f = request.files['photo']
        if f.filename:
            os.makedirs('static/uploads/activities', exist_ok=True)
            filename = f"act_{int(time.time())}_{f.filename.replace(' ', '_')}"
            save_path = os.path.join('static/uploads/activities', filename); f.save(save_path); photo_path = f"/static/uploads/activities/{filename}"
    conn=get_db(); cursor=conn.cursor()
    cursor.execute("INSERT INTO activities (title, description, activity_date, photo, uploaded_by) VALUES (?,?,?,?,?)", (title, desc, date or datetime.now().date(), photo_path, session.get('username'))); conn.commit()
    return redirect('/admin/dashboard')

@app.route('/api/delete_activity/<int:id>')
def delete_activity(id):
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cursor = conn.cursor(); cursor.execute('DELETE FROM activities WHERE id=?', (id,)); conn.commit(); return redirect('/admin/dashboard')

@app.route('/admin/category_report')
def category_report():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cursor=conn.cursor()
    try: cursor.execute("SELECT COALESCE(caste,'') as caste, COUNT(*) FROM admissions WHERE status='Approved' GROUP BY caste"); caste_data=cursor.fetchall()
    except: caste_data=[]
    sc=st=obc=general=other=0
    for row in caste_data:
        c=str(row[0]).upper().strip(); cnt=row[1]
        if 'SC' in c: sc+=cnt
        elif 'ST' in c: st+=cnt
        elif 'OBC' in c: obc+=cnt
        elif 'GEN' in c or 'OPEN' in c: general+=cnt
        else: other+=cnt
    total_approved=sc+st+obc+general+other
    def get_count(q, params=()):
        try: cursor.execute(q, params); r=cursor.fetchone(); return r[0] if r else 0
        except: return 0
    boys_total=get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(IFNULL(gender,''))) IN ('M','MALE','BOY')")
    girls_total=get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(IFNULL(gender,''))) IN ('F','FEMALE','GIRL')")
    total_11=get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%11TH%'")
    total_12=get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%12TH%'")
    boys_11=get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%11TH%' AND UPPER(TRIM(IFNULL(gender,''))) IN ('M','MALE','BOY')", ())
    girls_11=get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%11TH%' AND UPPER(TRIM(IFNULL(gender,''))) IN ('F','FEMALE','GIRL')", ())
    boys_12=get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%12TH%' AND UPPER(TRIM(IFNULL(gender,''))) IN ('M','MALE','BOY')", ())
    girls_12=get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%12TH%' AND UPPER(TRIM(IFNULL(gender,''))) IN ('F','FEMALE','GIRL')", ())
    data={'sc':sc,'st':st,'obc':obc,'general':general,'other':other,'total_approved':total_approved,'boys_total':boys_total,'girls_total':girls_total,'boys_11':boys_11,'girls_11':girls_11,'total_11':total_11,'boys_12':boys_12,'girls_12':girls_12,'total_12':total_12}
    return render_template('category_report.html', data=data, user=session.get('full_name'), role=session.get('role'))

@app.route('/admin/upload_marks')
def upload_marks_page():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cursor=conn.cursor()
    try: cursor.execute("SELECT DISTINCT TRIM(class_name) FROM admissions WHERE status='Approved' AND TRIM(class_name)!=''"); classes=[r[0].strip() for r in cursor.fetchall() if r[0]]
    except: classes=[]
    if not classes: classes=['11th','12th']
    selected_class=(request.args.get('class','') or '11th').strip()
    role=(session.get('role') or '').lower(); teacher_subject=(session.get('subject') or '').strip()
    try:
        like_class=f"%{selected_class}%"; like_sub=f"%{teacher_subject}%"
        if role in ['teacher','staff'] and teacher_subject and teacher_subject.lower()!='general':
            cursor.execute("SELECT adm_no, name, father_name, class_name, sub1, sub2, sub3, sub4, sub5 FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE UPPER(?) AND (UPPER(TRIM(IFNULL(sub1,''))) LIKE UPPER(?) OR UPPER(TRIM(IFNULL(sub2,''))) LIKE UPPER(?) OR UPPER(TRIM(IFNULL(sub3,''))) LIKE UPPER(?) OR UPPER(TRIM(IFNULL(sub4,''))) LIKE UPPER(?) OR UPPER(TRIM(IFNULL(sub5,''))) LIKE UPPER(?)) ORDER BY name",(like_class, like_sub, like_sub, like_sub, like_sub, like_sub))
        else:
            cursor.execute("SELECT adm_no, name, father_name, class_name, sub1, sub2, sub3, sub4, sub5 FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE UPPER(?) ORDER BY name",(like_class,))
        rows=cursor.fetchall(); cols=[d[0] for d in cursor.description] if cursor.description else []; students=[dict(zip(cols,r)) for r in rows]
    except: students=[]
    return render_template('upload_marks.html', classes=classes, selected_class=selected_class, students=students, teacher_subject=teacher_subject, role=session.get('role'), user=session.get('full_name'))

@app.route('/api/upload_bulk_marks', methods=['POST'])
def upload_bulk_marks():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cursor=conn.cursor()
    month=(request.form.get('month') or 'UT-1').strip(); subject=(request.form.get('subject') or '').strip()
    max_marks_val=int(request.form.get('max_marks','100'))
    user_role = str(session.get('role') or '').lower()
    if user_role not in ['admin', 'administrator']:
        if session.get('subject') and str(session.get('subject')).lower()!='general': subject=session.get('subject')
    adm_nos=request.form.getlist('adm_no'); marks_list=request.form.getlist('marks')
    if not adm_nos: adm_nos=request.form.getlist('adm_no[]')
    if not marks_list: marks_list=request.form.getlist('marks[]')
    selected_class=request.form.get('selected_class',''); count=0
    for adm_no,marks in zip(adm_nos, marks_list):
        adm_no=str(adm_no).strip().upper()
        if not adm_no or not str(marks).strip(): continue
        try:
            marks_int=int(float(marks))
            cursor.execute("DELETE FROM monthly_results WHERE TRIM(reg_no)=TRIM(?) AND LOWER(TRIM(subject))=LOWER(TRIM(?)) AND LOWER(TRIM(month))=LOWER(TRIM(?))",(adm_no,subject,month))
            cursor.execute("INSERT INTO monthly_results (reg_no, class_name, month, subject, marks, max_marks) VALUES (?,?,?,?,?,?)",(adm_no,selected_class,month,subject,marks_int,max_marks_val)); conn.commit(); count+=1
        except: pass
    return f"<h2>{count} Marks Uploaded for {subject} - {month}</h2><a href='/admin/dashboard'>Back</a>"

@app.route('/admin/class_result_report', methods=['GET','POST'])
def class_result_report():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cursor=conn.cursor()
    try: cursor.execute("SELECT DISTINCT class_name FROM admissions WHERE status='Approved' AND class_name!='' ORDER BY class_name"); classes=[r[0].strip() for r in cursor.fetchall() if r[0]]
    except: classes=['11th','12th']
    if not classes: classes=['11th','12th']
    selected_class=(request.form.get('class_name') or request.args.get('class_name') or classes[0]).strip()
    cursor.execute("SELECT DISTINCT adm_no, name, father_name, class_name, stream, sub1, sub2, sub3, sub4, sub5 FROM admissions WHERE status='Approved' AND class_name=? ORDER BY adm_no ASC",(selected_class,)); rows=cursor.fetchall()
    report_data=[]; sno=1
    for row in rows:
        adm_no, name, father_name, class_name, stream, sub1, sub2, sub3, sub4, sub5=row
        opted=[str(s).strip() for s in [sub1,sub2,sub3,sub4,sub5] if s and str(s).strip()][:5]
        while len(opted)<5: opted.append("")
        cursor.execute("SELECT subject, marks, max_marks FROM monthly_results WHERE TRIM(reg_no)=TRIM(?)",(adm_no,)); marks_map={subj.lower(): (m,mx) for subj,m,mx in cursor.fetchall() if subj}
        total_obt=sum([v[0] for v in marks_map.values()]); total_max=sum([v[1] for v in marks_map.values()])
        per=round(total_obt/total_max*100,2) if total_max else 0
        report_data.append({'sno':sno,'roll_no':adm_no,'adm_no':adm_no,'name':name,'father_name':father_name,'class_name':class_name,'stream':stream,'opted_subjects':opted,'total':total_obt,'max_total':total_max,'percentage':per,'result':'Pass' if per>=33 else 'Fail'}); sno+=1
    return render_template('class_result_report.html', classes=classes, report_data=report_data, selected_class=selected_class, selected_stream='', search_name='', user=session.get('full_name'), role=session.get('role'))

@app.route('/admin/subject_report')
def subject_report():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cursor=conn.cursor()
    cursor.execute("SELECT TRIM(subject) as subject_name, COUNT(*) as total_students FROM (SELECT sub1 as subject FROM admissions WHERE status='Approved' AND TRIM(IFNULL(sub1,''))!='' UNION ALL SELECT sub2 FROM admissions WHERE status='Approved' AND TRIM(IFNULL(sub2,''))!='' UNION ALL SELECT sub3 FROM admissions WHERE status='Approved' AND TRIM(IFNULL(sub3,''))!='' UNION ALL SELECT sub4 FROM admissions WHERE status='Approved' AND TRIM(IFNULL(sub4,''))!='' UNION ALL SELECT sub5 FROM admissions WHERE status='Approved' AND TRIM(IFNULL(sub5,''))!='') AS all_subs GROUP BY TRIM(subject) ORDER BY total_students DESC")
    subject_data=cursor.fetchall()
    cursor.execute("SELECT DISTINCT TRIM(class_name) FROM admissions WHERE status='Approved' AND class_name!=''"); classes=[r[0] for r in cursor.fetchall() if r[0]]
    return render_template('subject_report.html', subject_data=subject_data, breakdown=[], classes=classes, selected_class='', user=session.get('full_name'), role=session.get('role'))

@app.route('/admin/student_report')
def student_report():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cursor=conn.cursor()
    search_q=(request.args.get('q') or '').strip()
    sql="SELECT name, father_name, class_name, contact_no, stream, dob, registration_no, adm_no, caste FROM admissions WHERE status='Approved'"
    params=[]
    if search_q: sql+=" AND (name LIKE? OR adm_no LIKE?)"; params.extend([f"%{search_q}%", f"%{search_q}%"])
    sql+=" ORDER BY adm_no ASC"; cursor.execute(sql, tuple(params)); data=cursor.fetchall()
    class Obj: pass
    rows=[]
    for d in data:
        o=Obj(); o.name,o.father_name,o.class_name,o.contact_no,o.stream,o.dob,o.registration_no,o.adm_no,o.caste=d; rows.append(o)
    return render_template('student_report.html', rows=rows, search_q=search_q, user=session.get('full_name'), role=session.get('role'))

# Startup
print("Checking DB...")
if not os.path.exists(DATABASE):
    print("Creating school.db first time...")
    init_db()
else:
    init_db()

if __name__ == '__main__':
    if not FAST2SMS_API_KEY:
        print("WARNING: FAST2SMS_API_KEY not set in .env - SMS will not work")
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

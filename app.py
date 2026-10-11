from flask import Flask, render_template, request, redirect, session, jsonify, send_file, Response
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
import socket
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'ghss-01131502304'
FAST2SMS_API_KEY = "DnMZlzvTrHgeQqM22KNlVYxAOpWTR61u3DLr4D9zR5JbE5rpQicF606xcCid"
DATABASE = 'school.db'

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, designation TEXT, subject TEXT, exp TEXT, qualification TEXT, wef TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, full_name TEXT, role TEXT, subject TEXT, mobile TEXT, is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, enrollment_no TEXT UNIQUE, first_name TEXT, father_name TEXT, class TEXT, dob DATE, mobile TEXT, address TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS activities (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, activity_date DATE, photo TEXT, uploaded_by TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS monthly_results (id INTEGER PRIMARY KEY AUTOINCREMENT, reg_no TEXT, class_name TEXT, month TEXT, subject TEXT, marks INTEGER, max_marks INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS admissions (id INTEGER PRIMARY KEY AUTOINCREMENT, contact_no TEXT, aadhar_shilla TEXT, form_date DATE, session TEXT, class_name TEXT, adm_no TEXT UNIQUE, stream TEXT, appar_id TEXT, udise_no TEXT, name TEXT, father_name TEXT, mother_name TEXT, dob DATE, residence TEXT, caste TEXT, registration_no TEXT, ration_type TEXT, sub1 TEXT, sub2 TEXT, sub3 TEXT, sub4 TEXT, sub5 TEXT, middle_year TEXT, middle_marks TEXT, middle_per TEXT, middle_sub TEXT, middle_school TEXT, middle_re TEXT, sse_year TEXT, sse_marks TEXT, sse_per TEXT, sse_sub TEXT, sse_school TEXT, sse_re TEXT, hsp_year TEXT, hsp_marks TEXT, hsp_per TEXT, hsp_sub TEXT, hsp_school TEXT, hsp_re TEXT, aadhar_self TEXT, aadhar_father TEXT, aadhar_mother TEXT, father_occupation TEXT, father_income TEXT, bank_account TEXT, bank_ifsc TEXT, undertaking_name TEXT, undertaking_father TEXT, undertaking_ro TEXT, undertaking_class TEXT, gender TEXT, status TEXT DEFAULT 'Pending', created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    try: cur.execute("ALTER TABLE admissions ADD COLUMN gender TEXT")
    except: pass
    cur.execute("SELECT * FROM users WHERE username='principal'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password, full_name, role, is_active) VALUES (?,?,?,?,?)", ('principal', 'admin123', 'Principal', 'admin', 1))
    cur.execute("SELECT COUNT(*) FROM teachers")
    if cur.fetchone()[0]==0:
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
    conn.commit()
    conn.close()
    os.makedirs('static/uploads/activities', exist_ok=True)

init_db()

@app.route('/')
def home():
    conn = get_db(); cur = conn.cursor()
    cur.execute('SELECT * FROM teachers ORDER BY id'); teachers = cur.fetchall()
    try: cur.execute('SELECT * FROM activities ORDER BY id DESC'); activities = cur.fetchall()
    except: activities = []
    conn.close()
    return render_template('index.html', teachers=teachers, activities=activities)

@app.route('/teacher/<int:id>')
def teacher_detail(id):
    conn = get_db(); cur = conn.cursor(); cur.execute('SELECT * FROM teachers WHERE id=?', (id,)); t = cur.fetchone(); conn.close(); return render_template('teacher.html', t=t)

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username','').strip(); password = request.form.get('password','').strip()
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT id, username, password, full_name, role, subject FROM users WHERE username=? AND password=? AND is_active=1", (username, password))
        user = cur.fetchone(); conn.close()
        if user:
            session['admin']=True; session['user_id']=user[0]; session['username']=user[1]; session['full_name']=user[3]; session['role']=user[4]
            subj = (user[5] or '').strip()
            uname = str(user[1]).lower(); fname = str(user[3]).lower()
            if 'paramjit' in uname or 'paramjit' in fname: subj='Computer Science'
            elif 'shakti' in uname or 'shakti' in fname: subj='Chemistry'
            elif 'shammi' in fname: subj='Physics'
            elif not subj or subj.lower() in ['general','']:
                if str(user[4]).lower()!='admin': subj='Computer Science'
            session['subject']=subj
            return redirect('/admin/dashboard')
        else:
            return "<h3 style='color:red;text-align:center;margin-top:100px'>Invalid Login<br><a href='/admin'>Try Again</a></h3>"
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cur = conn.cursor()
    cur.execute('SELECT * FROM teachers'); teachers = cur.fetchall()
    try: cur.execute('SELECT * FROM users'); all_users = cur.fetchall()
    except: all_users = []
    try: cur.execute('SELECT COUNT(*) FROM students'); students_count = cur.fetchone()[0]
    except: students_count = 0
    try: cur.execute('SELECT COUNT(*) FROM monthly_results'); results_count = cur.fetchone()[0]
    except: results_count = 0
    try:
        cur.execute("SELECT COUNT(*) FROM admissions WHERE status='Approved'"); admissions_count = cur.fetchone()[0]
        cur.execute("SELECT * FROM admissions WHERE status='Pending' ORDER BY created_at DESC LIMIT 10"); pending_admissions = cur.fetchall()
        cur.execute("SELECT * FROM admissions WHERE status='Approved' ORDER BY created_at DESC LIMIT 10"); approved_admissions = cur.fetchall()
        admissions = pending_admissions
    except: admissions_count=0; admissions=[]; pending_admissions=[]; approved_admissions=[]
    try:
        cur.execute("SELECT enrollment_no, first_name FROM students WHERE enrollment_no IS NOT NULL AND TRIM(enrollment_no)!= '' LIMIT 500")
        students_for_result = cur.fetchall()
    except: students_for_result = []
    try: cur.execute('SELECT * FROM activities ORDER BY id DESC LIMIT 20'); activities = cur.fetchall()
    except: activities = []
    conn.close()
    stats = {'students': students_count, 'results': results_count, 'admissions': admissions_count, 'teachers': len(teachers)}
    return render_template('dashboard.html', teachers=teachers, stats=stats, users=all_users, admissions=admissions, pending_admissions=pending_admissions, approved_admissions=approved_admissions, students_for_result=students_for_result, activities=activities, user=session.get('full_name'), role=session.get('role'))

@app.route('/logout')
def logout(): session.clear(); return redirect('/admin')

@app.route('/admin/student_report')
def student_report():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cur = conn.cursor()
    search_q = (request.args.get('q') or '').strip()
    class_filter = (request.args.get('class') or '').strip()
    stream_filter = (request.args.get('stream') or '').strip()
    sql = "SELECT name, father_name, class_name, contact_no, stream, dob, registration_no, adm_no, caste FROM admissions WHERE status='Approved'"
    params = []
    if search_q:
        sql += " AND (name LIKE? OR father_name LIKE? OR adm_no LIKE? OR registration_no LIKE? OR contact_no LIKE?)"
        like = f"%{search_q}%"
        params.extend([like]*5)
    if class_filter:
        sql += " AND class_name LIKE?"
        params.append(f"%{class_filter}%")
    if stream_filter:
        sql += " AND stream =?"
        params.append(stream_filter)
    sql += " ORDER BY adm_no ASC"
    cur.execute(sql, tuple(params))
    data = cur.fetchall()
    conn.close()
    class Obj: pass
    rows = []
    for d in data:
        o = Obj()
        o.name, o.father_name, o.class_name, o.contact_no, o.stream, o.dob, o.registration_no, o.adm_no, o.caste = d
        rows.append(o)
    return render_template('student_report.html', rows=rows, search_q=search_q, class_filter=class_filter, stream_filter=stream_filter, user=session.get('full_name'), role=session.get('role'))

@app.route('/admin/category_report')
def category_report():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cur = conn.cursor()
    try: cur.execute("SELECT COALESCE(caste,'') as caste, COUNT(*) FROM admissions WHERE status='Approved' GROUP BY caste"); caste_data = cur.fetchall()
    except: caste_data = []
    sc = st = obc = general = other = 0
    for row in caste_data:
        c = str(row[0]).upper().strip(); cnt = row[1]
        if 'SC' in c: sc += cnt
        elif 'ST' in c: st += cnt
        elif 'OBC' in c: obc += cnt
        elif 'GEN' in c or 'OPEN' in c: general += cnt
        else: other += cnt
    total_approved = sc+st+obc+general+other
    def get_count(query, params=()):
        try:
            cur.execute(query, params); r=cur.fetchone(); return r[0] if r else 0
        except: return 0
    boys_where = "( UPPER(TRIM(gender))='M' OR UPPER(TRIM(gender))='MALE' OR UPPER(TRIM(gender)) LIKE '%BOY%' ) AND UPPER(TRIM(gender)) NOT LIKE '%FEMALE%'"
    girls_where = "( UPPER(TRIM(gender))='F' OR UPPER(TRIM(gender))='FEMALE' OR UPPER(TRIM(gender)) LIKE '%GIRL%' )"
    boys_total = get_count(f"SELECT COUNT(*) FROM admissions WHERE status='Approved' AND {boys_where}")
    girls_total = get_count(f"SELECT COUNT(*) FROM admissions WHERE status='Approved' AND {girls_where}")
    boys_11 = get_count(f"SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%11TH%' AND {boys_where}")
    girls_11 = get_count(f"SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%11TH%' AND {girls_where}")
    boys_12 = get_count(f"SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%12TH%' AND {boys_where}")
    girls_12 = get_count(f"SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%12TH%' AND {girls_where}")
    total_11 = get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%11TH%'")
    total_12 = get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%12TH%'")
    conn.close()
    data = {'sc': sc, 'st': st, 'obc': obc, 'general': general, 'other': other, 'total_approved': total_approved, 'boys_total': boys_total, 'girls_total': girls_total, 'boys_11': boys_11, 'girls_11': girls_11, 'total_11': total_11, 'boys_12': boys_12, 'girls_12': girls_12, 'total_12': total_12}
    return render_template('category_report.html', data=data, user=session.get('full_name'), role=session.get('role'))

@app.route('/admin/upload_marks')
def upload_marks_page():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("SELECT DISTINCT TRIM(class_name) FROM admissions WHERE status='Approved' AND TRIM(class_name)!=''")
        classes = sorted(list(set([r[0].strip() for r in cur.fetchall() if r[0]])))
    except: classes=[]
    if not classes: classes=['11th','12th']
    selected_class = (request.args.get('class','') or '11th').strip()
    role = (session.get('role') or '').lower()
    teacher_subject = (session.get('subject') or '').strip()
    students=[]
    try:
        like_class = f"%{selected_class}%"
        like_sub = f"%{teacher_subject}%"
        if role in ['teacher','staff'] and teacher_subject and teacher_subject.lower()!='general':
            cur.execute("""
                SELECT adm_no, name, father_name, class_name, sub1, sub2, sub3, sub4, sub5
                FROM admissions
                WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE UPPER(?)
                AND (UPPER(TRIM(IFNULL(sub1,''))) LIKE UPPER(?) OR UPPER(TRIM(IFNULL(sub2,''))) LIKE UPPER(?) OR UPPER(TRIM(IFNULL(sub3,''))) LIKE UPPER(?) OR UPPER(TRIM(IFNULL(sub4,''))) LIKE UPPER(?) OR UPPER(TRIM(IFNULL(sub5,''))) LIKE UPPER(?))
                ORDER BY name
            """, (like_class, like_sub, like_sub, like_sub, like_sub, like_sub))
        else:
            cur.execute("SELECT adm_no, name, father_name, class_name, sub1, sub2, sub3, sub4, sub5 FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE UPPER(?) ORDER BY name", (like_class,))
        rows=cur.fetchall()
        cols=[d[0] for d in cur.description] if cur.description else []
        students=[dict(zip(cols,r)) for r in rows]
    except Exception as e:
        print(f"Upload marks error: {e}")
    conn.close()
    return render_template('upload_marks.html', classes=classes, selected_class=selected_class, students=students, teacher_subject=teacher_subject, role=session.get('role'), user=session.get('full_name'))

@app.route('/api/upload_bulk_marks', methods=['POST'])
def upload_bulk_marks():
    if not session.get('admin'): return redirect('/admin')
    conn = get_db(); cur = conn.cursor()
    month = (request.form.get('month') or request.form.get('monthly_test') or 'UT-1').strip()
    subject = (request.form.get('subject') or '').strip()
    max_marks_val = request.form.get('max_marks','100')
    try: max_marks_val = int(max_marks_val)
    except: max_marks_val = 100
    user_role = str(session.get('role') or '').lower()
    if user_role not in ['admin', 'administrator'] :
        if session.get('subject') and str(session.get('subject')).lower()!='general':
            subject = session.get('subject')
    adm_nos = request.form.getlist('adm_no')
    marks_list = request.form.getlist('marks')
    if not adm_nos: adm_nos = request.form.getlist('adm_no[]') or request.form.getlist('reg_no')
    if not marks_list: marks_list = request.form.getlist('marks[]') or request.form.getlist('marks_obtained')
    selected_class = request.form.get('selected_class','') or request.args.get('class','')
    count = 0
    for adm_no, marks in zip(adm_nos, marks_list):
        adm_no = str(adm_no).strip().upper()
        marks_str = str(marks).strip()
        if not adm_no or marks_str=='': continue
        try:
            marks_int = int(float(marks_str))
            cur.execute("DELETE FROM monthly_results WHERE TRIM(reg_no)=TRIM(?) AND LOWER(TRIM(subject))=LOWER(TRIM(?)) AND LOWER(TRIM(month))=LOWER(TRIM(?))", (adm_no, subject, month))
            cur.execute("INSERT INTO monthly_results (reg_no, class_name, month, subject, marks, max_marks) VALUES (?,?,?,?,?,?)", (adm_no, selected_class, month, subject, marks_int, max_marks_val))
            conn.commit()
            count += 1
        except Exception as e:
            print(f"Insert fail {adm_no}: {e}")
    conn.close()
    return f"<div style='text-align:center;padding:50px'><h2 style='color:green'>{count} Marks Uploaded for {subject} - {month}</h2><p><a href='/admin/upload_marks?class={selected_class}'>Back</a> <a href='/admin/dashboard'>Dashboard</a></p></div>"

#... all other routes (admissions, activities, results, class_result_report, subject_report, etc.) same as Local but with SQLite syntax
# For full file, copy remaining routes from Local file and replace TOP with LIMIT

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

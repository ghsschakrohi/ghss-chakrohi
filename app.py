from flask import Flask, render_template, request, redirect, session, jsonify, send_file, Response
import sqlite3
import os
import io
import base64
import random
import requests
import urllib.parse
import time
from datetime import datetime
try:
    import pandas as pd
except:
    pd = None
try:
    import qrcode
except:
    qrcode = None

app = Flask(__name__)
app.secret_key = 'ghss-01131502304'
DATABASE = 'school.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS teachers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, designation TEXT, subject TEXT, exp TEXT, qualification TEXT, wef TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, full_name TEXT, role TEXT, subject TEXT, mobile TEXT, is_active INTEGER DEFAULT 1, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY AUTOINCREMENT, enrollment_no TEXT UNIQUE, first_name TEXT, father_name TEXT, class TEXT, dob TEXT, mobile TEXT, address TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS activities (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, activity_date DATE, photo TEXT, uploaded_by TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS monthly_results (id INTEGER PRIMARY KEY AUTOINCREMENT, reg_no TEXT, class_name TEXT, month TEXT, subject TEXT, marks INTEGER, max_marks INTEGER, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS admissions (id INTEGER PRIMARY KEY AUTOINCREMENT, contact_no TEXT, class_name TEXT, adm_no TEXT UNIQUE, name TEXT, father_name TEXT, dob DATE, residence TEXT, caste TEXT, registration_no TEXT, stream TEXT, sub1 TEXT, sub2 TEXT, sub3 TEXT, sub4 TEXT, sub5 TEXT, gender TEXT, status TEXT DEFAULT 'Pending', created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    try: cur.execute("ALTER TABLE admissions ADD COLUMN gender TEXT")
    except: pass
    try: cur.execute("ALTER TABLE admissions ADD COLUMN stream TEXT")
    except: pass
    try: cur.execute("ALTER TABLE admissions ADD COLUMN sub1 TEXT")
    except: pass
    try: cur.execute("ALTER TABLE admissions ADD COLUMN sub2 TEXT")
    except: pass
    try: cur.execute("ALTER TABLE admissions ADD COLUMN sub3 TEXT")
    except: pass
    try: cur.execute("ALTER TABLE admissions ADD COLUMN sub4 TEXT")
    except: pass
    try: cur.execute("ALTER TABLE admissions ADD COLUMN sub5 TEXT")
    except: pass
    try: cur.execute("ALTER TABLE admissions ADD COLUMN caste TEXT")
    except: pass
    cur.execute("SELECT * FROM users WHERE username='principal'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username, password, full_name, role, is_active) VALUES (?,?,?,?,?)", ('principal','admin123','Principal','admin',1))
    cur.execute("SELECT COUNT(*) FROM teachers")
    if cur.fetchone()[0]==0:
        staff=[('Mrs. Pushpa Lochan','Principal','Administration','25','Masters,B.Ed',''),('Mr. Gurmeet Singh','Sr. Lect Sociology - Vice Principal','Sociology','18','Masters, M.Phil,B.Ed',''),('Mr. Daleep Sharma','Sr. Lect Urdu','Urdu','18','Masters, P.hd, B.Ed',''),('Mr. Harveen Singh Sudan','Sr. Lect Political Science','Pol. Science','16','Masters, M.Phil, B.Ed',''),('Mrs. Neeru Ratta','Sr. Lect Education','Education','16','Masters, M.Phil,B.Ed',''),('Mrs. Bindu Devi','Sr. Lect Zoology','Zoology','16','Masters, B.Ed',''),('Mrs. Bindu Dogra','Sr. Lect Hindi','Hindi','16','Masters, NET, B.Ed',''),('Mr. Paramjit Singh','Sr. Lect Computer Science','Computer Science','17','MCA, M.Phil, B.Ed','26-01-2023'),('Mrs. Shammi Chib','Lecturer Physics','Physics','22','M.Sc, B.Ed',''),('Mr. Shakti Kumar','Lecturer Chemistry','Chemistry','33','M.Sc, B.Ed',''),('Mrs. Alka','Lecturer English','English','-','M.A, B.Ed',''),('Mrs. Darshan Kour','I/C Lect Electronics','Electronics','26','M.Sc, B.Ed',''),('Mr. Rajesh Gupta','I/C Lect Botany','Botany','22','M.Sc, B.Ed',''),('Mrs. Ravinder Kour','I/C Lect Maths','Mathematics','22','M.Sc, B.Ed',''),('Mrs. Neelam Sudan','Master','General','22','Masters, B.Ed',''),('Mr. Ram Lal','Master','General','19','Masters, B.Ed',''),('Mr. Shariq Ishaq Mir','Teacher','General','19','MA, B.Ed',''),('Mr. Rohit Gupta','Teacher','General','10','M.Sc, B.Ed',''),('Mrs. Indu Gandhi','Teacher','General','10','M.A, B.Ed',''),('Mr. Sudansh Sharma','Teacher','General','10','M.Sc, B.Ed',''),('Mrs. Meenakshi Gupta','Teacher','General','10','M.A, B.Ed',''),('Mrs. Rasmeet Kour','Teacher','General','10','M.Sc, B.Ed',''),('Mrs. Devinder Kour','Sr. Assistant','Non-Teaching','10','Graduate',''),('Mr. Karanjeet Kumar','Lab. Assistant','Non-Teaching','20','12th',''),('Mr. Rakesh Sharma','Lab Assistant','Non-Teaching','20','12th',''),('Mrs. Asha Devi','Class-IV','Non-Teaching','18','',''),('Mrs. Reena Devi','Class-IV','Non-Teaching','12','',''),('Mr. Ravinder Choudhary','Class-IV','Non-Teaching','10','',''),('Mr. Shubdeep Akash','Class-IV','Non-Teaching','5','MA',''),]
        for s in staff: cur.execute("INSERT INTO teachers (name, designation, subject, exp, qualification, wef) VALUES (?,?,?,?,?,?)", s)
    conn.commit(); conn.close()
    os.makedirs('static/uploads/activities', exist_ok=True)

init_db()

@app.route('/')
def home():
    conn=get_db(); cur=conn.cursor(); cur.execute('SELECT * FROM teachers ORDER BY id'); teachers=cur.fetchall()
    try: cur.execute('SELECT * FROM activities ORDER BY id DESC'); activities=cur.fetchall()
    except: activities=[]
    conn.close(); return render_template('index.html', teachers=teachers, activities=activities)

@app.route('/teacher/<int:id>')
def teacher_detail(id):
    conn=get_db(); cur=conn.cursor(); cur.execute('SELECT * FROM teachers WHERE id=?',(id,)); t=cur.fetchone(); conn.close(); return render_template('teacher.html', t=t)

@app.route('/admin', methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        username=request.form.get('username','').strip(); password=request.form.get('password','').strip()
        conn=get_db(); cur=conn.cursor(); cur.execute("SELECT id, username, password, full_name, role, subject FROM users WHERE username=? AND password=? AND is_active=1",(username,password)); user=cur.fetchone(); conn.close()
        if user:
            session['admin']=True; session['user_id']=user[0]; session['username']=user[1]; session['full_name']=user[3]; session['role']=user[4]
            subj=(user[5] or '').strip(); uname=str(user[1]).lower(); fname=str(user[3]).lower()
            if 'paramjit' in uname or 'paramjit' in fname: subj='Computer Science'
            elif 'shakti' in uname or 'shakti' in fname: subj='Chemistry'
            elif 'shammi' in fname: subj='Physics'
            elif not subj or subj.lower() in ['general','']:
                if str(user[4]).lower()!='admin': subj='Computer Science'
            session['subject']=subj
            return redirect('/admin/dashboard')
        else: return "<h3 style='color:red;text-align:center;margin-top:100px'>Invalid Login<br><a href='/admin'>Try Again</a></h3>"
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cur=conn.cursor(); cur.execute('SELECT * FROM teachers'); teachers=cur.fetchall()
    try: cur.execute('SELECT * FROM users'); all_users=cur.fetchall()
    except: all_users=[]
    try: cur.execute('SELECT COUNT(*) FROM students'); students_count=cur.fetchone()[0]
    except: students_count=0
    try: cur.execute('SELECT COUNT(*) FROM monthly_results'); results_count=cur.fetchone()[0]
    except: results_count=0
    try:
        cur.execute("SELECT COUNT(*) FROM admissions WHERE status='Approved'"); admissions_count=cur.fetchone()[0]
        cur.execute("SELECT * FROM admissions WHERE status='Pending' ORDER BY created_at DESC LIMIT 10"); pending_admissions=cur.fetchall()
        cur.execute("SELECT * FROM admissions WHERE status='Approved' ORDER BY created_at DESC LIMIT 10"); approved_admissions=cur.fetchall()
        admissions=pending_admissions
    except: admissions_count=0; admissions=[]; pending_admissions=[]; approved_admissions=[]
    try: cur.execute("SELECT enrollment_no, first_name FROM students WHERE enrollment_no IS NOT NULL AND TRIM(enrollment_no)!='' LIMIT 500"); students_for_result=cur.fetchall()
    except: students_for_result=[]
    try: cur.execute('SELECT * FROM activities ORDER BY id DESC LIMIT 20'); activities=cur.fetchall()
    except: activities=[]
    conn.close()
    stats={'students':students_count,'results':results_count,'admissions':admissions_count,'teachers':len(teachers)}
    return render_template('dashboard.html', teachers=teachers, stats=stats, users=all_users, admissions=admissions, pending_admissions=pending_admissions, approved_admissions=approved_admissions, students_for_result=students_for_result, activities=activities, user=session.get('full_name'), role=session.get('role'))

@app.route('/logout')
def logout(): session.clear(); return redirect('/admin')

# === LAB FIX - This was missing causing Not Found ===
@app.route('/lab/<lab_name>')
def lab_detail(lab_name):
    labs_data={
        'physics':{'name':'Physics Lab','description':'Well equipped Physics Lab with modern apparatus, vernier calipers, screw gauge, optical bench for practical learning.','photo':'/static/physics.jpg'},
        'chemistry':{'name':'Chemistry Lab','description':'Well equipped Chemistry Lab with chemicals, titration setup and safety measures.','photo':'/static/chemistry.jpg'},
        'biology':{'name':'Biology Lab','description':'Well equipped Biology Lab with microscopes, slides and specimens.','photo':'/static/biology.jpg'},
        'computer':{'name':'Computer Lab','description':'Modern Computer Lab with internet facility and latest systems for students.','photo':'/static/computer.jpg'}
    }
    lab=labs_data.get(lab_name.lower(), {'name':lab_name.title()+' Lab','description':'Well equipped lab for practical learning','photo':'/static/naps_2.jpg'})
    return render_template('lab.html', lab=lab)

@app.route('/results')
def results_page(): return render_template('results.html')

@app.route('/api/check_result', methods=['POST'])
def check_result():
    reg_no=request.form.get('reg_no','').strip().upper()
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT * FROM students WHERE enrollment_no=?",(reg_no,)); student=cur.fetchone()
    if not student: conn.close(); return f"<h2>Student {reg_no} not found</h2><a href='/results'>Back</a>"
    cur.execute("SELECT * FROM monthly_results WHERE reg_no=?",(reg_no,)); results=cur.fetchall(); conn.close()
    if not results: return f"<h2>No results for {reg_no}</h2><a href='/results'>Back</a>"
    total=sum([r[4] for r in results]); max_t=sum([r[5] for r in results]); per=round(total/max_t*100,2) if max_t else 0
    rows="".join([f"<tr><td>{i}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[5]}</td><td>{r[4]}</td></tr>" for i,r in enumerate(results,1)])
    return f"<html><body><h2>{student[2]} - {reg_no} - {total}/{max_t} {per}%</h2><table border=1><tr><th>#</th><th>Month</th><th>Sub</th><th>Max</th><th>Marks</th></tr>{rows}</table><a href='/results'>Back</a></body></html>"

@app.route('/admin/admissions')
def admissions_list():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cur=conn.cursor(); cur.execute('SELECT * FROM admissions ORDER BY created_at DESC'); admissions=cur.fetchall(); conn.close()
    return render_template('admissions_list.html', admissions=admissions, user=session.get('full_name'))

@app.route('/admin/approve/<adm_no>')
def approve_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cur=conn.cursor(); cur.execute("UPDATE admissions SET status='Approved' WHERE adm_no=?",(adm_no,)); conn.commit()
    try: cur.execute("INSERT INTO students (enrollment_no, first_name, father_name, class) SELECT adm_no, name, father_name, class_name FROM admissions WHERE adm_no=? AND adm_no NOT IN (SELECT enrollment_no FROM students)",(adm_no,)); conn.commit()
    except: pass
    conn.close(); return redirect('/admin/admissions')

@app.route('/admin/reject/<adm_no>')
def reject_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cur=conn.cursor(); cur.execute("UPDATE admissions SET status='Rejected' WHERE adm_no=?",(adm_no,)); conn.commit(); conn.close(); return redirect('/admin/admissions')

@app.route('/admin/view/<adm_no>')
def view_admission(adm_no):
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT * FROM admissions WHERE adm_no=?",(adm_no,)); row=cur.fetchone()
    if not row: conn.close(); return "Record not found"
    cols=[d[0] for d in cur.description]; data=dict(zip(cols,row)); conn.close()
    return render_template('admission_view.html', data=data, adm_no=adm_no, user=session.get('full_name'))

@app.route('/activities')
def activities_page():
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT * FROM activities ORDER BY id DESC"); acts=cur.fetchall(); conn.close()
    return render_template('activities.html', activities=acts)

@app.route('/api/upload_activity', methods=['POST'])
def upload_activity():
    if not session.get('admin'): return redirect('/admin')
    title=request.form.get('title','').strip(); desc=request.form.get('description','').strip(); date=request.form.get('activity_date')
    photo_path=""
    if 'photo' in request.files:
        f=request.files['photo']
        if f.filename:
            os.makedirs('static/uploads/activities', exist_ok=True)
            filename=f"act_{int(time.time())}_{f.filename.replace(' ', '_')}"
            save_path=os.path.join('static/uploads/activities', filename); f.save(save_path); photo_path=f"/static/uploads/activities/{filename}"
    conn=get_db(); cur=conn.cursor(); cur.execute("INSERT INTO activities (title, description, activity_date, photo, uploaded_by) VALUES (?,?,?,?,?)",(title,desc,date or datetime.now().date(),photo_path,session.get('username'))); conn.commit(); conn.close()
    return redirect('/admin/dashboard')

@app.route('/api/delete_activity/<int:id>')
def delete_activity(id):
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cur=conn.cursor(); cur.execute('DELETE FROM activities WHERE id=?',(id,)); conn.commit(); conn.close(); return redirect('/admin/dashboard')

@app.route('/admin/student_report')
def student_report():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cur=conn.cursor(); cur.execute("SELECT name, father_name, class_name, contact_no, stream, dob, registration_no, adm_no, caste FROM admissions WHERE status='Approved' ORDER BY adm_no ASC"); data=cur.fetchall(); conn.close()
    class Obj: pass
    rows=[]
    for d in data:
        o=Obj(); o.name,o.father_name,o.class_name,o.contact_no,o.stream,o.dob,o.registration_no,o.adm_no,o.caste=d; rows.append(o)
    return render_template('student_report.html', rows=rows, user=session.get('full_name'), role=session.get('role'))

@app.route('/admin/category_report')
def category_report():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cur=conn.cursor()
    try: cur.execute("SELECT COALESCE(caste,'') as caste, COUNT(*) FROM admissions WHERE status='Approved' GROUP BY caste"); caste_data=cur.fetchall()
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
    def get_count(q):
        try: cur.execute(q); r=cur.fetchone(); return r[0] if r else 0
        except: return 0
    boys_total=get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(gender)) IN ('M','MALE','BOY')")
    girls_total=get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(gender)) IN ('F','FEMALE','GIRL')")
    total_11=get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%11TH%'")
    total_12=get_count("SELECT COUNT(*) FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE '%12TH%'")
    conn.close()
    data={'sc':sc,'st':st,'obc':obc,'general':general,'other':other,'total_approved':total_approved,'boys_total':boys_total,'girls_total':girls_total,'boys_11':0,'girls_11':0,'total_11':total_11,'boys_12':0,'girls_12':0,'total_12':total_12}
    return render_template('category_report.html', data=data, user=session.get('full_name'), role=session.get('role'))

@app.route('/admin/upload_marks')
def upload_marks_page():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cur=conn.cursor()
    try: cur.execute("SELECT DISTINCT TRIM(class_name) FROM admissions WHERE status='Approved' AND TRIM(class_name)!=''"); classes=sorted(list(set([r[0].strip() for r in cur.fetchall() if r[0]])))
    except: classes=[]
    if not classes: classes=['11th','12th']
    selected_class=(request.args.get('class','') or '11th').strip()
    role=(session.get('role') or '').lower(); teacher_subject=(session.get('subject') or '').strip()
    students=[]
    try:
        like_class=f"%{selected_class}%"; like_sub=f"%{teacher_subject}%"
        if role in ['teacher','staff'] and teacher_subject and teacher_subject.lower()!='general':
            cur.execute("SELECT adm_no, name, father_name, class_name, sub1, sub2, sub3, sub4, sub5 FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE UPPER(?) AND (UPPER(TRIM(IFNULL(sub1,''))) LIKE UPPER(?) OR UPPER(TRIM(IFNULL(sub2,''))) LIKE UPPER(?) OR UPPER(TRIM(IFNULL(sub3,''))) LIKE UPPER(?) OR UPPER(TRIM(IFNULL(sub4,''))) LIKE UPPER(?) OR UPPER(TRIM(IFNULL(sub5,''))) LIKE UPPER(?)) ORDER BY name",(like_class, like_sub, like_sub, like_sub, like_sub, like_sub))
        else: cur.execute("SELECT adm_no, name, father_name, class_name, sub1, sub2, sub3, sub4, sub5 FROM admissions WHERE status='Approved' AND UPPER(TRIM(class_name)) LIKE UPPER(?) ORDER BY name",(like_class,))
        rows=cur.fetchall(); cols=[d[0] for d in cur.description] if cur.description else []; students=[dict(zip(cols,r)) for r in rows]
    except Exception as e: print(f"Upload marks error: {e}")
    conn.close(); return render_template('upload_marks.html', classes=classes, selected_class=selected_class, students=students, teacher_subject=teacher_subject, role=session.get('role'), user=session.get('full_name'))

@app.route('/api/upload_bulk_marks', methods=['POST'])
def upload_bulk_marks():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cur=conn.cursor()
    month=(request.form.get('month') or 'UT-1').strip(); subject=(request.form.get('subject') or '').strip()
    max_marks_val=request.form.get('max_marks','100')
    try: max_marks_val=int(max_marks_val)
    except: max_marks_val=100
    user_role=str(session.get('role') or '').lower()
    if user_role not in ['admin','administrator']:
        if session.get('subject') and str(session.get('subject')).lower()!='general': subject=session.get('subject')
    adm_nos=request.form.getlist('adm_no'); marks_list=request.form.getlist('marks')
    if not adm_nos: adm_nos=request.form.getlist('adm_no[]')
    if not marks_list: marks_list=request.form.getlist('marks[]')
    selected_class=request.form.get('selected_class',''); count=0
    for adm_no,marks in zip(adm_nos, marks_list):
        adm_no=str(adm_no).strip().upper(); marks_str=str(marks).strip()
        if not adm_no or marks_str=='': continue
        try:
            marks_int=int(float(marks_str))
            cur.execute("DELETE FROM monthly_results WHERE TRIM(reg_no)=TRIM(?) AND LOWER(TRIM(subject))=LOWER(TRIM(?)) AND LOWER(TRIM(month))=LOWER(TRIM(?))",(adm_no,subject,month))
            cur.execute("INSERT INTO monthly_results (reg_no, class_name, month, subject, marks, max_marks) VALUES (?,?,?,?,?,?)",(adm_no,selected_class,month,subject,marks_int,max_marks_val)); conn.commit(); count+=1
        except Exception as e: print(f"Insert fail {adm_no}: {e}")
    conn.close()
    return f"<div style='text-align:center;padding:50px'><h2 style='color:green'>{count} Marks Uploaded for {subject} - {month}</h2><p><a href='/admin/upload_marks?class={selected_class}'>Back</a> <a href='/admin/dashboard'>Dashboard</a></p></div>"

@app.route('/admin/class_result_report', methods=['GET','POST'])
def class_result_report():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cur=conn.cursor()
    try: cur.execute("SELECT DISTINCT class_name FROM admissions WHERE status='Approved' AND class_name IS NOT NULL AND class_name!= '' ORDER BY class_name"); classes=[r[0].strip() for r in cur.fetchall() if r[0]]
    except: classes=['11th','12th']
    if not classes: classes=['11th','12th']
    selected_class=(request.form.get('class_name') or request.args.get('class_name') or classes[0]).strip()
    base_query="SELECT DISTINCT adm_no, name, father_name, class_name, stream, sub1, sub2, sub3, sub4, sub5 FROM admissions WHERE status='Approved' AND class_name =? ORDER BY adm_no ASC"
    cur.execute(base_query, (selected_class,)); rows=cur.fetchall()
    report_data=[]; sno=1
    for row in rows:
        adm_no, name, father_name, class_name, stream, sub1, sub2, sub3, sub4, sub5=row
        opted=[str(s).strip() for s in [sub1,sub2,sub3,sub4,sub5] if s and str(s).strip()][:5]
        while len(opted)<5: opted.append("")
        try: cur.execute("SELECT subject, marks, max_marks FROM monthly_results WHERE TRIM(reg_no)=TRIM(?)",(adm_no,)); marks_map={subj.strip().lower(): (m, mx) for subj, m, mx in cur.fetchall() if subj}
        except: marks_map={}
        total_obt=0; total_max=0
        for sub in opted:
            if sub.lower() in marks_map:
                total_obt+=marks_map[sub.lower()][0] or 0; total_max+=marks_map[sub.lower()][1] or 10
        per=round(total_obt/total_max*100,2) if total_max else 0
        report_data.append({'sno':sno,'roll_no':adm_no,'adm_no':adm_no,'name':name,'father_name':father_name,'class_name':class_name,'stream':stream,'opted_subjects':opted,'total':total_obt,'max_total':total_max,'percentage':per,'result':'Pass' if per>=33 else 'Fail'}); sno+=1
    conn.close()
    return render_template('class_result_report.html', classes=classes, report_data=report_data, selected_class=selected_class, selected_stream='', search_name='', user=session.get('full_name'), role=session.get('role'))

@app.route('/admin/subject_report')
def subject_report():
    if not session.get('admin'): return redirect('/admin')
    conn=get_db(); cur=conn.cursor()
    query="SELECT TRIM(subject) as subject_name, COUNT(*) as total_students FROM (SELECT sub1 as subject FROM admissions WHERE status='Approved' AND TRIM(IFNULL(sub1,''))!= '' UNION ALL SELECT sub2 FROM admissions WHERE status='Approved' AND TRIM(IFNULL(sub2,''))!= '' UNION ALL SELECT sub3 FROM admissions WHERE status='Approved' AND TRIM(IFNULL(sub3,''))!= '' UNION ALL SELECT sub4 FROM admissions WHERE status='Approved' AND TRIM(IFNULL(sub4,''))!= '' UNION ALL SELECT sub5 FROM admissions WHERE status='Approved' AND TRIM(IFNULL(sub5,''))!= '') AS all_subs GROUP BY TRIM(subject) ORDER BY total_students DESC"
    cur.execute(query); subject_data=cur.fetchall()
    cur.execute("SELECT DISTINCT TRIM(class_name) FROM admissions WHERE status='Approved' AND class_name!= ''"); classes=[r[0] for r in cur.fetchall() if r[0]]
    conn.close(); return render_template('subject_report.html', subject_data=subject_data, breakdown=[], classes=classes, selected_class='', user=session.get('full_name'), role=session.get('role'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)

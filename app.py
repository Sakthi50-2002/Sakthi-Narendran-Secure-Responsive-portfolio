import os, sqlite3, csv, shutil
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, flash, session, jsonify, send_from_directory
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'sakthi-secret')
ADMIN_USER = os.getenv('ADMIN_USER', 'Sakthi')
ADMIN_PASS = os.getenv('ADMIN_PASS', 'sakthi50.')

security_logs, activity_logs, request_logs = [], [], []
blocked_ips = set()
spam_words = ['buy now', 'click here', 'lottery', 'prize']
failed_attempts = {}

def add_security_log(event, level='INFO'):
    security_logs.append({'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'event': event,'level': level,'ip': request.remote_addr or '127.0.0.1'})
    if len(security_logs) > 100: security_logs.pop(0)
def add_activity_log(action):
    activity_logs.append({'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'action': action,'ip': request.remote_addr or '127.0.0.1'})

DB_NAME = 'portfolio.db'
def init_db():
    conn = sqlite3.connect(DB_NAME); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT,email TEXT,phone TEXT,subject TEXT,message TEXT,spam INTEGER DEFAULT 0,date TEXT,ip TEXT)''')
    conn.commit(); conn.close()
init_db()

def get_messages(search=None):
    conn = sqlite3.connect(DB_NAME); conn.row_factory = sqlite3.Row; c = conn.cursor()
    if search: c.execute("SELECT * FROM messages WHERE name LIKE? OR email LIKE? OR message LIKE? ORDER BY id DESC",(f'%{search}%',f'%{search}%',f'%{search}%'))
    else: c.execute("SELECT * FROM messages ORDER BY id DESC")
    rows = c.fetchall(); conn.close(); return rows

# ===== ADVANCE SKILLS & PROJECTS - CLICKABLE FIX =====
skills_data = {
 1: {'name':'Python','percent':90,'level':'Advanced','exp':'2+ Years','desc':'Advanced Python Flask Secure Coding - Portfolio Project','details':['Flask Framework','Secure Authentication','SQLAlchemy ORM','REST APIs','Jinja2 Templates','Honeypot Spam Detection','Brute Force Protection 3 Attempts','Admin Dashboard with Logs'],'icon':'fa-python','color':'#3776AB'},
 2: {'name':'Java','percent':75,'level':'Intermediate','exp':'1.5 Years','desc':'Java OOPs Concepts - Strong OOPs foundation','details':['OOPs Principles','Exception Handling','Collections Framework','Multithreading','JDBC Connection','Spring Boot Basics'],'icon':'fa-java','color':'#ED8B00'},
 3: {'name':'CSS','percent':85,'level':'Advanced','exp':'2 Years','desc':'Modern Responsive CSS - Animations & Design','details':['Flexbox Layout','CSS Grid','Keyframes Animations','Media Queries Responsive','Bootstrap 5','Gradient Design','AOS Library','Float Animations'],'icon':'fa-css3-alt','color':'#1572B6'},
 4: {'name':'JavaScript','percent':80,'level':'Advanced','exp':'1.5 Years','desc':'JavaScript ES6+ Advance - Interactive Web','details':['ES6+ Features','DOM Manipulation','Fetch API','Async Await','Typing Animation Effect','Form Validation','LocalStorage'],'icon':'fa-js','color':'#F7DF1E'},
 5: {'name':'UI/UX Designer','percent':88,'level':'Advanced','exp':'2 Years','desc':'Figma Modern Design - User Friendly','details':['Figma Design','User Research','Wireframing','Prototyping','Responsive Design','Color Theory','Adobe XD'],'icon':'fa-palette','color':'#FF3366'},
 6: {'name':'C++','percent':82,'level':'Intermediate','exp':'1 Year','desc':'C++ OOPs STL Advance - Data Structures','details':['OOPs Concepts','STL Library','Pointers Advance','File Handling','Data Structures','Algorithms'],'icon':'fa-code','color':'#00599C'}
}

projects_data = {
 1: {'title':'Blood Bank Management','tech':'Python Flask MySQL','tables':'8 Tables','status':'Live','desc':'Secure Blood Bank donor management system with 8 tables - donor, blood stock, request, hospital integration. Real-world project with secure authentication.','features':['Donor Registration with Validation','Blood Stock Management Live','Request Tracking System','Hospital Integration','Admin Dashboard with Search','Secure Login with Logs'],'tech_stack':['Python Flask','MySQL 8 Tables','Bootstrap 5','Security Logs','Responsive Design'],'db_info':'8 Tables: users, donors, blood_stock, requests, hospitals, donations, admins, logs','icon':'fa-tint','color':'#ff0000'},
 2: {'title':'Crime Tracking Management','tech':'Python Flask MySQL','tables':'9 Tables','status':'Secure','desc':'Crime tracking with FIR, investigation, evidence management - 9 tables secure system with role based access.','features':['FIR Registration','Investigation Tracking','Evidence Management','Criminal Database Search','Police Dashboard','Case Status Update'],'tech_stack':['Python Flask','MySQL 9 Tables','Secure Auth','Role Based Access'],'db_info':'9 Tables: fir, crime, criminals, evidence, police, stations, investigation, users, logs','icon':'fa-shield-alt','color':'#2c3e50'},
 3: {'title':'Hospital Management','tech':'Python Flask MySQL','tables':'10 Tables','status':'ACID','desc':'Hospital management with patient, doctor, appointment, billing - 10 tables ACID compliant transaction.','features':['Patient Management System','Doctor Scheduling','Appointment Booking Advance','Billing System with Tax','Lab Reports Upload','Pharmacy Integration'],'tech_stack':['Python Flask','MySQL ACID','Transaction Management','Bootstrap'],'db_info':'10 Tables: patients, doctors, appointments, billing, lab, pharmacy, staff, rooms, users, logs','icon':'fa-hospital','color':'#00b894'},
 4: {'title':'Bank Management','tech':'Python Flask MySQL ACID','tables':'10 Tables','status':'ACID + Transaction','desc':'Bank management with ACID transaction, deposit, withdrawal, loan - secure banking system with audit.','features':['Account Creation Secure','Deposit Withdrawal ACID','Fund Transfer with OTP','Loan Management','Transaction History Logs','ACID Compliance Banking'],'tech_stack':['Python Flask','MySQL ACID','Transaction','Security Audit'],'db_info':'10 Tables: accounts, customers, transactions, loans, deposits, branches, employees, users, audit, logs','icon':'fa-university','color':'#e17055'},
 5: {'title':'Library Management','tech':'Python Flask SQLite','tables':'7 Tables','status':'SQLite','desc':'Library book issue, return, fine, student management - 7 tables SQLite lightweight system.','features':['Book Management CRUD','Issue Return Tracking','Fine Calculation Auto','Student Tracking','Search Books Advance','Inventory Management'],'tech_stack':['Python Flask','SQLite 7 Tables','Bootstrap','CRUD Operations'],'db_info':'7 Tables: books, students, issue, return, fine, staff, users','icon':'fa-book','color':'#6c5ce7'},
 6: {'title':'Education Management','tech':'Python Flask MySQL','tables':'12 Tables','status':'NEW','desc':'Education management with student, course, exam, attendance - 12 tables NEW advance system with result generation.','features':['Student Management','Course Management Advance','Exam Scheduling Auto','Attendance Tracking','Result Generation','Fee Management System'],'tech_stack':['Python Flask','MySQL 12 Tables','Advance Features','12 Tables NEW'],'db_info':'12 Tables: students, courses, exams, attendance, fees, teachers, classes, results, timetable, library, hostel, users','icon':'fa-chalkboard-teacher','color':'#0984e3'}
}

@app.route('/')
def index(): return render_template('index.html')

@app.route('/cert/<filename>')
def serve_cert(filename):
    cert_folder = os.path.join('static','certificates')
    exact_path = os.path.join(cert_folder,filename)
    if os.path.exists(exact_path): return send_from_directory(cert_folder,filename)
    if os.path.exists(cert_folder):
        for f in os.listdir(cert_folder):
            if filename.lower().split('.')[0] in f.lower() or f.lower().split('.')[0] in filename.lower(): return send_from_directory(cert_folder,f)
    return "Cert Not Found",404

@app.route('/profile-image')
def serve_profile():
    for folder,file in [(os.path.join('static','images'),'profile.jpeg'),(os.path.join('static','images'),'profile.jpg')]:
        if os.path.exists(os.path.join(folder,file)): return send_from_directory(folder,file)
    return redirect('https://via.placeholder.com/260?text=SAKTHI')

@app.route('/resume')
def serve_resume():
    for folder in [os.path.join('static','certificates'),os.path.join('static','images'),'static']:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if 'resume' in f.lower() and f.lower().endswith('.pdf'): return send_from_directory(folder,f)
    return "Resume not found",404

@app.route('/contact',methods=['POST'])
def contact():
    if request.form.get('website'): add_security_log('Honeypot Bot blocked','WARNING'); flash('Bot blocked!','danger'); return redirect('/#contact')
    name=request.form.get('name','').strip(); email=request.form.get('email','').strip(); phone=request.form.get('phone','').strip(); subject=request.form.get('subject','').strip(); message=request.form.get('message','').strip()
    spam=0; lower=message.lower()
    for w in spam_words:
        if w in lower: spam=1; break
    if not name or not email or not message: flash('Fill required fields!','danger'); return redirect('/#contact')
    conn=sqlite3.connect(DB_NAME); c=conn.cursor(); c.execute("INSERT INTO messages (name,email,phone,subject,message,spam,date,ip) VALUES (?,?,?,?,?,?,?,?)",(name,email,phone,subject,message,spam,datetime.now().strftime('%Y-%m-%d %H:%M:%S'),request.remote_addr)); conn.commit(); conn.close()
    if spam==1: add_security_log(f'Spam from {name}','WARNING')
    else: add_security_log(f'Good message from {name}','SUCCESS')
    add_activity_log(f'Contact: {name}'); request_logs.append({'time':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'ip':request.remote_addr,'name':name})
    flash(f'Thank you {name}! Message Sent Successfully ✅','success'); return redirect('/#contact')

@app.route('/skill/<int:sid>')
def skill_detail(sid):
    s = skills_data.get(sid)
    if not s: return jsonify({'error':'Not found'}),404
    return jsonify(s)

@app.route('/project/<int:pid>')
def project_detail(pid):
    p = projects_data.get(pid)
    if not p: return "Project Not Found - Check app.py projects_data",404
    return render_template('detail_page.html', project=p, pid=pid)

def login_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        if 'admin_logged_in' not in session: return redirect('/admin/login')
        return f(*args,**kwargs)
    return decorated

@app.route('/admin/login',methods=['GET','POST'])
def admin_login():
    ip = request.remote_addr or '127.0.0.1'
    if ip in failed_attempts:
        data = failed_attempts[ip]
        if data['count'] >= 3:
            diff = (datetime.now() - data['last_time']).total_seconds()
            if diff < 300:
                flash(f'Too many failed attempts! Blocked for {int((300-diff)//60)+1} min.','danger')
                return render_template('admin_login.html', attempts=data['count'], blocked=True)
            else: failed_attempts[ip] = {'count': 0, 'last_time': datetime.now()}
    if request.method=='POST':
        if ip in failed_attempts and failed_attempts[ip]['count'] >= 3:
            diff = (datetime.now() - failed_attempts[ip]['last_time']).total_seconds()
            if diff < 300:
                flash('Blocked! Wait 5 minutes.','danger')
                return render_template('admin_login.html', attempts=3, blocked=True)
        user=request.form.get('username'); pwd=request.form.get('password')
        if user==ADMIN_USER and pwd==ADMIN_PASS:
            if ip in failed_attempts: del failed_attempts[ip]
            session['admin_logged_in']=True; add_security_log('ADMIN LOGIN SUCCESS','SUCCESS'); flash('Login Success!','success'); return redirect('/admin/dashboard')
        else:
            if ip not in failed_attempts: failed_attempts[ip] = {'count': 1, 'last_time': datetime.now()}
            else: failed_attempts[ip]['count'] += 1; failed_attempts[ip]['last_time'] = datetime.now()
            count = failed_attempts[ip]['count']; add_security_log(f'ADMIN LOGIN FAILED Attempt {count}/3','FAILED')
            if count >= 3:
                flash(f'Invalid! 3/3 Failed! Blocked 5 min!','danger'); return render_template('admin_login.html', attempts=count, blocked=True)
            else:
                flash(f'Invalid! Attempt {count}/3 - {3-count} left!','danger'); return render_template('admin_login.html', attempts=count, blocked=False)
    count = failed_attempts.get(ip, {}).get('count', 0)
    return render_template('admin_login.html', attempts=count, blocked=False)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    messages=get_messages(); total=len(messages)
    return render_template('admin_dashboard.html',messages=messages,total=total,security_logs=security_logs[-20:][::-1],activity_logs=activity_logs[-20:][::-1],req_logs=request_logs[-20:][::-1],blocked_ips=list(blocked_ips),search=None)

@app.route('/admin/logout')
def admin_logout(): session.pop('admin_logged_in',None); flash('Logged out!','info'); return redirect('/admin/login')
@app.route('/admin/delete/<int:mid>')
@login_required
def admin_delete(mid): conn=sqlite3.connect(DB_NAME); c=conn.cursor(); c.execute("DELETE FROM messages WHERE id=?",(mid,)); conn.commit(); conn.close(); flash(f'Msg {mid} deleted!','success'); return redirect('/admin/dashboard')
@app.route('/admin/search')
@login_required
def admin_search(): q=request.args.get('q',''); messages=get_messages(search=q); total=len(get_messages()); return render_template('admin_dashboard.html',messages=messages,total=total,security_logs=security_logs[-20:][::-1],activity_logs=activity_logs[-20:][::-1],req_logs=request_logs[-20:][::-1],blocked_ips=list(blocked_ips),search=q)
@app.route('/admin/backup')
@login_required
def admin_backup(): fname=f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"; shutil.copy(DB_NAME,fname); add_security_log(f'Backup {fname}','INFO'); return send_from_directory('.',fname,as_attachment=True)
@app.route('/admin/export-csv')
@login_required
def export_csv():
    messages=get_messages(); fname='messages_export.csv'
    with open(fname,'w',newline='',encoding='utf-8') as f:
        writer=csv.writer(f); writer.writerow(['ID','Name','Email','Phone','Subject','Message','Spam','Date','IP'])
        for m in messages: writer.writerow([m['id'],m['name'],m['email'],m['phone'],m['subject'],m['message'],m['spam'],m['date'],m['ip']])
    return send_from_directory('.',fname,as_attachment=True)

if __name__=='__main__': app.run(debug=True)
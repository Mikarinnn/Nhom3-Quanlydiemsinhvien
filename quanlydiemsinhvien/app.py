from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = '123456'

# CẤU HÌNH DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/quanlydiemsinhvien'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# KHỞI TẠO DATABASE
db = SQLAlchemy(app)

# 1. Role - phân quyền
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    # Thiết lập mối quan hệ
    users = db.relationship('User', backref='role', lazy=True)

# 2. User - tài khoản
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False) 
    password_hash = db.Column(db.String(255), nullable=False)        
    full_name = db.Column(db.String(100), nullable=False)            
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# 3. Lớp/ngành
class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    major = db.Column(db.String(100), nullable=False)      
    
    scores = db.relationship('Score', backref='student', lazy=True, cascade="all, delete-orphan")

# 4. Môn học
class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    
    scores = db.relationship('Score', backref='subject', lazy=True)

# 5. Điểm số
class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    
    score_a = db.Column(db.Float, nullable=False, default=0.0)  
    score_b = db.Column(db.Float, nullable=False, default=0.0)  
    score_c = db.Column(db.Float, nullable=False, default=0.0) 

    @property
    def gpa_scale_10(self):
        total = (self.score_a * 0.1) + (self.score_b * 0.3) + (self.score_c * 0.6)
        return round(total, 2)
    
    @property
    def gpa_scale_4(self):
        score_10 = self.gpa_scale_10
        if score_10 >= 8.5: return 4.0  
        if score_10 >= 7.0: return 3.0  
        if score_10 >= 5.5: return 2.0  
        if score_10 >= 4.0: return 1.0  
        return 0.0                      

# TRANG CHỦ
@app.route('/')
def trangchu():
    return render_template('trangchu.html')

# ĐĂNG KÝ
@app.route('/dangky', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('trangchu'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        class_name = request.form.get('class_name')
        major = request.form.get('major')
        
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Tài khoản này đã tồn tại!')
            return redirect(url_for('register')) 
            
        student_role = Role.query.filter_by(name='Student').first()
        if not student_role:
            student_role = Role(name='Student')
            db.session.add(student_role)
            db.session.commit()
            
        # Lưu thông tin User mới
        new_user = User(username=username, full_name=full_name, role=student_role)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Lưu thông tin Lớp và Ngành 
        new_profile = StudentProfile(user_id=new_user.id, class_name=class_name, major=major)
        db.session.add(new_profile)
        db.session.commit()
        
        flash('Đăng ký tài khoản sinh viên thành công! Vui lòng đăng nhập.')
        return redirect(url_for('login')) 
        
    return render_template('dangky.html')

# ĐĂNG NHẬP
@app.route('/dangnhap', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('trangchu')) 
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['full_name'] = user.full_name
            session['role'] = user.role.name 
            
            return redirect(url_for('trangchu')) 
        else:
            flash('Sai tài khoản hoặc mật khẩu!')
            return redirect(url_for('login')) 
            
    return render_template('dangnhap.html')

# ĐĂNG XUẤT
@app.route('/dangxuat')
def logout():
    session.clear() 
    return redirect(url_for('trangchu'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all() #Tạo database
        
        # Tạo role admin cho database
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            admin_role = Role(name='Admin')
            db.session.add(admin_role)
            db.session.commit()
            
        # Tạo tài khoản admin mặc định
        check_admin = User.query.filter_by(username='admin').first()
        if not check_admin:
            admin_user = User(username='admin', full_name='Giảng viên A', role=admin_role)
            admin_user.set_password('123456')
            db.session.add(admin_user)
            db.session.commit()
            print("Đã tự động khởi tạo tài khoản Admin (admin / 123456)")
            
    app.run(debug=True)
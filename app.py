from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# CẤU HÌNH DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/quanlydiemsinhvien'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# KHỞI TẠO DATABASE
db = SQLAlchemy(app)

# Role - phân quyền
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    
    # Thiết lập mối quan hệ: Một quyền có thể áp dụng cho nhiều Người dùng
    users = db.relationship('User', backref='role', lazy=True)

# 2. User - tài khoản
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False) # Tài khoản
    password_hash = db.Column(db.String(255), nullable=False)        # Mật khẩu (đã mã hóa)
    full_name = db.Column(db.String(100), nullable=False)            # Họ và tên
    
    # liên kết tới bảng Quyền
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan")

    # Hàm hỗ trợ mã hóa mật khẩu bảo mật
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Lớp/ngành
class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    major = db.Column(db.String(100), nullable=False)      
    
    # Mối quan hệ: Một sinh viên có thể có nhiều đầu điểm
    scores = db.relationship('Score', backref='student', lazy=True, cascade="all, delete-orphan")

# Môn học
class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False) # Tên môn học
    
    scores = db.relationship('Score', backref='subject', lazy=True)

# Điểm số
class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    
    # Chia làm 3 đầu điểm a b c
    score_a = db.Column(db.Float, nullable=False, default=0.0)  
    score_b = db.Column(db.Float, nullable=False, default=0.0)  
    score_c = db.Column(db.Float, nullable=False, default=0.0) 

    @property
    def gpa_scale_10(self):
        total = (self.score_a * 0.1) + (self.score_b * 0.3) + (self.score_c * 0.6)
        return round(total, 2)
    
    # Tự động quy đổi từ Hệ 10 sang Hệ 4 (GPA tiêu chuẩn đại học)
    @property
    def gpa_scale_4(self):
        score_10 = self.gpa_scale_10
        if score_10 >= 8.5: return 4.0  
        if score_10 >= 7.0: return 3.0  
        if score_10 >= 5.5: return 2.0  
        if score_10 >= 4.0: return 1.0  
        return 0.0                      

# TRANG CHỦ
@app.route('/trangchu')
def index():
    return "Kết nối Laragon MySQL thành công!"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
    app.run(debug=True)
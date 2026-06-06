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
    major = db.Column(db.String(100), nullable=False, default='Đại cương')
    
    scores = db.relationship('Score', backref='subject', lazy=True)

# 5. Điểm số
class Score(db.Model):
    __tablename__ = 'scores'
    id = db.Column(db.Integer, primary_key=True)
    student_profile_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    
    semester = db.Column(db.String(50), nullable=False, default='Học kỳ 1')
    
    score_a = db.Column(db.Float, nullable=False, default=0.0)  
    score_b = db.Column(db.Float, nullable=False, default=0.0)  
    score_c = db.Column(db.Float, nullable=False, default=0.0) 

    @property
    def gpa_scale_10(self):
        total = (self.score_a * 0.6) + (self.score_b * 0.3) + (self.score_c * 0.1)
        return round(total, 2)
    
    @property
    def gpa_scale_4(self):
        score_10 = self.gpa_scale_10
        # Thang điểm chuẩn hệ tín chỉ Việt Nam
        if score_10 >= 8.5: return 4.0  # Điểm A
        if score_10 >= 8.0: return 3.5  # Điểm B+
        if score_10 >= 7.0: return 3.0  # Điểm B
        if score_10 >= 6.5: return 2.5  # Điểm C+
        if score_10 >= 5.5: return 2.0  # Điểm C
        if score_10 >= 5.0: return 1.5  # Điểm D+
        if score_10 >= 4.0: return 1.0  # Điểm D
        return 0.0                      # Điểm F                     

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

######################################################
# Minh Đức

# QUẢN LÝ DANH SÁCH SINH VIÊN
@app.route('/admin/students')
def admin_students():
    if session.get('role') != 'Admin':
        return redirect(url_for('trangchu'))
            
    keyword = request.args.get('keyword', '')
    class_filter = request.args.get('class_filter', '')
    major_filter = request.args.get('major_filter', '')

    query = User.query.join(Role).filter(Role.name == 'Student').outerjoin(StudentProfile)

    #Lọc theo từ khóa
    if keyword:
        query = query.filter(db.or_(
            User.username.ilike(f'%{keyword}%'),
            User.full_name.ilike(f'%{keyword}%')
        ))
        
    #Lọc theo Lớp
    if class_filter:
        query = query.filter(StudentProfile.class_name == class_filter)
        
    #Lọc theo Ngành
    if major_filter:
        query = query.filter(StudentProfile.major == major_filter)

    students = query.all()

    classes = db.session.query(StudentProfile.class_name).distinct().filter(StudentProfile.class_name != None).all()
    classes = [c[0] for c in classes] 
    
    majors = db.session.query(StudentProfile.major).distinct().filter(StudentProfile.major != None).all()
    majors = [m[0] for m in majors]

    return render_template('quanlysinhvien.html', 
                           students=students, 
                           keyword=keyword, 
                           class_filter=class_filter, 
                           major_filter=major_filter,
                           classes=classes,
                           majors=majors)

# SỬA SINH VIÊN
@app.route('/admin/students/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_student(user_id):
    if session.get('role') != 'Admin':
        return redirect(url_for('trangchu'))
        
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        if user.student_profile:
            user.student_profile.class_name = request.form.get('class_name')
            user.student_profile.major = request.form.get('major')
            
        db.session.commit()
        flash('Đã cập nhật thông tin sinh viên thành công!')
        return redirect(url_for('admin_students'))
        
    return render_template('suasinhvien.html', user=user)

# XÓA SINH VIÊN
@app.route('/admin/students/delete/<int:user_id>')
def delete_student(user_id):
    if session.get('role') != 'Admin':
        return redirect(url_for('trangchu'))
        
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Đã xóa sinh viên và toàn bộ dữ liệu liên quan.')
    return redirect(url_for('admin_students'))

# QUẢN LÝ HỌC PHẦN
@app.route('/admin/subjects', methods=['GET', 'POST'])
def manage_subjects():
    if session.get('role') != 'Admin':
        return redirect(url_for('trangchu'))
        
    # XỬ LÝ THÊM MÔN HỌC
    if request.method == 'POST':
        subject_name = request.form.get('name')
        subject_major = request.form.get('major') 
        
        exists = Subject.query.filter_by(name=subject_name).first()
        if exists:
            flash('Môn học này đã tồn tại trong hệ thống!')
        else:
            new_subject = Subject(name=subject_name, major=subject_major)
            db.session.add(new_subject)
            db.session.commit()
            flash('Thêm môn học thành công!')
            
        return redirect(url_for('manage_subjects'))
        
    # XỬ LÝ LỌC & TÌM KIẾM
    keyword = request.args.get('keyword', '')
    major_filter = request.args.get('major_filter', '')
    
    query = Subject.query
    if keyword:
        query = query.filter(Subject.name.ilike(f'%{keyword}%'))
    if major_filter:
        query = query.filter(Subject.major == major_filter)
        
    # SẮP XẾP THEO CHUYÊN NGÀNH
    subjects = query.order_by(Subject.major, Subject.name).all()
    
    # LẤY DANH SÁCH CHUYÊN NGÀNH HIỆN CÓ
    majors = db.session.query(Subject.major).distinct().all()
    majors = [m[0] for m in majors if m[0]]

    return render_template('quanlyhocphan.html', subjects=subjects, keyword=keyword, major_filter=major_filter, majors=majors)

# XÓA HỌC PHẦN
@app.route('/admin/subjects/delete/<int:subject_id>')
def delete_subject(subject_id):
    if session.get('role') != 'Admin':
        return redirect(url_for('trangchu'))
        
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Đã xóa môn học!')
    return redirect(url_for('manage_subjects'))

# QUẢN LÝ HỌC PHẦN DÀNH CHO GIẢNG VIÊN
@app.route('/admin/enroll', methods=['GET'])
def admin_enroll():
    if session.get('role') != 'Admin':
        return redirect(url_for('trangchu'))

    keyword = request.args.get('keyword', '')
    class_filter = request.args.get('class_filter', '')
    major_filter = request.args.get('major_filter', '')

    query = User.query.join(Role).filter(Role.name == 'Student').outerjoin(StudentProfile)

    if keyword:
        query = query.filter(db.or_(User.username.ilike(f'%{keyword}%'), User.full_name.ilike(f'%{keyword}%')))
    if class_filter:
        query = query.filter(StudentProfile.class_name == class_filter)
    if major_filter:
        query = query.filter(StudentProfile.major == major_filter)

    students = query.all()

    classes = [c[0] for c in db.session.query(StudentProfile.class_name).distinct().filter(StudentProfile.class_name != None).all()]
    majors = [m[0] for m in db.session.query(StudentProfile.major).distinct().filter(StudentProfile.major != None).all()]

    return render_template('quanlyhocphansinhvien.html', students=students, keyword=keyword, class_filter=class_filter, major_filter=major_filter, classes=classes, majors=majors)

# THÊM/XÓA HỌC PHẦN
@app.route('/admin/enroll/<int:profile_id>', methods=['GET', 'POST'])
def admin_manage_student_enrollment(profile_id):
    if session.get('role') != 'Admin':
        return redirect(url_for('trangchu'))
        
    profile = StudentProfile.query.get_or_404(profile_id)
    
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        semester = request.form.get('semester') 
        
        existing = Score.query.filter_by(student_profile_id=profile.id, subject_id=subject_id).first()
        if existing:
            flash('Lỗi: Sinh viên đã có học phần này!')
        else:
            new_enrollment = Score(student_profile_id=profile.id, subject_id=subject_id, semester=semester)
            db.session.add(new_enrollment)
            db.session.commit()
            flash('Đã thêm học phần thành công!')
        return redirect(url_for('admin_manage_student_enrollment', profile_id=profile.id))
        
    # LẤY DANH SÁCH CÁC MÔN ĐÃ ĐĂNG KÝ
    enrolled_scores = Score.query.filter_by(student_profile_id=profile.id).all()
    enrolled_sub_ids = [s.subject_id for s in enrolled_scores]
    
    # LỌC CÁC MÔN CHƯA ĐĂNG KÝ
    available_subjects = [sub for sub in Subject.query.all() if sub.id not in enrolled_sub_ids]
    
    return render_template('chitiethocphan.html', profile=profile, enrolled_scores=enrolled_scores, available_subjects=available_subjects)

# XÓA HỌC PHẦN
@app.route('/admin/enroll/delete/<int:score_id>')
def admin_delete_enrollment(score_id):
    if session.get('role') != 'Admin':
        return redirect(url_for('trangchu'))
        
    score = Score.query.get_or_404(score_id)
    profile_id = score.student_profile_id
    db.session.delete(score)
    db.session.commit()
    flash('Đã hủy đăng ký học phần.')
    return redirect(url_for('admin_manage_student_enrollment', profile_id=profile_id))

########################################
# Nhất Khang

# QUẢN LÝ ĐIỂM SINH VIÊN
@app.route('/admin/gradebook', methods=['GET'])
def admin_gradebook():
    if session.get('role') != 'Admin':
        return redirect(url_for('trangchu'))
        
    major_filter = request.args.get('major_filter', '')
    selected_subject_id = request.args.get('subject_id', type=int)
    keyword = request.args.get('keyword', '')

    # LẤY DANH SÁCH CHUYÊN NGÀNH
    majors = db.session.query(Subject.major).distinct().all()
    majors = [m[0] for m in majors if m[0]]

    # LỌC MÔN DỰA TRÊN CHUYÊN NGÀNH
    subjects_query = Subject.query
    if major_filter:
        subjects_query = subjects_query.filter(Subject.major == major_filter)
    subjects = subjects_query.all()

    # NẾU MÔN KHÔNG THUỘC CHUYÊN NGÀNH THÌ RESET
    if selected_subject_id and selected_subject_id not in [s.id for s in subjects]:
        selected_subject_id = None

    scores = []
    # LẤY DANH SÁCH SINH VIÊN (THEO MSV VÀ TÊN)
    if selected_subject_id:
        query = Score.query.join(StudentProfile).join(User).filter(Score.subject_id == selected_subject_id)
        
        if keyword:
            query = query.filter(db.or_(
                User.username.ilike(f'%{keyword}%'),
                User.full_name.ilike(f'%{keyword}%')
            ))
            
        scores = query.all()
        
    return render_template('quanlydiemsinhvien.html', 
                           majors=majors,
                           major_filter=major_filter,
                           subjects=subjects, 
                           scores=scores, 
                           selected_subject_id=selected_subject_id,
                           keyword=keyword)

# CẬP NHẬT ĐIỂM SINH VIÊN
@app.route('/admin/gradebook/update', methods=['POST'])
def update_gradebook():
    if session.get('role') != 'Admin':
        return redirect(url_for('trangchu'))
        
    score_id = request.form.get('score_id')
    subject_id = request.form.get('subject_id') 
    
    score_record = Score.query.get(score_id)
    if score_record:
        score_record.score_a = float(request.form.get('score_a') or 0.0)
        score_record.score_b = float(request.form.get('score_b') or 0.0)
        score_record.score_c = float(request.form.get('score_c') or 0.0)
        db.session.commit()
        flash('Đã lưu điểm thành công!')
        
    return redirect(url_for('admin_gradebook', subject_id=subject_id))

# BẢNG ĐIỂM SINH VIÊN
@app.route('/student/scores')
def student_scores():
    if session.get('role') != 'Student':
        return redirect(url_for('trangchu'))
        
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    profile = user.student_profile
    
    if not profile:
        flash('Lỗi: Không tìm thấy hồ sơ sinh viên.')
        return redirect(url_for('trangchu'))

    scores_by_semester = {}
    total_score_10 = 0
    total_score_4 = 0
    total_subjects = 0

    for score in profile.scores:
        sem = score.semester
        if sem not in scores_by_semester:
            scores_by_semester[sem] = []
        scores_by_semester[sem].append(score)
        
        total_score_10 += score.gpa_scale_10
        total_score_4 += score.gpa_scale_4
        total_subjects += 1

    # Tính ĐIỂM TB TÍCH LŨY
    cpa_10 = round(total_score_10 / total_subjects, 2) if total_subjects > 0 else 0.0
    cpa_4 = round(total_score_4 / total_subjects, 2) if total_subjects > 0 else 0.0

    # PHÂN LOẠI HỌC LỰC
    hoc_luc = "Chưa xếp loại"
    if total_subjects > 0:
        if cpa_4 >= 3.6: hoc_luc = "Xuất sắc"
        elif cpa_4 >= 3.2: hoc_luc = "Giỏi"
        elif cpa_4 >= 2.5: hoc_luc = "Khá"
        elif cpa_4 >= 2.0: hoc_luc = "Trung bình"
        else: hoc_luc = "Yếu"

    # TÍNH ĐIỂM TRUNG BÌNH TỪNG KỲ HỌC
    semester_stats = {}
    for sem, s_list in scores_by_semester.items():
        s_len = len(s_list)
        sem_gpa_10 = round(sum(s.gpa_scale_10 for s in s_list) / s_len, 2) if s_len > 0 else 0.0
        sem_gpa_4 = round(sum(s.gpa_scale_4 for s in s_list) / s_len, 2) if s_len > 0 else 0.0
        semester_stats[sem] = {'gpa_10': sem_gpa_10, 'gpa_4': sem_gpa_4}

    sorted_semesters = sorted(scores_by_semester.keys())

    return render_template('bangdiemsinhvien.html', 
                           profile=profile,
                           scores_by_semester=scores_by_semester,
                           sorted_semesters=sorted_semesters,
                           semester_stats=semester_stats,
                           cpa_10=cpa_10,
                           cpa_4=cpa_4,
                           hoc_luc=hoc_luc)

# SINH VIÊN ĐĂNG KÝ HỌC PHẦN
@app.route('/student/enroll', methods=['GET', 'POST'])
def student_enroll():
    if session.get('role') != 'Student':
        return redirect(url_for('trangchu'))
        
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    profile = user.student_profile
    
    if not profile:
        flash('Lỗi: Không tìm thấy hồ sơ sinh viên.')
        return redirect(url_for('trangchu'))

    # LẤY DANH SÁCH CÁC MÔN SINH VIÊN ĐĂNG KÝ
    enrolled_scores = Score.query.filter_by(student_profile_id=profile.id).all()
    enrolled_subject_ids = [score.subject_id for score in enrolled_scores]
    
    # LẤY CÁC MÔN CÙNG CHUYÊN NGÀNH VỚI SINH VIÊN
    all_subjects = Subject.query.filter_by(major=profile.major).all()
    available_subjects = [sub for sub in all_subjects if sub.id not in enrolled_subject_ids]

    if request.method == 'POST':
        subject_id = int(request.form.get('subject_id'))
        semester = request.form.get('semester') 
        
        # KIỂM TRA DANH SÁCH XEM CÓ PHÙ HỢP HAY KHÔNG
        valid_subject_ids = [sub.id for sub in available_subjects]
        
        if subject_id in valid_subject_ids:
            new_enrollment = Score(student_profile_id=profile.id, subject_id=subject_id, semester=semester)
            db.session.add(new_enrollment)
            db.session.commit()
            flash('Đăng ký học phần thành công!')
        else:
            flash('Lỗi: Học phần không hợp lệ, đã đăng ký, hoặc không thuộc chuyên ngành của bạn.')
            
        return redirect(url_for('student_enroll'))
        
    return render_template('dangkyhocphan.html', 
                           available_subjects=available_subjects, 
                           enrolled_scores=enrolled_scores,
                           profile=profile)

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        
        # TẠO ROLE ADMIN
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            admin_role = Role(name='Admin')
            db.session.add(admin_role)
            db.session.commit()
    
        # THIẾT LẬP TÀI KHOẢN ADMIN MẶC ĐỊNH
        check_admin = User.query.filter_by(username='admin').first()
        if not check_admin:
            admin_user = User(username='admin', full_name='Giảng viên A', role=admin_role)
            admin_user.set_password('123456')
            db.session.add(admin_user)
            db.session.commit()
            print("Đã tự động khởi tạo tài khoản Admin (admin / 123456)")
            
    app.run(debug=True)
from flask import Flask, render_template, request, session, redirect, flash, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Config - Update as per local setup
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'login'  # Your DB name

mysql = MySQL(app)


# ---------- SIGNUP (Register) ----------

@app.route('/')
def signup():
    return render_template('signup.html')


# ---------- REGISTER ROUTE ----------
@app.route('/register', methods=['POST'])
def register():
    msg = ''
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')
        mobile = request.form.get('mobile')

        # 1️⃣ Field Validation
        if not (full_name and email and password and confirm_password and mobile):
            msg = "⚠️ Please fill all fields!"
            return render_template('signup.html', msg=msg)

        if password != confirm_password:
            msg = "❌ Passwords do not match!"
            return render_template('signup.html', msg=msg)

        # 2️⃣ Check if email already exists
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM signup WHERE email = %s", (email,))
        account = cursor.fetchone()

        if account:
            msg = "⚠️ Email already exists!"
        else:
            cursor.execute("""
                INSERT INTO signup (full_name, email, password, mobile)
                VALUES (%s, %s, %s, %s)
            """, (full_name, email, password, mobile))
            mysql.connection.commit()
            msg = "✅ Account created successfully! Please login."

        cursor.close()
        return render_template('signup.html', msg=msg)
    else:
        return redirect('/')

# ---------- LOGIN ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            msg = '⚠️ Please enter both email and password!'
            return render_template('login.html', msg=msg)

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM signup WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()

        if user:
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['full_name']
            return redirect('/web')  # redirects to main page
        else:
            msg = '❌ Incorrect email or password!'
    return render_template('login.html', msg=msg)


# ---------- MAIN PAGE ----------
@app.route('/web')
def main_page():
    if 'loggedin' in session:
        return render_template('web.html', username=session['username'])
    else:
        return redirect('/login')


# ---------- LOGOUT ----------
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect('/login')



# ---------------- Routes ----------------
@app.route('/qr')
def qr_page():
    return render_template('qr.html')   # your HTML file name


# ---------- API endpoint to save enrollment ----------
@app.route('/enroll', methods=['POST'])
def enroll_course():
    try:
        data = request.get_json()
        user_email = data.get('email')
        course_name = data.get('course_name')
        course_amount = data.get('course_amount')
        payment_method = data.get('payment_method')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("""
            INSERT INTO qr (user_email, course_name, course_amount, payment_method, payment_status)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_email, course_name, course_amount, payment_method, "Pending"))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Enrollment saved successfully!"}), 200

    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Error saving enrollment", "error": str(e)}), 500


    # ---------- FORGOT PASSWORD ----------
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    msg = ''
    if request.method == 'POST':
        email = request.form.get('email')
        print("EMAIL ENTERED:", email)  # DEBUG
        
        email = email.strip().lower()  # trim & lowercase
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM signup WHERE LOWER(email) = %s", (email,))
        account = cursor.fetchone()
        cursor.close()
        
        print("ACCOUNT FOUND:", account)  # DEBUG
        
        if account:
            session['reset_email'] = email
            return redirect('/reset')
        else:
            msg = "❌ Email not found! Please check again."
        
    return render_template('forgot-password.html', msg=msg)




@app.route('/reset', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session:
        return redirect('/forgot-password')  # ✅ security check

    msg = ''
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            msg = "❌ Passwords do not match!"
        else:
            cursor = mysql.connection.cursor()
            cursor.execute("UPDATE signup SET password = %s WHERE email = %s", 
                           (password, session['reset_email']))
            mysql.connection.commit()
            cursor.close()
            
            session.pop('reset_email', None)  # clear session
            msg = "✅ Password updated successfully!"
            return redirect('/login')  # redirect to login page

    return render_template('reset.html', msg=msg)





# ---------- PROFILE PAGE ----------
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'loggedin' not in session:
        return redirect('/login')

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # When updating profile
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        mobile = request.form.get('mobile')

        cursor.execute("""
            UPDATE signup SET full_name = %s, mobile = %s WHERE id = %s
        """, (full_name, mobile, session['id']))
        mysql.connection.commit()
        session['username'] = full_name  # Update session name
        flash('✅ Profile updated successfully!', 'success')

    cursor.execute("SELECT * FROM signup WHERE id = %s", (session['id'],))
    account = cursor.fetchone()
    cursor.close()

    return render_template('profile.html', account=account)
    





@app.route('/3D-Modeling-with-SolidWorks')
def solid():
    return render_template('3D-Modeling-with-SolidWorks.html')


@app.route('/Adobe-Photoshop-Basics')
def adobe():
    return render_template('Adobe-Photoshop-Basics.html')


@app.route('/AI-for-Business-Applications')
def AI():
    return render_template('AI-for-Business-Applications.html')


@app.route('/AutoCAD-for-Beginners')
def auto():
    return render_template('AutoCAD-for-Beginners.html')


@app.route('/Big-Data-Analytics-with-Hadoop')
def big():
    return render_template('Big-Data-Analytics-with-Hadoop.html')

@app.route('/Brand-Identity-Design')
def brand():
    return render_template('Brand-Identity-Design.html')

@app.route('/Business-Communication-Skills')
def business():
    return render_template('Business-Communication-Skills.html')


@app.route('/C++-for-Problem-Solving')
def c():
    return render_template('C++-for-Problem-Solving.html')


@app.route('/Canva-Design-Masterclass')
def canva():
    return render_template('Canva-Design-Masterclass.html')


@app.route('/Civil-Engineering-Project-Planning')
def civil():
    return render_template('Civil-Engineering-Project-Planning.html')


@app.route('/Cloud-Security-Basics')
def cloud():
    return render_template('Cloud-Security-Basics.html')

@app.route('/Computer-Vision-with-OpenCV')
def computer():
    return render_template('Computer-Vision-with-OpenCV.html')


@app.route('/Customer-Relationship-Management')
def customer():
    return render_template('Customer-Relationship-Management.html')


@app.route('/Cybersecurity-Essentials')
def cyber():
    return render_template('Cybersecurity-Essentials.html')

@app.route('/Data-Structures-&-Algorithms')
def data():
    return render_template('Data-Structures-&-Algorithms.html')


@app.route('/Data-Visualization-using-Power-BI')
def datav():
    return render_template('Data-Visualization-using-Power-BI.html')

@app.route('/Data-Wrangling-with-Pandas')
def dataw():
    return render_template('Data-Wrangling-with-Pandas.html')

@app.route('/Deep-Learning-with-TensorFlow')
def deep():
    return render_template('Deep-Learning-with-TensorFlow.html')


@app.route('/Design-Thinking-for-Engineers')
def design():
    return render_template('Design-Thinking-for-Engineers.html')

@app.route('/Electrical-Circuit-Design-Basics')
def electriccal():
    return render_template('Electrical-Circuit-Design-Basics.html')

@app.route('/Entrepreneurship-&-Startup-Growth')
def enter():
    return render_template('Entrepreneurship-&-Startup-Growth.html')

@app.route('/Ethical-Hacking-Fundamentals')
def ethical():
    return render_template('Ethical-Hacking-Fundamentals.html')

@app.route('/Figma-for-Beginners')
def figma():
    return render_template('Figma-for-Beginners.html')

@app.route('/Financial-Management-Essentials')
def financial():
    return render_template('Financial-Management-Essentials.html')


@app.route('/Firewalls-&-VPN-Configuration')
def fire():
    return render_template('Firewalls-&-VPN-Configuration.html')


@app.route('/Go-Programming-Essentials')
def go():
    return render_template('Go-Programming-Essentials.html')

@app.route('/Graphic-Design-Principles')
def graphic():
    return render_template('Graphic-Design-Principles.html')


@app.route('/Human-Resource-Management-Basics')
def human():
    return render_template('Human-Resource-Management-Basics.html')



@app.route('/Human-Computer-Interaction')
def humancom():
    return render_template('Human-Computer-Interaction.html')

@app.route('/Identity-&-Access-Management')
def identity():
    return render_template('Identity-&-Access-Management.html')



@app.route('/Incident-Response-Management')
def incident():
    return render_template('Incident-Response-Management.html')


@app.route('/Introduction-to-Networking')
def intro():
    return render_template('Introduction-to-Networking.html')


@app.route('/Introduction-to-Robotics')
def introduction():
    return render_template('Introduction-to-Robotics.html')


@app.route('/Java-Programming-Fundamentals')
def ja():
    return render_template('Java-Programming-Fundamentals.html')


@app.route('/JavaScript-from-Scratch')
def java():
    return render_template('JavaScript-from-Scratch.html')


@app.route('/Leadership-&-Team-Building')
def leader():
    return render_template('Leadership-&-Team-Building.html')


@app.route('/Machine-Learning-with-Scikit-Learn')
def machine():
    return render_template('Machine-Learning-with-Scikit-Learn.html')


@app.route('/Marketing-Strategy-Masterclass')
def marketing():
    return render_template('Marketing-Strategy-Masterclass.html')


@app.route('/Mechanical-Engineering-Fundamentals')
def mechancial():
    return render_template('Mechanical-Engineering-Fundamentals.html')


@app.route('/Mobile-Programming-with-Kotlin')
def mobile():
    return render_template('Mobile-Programming-with-Kotlin.html')


@app.route('/Motion-Graphics-with-After-Effects')
def motion():
    return render_template('Motion-Graphics-with-After-Effects.html')


@app.route('/Natural-Language-Processing-Basics')
def natural():
    return render_template('Natural-Language-Processing-Basics.html')


@app.route('/Network-Protocols-Explained')
def network():
    return render_template('Network-Protocols-Explained.html')


@app.route('/Operations-&-Supply-Chain-Management')
def operations():
    return render_template('Operations-&-Supply-Chain-Management.html')


@app.route('/Penetration-Testing-Made-Easy')
def penetration():
    return render_template('Penetration-Testing-Made-Easy.html')


@app.route('/PHP-&-MySQL-Web-Development')
def php():
    return render_template('PHP-&-MySQL-Web-Development.html')


@app.route('/Product-Design-&-Innovation')
def product():
    return render_template('Product-Design-&-Innovation.html')


@app.route('/Python-for-Data-Science')
def python():
    return render_template('Python-for-Data-Science.html')


@app.route('/Python-Programming-Basics')
def pythonn():
    return render_template('Python-Programming-Basics.html')



@app.route('/Rust-Programming-for-Beginners')
def rust():
    return render_template('Rust-Programming-for-Beginners.html')


@app.route('/Statistics-for-Data-Science')
def stat():
    return render_template('Statistics-for-Data-Science.html')



@app.route('/Structural-Analysis-Made-Easy')
def structural():
    return render_template('Structural-Analysis-Made-Easy.html')


@app.route('/Thermodynamics-&-Heat-Transfer')
def thermo():
    return render_template('Thermodynamics-&-Heat-Transfer.html')


@app.route('/UI/UX-Design-Fundamentals')
def ui():
    return render_template('UI/UX-Design-Fundamentals.html')


@app.route('/Web-Accessibility-Basics')
def webacc():
    return render_template('Web-Accessibility-Basics.html')


@app.route('/Web-Development-with-React')
def webd():
    return render_template('Web-Development-with-React.html')


@app.route('/Wireframing-&-Prototyping')
def wire():
    return render_template('Wireframing-&-Prototyping.html')


@app.route('/Wireshark-for-Beginners')
def wireshark():
    return render_template('Wireshark-for-Beginners.html')


@app.route('/Project-Management-Fundamentals')
def pmf():
    return render_template('Project-Management-Fundamentals.html')


@app.route('/Business')
def bus():
    return render_template('business.html')

@app.route('/qr')
def qr():
    return render_template('qr.html')


if __name__=='__main__':
    app.run(debug=True)
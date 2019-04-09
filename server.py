from flask import Flask, render_template, redirect, request, session, flash, url_for
from mysqlconnection import connectToMySQL
import re
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, emit
app = Flask(__name__)
bcrypt = Bcrypt(app)
socketio = SocketIO(app)
app.secret_key = 'theansweris42'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]{3}$') 
PW_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,15}$")


@app.route('/')
def root():    
    return render_template('index.html')


@app.route('/validate', methods=['POST'])
def validate_fields():    
    error = 0
    if request.form['form_side']== 'register' :       
        if len(request.form['fname']) < 2:
            flash('fname_error')
            error = 1
        else:
            session['fname'] = request.form['fname']
        if len(request.form['lname']) < 2:
            flash('lname_error')
            error = 1
        else:
            session['lname'] = request.form['lname']             
        if not EMAIL_REGEX.match(request.form['email']):
            flash('email_error')
            error = 1
        else:
            session['email'] = request.form['email']              
        if not request.form['pass_it'] == request.form['times_two']:
            flash('match_error')
            error = 1        
        else:
            if not PW_REGEX.match(request.form['pass_it']):
                flash('format_error')
                error = 1            
        if not error == 0:        
            return redirect('/')
        else:
            mysql = connectToMySQL("private_wall")
            query = "SELECT  * FROM users WHERE email = %(e)s"
            data = {
                "e": request.form['email']
            }
            if_exists = mysql.query_db(query, data)        
            if if_exists:
                session.clear()
                flash('already_exists')                                               
                return redirect('/')
            else:
                i_love_hash = bcrypt.generate_password_hash(request.form['pass_it'])
                mysql = connectToMySQL("private_wall")
                query = "INSERT INTO users (first_name, last_name, email, code_word, created_at) VALUES (%(fn)s, %(ln)s, %(e)s , %(hash)s, NOW())"   
                data = { 'fn': request.form['fname'],
                    'ln': request.form['lname'],
                    'e': request.form['email'],                    
                    "hash" : i_love_hash
                }
                user_info = mysql.query_db(query, data)
                print(user_info)
                session.clear()
                mysql = connectToMySQL("private_wall")
                query = "SELECT * FROM users WHERE id = %(i)s"
                data = {
                    "i": user_info
                }
                user_info = mysql.query_db(query, data)
                session['user'] = user_info[0]
                return redirect('/get_info')
            
    elif request.form['form_side']=='login':
        
        if not EMAIL_REGEX.match(request.form['log_email']):
            flash("login_no_dice")
            return reroute('/')
        if not PW_REGEX.match(request.form['log_password']):            
            flash("login_no_dice")
            return redirect('/')        
        mysql = connectToMySQL("private_wall")
        query = "SELECT * FROM users WHERE email = %(e)s"
        data = {
            "e" : request.form['log_email']
        }
        user_info = mysql.query_db(query, data)
        print (user_info)
        if not user_info == ():
            i_love_hash = bcrypt.generate_password_hash(request.form['log_password'])         
            if bcrypt.check_password_hash(user_info[0]['code_word'], request.form['log_password']):
                session.clear()
                session['user'] = user_info[0]
                return redirect('/get_info')
            else:
                flash("login_no_dice")
                return redirect('/')
        else:
            flash("login_no_dice")
            return(redirect('/'))
        


@app.route('/get_info')
def get_from_db():
    mysql = connectToMySQL('private_wall')
    query = "SELECT * FROM users"   
    active_users = mysql.query_db(query)
    mysql = connectToMySQL('private_wall')
    query = "SELECT users.first_name, users2.first_name, messages.content, messages.created_at, messages.id FROM users JOIN messages ON users.id = messages.to_id JOIN users AS users2 on messages.from_id = users2.id WHERE messages.to_id = %(uzr)s;"
    data = {
        'uzr': session['user']['id']
    }
    query = mysql.query_db(query, data)
    return render_template('wall.html', active=active_users, query = query)

@app.route('/wall')
def success():
    if 'user' in session:   
        return render_template('wall.html')
    else:
        return redirect('/')
    
@app.route('/submit_msg', methods=["POST"])
def submit_new_msg():
    if len(request.form['msg_txt']) > 3:       
        mysql = connectToMySQL("private_wall")
        query = "INSERT INTO messages (content, from_id, to_id, created_at) VALUES (%(ct)s, %(sf)s, %(id)s, NOW())"
        data = {
            "ct": request.form['msg_txt'],
            "sf": session['user']['id'],
            "id": request.form['directed_at']
        }
        msg_loc = mysql.query_db(query, data)
        return redirect('/get_info')
    
    
@app.route('/remove_it', methods=['POST'])
def remove_message():
    mysql = connectToMySQL("private_wall")
    query = "DELETE FROM messages WHERE id= %(id)s"
    data = {
        "id": request.form['msg_id']
    }
    results = mysql.query_db(query, data)
    return redirect('get_info')
    
    

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
        
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
        

    





























if __name__ == '__main__':
    app.run(debug=True)

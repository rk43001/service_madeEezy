from flask import Flask, render_template, request, flash, url_for, redirect
import pandas as pd 
import os
from datetime import date
import random
from werkzeug.utils import secure_filename
from PIL import Image
from dotenv import load_dotenv
import os

from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import service_pb2_grpc
stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())

from clarifai_grpc.grpc.api import service_pb2, resources_pb2
from clarifai_grpc.grpc.api.status import status_code_pb2
metadata = (('authorization', 'Key 02aad03316c148aab10375c462ae4f68'),)

app = Flask(__name__)

def get_tags_from_path(image_path):
    print("image path => ",image_path)
    with open(image_path,"rb") as f:
        file_bytes = f.read()
    tags = []
    request = service_pb2.PostModelOutputsRequest(
    model_id='aaa03c23b3724a16a56b629203edc62c',
    inputs=[
      resources_pb2.Input(data=resources_pb2.Data(image=resources_pb2.Image(base64=file_bytes)))
    ])
    response = stub.PostModelOutputs(request, metadata=metadata)

    if response.status.code != status_code_pb2.SUCCESS:
        raise Exception("Request failed, status code: " + str(response.status.code))

    for concept in response.outputs[0].data.concepts:
        tags.append(concept.name)
    return tags

img_path = "static/image.jpg"
path = "static/image.jpg"

def classification(image_path):
    ## Code for image classification

    tags = get_tags_from_path(image_path)
    print(tags)
    plumber_set = ['faucet','pipes','pipe','shower','wash','basin','water','washcloset','bathroom','water closet','flush','bathtub','steel','plumber','plumbing','wet']
    electrical_set = ['electrical','electronics','power','appliance','computer','conditioner','technology','wire','connection','switch','electricity','lamp','ceiling','fan','heater']
    carpenter_set = ['wood', 'wooden', 'furniture', 'table', 'chair', 'stool','carpentry','antique','comfort','armchair','old', 'inside', 'empty', 'family', 'no person', 'seat', 'antique', 'vintage', 'house', 'desk', 'design', 'desktop', 'room', 'decoration', 'luxury',  'wardrobe', 'cabinet', 'interior design', 'drawer', 'cupboard', 'indoor']

    score_plumber = 0
    score_electrical = 0
    score_carpenter = 0

    #### has n^2 complexity
    for tag in tags:
        if(tag in plumber_set):
            score_plumber+=1
        if(tag in electrical_set):
            score_electrical+=1
        if(tag in carpenter_set):
            score_carpenter += 1


    if(max(score_electrical,score_plumber, score_carpenter)==0):
        return "something went wrong, could not predict the department"
    else:
        if(score_plumber == max(score_electrical,score_plumber, score_carpenter)):
            return "plumber"
        if(score_electrical == max(score_electrical,score_plumber, score_carpenter)):
            return "electrical"
        else:
            return "carpenter"
    

user_database = pd.read_excel(r"users.xlsx")
service_provider_database = pd.read_excel(r"service_providers.xlsx")
current = pd.read_excel(r"current_user.xlsx")
current_service = pd.read_excel(r"current_service_provider.xlsx")
req_database = pd.read_excel(r"requests.xlsx")

def email_found(email):
        for i in user_database['Email']:
            if(email == i):
                return True
        
        return False

def phone_found(phone):
        for i in user_database['Phone Number']:
            if(phone == i):
                return True
        
        return False

def match(email, password):
    p = 0
    q = 0
    for i in user_database['Email']:
        p += 1
        if(email == i):
            for j in user_database['Password']:
                q += 1 
                if j == password and p == q:
                    return True
    return False

def email_found2(email):
        for i in service_provider_database['Email']:
            if(email == i):
                return True
        
        return False

def phone_found2(phone):
        for i in service_provider_database['Phone Number']:
            if(phone == i):
                return True
        
        return False

def match2(email, password):
    p = 0
    q = 0
    for i in service_provider_database['Email']:
        p += 1
        if(email == i):
            for j in service_provider_database['Password']:
                q += 1 
                if j == password and p == q:
                    return True
    return False

def find_name(email):
    p = 0
    q = 0
    for i in user_database['Email']:
        p += 1
        if(email == i):
            for j in user_database['Name']:
                q += 1 
                if p == q:
                    return j
    return False

def find_phone(email):
    p = 0
    q = 0
    for i in user_database['Email']:
        p += 1
        if(email == i):
            for j in user_database['Phone']:
                q += 1 
                if p == q:
                    return j
    return False

def find_phone2(email):
    p = 0
    q = 0
    for i in service_provider_database['Email']:
        p += 1
        if(email == i):
            for j in service_provider_database['Phone']:
                q += 1 
                if p == q:
                    return j
    return False

def find_address(email):
    p = 0
    q = 0
    for i in user_database['Email']:
        p += 1
        if(email == i):
            for j in user_database['Address']:
                q += 1 
                if p == q:
                    return j
    return False

def find_servicename(email):
    p = 0
    q = 0
    for i in service_provider_database['Email']:
        p += 1
        if(email == i):
            for j in service_provider_database['Name']:
                q += 1 
                if p == q:
                    return j
    return False

def find_service_type(email):
    p = 0
    q = 0
    for i in service_provider_database['Email']:
        p += 1
        if(email == i):
            for j in service_provider_database['Service Type']:
                q += 1 
                if p == q:
                    return j
    return False

@app.route('/')
def ini():
        return render_template('user_service_provider.html')

@app.route('/user_login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')            

            #email and password found and match, then authenticate

            if email_found(email):
                if(match(email, password)):
                    flash('Logged in successfully!', category='success')
                    current_new = current[0:0]
                    current_new.loc[len(current_new.index)] = [email]
                    current_new.to_excel("current_user.xlsx", index=False)
                    return redirect(url_for('added_requests'))
                else:
                    flash('Incorrect password, try again.', category='error')
            else:
                flash('Email does not exist, Please Sign Up', category='error')
    return render_template("login.html")


@app.route('/service_login', methods = ['GET', 'POST'])
def login2():
    if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            #email and password found and match, then authenticate

            if email_found2(email):
                if(match2(email, password)):
                    flash('Logged in successfully!', category='success')
                    current_service_new = current_service[0:0]
                    current_service_new.loc[len(current_service_new.index)] = [email]
                    current_service_new.to_excel("current_service_provider.xlsx", index = False)
                    return redirect(url_for('pending_requests'))
                else:
                    flash('Incorrect password, try again.', category='error')
                    return render_template("service_login.html")
            else:
                flash('Email does not exist, Please Sign Up', category='error')
                return render_template("service_login.html")
            
    return render_template("service_login.html")

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password1')
        confirmpass = request.form.get('password2')
        name = request.form.get('Name')
        address = request.form.get('address')
        phone = request.form.get('Phone Number')
        user_database.loc[len(user_database.index)] = [email, password, name, address, phone] 
        user_database.to_excel('users.xlsx', index=False)
        if(email_found(email) or phone_found(phone)):
            flash('Error! Try again.', category='error')
        else:
            flash('Logged in successfully!', category='success')
    return render_template("sign_up.html")

@app.route('/service_sign_up', methods = ['GET', 'POST'])
def service_sign_up():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password1')
        confirmpass = request.form.get('password2')
        name = request.form.get('Name')
        address = request.form.get('address')
        phone = request.form.get('Phone Number')
        type = request.form.get('type')
        if(email_found2(email) or phone_found2(phone)):
            flash('Error! Try again.', category='error')
        else:
            service_provider_database.loc[len(service_provider_database.index)] = [email, password, name, address, phone, type] 
            service_provider_database.to_excel('service_providers.xlsx', index=False)
            flash('Signed Up in successfully!', category='success')

    return render_template('service_sign_up.html')

@app.route('/add_service', methods=['GET', 'POST'])
def add_service():
    df_current = pd.read_excel("current_user.xlsx")
    return render_template("add_service.html", current_user_name = find_name(df_current['Current'][0]))

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    current.drop(current.tail(1).index,inplace=True)
    current.to_excel('current_user.xlsx', index = False)
    return redirect(url_for('login'))


@app.route('/added_requests', methods=['GET', 'POST'])
def added_requests():
    listt = []
    df = pd.read_excel(r'requests.xlsx')
    df_current = pd.read_excel(r'current_user.xlsx')
    current_user = df_current['Current'][0]
    j = 0
    user_name = find_name(df_current['Current'][0])
    for i in df['from']:
        if(i == current_user):
            id = df['ID'][j]
            name = find_servicename(df['to'][j])
            ph = find_phone2(df['to'][j])
            dpt = find_service_type(df['to'][j])
            status = ""
            booking = df['requested'][j]
            estim = df['estimated'][j]
            if(df['accepted or declined'][j] == 1):
                status = "Accepted"
            elif(df['accepted or declined'][j] == -1):
                status = "Pending"
            else:
                status = "Declined"
            if(df['deleted'][j] == 0 and df['completed'][j] == 0):
                listt.append([id, name, int(ph), dpt, status, booking, estim])
        
        j += 1

    return render_template("home.html", current_user_name = user_name, listt = listt)

@app.route('/logout_service_provider', methods=['GET', 'POST'])
def service_logout():
    current_service.drop(current_service.tail(1).index,inplace=True)
    current.to_excel('current_service_provider.xlsx', index = False)
    return redirect(url_for('login2'))

@app.route('/pending_requests')
def pending_requests():
    listt = []
    df = pd.read_excel(r'requests.xlsx')
    df_current = pd.read_excel(r'current_service_provider.xlsx')
    current_service_provider = df_current['Current'][0]
    j = 0
    service_man_name = find_servicename(current_service_provider)
    for i in df['to']:
        if(i == current_service_provider):
            id = df['ID'][j]
            name = find_name(df['from'][j])
            ph = find_phone(df['from'][j])
            booking = df['requested'][j]
            email = df['from'][j]
            address = find_address(df['from'][j])
            if(df['deleted'][j] == 0 and df['completed'][j] == 0 and df['accepted or declined'][j] == -1):
                listt.append([id, name, int(ph), booking, email, address])
        
        j += 1
    return render_template('service_provider_home.html', listt = listt, current_service_name = service_man_name)

@app.route('/accepted_requests', methods=['GET', 'POST'])
def accepted_requests():
    listt = []
    df = pd.read_excel(r'requests.xlsx')
    df_current = pd.read_excel(r'current_service_provider.xlsx')
    current_service_provider = df_current['Current'][0]
    service_man_name = find_servicename(current_service_provider)
    j = 0
    for i in df['to']:
        if(i == current_service_provider):
            id = df['ID'][j]
            name = find_name(df['from'][j])
            ph = find_phone(df['from'][j])
            booking = df['requested'][j]
            email = df['from'][j]
            address = find_address(df['from'][j])
            estimated = df['estimated'][j]
            visiting_charge = df['visiting charge'][j]
            if(df['accepted or declined'][j] == 1):
                listt.append([id, name, int(ph), booking, email, address, visiting_charge, estimated])
        
        j += 1
    return render_template('accepted_requests.html', listt = listt, current_service_name = service_man_name)

@app.route('/completed_requests', methods=['GET', 'POST'])
def completed_requests():
    listt = []
    df = pd.read_excel(r'requests.xlsx')
    df_current = pd.read_excel(r'current_service_provider.xlsx')
    current_service_provider = df_current['Current'][0]
    service_man_name = find_servicename(current_service_provider)
    j = 0
    for i in df['to']:
        if(i == current_service_provider):
            id = df['ID'][j]
            name = find_name(df['from'][j])
            ph = find_phone(df['from'][j])
            booking = df['requested'][j]
            email = df['from'][j]
            address = find_address(df['from'][j])
            completion = df['completion'][j]
            feedback = df['feedback'][j]
            if df['completed'][j] == 1:
                listt.append([id, name, int(ph), booking, email, address, completion, feedback])
        
        j += 1
    return render_template('completed_requests.html', listt = listt,current_service_name = service_man_name)

@app.route('/deleted_services', methods=['GET', 'POST'])
def deleted_services():
    listt = []
    df = pd.read_excel(r'requests.xlsx')
    df_current = pd.read_excel(r'current_user.xlsx')
    current_user = df_current['Current'][0]
    j = 0
    for i in df['from']:
        if(i == current_user):
            name = find_servicename(df['to'][j])
            ph = find_phone2(df['to'][j])
            dpt = find_service_type(df['to'][j])
            booking = df['requested'][j]
            today_date =  date.today()
            if(df['deleted'][j] == 1):
                listt.append([name, int(ph), dpt, booking, today_date])
        
        j += 1

    return render_template("deleted_services.html", listt = listt, current_user_name = find_name(df_current['Current'][0]))


@app.route('/completed_services_user', methods=['GET', 'POST'])
def user_completed():
    listt = []
    df = pd.read_excel(r'requests.xlsx')
    df_current = pd.read_excel(r'current_user.xlsx')
    current_user = df_current['Current'][0]
    j = 0
    for i in df['from']:
        if(i == current_user):
            name = find_servicename(df['to'][j])
            ph = find_phone2(df['to'][j])
            dpt = find_service_type(df['to'][j])
            booking = df['requested'][j]
            compl = df['completion'][j]
            visiting = df['visiting charge'][j]
            feedback = df['feedback'][j]
            if(df['completed'][j] == 1):
                listt.append([name, int(ph), dpt, booking, compl, visiting, feedback])
        
        j += 1

    return render_template("completed_user.html", listt = listt, current_user_name = find_name(df_current['Current'][0]))


@app.route('/<parameter>/add_this_service', methods=['GET', 'POST'])
def add_this_service(parameter):
    df_current = pd.read_excel("current_user.xlsx")
    frrom = df_current['Current'][0]
    to = parameter
    current_data = date.today()
    id = random.randint(100000, 1000000 - 1)
    req_database.loc[len(req_database.index)] = [id, frrom, to, current_data, "", "", 0, 0, -1, 0, 0]
    req_database.to_excel("requests.xlsx", index=False)
    return redirect(url_for('added_requests'))

@app.route('/<parameter>/delete_this_service', methods=['GET', 'POST'])
def delete_this_service(parameter):
    j = 0
    for i in req_database['ID']:
        if i == int(parameter):
            req_database['deleted'][j] = 1
            break
        j += 1

    req_database.to_excel("requests.xlsx", index=False)
    return redirect(url_for('added_requests'))

@app.route('/<parameter>/accept_this_service', methods=['GET', 'POST'])
def accept_this_service(parameter):
    j = 0
    for i in req_database['ID']:
        if i == int(parameter):
            req_database['accepted or declined'][j] = 1
            break
        j += 1

    req_database.to_excel("requests.xlsx", index=False)
    df = pd.read_excel("rough.xlsx")
    df.loc[len(df.index)] = [parameter]
    df.to_excel("rough.xlsx", index = False)
    return render_template("visiting_fees.html")


@app.route('/<parameter>/decline_this_service', methods=['GET', 'POST'])
def decline_this_service(parameter):
    j = 0
    for i in req_database['ID']:
        if i == int(parameter):
            req_database['accepted or declined'][j] = 0
            req_database.to_excel("requests.xlsx", index=False)
            break
        j += 1

    return redirect(url_for('pending_requests'))


@app.route('/<parameter>/complete_this_service', methods=['GET', 'POST'])
def complete_this_service(parameter):
    j = 0
    for i in req_database['ID']:
        if i == int(parameter):
            req_database['completed'][j] = 1
            break
        j += 1

    req_database.to_excel("requests.xlsx", index=False)
    df = pd.read_excel("rough.xlsx")
    df.loc[len(df.index)] = [parameter]
    df.to_excel("rough.xlsx", index = False)
    return render_template("feedback.html")


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == "POST":
        feedback = request.form.get("feedback")
        df = pd.read_excel("rough.xlsx")
        id = df['ID'][0]
        j = 0
        dt = date.today()
        for i in req_database['ID']:
            if i == int(id):
                req_database['completion'][j] = dt
                req_database['feedback'][j] = feedback
                req_database.to_excel("requests.xlsx", index=False)
                break
            j += 1
        df = df[0:0]
        df.to_excel("rough.xlsx", index = False)
    return redirect(url_for('user_completed'))
pd.options.mode.chained_assignment = None
@app.route('/visiting_fees', methods=['GET', 'POST'])
def visiting_fees():
    if request.method == "POST":
        visiting_fees = request.form.get("fees")
        estimated_date = request.form.get("date")
        df = pd.read_excel("rough.xlsx")
        id = df['ID'][0]
        j = 0
        for i in req_database['ID']:
            if i == int(id):
                req_database['accepted or declined'][j] = 1
                req_database['visiting charge'][j] = int(visiting_fees)
                req_database['estimated'][j] = estimated_date
                req_database.to_excel("requests.xlsx", index=False)
                break
        j += 1
        df = df[0:0]
        df.to_excel("rough.xlsx", index= False)
    return redirect(url_for('accepted_requests'))
       
app.config['UPLOAD_FOLDER'] = 'static'

@app.route("/display_list" , methods=['GET', 'POST'])
def display_list():
    ls = []
    q = 0
    df_current = pd.read_excel("current_user.xlsx")
    # ml code
    type = classification(img_path)
    for i in service_provider_database['Email']:
        if(service_provider_database['Service Type'][q] == type):
            ls.append([service_provider_database['Email'][q], service_provider_database['Name'][q], service_provider_database['Phone'][q], service_provider_database['Address'][q]])
        q += 1
    
    return render_template("add_service_2.html", current_user_name = find_name(df_current['Current'][0]), list_of_services = ls)




@app.route("/uploader" , methods=['GET', 'POST'])
def uploader():
    if request.method=='POST':
        f = request.files['file1']
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename("image.jpg")))
        return redirect(url_for("display_list"))

if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'reet'
    app.run(debug=True)
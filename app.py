from flask import Flask, redirect, make_response, abort
from flask import request
from flask import render_template
from bson.objectid import ObjectId
import random
from pymongo import MongoClient
import hashlib
import uuid


#import pdb
#pdb.set_trace()

app = Flask(__name__)
client = MongoClient()
db = client.ab2019

def get_user_from_session():
    session_id = request.cookies.get("session_id")
    session = db.session.find_one({
        "session_id": session_id
    })
    if not session:
        return

    user_id = session["user"]
    user = db.users.find_one({
        "_id" : user_id,
        "is_admin" : True
    })

    return user;



def roll():
    return random.choice(["yek","du","se","car","penc","se"])

def get_messages():
    return db.messages.find()

def get_approved_messages():
    return db.messages.find({
        "approved":True
    })

@app.route('/', methods=["GET","POST"])
def main():
    if request.method == "POST":
        sender = request.form["sender"]
        body = request.form["body"]
        db.messages.insert({"sender":sender, "body":body, "approved":False})
    user = get_user_from_session()
    return render_template("main.html",user=user, messages = get_approved_messages())

@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "POST":
        uname = request.form["uname"]
        password = request.form["password"]
        password_enc = hashlib.sha256(password.encode("utf-8"))

        user = db.users.find_one({"username":uname, "password": password_enc.hexdigest(), "is_admin":True})

        if not user:
            return "Wrong username or password!"

        session_id = str(uuid.uuid4())

        db.session.insert({
            "session_id": session_id,
            "user": user["_id"]
        })

        response = make_response(render_template("login.html", success = True))
        response.set_cookie("session_id",session_id)
        return response

    return render_template("login.html")

@app.route('/edit/<document_id>', methods=["GET","POST"])
def edit(document_id):
    if not get_user_from_session():
        abort(401)

    if request.method == "POST":
        sender = request.form["sender"]
        body = request.form["body"]
        db.messages.update_one({"_id": ObjectId(document_id)},
                               {"$set": {
                                   "sender": sender,
                                   "body": body
                                }})
        return redirect("/admin")

    message = db.messages.find_one({"_id":ObjectId(document_id)})
    return render_template("edit.html", message = message)

@app.route('/remove/<document_id>')
def remove(document_id):
    if not get_user_from_session():
        abort(401)

    db.messages.remove({"_id": ObjectId(document_id)})
    return redirect("/admin")

@app.route('/logout')
def logout():
    if not get_user_from_session():
        abort(401)

    response = make_response(render_template("main.html", success=False, messages = get_approved_messages()))
    response.set_cookie("session_id", "")
    return response


@app.route('/approve/<document_id>')
def approve(document_id):
    if not get_user_from_session():
        abort(401)

    db.messages.update_one({"_id": ObjectId(document_id)},
                               {"$set": {
                                   "approved": True,
                                }})
    return redirect("/admin")

@app.route('/revoke/<document_id>')
def revoke(document_id):
    if not get_user_from_session():
        abort(401)

    db.messages.update_one({"_id": ObjectId(document_id)},
                               {"$set": {
                                   "approved": False,
                                }})
    return redirect("/admin")

@app.route('/submit')
def submit():
    return render_template("submit.html")\

@app.route('/admin')
def admin():
    user = get_user_from_session()
    if not user:
        return "forbidden"
    return render_template("admin.html",user=user, messages = get_messages())


if __name__ == '__main__':
    app.run()
1
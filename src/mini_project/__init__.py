from flask import Flask , request
from uuid import uuid4
from pymongo import MongoClient
from urllib.parse import quote_plus
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager,create_access_token,jwt_required,get_jwt_identity
from datetime import datetime
from zoneinfo import ZoneInfo
db_url = f"mongodb+srv://nexturn-db:WIObj0a299SvgCXK@cluster0.79xwdan.mongodb.net/?appName=Cluster0"

mongo_client = MongoClient(db_url) 

db = mongo_client["blog_database"] 

users = db["users"] 

blogs = db["blogs"]

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "my-secret-key" 

jwt = JWTManager(app)

def generate_id(prefix): 
    
    return f"{prefix}_{uuid4().hex}"

@app.route("/api/auth/register", methods=["POST"])
def handle_register():

    data = request.json

    if not data or "name" not in data or "email" not in data or "password" not in data:
        return "Invalid data", 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    user = users.find_one({"email": email})

    if user:
        return "User already exists", 409

    hashed_password = generate_password_hash(password)

    user_id = generate_id("USER")

    users.insert_one({
        "user_id": user_id,
        "name": name,
        "email": email,
        "password": hashed_password
    })

    return "User added", 201
@app.post("/login")
def login():
    body_param=request.json
    email=body_param["email"]
    password=body_param["password"]
    user=user_collection.find_one({"email":email})  
    if not user:
        return {
            "message":"Signup required"
        },401
    hashed_password=user["hashed_password"]
    if not check_password_hash(hashed_password,password):
        return {
            "message":"Invalid password"
        },401
    token=create_access_token(email)
    return {
        "message":"Logged in successfully",
        "token":token
    },200

@app.post("/blog")
@jwt_required()
def create_blog():

    data = request.json

    title = data.get("title")
    content = data.get("content")

    if not title or not content:
        return "Title and content are required", 400

    user_id = get_jwt_identity()

    blog_id = generate_id("BLOG")

    now = datetime.now(ZoneInfo("Africa/jaipur"))
    blogs.insert_one({
        "blog_id": blog_id,
        "title": title,
        "content": content,
        "author_id": user_id,
        "status": "draft",
        "created_at": now,
        "updated_at":now
    })

    return {
        "message": "Blog created",
        "blog_id": blog_id
    }, 201
@app.put("/blogs/publish/<blog_id>")
@jwt_required()
def publish(blog_id):
    blog=blog_collection.find_one({"blog_id":blog_id})
    email=get_jwt_identity()
    user_id=user_collection.find_one({"email":email})["id"]
    if user_id!=blog["author_id"]:
        return {
            "message":"Only the authors can publish their blogs"
        },400
    blog_collection.find_one_and_update({"blog_id":blog_id},{
        "$set":{
            "status":"published",
            "published_at":datetime.now()
        }
    })
    return {
        "message":"Blog published successfully"
    },201  

@app.get("/blogs/<blog_id>")
@jwt_required()
def get_blog(blog_id):
    blog=blog_collection.find_one({"blog_id":blog_id})
    if not blog:
        return {
            "message":f"No blog with this {blog_id} id"
        },400
    if blog["status"]!="published":
        return {
            "message":f"This blog is not published yet"
        },400
    return blog,201

@app.get("/blogs")
@jwt_required()
def get_blogs():
    blogs_cursor=blog_collection.find({"status":"published"})
    blogs=list(blogs_cursor)
    sorted_blogs=sorted(blogs,key=lambda x:x["published_at"])
    if not sorted_blogs:
        return {
            "message":"No blogs are published yet"
        },400
    return sorted_blogs,201

if __name__=="__main__":
    app.run(debug=True)
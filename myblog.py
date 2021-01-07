from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from flask_sqlalchemy import SQLAlchemy
from passlib.hash import sha256_crypt
from functools import wraps

import psycopg2
#Kullanıcı Giriş Decoratorü
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:           
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın","danger")
            return redirect(url_for("login"))
    return decorated_function

#Kullanıcı kayıt formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.length(min=4,max=25)])
    username = StringField("Kullanıcı adı",validators=[validators.length(min=5,max=35)])
    email = StringField("Email",validators=[validators.Email(message="Lütfen Geçerli bir email adresi girin...")])
    password = PasswordField("Parola",validators=[
        validators.DataRequired(message="Lütfen bir parola belirleyin"),
        validators.EqualTo(fieldname="confirm",message="Parolanız uyuşmuyor")
    ])
    confirm=PasswordField("Parola Doğrula")

class LoginForm(Form):
    username=StringField("Kullanıcı Adı")
    password=PasswordField("Parola")

app=Flask(__name__)
app.secret_key="tariflerblog"
@app.route("/")
def index():
    yemekler=[
        {"id":1,"title":"çikolatalı kurabiye","content":"çikolata,süt,şeker,un,kabartma tozu,vanilya"},
        {"id":2,"title":"Ev poğaçası","content":"un, tuz,süt,yoğurt,peynir,çörek otu, kabartama tozu"},
        {"id":3,"title":"patates salatası","content":"patates,minik soğanlar,turşu,kara biber"} 
    ]
    return render_template("indexx.html",yemekler=yemekler)
@app.route("/tarifler/<string:id>")
def details(id):
    return "Tarif: " + id

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/articles")
def articles():
    db_conn = psycopg2.connect("host='localhost' dbname=blogdb user=postgres password='12345'")
    db_cursor = db_conn.cursor()

    sorgu="Select * from receipes"
    db_cursor.execute(sorgu)
    result=db_cursor.rowcount
    if result>0:
        articles=db_cursor.fetchall()
        #result 0 olmadığında articlesları gönderiyoruz yoksa göndermiyoruz.
        return render_template("articles.html",articles=articles)
    else:
        return render_template("articles.html")
    db_cursor.close()
@app.route("/dashboard")
@login_required
def dashboard():
    db_conn = psycopg2.connect("host='localhost' dbname=blogdb user=postgres password='12345'")
    db_cursor = db_conn.cursor()
    sorgu="Select * from receipes where author= %s"
    db_cursor.execute(sorgu,(session["username"],))
    result=db_cursor.rowcount 
    if result >0:
        articles=db_cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")

#Giriş yapıldıysa bu fonksiyon çalışsın yoksa çalışmasın o yüzden decorator kullanıyoruz.
#Bir tane fonksiyonu çalıştırmadan önce bu decoratoru kullanmalısın.


#Kayıt olma
@app.route('/register',methods=["GET","POST"])
def register():
    form =RegisterForm(request.form)

    if request.method=="POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data) 

        db_conn = psycopg2.connect("host='localhost' dbname=blogdb user=postgres password='12345'")
        db_cursor = db_conn.cursor()

        sorgu="INSERT INTO customer(name,email,username,password) VALUES(%s,%s,%s,%s)"
        val=(name,email,username,password)
        db_cursor.execute(sorgu,val)
        db_conn.commit()

        flash("Başarı ile kayıt oldunuz. ","success")

        return redirect(url_for("login"))
    #GET sayfayı getirecek.formu register htmlmye göndermek isitoyrum o yüzden form=form
    else: 
        return render_template("register.html",form=form)
    
@app.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method=="POST":
       username=form.username.data
       password_entered=form.password.data 

       db_conn = psycopg2.connect("host='localhost' dbname=blogdb user=postgres password='12345'")
       db_cursor = db_conn.cursor()


       query = "select * from customer where username = %s"
       db_cursor.execute(query,(username,))
       result=db_cursor.rowcount
       if result> 0:
           data=db_cursor.fetchone()
           real_password=data[4]
           if sha256_crypt.verify(password_entered,real_password):
               flash("Başarı ile giriş yaptınız.","success")

               #session yapıyoruz.
               session["logged_in"]=True
               session["username"]=username

               return redirect(url_for("index"))
           else:
               flash("Parolanızı yanlış girdiniz !","danger")
               return redirect(url_for("login"))

       else:
           flash("Böyle bir kullanıcı bulunmuyor! ","danger")
           return redirect(url_for("login"))
       db_cursor.close()

    return render_template("login.html",form=form)

#Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
     db_conn = psycopg2.connect("host='localhost' dbname=blogdb user=postgres password='12345'")
     db_cursor = db_conn.cursor()
     sorgu="Select * from receipes where id= %s"
     db_cursor.execute(sorgu,(id,))
     result=db_cursor.rowcount

     if result>0:
         article=db_cursor.fetchone()
         return render_template("article.html",article=article)
     else:
         return render_template("article.html")

#Logout İşlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Makale Ekleme
@app.route("/addArticle",methods=["GET","POST"])
def addArticle():
    #objesini oluşturdum
    form=ArticleForm(request.form)
    if request.method=="POST" and form.validate():
        title=form.title.data
        content=form.content.data
        
        db_conn = psycopg2.connect("host='localhost' dbname=blogdb user=postgres password='12345'")
        db_cursor = db_conn.cursor()

        sorgu="Insert into receipes(title,author,content) VALUES(%s,%s,%s)"
        val=(title,session["username"],content)
        db_cursor.execute(sorgu,val)
        #veritabanına kaydetmesi için commit etmek lazım.
        db_conn.commit()
        db_cursor.close()
        flash(" Tarifiniz Başarıyla Kaydedildi","success")
        return redirect(url_for("dashboard"))

    return render_template("addArticle.html",form=form)
#Makale silme
@app.route("/delete/<string:id>",methods=['GET', 'POST'])
@login_required
def delete(id):
     db_conn = psycopg2.connect("host='localhost' dbname=blogdb user=postgres password='12345'")
     db_cursor = db_conn.cursor()

     sorgu="Select * from receipes where author= %s and id= %s "

     db_cursor.execute(sorgu,(session["username"],id))
     result=db_cursor.rowcount
     if result>0:
         sorgu2="Delete from receipes where id=%s"
         db_cursor.execute(sorgu2,(id,))
         db_conn.commit()
         return redirect(url_for("dashboard"))
         
     else:
         flash("Böyle bir makaele yok veya bu işleme yetkiniz yok.","danger")
         return redirect(url_for("index"))


#Makale Güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def update(id):
    if request.method=="GET":
        db_conn = psycopg2.connect("host='localhost' dbname=blogdb user=postgres password='12345'")
        db_cursor = db_conn.cursor()

        sorgu="select * from receipes where id=%s and author=%s"
        db_cursor.execute(sorgu,(id,session["username"]))
        result=db_cursor.rowcount

        if result== 0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok !","danger")
            return redirect(url_for("index"))
        else:
            article=db_cursor.fetchone()
            form=ArticleForm()

            form.title.data=article[1]
            form.content.data=article[3]
            return render_template("update.html",form=form)

        
    #POST Request
    else:
        db_conn = psycopg2.connect("host='localhost' dbname=blogdb user=postgres password='12345'")
        form=ArticleForm(request.form)
        newTitle=form.title.data
        newContent=form.content.data
        db_cursor = db_conn.cursor()
        sorgu2="Update receipes Set title=%s,content=%s where id=%s"

        db_cursor.execute(sorgu2,(newTitle,newContent,id))
        db_conn.commit()
        db_conn.close()

        flash("Tarif başarıyla güncellendi.","success")
        return redirect(url_for("dashboard"))

#Arama URL
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        return redirect(url_for("index"))
    else:
        keyword=request.form.get("keyword")

        db_conn = psycopg2.connect("host='localhost' dbname=blogdb user=postgres password='12345'")
        db_cursor = db_conn.cursor()
        sorgu="select * from receipes where title like '%" + keyword + "%'"
        db_cursor.execute(sorgu)
        result=db_cursor.rowcount

        if result ==0:
            flash("Aranan kelimeye uygun tarif bulunamadı...","warning")
            return redirect(url_for("articles"))
        else:
            articles=db_cursor.fetchall()
            return render_template("articles.html",articles=articles)



#MakaleForm
#Form u inherit edecek
class ArticleForm(Form):
    title=StringField("Tarif Başlıgı",validators=[validators.Length(min=5,max=100)])
    content=TextAreaField("Tarif İçeriği",validators=[validators.Length(min=10)])

def method_name():
   pass 
if __name__== "__main__":
    app.run(debug=True)


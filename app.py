from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello, Flask CI/CD is running successfully on EC2 with Jenkins and Nginx!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

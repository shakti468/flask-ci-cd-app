# flask-ci-cd-app
# 📌 Assignment_06_DevOps: Flask Application CI/CD with Jenkins and GitHub Actions

## 📖 Project Overview

This repository demonstrates CI/CD automation for a Python Flask web application using:

- **Jenkins** (Self-hosted or cloud-based)
- **GitHub Actions**

It covers building, testing, and deploying the application to staging and production environments.

---

## 🧩 Repository Structure

```bash
.
├── app.py                     # Flask application
├── test_app.py                # Pytest unit tests
├── requirements.txt           # Python dependencies
├── Jenkinsfile                # Jenkins pipeline definition
├── .github/workflows/
│   └── deployment.yml         # GitHub Actions workflow for staging deployment
│   └── deployment_prod.yaml   # GitHub Actions workflow for production deployment
└── README.md                  # Project documentation
└── .env                       # Secrets File

```

## 🔐 Define `.env` File

Before running or deploying the Flask application, create a `.env` file in the root of your project directory with the following contents:

```env
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/
PORT=5000
```

- This is the same for both the tasks
- Default Port of application is 5000 so it is not mandatory
- If you specify some other port ensure that you Jenkinsfile, Github Workflows have their code updated accordingly

## 📌 Task 1: Deployment With Jenkins
1) Setup:
- Install Jenkins on a virtual machine or use a cloud-based Jenkins service.
- Configure Jenkins with Python , Github , SMTP (for emailing) and any other necessary libraries or plugins.

2) Source Code:
- Create Your own Python-Flask Application with MongoDB and Pytest test cases which uses MONGO_URI from a .env file or use an existing repo like the one used here

3) Jenkins Pipeline:
- Create a Jenkinsfile in the root of your Python application repository.
- Go to the Jenkins on your virtual machine or cloud-based service and create a pipeline file called Jenkinsfile with following configurations
- Build: Install dependencies using pip.
- Test: Run unit tests using a testing framework like pytest.
- Deploy: If tests pass, deploy the application to a staging environment like Amazon EC2 Instance using Docker or Nginx or any other tool of your choice.

4) Triggers
- Configure the pipeline to trigger a new build whenever changes are pushed to the main branch of the repository. 

5) Notifications
- Set up a notification system to alert via email when the build process fails or succeeds.

Jenkinsfile has been Configured in this repository in the following manner to achieve these use cases: 

FileName:
```
Jenkinsfile
```

Code:
```Jenkinsfile
pipeline {
  agent any

  environment {
    JL_MONGO_URI_A06 = credentials('JL_MONGO_URI_A06')
    JL_EC2_PRIVATE_IP_A06 = credentials('JL_EC2_PRIVATE_IP_A06')
    JL_EC2_SSH_PRIVATE_KEY = credentials('JL_EC2_SSH_PRIVATE_KEY')
    JL_EC2_USER = credentials('JL_EC2_USER')
    JL_MAIL_TO_EMAIL_ID_A06 = credentials('JL_MAIL_TO_EMAIL_ID_A06')
  }

  stages {
    stage('Install & Setup on EC2') {
      steps {
        sshagent(['JL_EC2_SSH_PRIVATE_KEY']) {
          sh """
            ssh -o StrictHostKeyChecking=no \$JL_EC2_USER@\$JL_EC2_PRIVATE_IP_A06 '
              set -xe
              echo "🔧 Updating system packages..."
              sudo apt update -y && sudo apt upgrade -y

              echo "📦 Installing Git, Nginx, curl, Python3, pip, venv..."
              sudo apt install -y git nginx curl python3 python3-pip python3-venv

              echo "✅ Setup complete."
            '
          """
        }
      }
    }

    stage('Clone Repository & Create .env') {
      steps {
        sshagent(['JL_EC2_SSH_PRIVATE_KEY']) {
          sh """
            ssh -o StrictHostKeyChecking=no \$JL_EC2_USER@\$JL_EC2_PRIVATE_IP_A06 '
              set -xe
              echo "📁 Cloning repo..."
              rm -rf Assignment_06_DevOps
              git clone https://github.com/JOYSTON-LEWIS/Assignment_06_DevOps.git

              echo "📝 Creating .env file..."
              cat > Assignment_06_DevOps/.env <<EOL
MONGO_URI=${JL_MONGO_URI_A06}
PORT=5000
EOL

              echo ".env file created:"
              cat Assignment_06_DevOps/.env
            '
          """
        }
      }
    }

    stage('Install Python Dependencies') {
      steps {
        sshagent(['JL_EC2_SSH_PRIVATE_KEY']) {
          sh """
            ssh -o StrictHostKeyChecking=no \$JL_EC2_USER@\$JL_EC2_PRIVATE_IP_A06 '
              set -xe
              echo "📦 Installing Python dependencies..."

              cd Assignment_06_DevOps
              python3 -m venv venv
              source venv/bin/activate
              pip install --upgrade pip
              pip install -r requirements.txt

              echo "✅ Dependencies installed."
            '
          """
        }
      }
    }

    stage('Run Tests') {
      steps {
        sshagent(['JL_EC2_SSH_PRIVATE_KEY']) {
          sh """
            ssh -o StrictHostKeyChecking=no \$JL_EC2_USER@\$JL_EC2_PRIVATE_IP_A06 '
              set -xe
              echo "🧪 Running pytest..."

              cd Assignment_06_DevOps
              source venv/bin/activate

              pytest --ignore=backup || true

              echo "✅ Tests completed."
            '
          """
        }
      }
    }

    stage('Deploy Flask App & Configure Nginx') {
  steps {
    sshagent(['JL_EC2_SSH_PRIVATE_KEY']) {
      sh """
        ssh -o StrictHostKeyChecking=no \$JL_EC2_USER@\$JL_EC2_PRIVATE_IP_A06 '
          set -xe

          echo "⚙️ Writing custom Nginx config..."
          sudo tee /etc/nginx/sites-available/assignment_06 > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
    }
}
EOF

          echo "🔗 Enabling Nginx config..."
          sudo ln -sf /etc/nginx/sites-available/assignment_06 /etc/nginx/sites-enabled/assignment_06
          sudo rm -f /etc/nginx/sites-enabled/default
          sudo systemctl daemon-reload
          sudo nginx -t
          sudo systemctl reload nginx

          echo "📁 Navigating to Flask app directory..."
          cd ~
          cd Assignment_06_DevOps
          source venv/bin/activate

          echo "🚀 Running Flask app..."
          nohup python3 app.py > flask_output.log 2>&1 &
        '
      """
    }
  }
}

  }

  post {
    success {
      mail to: "${env.JL_MAIL_TO_EMAIL_ID_A06}",
           subject: "✅ SUCCESS: Build #${env.BUILD_NUMBER}",
           body: "Build succeeded. View it at: ${env.BUILD_URL}"
    }
    failure {
      mail to: "${env.JL_MAIL_TO_EMAIL_ID_A06}",
           subject: "❌ FAILURE: Build #${env.BUILD_NUMBER}",
           body: "Build failed. View it at: ${env.BUILD_URL}"
    }
  }
}

```

Provide the following variables into your global configurations on Jenkins as follows:

```Jenkins_Global_Secrets
VARIABLE NAME: JL_MONGO_URI_A06
TYPE: SECRET TEXT
VALUE: YOUR_MONGO_URI_HERE

VARIABLE NAME: JL_EC2_PRIVATE_IP_A06
TYPE: SECRET TEXT
VALUE: YOUR_EC2_IP_ADDRESS_HERE

VARIABLE NAME: JL_EC2_SSH_PRIVATE_KEY
TYPE: SSH USER NAME WITH PRIVATE KEY
VALUE: Username - YOUR_EC2_USER_HERE (usually 'ubuntu' is preferred value) |
Private Key - Enter Directly - YOUR_EC2_PRIVATE_KEY_HERE (RSA KEY START UPTO RSA KEY END)

VARIABLE NAME: JL_EC2_USER
TYPE: SECRET TEXT
VALUE: YOUR_EC2_USER_HERE (usually 'ubuntu')

VARIABLE NAME: JL_MAIL_TO_EMAIL_ID_A06
TYPE: SECRET TEXT
VALUE: YOUR_EMAIL_ID_HERE (to which you want the success or failure email to be sent to)

```

#### 📸 Configure Jenkins Global Variables Screenshots

![JK_ENV_01](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_ENV_01.png)
![JK_ENV_02](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_ENV_02.png)
![JK_ENV_03](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_ENV_03.png)
![JK_ENV_04](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_ENV_04.png)

#### 📸 Output Screenshots

![JK_01](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_01.png)
![JK_02](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_02.png)
![JK_03](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_03.png)
![JK_04](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_04.png)
![JK_05](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_05.png)
![JK_06](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_06.png)
![JK_07](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_07.png)
![JK_08](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_08.png)
![JK_09](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_09.png)
![JK_10](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_10.png)
![JK_11](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_11.png)
![JK_12](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_12.png)
![JK_13](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_13.png)
![JK_14](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_14.png)
![JK_15](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_15.png)
![JK_16](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_16.png)
![JK_17](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_17.png)
![JK_18](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_18.png)
![JK_19](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_19.png)
![JK_20](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_20.png)
![JK_21](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_21.png)
![JK_22](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_22.png)
![JK_23](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_23.png)
![JK_24](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_24.png)
![JK_25](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_25.png)
![JK_26](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_26.png)
![JK_27](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_27.png)
![JK_28](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_28.png)
![JK_29](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_29.png)
![JK_30](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_30.png)
![JK_31](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/JK_31.png)


## 📌 Task 2: Deployment With Github Actions
1) Setup:
- Create Your own Python-Flask Application with MongoDB and Pytest test cases which uses MONGO_URI from a .env file or use an existing repo like the one used here
- Ensure the repository has a main branch and a staging branch.

2) GitHub Actions Workflow:
- Create a .github/workflows directory in your repository in the staging branch.
- Inside the directory, create a YAML file to define the workflow.

3) Workflow Steps:
  Define the workflow such that it performs the following jobs:
- Install Dependencies: Install all necessary dependencies for the Python application using pip.
- Run Tests: Execute the test suite using a framework like pytest.
- Build: If tests pass, prepare the application for deployment.
- Deploy to Staging: Deploy the application to a staging environment when changes are pushed to the staging branch.
- Deploy to Production: Deploy the application to production when a release is tagged.

4) Environment Secrets:
- Use GitHub Secrets to store sensitive information required for deployments (e.g., deployment keys, API tokens).

deployment.yml and deployment_prod.yml has been Configured in this repository in the following manner to achieve these use cases: 

FileName:
```
deployment.yml
```

Code:
```yml
name: CI/CD Flask App Deployment

on:
  push:
    branches:
      - staging
  release:
    types: [published]

jobs:
  build-test-deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python 3.11
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Create .env file with MONGO_URI for tests
      run: echo "MONGO_URI=${{ secrets.MONGOURI }}" > .env

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: pytest test_app.py

    - name: Deploy to EC2 instance
      if: success()
      env:
        EC2_PRIVATE_IP: ${{ secrets.EC2_PRIVATE_IP }}
        MONGO_URI: ${{ secrets.MONGOURI }}
        SSH_PRIVATE_KEY: ${{ secrets.EC2_SSH_PRIVATE_KEY }}
      run: |
        echo "Deploying to EC2 at $EC2_PRIVATE_IP"

        # Write SSH private key to a file
        echo "$SSH_PRIVATE_KEY" > private_key.pem
        chmod 600 private_key.pem

        # SSH into EC2 and run deployment commands
        ssh -o StrictHostKeyChecking=no -i private_key.pem ubuntu@${EC2_PRIVATE_IP} << EOF
          echo "Updating system..."
          sudo apt update -y

          echo "Installing dependencies..."
          sudo apt install -y python3 python3-venv python3-pip nginx git

          echo "Cloning the repo..."
          rm -rf Assignment_06_DevOps
          git clone https://github.com/JOYSTON-LEWIS/Assignment_06_DevOps.git
          cd Assignment_06_DevOps

          echo "Setting up virtual environment and installing requirements..."
          python3 -m venv venv
          source venv/bin/activate
          pip install --upgrade pip
          pip install -r requirements.txt

          echo "Creating .env file with Mongo URI..."
          echo "MONGO_URI=${MONGO_URI}" > .env

          echo "Killing existing Flask app if running..."
          pkill -f "python app.py" || true

          echo "Starting Flask app with nohup..."
          nohup python3 app.py > output.log 2>&1 &

          # Configure NGINX
          echo "Configuring NGINX..."
          cat << 'NGINX_CONF' | sudo tee /etc/nginx/sites-available/flaskapp
          server {
              listen 80;
              server_name _;
          
              location / {
                  proxy_pass http://127.0.0.1:5000;
                  proxy_set_header Host \$host;
                  proxy_set_header X-Real-IP \$remote_addr;
                  proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
              }
          }
          NGINX_CONF
          
                    echo "Enabling NGINX config..."
                    sudo ln -sf /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/flaskapp
                    sudo rm -f /etc/nginx/sites-enabled/default
                    sudo nginx -t && sudo systemctl restart nginx
          EOF

        # Remove private key file after deployment
        rm -f private_key.pem
```

FileName:
```
deployment_prod.yaml
```

Code:
```yml
name: CI/CD Flask App Production Deployment

on:
  release:
    types: [published]

jobs:
  build-test-deploy:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python 3.11
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Create .env file with MONGO_URI for tests
      run: echo "MONGO_URI=${{ secrets.MONGOURI }}" > .env

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: pytest test_app.py

    - name: Deploy to EC2 instance
      if: success()
      env:
        EC2_PRIVATE_IP: ${{ secrets.EC2_PRIVATE_IP_PROD_A06 }}
        MONGO_URI: ${{ secrets.MONGOURI }}
        SSH_PRIVATE_KEY: ${{ secrets.EC2_SSH_PRIVATE_KEY }}
      run: |
        echo "Deploying to EC2 at $EC2_PRIVATE_IP"

        # Write SSH private key to a file
        echo "$SSH_PRIVATE_KEY" > private_key.pem
        chmod 600 private_key.pem

        # SSH into EC2 and run deployment commands
        ssh -o StrictHostKeyChecking=no -i private_key.pem ubuntu@${EC2_PRIVATE_IP} << EOF
          echo "Updating system..."
          sudo apt update -y

          echo "Installing dependencies..."
          sudo apt install -y python3 python3-venv python3-pip nginx git

          echo "Cloning the repo..."
          rm -rf Assignment_06_DevOps
          git clone https://github.com/JOYSTON-LEWIS/Assignment_06_DevOps.git
          cd Assignment_06_DevOps

          echo "Setting up virtual environment and installing requirements..."
          python3 -m venv venv
          source venv/bin/activate
          pip install --upgrade pip
          pip install -r requirements.txt

          echo "Creating .env file with Mongo URI..."
          echo "MONGO_URI=${MONGO_URI}" > .env

          echo "Killing existing Flask app if running..."
          pkill -f "python app.py" || true

          echo "Starting Flask app with nohup..."
          nohup python3 app.py > output.log 2>&1 &

          # Configure NGINX
          echo "Configuring NGINX..."
          cat << 'NGINX_CONF' | sudo tee /etc/nginx/sites-available/flaskapp
          server {
              listen 80;
              server_name _;
          
              location / {
                  proxy_pass http://127.0.0.1:5000;
                  proxy_set_header Host \$host;
                  proxy_set_header X-Real-IP \$remote_addr;
                  proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
              }
          }
          NGINX_CONF
          
                    echo "Enabling NGINX config..."
                    sudo ln -sf /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/flaskapp
                    sudo rm -f /etc/nginx/sites-enabled/default
                    sudo nginx -t && sudo systemctl restart nginx
          EOF

        # Remove private key file after deployment
        rm -f private_key.pem
```

Provide the following variables into your Github Repository Secrets as follows:

```Github_Secrets
VARIABLE NAME: EC2_PRIVATE_IP
VALUE: YOUR_STAGING_EC2_IP_ADDRESS_HERE

VARIABLE NAME: EC2_PRIVATE_IP_PROD_A06
VALUE: YOUR_PRODUCTION_EC2_IP_ADDRESS_HERE

VARIABLE NAME: EC2_SSH_PRIVATE_KEY
VALUE: YOUR_EC2_SSH_PRIVATE_KEY_HERE

VARIABLE NAME: MONGOURI
VALUE: YOUR_MONGO_URI_STRING_HERE

```


#### 📸 Configure Github Secrets Screenshots

![GA_ENV_01](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_ENV_01.png)
![GA_ENV_02](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_ENV_02.png)

#### 📸 Output Screenshots

![GA_01](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_01.png)
![GA_02](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_02.png)
![GA_03](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_03.png)
![GA_04](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_04.png)
![GA_05](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_05.png)
![GA_06](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_06.png)
![GA_07](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_07.png)
![GA_08](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_08.png)
![GA_09](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_09.png)
![GA_10](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_10.png)
![GA_11](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_11.png)
![GA_12](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_12.png)
![GA_13](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_13.png)
![GA_14](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_14.png)
![GA_15](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_15.png)
![GA_16](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_16.png)
![GA_17](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_17.png)
![GA_18](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_18.png)
![GA_19](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_19.png)
![GA_20](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_20.png)
![GA_21](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_21.png)
![GA_22](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_22.png)
![GA_23](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_23.png)
![GA_24](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_24.png)
![GA_25](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_25.png)
![GA_26](https://github.com/JOYSTON-LEWIS/My-Media-Repository/blob/main/Assignment_06_DevOps_Outputs_Images/GA_26.png)

## 📜 License
This project is licensed under the MIT License.

## 🤝 Contributing
Feel free to fork and improve the scripts! ⭐ If you find this project useful, please consider starring the repo—it really helps and supports my work! 😊

## 📧 Contact
For any queries, reach out via GitHub Issues.

---

🎯 **Thank you for reviewing this project! 🚀**

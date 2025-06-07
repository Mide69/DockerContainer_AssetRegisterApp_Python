# DockerContainer_AssetRegisterApp_Python
# AR Python App

A Python application with AR (Augmented Reality) capabilities, containerized with Docker and deployed on AWS EC2.

## 🚀 Project Overview

This project is an AR-enabled Python application that provides asset configuration and management service for ITSM professionals. The application is containerized using Docker and deployed on AWS EC2 for scalable cloud hosting.

## 🏗️ Architecture

- Application: Python-based AR application
- Containerization: Docker
- Deployment: AWS EC2 (myDockerServer)
- Registry: Docker Hub (`tekktribe/ar-python-app`)

## 📋 Prerequisites

- Python 3.x
- Docker
- AWS CLI (for EC2 deployment)
- Docker Hub account

## 🛠️ Installation & Setup

### Local Development

1. Clone the repository:
   ```bash
   git clone <your-repository-url>
   cd AR-python-app
   

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application locally:
   ```bash
   python app.py
   ```

 Docker Deployment

1. **Build the Docker image:**
   ```bash
   docker build -t tekktribe/ar-python-app .
   ```

2. Run the container locally:
   ```bash
   docker run -p 8080:8080 tekktribe/ar-python-app
   ```

3. Push to Docker Hub:
   ```bash
   docker push tekktribe/ar-python-app
   ```

🌐 AWS EC2 Deployment

Server Setup (myDockerServer)

The application is deployed on AWS EC2 instance named `myDockerServer`.

Server Details:
- Instance Name: myDockerServer
- Instance Type: t2 micro
- Region: US-EAST-1

Deployment Steps

1. Connect to EC2 instance:
   ```
   Amazon EC2 Instance Connect
   ```

2. Pull the Docker image:
   ```bash
   docker pull tekktribe/ar-python-app
   ```

3. build the application:
   ```bash
   docker build -t tekktribe/ar-python-app
   ```

 
## 📁 Project Structure

```
AR-python-app/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration             
└── README.md            # This file

```
### Common Issues

1. Docker build fails:
   ```
   # Make sure you're in the correct directory
   docker build -t tekktribe/ar-python-app .
   ```

2. Push fails:
   ```
   # Login to Docker Hub first
   docker login
   docker push tekktribe/ar-python-app
   ```


## 🚀 Deployment Commands Quick Reference

```bash
# Build and push
docker build -t tekktribe/ar-python-app .
docker push tekktribe/ar-python-app

# Deploy on EC2
ssh -i your-key.pem ubuntu@your-ec2-ip
docker pull tekktribe/ar-python-app
```
![Screenshot (47)](https://github.com/user-attachments/assets/f9e9328c-f28e-43c5-b1ab-edcea168d87b)
![Screenshot (46)](https://github.com/user-attachments/assets/6ccb4288-c749-4b7a-b8d0-185b3ed0cf2a)
![Screenshot (45)](https://github.com/user-attachments/assets/57b02ace-a00b-4c10-b3fb-db32a9c47851)
![Screenshot (48)](https://github.com/user-attachments/assets/d7533681-e3e1-46f2-8726-3df6b5355e58)


**Last Updated:** [Current Date]
**Version:** 1.0.0

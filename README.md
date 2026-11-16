# 🚨 AWS Incident Response Panic Button

A fully serverless, event-driven cloud application designed to simulate a physical emergency trigger. When activated, it bypasses manual human delay, instantly executing an automated incident response playbook and notifying administrators in under 2 seconds.

## 📖 Overview
During active security breaches, every second counts. This project demonstrates how to bridge edge hardware simulations securely to enterprise cloud backends. It uses a Python CLI as "virtual hardware" to publish a secure MQTT message via Mutual TLS (X.509) to AWS IoT Core, which then triggers a serverless backend pipeline.

## 🏗️ Architecture & AWS Services Used
1. **AWS IoT Core:** Securely ingests MQTT messages from the Python simulator over port 8883.
2. **AWS Lambda (PanicProcessor):** The "Brain" triggered by an IoT Rule. It updates the database and fires alerts.
3. **Amazon DynamoDB:** NoSQL database storing the system state (`ARMED` or `INCIDENT_ACTIVE`).
4. **Amazon SNS:** Dispatches immediate critical email alerts to administrators.
5. **AWS Lambda (PanicGetter):** Serves the DynamoDB data via a public Function URL.
6. **Amazon S3:** Hosts the frontend "Command Center" static website dashboard.

## 🚀 Live Demo
* **Live Dashboard URL:** [http://panic-dashboard-manisathwik-2026.s3-website-ap-southeast-2.amazonaws.com](http://panic-dashboard-manisathwik-2026.s3-website-ap-southeast-2.amazonaws.com)
* **Backend:** Live on AWS (`ap-southeast-2` Sydney)
* **Hardware Simulator:** Local Python CLI

## 💻 Tech Stack
* **Cloud:** AWS (IoT Core, Lambda, DynamoDB, SNS, S3, IAM)
* **Backend:** Python 3.12, Boto3, Paho-MQTT
* **Frontend:** HTML5, CSS3 (Glassmorphism UI), Vanilla JavaScript

## ⚙️ How to Run the Simulator Locally
> **⚠️ Security Notice:** The `certs/` folder containing X.509 certificates and private keys is **NOT** included in this repository for security reasons.

1. Clone the repository:
   ```bash
   git clone https://github.com/manisathwik320-prog/aws-incident-response-panic-button.git

AcuVerify: Academic Integrity & Verification System

A secure Django-based platform designed to automate student grading, generate digital report cards, and eliminate academic forgery through QR-code verification.

🌟 Core Mission

To provide a "Single Source of Truth" for academic records, ensuring that student marks are tamper-proof and easily verifiable by parents and school administrators.

🛠️ Key Technical Features

Anti-Forgery Engine: Automatically generates a unique cryptographic hash and QR Code for every report card.

Automated PDF Generation: High-fidelity report cards generated on-the-fly using ReportLab.

Role-Based Access Control (RBAC): * Teachers: Secure entry for marks and assignment distribution.

Parents: Real-time monitoring of student tasks and holiday engagement.

Admins: System-wide audit logs and user management.

Progress Tracking: Visual dashboard for monitoring student performance trends over multiple terms.

🚀 Tech Stack

Backend: Django (Python 3.10)

Database: PostgreSQL (Relational integrity for student/subject mapping)

Security: QR Code generation (Segno/Python-QR), Role-based permissions

Frontend: Bootstrap 5 (Responsive for mobile-first parent access)

🔧 Installation & Deployment

Clone the repository

Bash

git clone https://github.com/dnyongesa244-pro/AcuVerify.git cd AcuVerify 

Environment Setup

Bash

python -m venv venv source venv/bin/activate # On Windows: venv\Scripts\activate pip install -r requirements.txt 

Database Migration

Bash

python manage.py makemigrations python manage.py migrate 

Run Server

Bash

python manage.py runserver 

🔐 The Verification Workflow

A teacher submits marks → 2. System generates a unique digital signature → 3. Signature is embedded into a QR code on the PDF → 4. Anyone with the physical/digital report can scan to verify the data against the live database.


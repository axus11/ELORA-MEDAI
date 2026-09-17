from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from datetime import datetime

import os
from dotenv import load_dotenv
import uuid
import re
import json
import urllib.parse
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

load_dotenv()
# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "ELORA_SECRET_KEY",
    "dev-only-secret-change-me"
)

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///"
    + os.path.join(
        BASE_DIR,
        "elora_medai.db"
    )
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
# =========================================================
# CHAT — CONVERSATION
# =========================================================

class ChatConversation(db.Model):

    __tablename__ = "chat_conversations"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctor.id"),
        nullable=False
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patient.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships

    doctor = db.relationship(
        "Doctor",
        backref=db.backref(
            "chat_conversations",
            lazy=True
        )
    )

    patient = db.relationship(
        "Patient",
        backref=db.backref(
            "chat_conversations",
            lazy=True
        )
    )

    messages = db.relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at.asc()"
    )


# =========================================================
# CHAT — MESSAGE
# =========================================================

class ChatMessage(db.Model):

    __tablename__ = "chat_messages"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    conversation_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "chat_conversations.id"
        ),
        nullable=False
    )

    sender_type = db.Column(
        db.String(20),
        nullable=False
    )

    sender_id = db.Column(
        db.Integer,
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    conversation = db.relationship(
        "ChatConversation",
        back_populates="messages"
    )
# =========================================================
# DOCTOR SETTINGS MODEL
# =========================================================

class DoctorSettings(db.Model):

    __tablename__ = "doctor_settings"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctor.id"),
        unique=True,
        nullable=False
    )

    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    email_notifications = db.Column(
        db.Boolean,
        default=True
    )

    case_notifications = db.Column(
        db.Boolean,
        default=True
    )

    evidence_notifications = db.Column(
        db.Boolean,
        default=True
    )

    security_notifications = db.Column(
        db.Boolean,
        default=True
    )

    # =====================================================
    # APPEARANCE
    # =====================================================

    theme = db.Column(
        db.String(30),
        default="dark"
    )

    compact_mode = db.Column(
        db.Boolean,
        default=False
    )

    animations = db.Column(
        db.Boolean,
        default=True
    )

    # =====================================================
    # AI PREFERENCES
    # =====================================================

    ai_assistance = db.Column(
        db.Boolean,
        default=True
    )

    ai_evidence = db.Column(
        db.Boolean,
        default=True
    )

    ai_risk_alerts = db.Column(
        db.Boolean,
        default=True
    )

    ai_explanations = db.Column(
        db.Boolean,
        default=True
    )

    ai_confidence = db.Column(
        db.String(30),
        default="balanced"
    )

    # =====================================================
    # CLINICAL PREFERENCES
    # =====================================================

    default_case_status = db.Column(
        db.String(50),
        default="New"
    )

    auto_save = db.Column(
        db.Boolean,
        default=True
    )

    confirm_deletions = db.Column(
        db.Boolean,
        default=True
    )

    metric_units = db.Column(
        db.Boolean,
        default=True
    )

    show_patient_id = db.Column(
        db.Boolean,
        default=True
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    doctor = db.relationship(
        "Doctor",
        backref=db.backref(
            "settings",
            uselist=False
        )
    )
# =========================================================
# DATABASE MODELS
# =========================================================


class Doctor(db.Model):

    __tablename__ = "doctor"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(50),
        default="doctor"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    cases = db.relationship(
        "ClinicalCase",
        backref="doctor",
        lazy=True
    )

    evidence_items = db.relationship(
        "Evidence",
        backref="doctor",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Patient(db.Model):

    __tablename__ = "patient"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    patient_id = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    first_name = db.Column(
        db.String(100),
        nullable=False
    )

    last_name = db.Column(
        db.String(100),
        nullable=False
    )

    date_of_birth = db.Column(
        db.String(20),
        nullable=False
    )

    gender = db.Column(
        db.String(30)
    )

    email = db.Column(
        db.String(120)
    )

    phone = db.Column(
        db.String(50)
    )
    password_hash = db.Column(
        db.String(255),
        nullable=True
    )

    patient_account_active = db.Column(
        db.Boolean,
        default=True
    )
    
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    cases = db.relationship(
        "ClinicalCase",
        backref="patient",
        lazy=True,
        cascade="all, delete-orphan"
    )

    @property
    def full_name(self):

        return (
            f"{self.first_name} "
            f"{self.last_name}"
        )

patient_password_hash = db.Column(
    db.String(255),
    nullable=True
)

patient_account_active = db.Column(
    db.Boolean,
    default=False,
    nullable=False
)
patient_last_login = db.Column(
    db.DateTime,
    nullable=True
)

class ClinicalCase(db.Model):

    __tablename__ = "clinical_case"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    case_id = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    patient_id = db.Column(
        db.Integer,
        db.ForeignKey("patient.id"),
        nullable=False
    )

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctor.id"),
        nullable=False
    )

    # =====================================================
    # CLINICAL INFORMATION
    # =====================================================

    chief_complaint = db.Column(
        db.Text
    )

    symptoms = db.Column(
        db.Text
    )

    onset = db.Column(
        db.String(100)
    )

    severity = db.Column(
        db.String(50)
    )

    # =====================================================
    # VITAL SIGNS
    # =====================================================

    blood_pressure = db.Column(
        db.String(30)
    )

    heart_rate = db.Column(
        db.String(30)
    )

    temperature = db.Column(
        db.String(30)
    )

    spo2 = db.Column(
        db.String(30)
    )

    respiratory_rate = db.Column(
        db.String(30)
    )

    weight = db.Column(
        db.String(30)
    )

    # =====================================================
    # MEDICAL INFORMATION
    # =====================================================

    medical_history = db.Column(
        db.Text
    )

    medications = db.Column(
        db.Text
    )

    # =====================================================
    # STATUS
    # =====================================================

    status = db.Column(
        db.String(50),
        default="New"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    evidence_items = db.relationship(
        "Evidence",
        backref="clinical_case",
        lazy=True,
        cascade="all, delete-orphan"
    )


# =========================================================
# EVIDENCE MODEL
# =========================================================


class Evidence(db.Model):

    __tablename__ = "evidence"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # -----------------------------------------------------
    # SOURCE IDENTIFICATION
    # -----------------------------------------------------

    pmid = db.Column(
        db.String(50),
        index=True
    )

    doi = db.Column(
        db.String(255)
    )

    source = db.Column(
        db.String(100),
        default="PubMed"
    )

    url = db.Column(
        db.Text
    )

    # -----------------------------------------------------
    # ARTICLE INFORMATION
    # -----------------------------------------------------

    title = db.Column(
        db.Text,
        nullable=False
    )

    abstract = db.Column(
        db.Text
    )

    journal = db.Column(
        db.String(500)
    )

    publication_date = db.Column(
        db.String(100)
    )

    authors = db.Column(
        db.Text
    )

    article_type = db.Column(
        db.String(255)
    )

    # -----------------------------------------------------
    # ELORA INFORMATION
    # -----------------------------------------------------

    notes = db.Column(
        db.Text
    )

    tags = db.Column(
        db.Text
    )

    relevance = db.Column(
        db.String(50),
        default="Unreviewed"
    )

    # -----------------------------------------------------
    # OWNERSHIP
    # -----------------------------------------------------

    doctor_id = db.Column(
        db.Integer,
        db.ForeignKey("doctor.id"),
        nullable=False
    )

    case_id = db.Column(
        db.Integer,
        db.ForeignKey("clinical_case.id"),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

with app.app_context():

    db.create_all()
# =========================================================
# PHASE 2 — PATIENT CHAT API
# =========================================================


# =========================================================
# CHAT SERIALIZER
# =========================================================

def chat_message_to_dict(message):

    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sender_type": message.sender_type,
        "sender_id": message.sender_id,
        "message": message.message,
        "is_read": bool(message.is_read),
        "created_at": (
            message.created_at.isoformat()
            if message.created_at
            else None
        )
    }


def chat_conversation_to_dict(conversation):

    return {
        "id": conversation.id,
        "doctor_id": conversation.doctor_id,
        "patient_id": conversation.patient_id,
        "created_at": (
            conversation.created_at.isoformat()
            if conversation.created_at
            else None
        ),
        "updated_at": (
            conversation.updated_at.isoformat()
            if conversation.updated_at
            else None
        )
    }


# =========================================================
# START / GET CONVERSATION
# =========================================================

@app.route(
    "/api/chat/start/<int:patient_id>",
    methods=["POST"]
)
def start_chat(patient_id):

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    doctor_id = session["doctor_id"]

    # -----------------------------------------------------
    # VERIFY PATIENT
    # -----------------------------------------------------

    patient = Patient.query.filter_by(
        id=patient_id
    ).first()

    if not patient:

        return jsonify({
            "success": False,
            "error": "Patient not found."
        }), 404

    # -----------------------------------------------------
    # CHECK EXISTING CONVERSATION
    # -----------------------------------------------------

    conversation = ChatConversation.query.filter_by(
        doctor_id=doctor_id,
        patient_id=patient.id
    ).first()

    # -----------------------------------------------------
    # CREATE IF NEEDED
    # -----------------------------------------------------

    if not conversation:

        conversation = ChatConversation(
            doctor_id=doctor_id,
            patient_id=patient.id
        )

        try:

            db.session.add(
                conversation
            )

            db.session.commit()

        except Exception as error:

            db.session.rollback()

            print(
                "START CHAT ERROR:",
                error
            )

            return jsonify({
                "success": False,
                "error": "Unable to start conversation."
            }), 500

    return jsonify({

        "success": True,

        "conversation":
            chat_conversation_to_dict(
                conversation
            ),

        "patient": {

            "id": patient.id,

            "patient_id":
                patient.patient_id,

            "name":
                patient.full_name

        }

    })


# =========================================================
# GET CHAT MESSAGES
# =========================================================

@app.route(
    "/api/chat/<int:conversation_id>/messages",
    methods=["GET"]
)
def get_chat_messages(conversation_id):

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    doctor_id = session["doctor_id"]

    # -----------------------------------------------------
    # VERIFY CONVERSATION BELONGS TO DOCTOR
    # -----------------------------------------------------

    conversation = ChatConversation.query.filter_by(
        id=conversation_id,
        doctor_id=doctor_id
    ).first()

    if not conversation:

        return jsonify({
            "success": False,
            "error": "Conversation not found."
        }), 404

    messages = ChatMessage.query.filter_by(
        conversation_id=conversation.id
    ).order_by(
        ChatMessage.created_at.asc()
    ).all()

    return jsonify({

        "success": True,

        "conversation":
            chat_conversation_to_dict(
                conversation
            ),

        "messages": [

            chat_message_to_dict(
                message
            )

            for message in messages

        ]

    })


# =========================================================
# SEND MESSAGE
# =========================================================

@app.route(
    "/api/chat/<int:conversation_id>/send",
    methods=["POST"]
)
def send_chat_message(conversation_id):

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    doctor_id = session["doctor_id"]

    # -----------------------------------------------------
    # VERIFY CONVERSATION
    # -----------------------------------------------------

    conversation = ChatConversation.query.filter_by(
        id=conversation_id,
        doctor_id=doctor_id
    ).first()

    if not conversation:

        return jsonify({
            "success": False,
            "error": "Conversation not found."
        }), 404

    # -----------------------------------------------------
    # READ REQUEST
    # -----------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    message_text = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    # -----------------------------------------------------
    # VALIDATE MESSAGE
    # -----------------------------------------------------

    if not message_text:

        return jsonify({
            "success": False,
            "error": "Message cannot be empty."
        }), 400

    if len(message_text) > 5000:

        return jsonify({
            "success": False,
            "error":
                "Message cannot exceed 5000 characters."
        }), 400

    # -----------------------------------------------------
    # CREATE MESSAGE
    # -----------------------------------------------------

    message = ChatMessage(

        conversation_id=conversation.id,

        sender_type="doctor",

        sender_id=doctor_id,

        message=message_text,

        is_read=False

    )

    try:

        db.session.add(
            message
        )

        conversation.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({

            "success": True,

            "message":
                chat_message_to_dict(
                    message
                )

        })

    except Exception as error:

        db.session.rollback()

        print(
            "SEND CHAT MESSAGE ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "error": "Unable to send message."
        }), 500


# =========================================================
# MARK MESSAGES AS READ
# =========================================================

@app.route(
    "/api/chat/<int:conversation_id>/read",
    methods=["POST"]
)
def mark_chat_messages_read(conversation_id):

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    doctor_id = session["doctor_id"]

    # -----------------------------------------------------
    # VERIFY CONVERSATION
    # -----------------------------------------------------

    conversation = ChatConversation.query.filter_by(
        id=conversation_id,
        doctor_id=doctor_id
    ).first()

    if not conversation:

        return jsonify({
            "success": False,
            "error": "Conversation not found."
        }), 404

    # -----------------------------------------------------
    # MARK PATIENT MESSAGES AS READ
    # -----------------------------------------------------

    unread_messages = ChatMessage.query.filter_by(
        conversation_id=conversation.id,
        sender_type="patient",
        is_read=False
    ).all()

    for message in unread_messages:

        message.is_read = True

    try:

        db.session.commit()

        return jsonify({

            "success": True,

            "marked_read":
                len(unread_messages)

        })

    except Exception as error:

        db.session.rollback()

        print(
            "MARK CHAT READ ERROR:",
            error
        )

        return jsonify({
            "success": False,
            "error":
                "Unable to update message status."
        }), 500


# =========================================================
# GET CHAT SUMMARY FOR PATIENT
# =========================================================

@app.route(
    "/api/chat/patient/<int:patient_id>",
    methods=["GET"]
)
def get_patient_chat(patient_id):

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    doctor_id = session["doctor_id"]

    # -----------------------------------------------------
    # VERIFY PATIENT
    # -----------------------------------------------------

    patient = Patient.query.filter_by(
        id=patient_id
    ).first()

    if not patient:

        return jsonify({
            "success": False,
            "error": "Patient not found."
        }), 404

    # -----------------------------------------------------
    # FIND CONVERSATION
    # -----------------------------------------------------

    conversation = ChatConversation.query.filter_by(
        doctor_id=doctor_id,
        patient_id=patient.id
    ).first()

    # -----------------------------------------------------
    # NO CONVERSATION YET
    # -----------------------------------------------------

    if not conversation:

        return jsonify({

            "success": True,

            "exists": False,

            "patient": {

                "id": patient.id,

                "patient_id":
                    patient.patient_id,

                "name":
                    patient.full_name

            }

        })

    # -----------------------------------------------------
    # GET LAST MESSAGE
    # -----------------------------------------------------

    last_message = ChatMessage.query.filter_by(
        conversation_id=conversation.id
    ).order_by(
        ChatMessage.created_at.desc()
    ).first()

    unread_count = ChatMessage.query.filter_by(
        conversation_id=conversation.id,
        sender_type="patient",
        is_read=False
    ).count()

    return jsonify({

        "success": True,

        "exists": True,

        "conversation":
            chat_conversation_to_dict(
                conversation
            ),

        "last_message": (

            chat_message_to_dict(
                last_message
            )

            if last_message
            else None

        ),

        "unread_count":
            unread_count

    })

# =========================================================
# AUTHENTICATION HELPERS
# =========================================================


def doctor_logged_in():

    return "doctor_id" in session

def patient_logged_in():
    return "patient_id" in session
def get_current_doctor():

    if not doctor_logged_in():

        return None

    return Doctor.query.get(
        session["doctor_id"]
    )


def get_doctor_initials():

    doctor_name = session.get(
        "doctor_name",
        "Doctor"
    )

    initials = "".join(
        word[0].upper()
        for word in doctor_name.split()
        if word
    )

    return initials[:2]


def doctor_context():

    return {

        "doctor_name": session.get(
            "doctor_name",
            "Doctor"
        ),

        "doctor_email": session.get(
            "doctor_email"
        ),

        "doctor_initials": get_doctor_initials()

    }


# =========================================================
# SAFE NUMBER PARSER
# =========================================================


def parse_number(value):

    if value is None:

        return None

    try:

        match = re.search(
            r"-?\d+(?:\.\d+)?",
            str(value)
        )

        if match:

            return float(
                match.group()
            )

    except Exception:

        pass

    return None


# =========================================================
# BLOOD PRESSURE PARSER
# =========================================================


def parse_blood_pressure(value):

    if not value:

        return None, None

    match = re.search(
        r"(\d{2,3})\s*/\s*(\d{2,3})",
        str(value)
    )

    if not match:

        return None, None

    try:

        return (
            int(match.group(1)),
            int(match.group(2))
        )

    except Exception:

        return None, None


# =========================================================
# ELORA MEDAI CLINICAL ANALYZER
# =========================================================


def analyze_clinical_case(
    clinical_case
):

    findings = []

    risk_flags = []

    differential = []

    recommendations = []

    evidence = []

    symptoms_text = (
        f"{clinical_case.chief_complaint or ''} "
        f"{clinical_case.symptoms or ''} "
        f"{clinical_case.medical_history or ''}"
    ).lower()

    severity = (
        clinical_case.severity or ""
    ).lower()

    # =====================================================
    # PARSE VITALS
    # =====================================================

    temperature = parse_number(
        clinical_case.temperature
    )

    heart_rate = parse_number(
        clinical_case.heart_rate
    )

    spo2 = parse_number(
        clinical_case.spo2
    )

    respiratory_rate = parse_number(
        clinical_case.respiratory_rate
    )

    systolic, diastolic = parse_blood_pressure(
        clinical_case.blood_pressure
    )

    # =====================================================
    # BLOOD PRESSURE
    # =====================================================

    if (
        systolic is not None
        and diastolic is not None
    ):

        if (
            systolic >= 180
            or diastolic >= 120
        ):

            risk_flags.append({

                "level": "HIGH",

                "title": (
                    "Markedly elevated "
                    "blood pressure"
                ),

                "detail": (
                    f"Recorded blood pressure "
                    f"is {systolic}/{diastolic} mmHg."
                )

            })

            findings.append(
                "Blood pressure is markedly elevated."
            )

        elif (
            systolic >= 140
            or diastolic >= 90
        ):

            risk_flags.append({

                "level": "MODERATE",

                "title": (
                    "Elevated blood pressure"
                ),

                "detail": (
                    f"Recorded blood pressure "
                    f"is {systolic}/{diastolic} mmHg."
                )

            })

            findings.append(
                "Blood pressure is elevated."
            )

        elif (
            systolic < 90
            or diastolic < 60
        ):

            risk_flags.append({

                "level": "MODERATE",

                "title": (
                    "Low blood pressure"
                ),

                "detail": (
                    f"Recorded blood pressure "
                    f"is {systolic}/{diastolic} mmHg."
                )

            })

            findings.append(
                "Blood pressure is below typical "
                "adult resting ranges."
            )

    # =====================================================
    # HEART RATE
    # =====================================================

    if heart_rate is not None:

        if heart_rate >= 120:

            risk_flags.append({

                "level": "MODERATE",

                "title": "Marked tachycardia",

                "detail": (
                    f"Heart rate recorded at "
                    f"{heart_rate} BPM."
                )

            })

            findings.append(
                "Heart rate is significantly elevated."
            )

        elif heart_rate > 100:

            findings.append(
                "Heart rate is above the usual "
                "adult resting range."
            )

        elif heart_rate < 50:

            findings.append(
                "Heart rate is below the usual "
                "adult resting range."
            )

    # =====================================================
    # TEMPERATURE
    # =====================================================

    if temperature is not None:

        if temperature >= 39:

            risk_flags.append({

                "level": "MODERATE",

                "title": "High fever",

                "detail": (
                    f"Temperature recorded at "
                    f"{temperature} °C."
                )

            })

            findings.append(
                "Temperature is significantly elevated."
            )

        elif temperature >= 38:

            findings.append(
                "Temperature is consistent with "
                "a febrile measurement."
            )

        elif temperature < 35:

            risk_flags.append({

                "level": "HIGH",

                "title": "Low body temperature",

                "detail": (
                    f"Temperature recorded at "
                    f"{temperature} °C."
                )

            })

            findings.append(
                "Temperature is markedly low."
            )

    # =====================================================
    # OXYGEN SATURATION
    # =====================================================

    if spo2 is not None:

        if spo2 < 90:

            risk_flags.append({

                "level": "HIGH",

                "title": "Low oxygen saturation",

                "detail": (
                    f"SpO₂ recorded at {spo2}%."
                )

            })

            findings.append(
                "Oxygen saturation is markedly reduced."
            )

        elif spo2 < 94:

            risk_flags.append({

                "level": "MODERATE",

                "title": (
                    "Reduced oxygen saturation"
                ),

                "detail": (
                    f"SpO₂ recorded at {spo2}%."
                )

            })

            findings.append(
                "Oxygen saturation is below the "
                "usual target range."
            )

    # =====================================================
    # RESPIRATORY RATE
    # =====================================================

    if respiratory_rate is not None:

        if respiratory_rate > 24:

            risk_flags.append({

                "level": "MODERATE",

                "title": (
                    "Increased respiratory rate"
                ),

                "detail": (
                    f"Respiratory rate recorded "
                    f"at {respiratory_rate}/min."
                )

            })

            findings.append(
                "Respiratory rate is elevated."
            )

        elif respiratory_rate < 10:

            risk_flags.append({

                "level": "MODERATE",

                "title": (
                    "Low respiratory rate"
                ),

                "detail": (
                    f"Respiratory rate recorded "
                    f"at {respiratory_rate}/min."
                )

            })

            findings.append(
                "Respiratory rate is below the "
                "usual adult resting range."
            )

    # =====================================================
    # RESPIRATORY PATTERN
    # =====================================================

    respiratory_keywords = [

        "cough",
        "shortness of breath",
        "dyspnea",
        "breathlessness",
        "wheezing",
        "chest pain",
        "sputum"

    ]

    if any(
        keyword in symptoms_text
        for keyword in respiratory_keywords
    ):

        differential.append({

            "condition": (
                "Respiratory tract process"
            ),

            "reason": (
                "Respiratory symptoms are present "
                "and require correlation with "
                "examination and history."
            )

        })

    # =====================================================
    # INFECTION / INFLAMMATORY PATTERN
    # =====================================================

    infection_keywords = [

        "fever",
        "chills",
        "infection",
        "sore throat",
        "cough",
        "fatigue",
        "body ache"

    ]

    infection_match = any(
        keyword in symptoms_text
        for keyword in infection_keywords
    )

    if (
        infection_match
        or (
            temperature is not None
            and temperature >= 38
        )
    ):

        differential.append({

            "condition": (
                "Infectious or inflammatory process"
            ),

            "reason": (
                "Symptoms and/or temperature may "
                "be compatible with an infectious "
                "or inflammatory process."
            )

        })

        evidence.append(
            "Correlate fever and systemic symptoms "
            "with history, examination and appropriate testing."
        )

    # =====================================================
    # CARDIOVASCULAR PATTERN
    # =====================================================

    cardiovascular_keywords = [

        "chest pain",
        "palpitations",
        "syncope",
        "fainting",
        "dizziness"

    ]

    if any(
        keyword in symptoms_text
        for keyword in cardiovascular_keywords
    ):

        differential.append({

            "condition": (
                "Cardiovascular cause"
            ),

            "reason": (
                "Cardiovascular symptoms are present; "
                "clinical assessment should determine "
                "whether urgent evaluation is required."
            )

        })

    # =====================================================
    # NEUROLOGICAL RED FLAGS
    # =====================================================

    neurological_keywords = [

        "confusion",
        "weakness",
        "seizure",
        "loss of consciousness",
        "stroke",
        "facial droop",
        "speech difficulty"

    ]

    if any(
        keyword in symptoms_text
        for keyword in neurological_keywords
    ):

        risk_flags.append({

            "level": "HIGH",

            "title": (
                "Neurological red flag"
            ),

            "detail": (
                "Neurological warning symptoms "
                "were identified in the submitted "
                "clinical text."
            )

        })

        differential.append({

            "condition": (
                "Neurological process"
            ),

            "reason": (
                "Neurological symptoms require "
                "focused neurologic assessment."
            )

        })

    # =====================================================
    # SEVERITY
    # =====================================================

    if severity in [
        "critical",
        "severe"
    ]:

        risk_flags.append({

            "level": "HIGH",

            "title": (
                "High reported severity"
            ),

            "detail": (
                f"The submitted case severity "
                f"is {clinical_case.severity}."
            )

        })

    # =====================================================
    # CHEST PAIN
    # =====================================================

    if "chest pain" in symptoms_text:

        risk_flags.append({

            "level": "HIGH",

            "title": "Chest pain reported",

            "detail": (
                "Chest pain requires clinical "
                "assessment for potentially "
                "serious causes."
            )

        })

        recommendations.append(
            "Assess chest pain characteristics, "
            "associated symptoms and cardiovascular "
            "risk factors."
        )

    # =====================================================
    # GENERAL RECOMMENDATIONS
    # =====================================================

    recommendations.extend([

        "Review the complete history and physical examination.",

        "Confirm abnormal vital signs with repeat measurements when appropriate.",

        "Correlate automated findings with the patient's clinical presentation.",

        "Consider targeted laboratory or diagnostic testing based on clinical judgment."

    ])

    # =====================================================
    # HIGH-RISK RECOMMENDATION
    # =====================================================

    high_risk = any(
        flag["level"] == "HIGH"
        for flag in risk_flags
    )

    if high_risk:

        recommendations.insert(
            0,
            "Urgently assess the identified red flags "
            "and determine whether escalation of care "
            "is required."
        )

    # =====================================================
    # DEFAULT FINDING
    # =====================================================

    if not findings:

        findings.append(
            "No major abnormal vital-sign pattern "
            "was identified from the values supplied."
        )

    # =====================================================
    # DEFAULT DIFFERENTIAL
    # =====================================================

    if not differential:

        differential.append({

            "condition": (
                "Non-specific clinical presentation"
            ),

            "reason": (
                "The submitted information does not "
                "establish a specific diagnostic pattern."
            )

        })

    # =====================================================
    # RISK LEVEL
    # =====================================================

    if any(
        flag["level"] == "HIGH"
        for flag in risk_flags
    ):

        overall_risk = "HIGH"

    elif any(
        flag["level"] == "MODERATE"
        for flag in risk_flags
    ):

        overall_risk = "MODERATE"

    else:

        overall_risk = "LOW"

    # =====================================================
    # CONFIDENCE
    # =====================================================

    clinical_fields = [

        clinical_case.chief_complaint,
        clinical_case.symptoms,
        clinical_case.onset,
        clinical_case.severity,
        clinical_case.blood_pressure,
        clinical_case.heart_rate,
        clinical_case.temperature,
        clinical_case.spo2,
        clinical_case.respiratory_rate,
        clinical_case.medical_history,
        clinical_case.medications

    ]

    data_points = sum(

        1
        for field in clinical_fields
        if field
        and str(field).strip()

    )

    if data_points >= 8:

        confidence = "HIGH"

    elif data_points >= 4:

        confidence = "MODERATE"

    else:

        confidence = "LIMITED"

    # =====================================================
    # SUMMARY
    # =====================================================

    if overall_risk == "HIGH":

        summary = (
            "The submitted case contains one or more "
            "findings that warrant prompt clinical review."
        )

    elif overall_risk == "MODERATE":

        summary = (
            "The submitted case contains findings that "
            "warrant clinical correlation and further assessment."
        )

    else:

        summary = (
            "No major automated red-flag pattern was "
            "identified from the available information."
        )

    # =====================================================
    # RETURN
    # =====================================================

    return {

        "engine": (
            "ELORA MEDAI Clinical Intelligence Engine"
        ),

        "version": "0.2",

        "timestamp": (
            datetime.utcnow().isoformat()
            + "Z"
        ),

        "risk_level": overall_risk,

        "confidence": confidence,

        "summary": summary,

        "findings": findings,

        "risk_flags": risk_flags,

        "differential": differential,

        "recommendations": recommendations,

        "evidence": evidence,

        "disclaimer": (
            "This analysis is generated by a clinical "
            "decision-support prototype. It is not a diagnosis "
            "and must be independently reviewed by a qualified clinician."
        )

    }


# =========================================================
# PUBMED HELPERS
# =========================================================


PUBMED_BASE_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
)


def pubmed_request(
    endpoint,
    params
):

    query_string = urllib.parse.urlencode(
        params
    )

    url = (
        PUBMED_BASE_URL
        + endpoint
        + "?"
        + query_string
    )

    request_object = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "ELORA-MEDAI/0.2 "
                "clinical-evidence-system"
            )
        }
    )

    try:

        with urllib.request.urlopen(
            request_object,
            timeout=15
        ) as response:

            return response.read()

    except urllib.error.URLError as error:

        print(
            "PUBMED REQUEST ERROR:",
            error
        )

        raise


def pubmed_search(
    query,
    limit=10
):

    query = (query or "").strip()

    if not query:

        return []

    try:

        data = pubmed_request(
            "esearch.fcgi",
            {
                "db": "pubmed",
                "term": query,
                "retmode": "json",
                "retmax": min(
                    max(int(limit), 1),
                    25
                )
            }
        )

        parsed = json.loads(
            data.decode("utf-8")
        )

        ids = (
            parsed
            .get("esearchresult", {})
            .get("idlist", [])
        )

        if not ids:

            return []

        articles_xml = pubmed_request(
            "efetch.fcgi",
            {
                "db": "pubmed",
                "id": ",".join(ids),
                "retmode": "xml"
            }
        )

        return parse_pubmed_articles(
            articles_xml
        )

    except Exception as error:

        print(
            "PUBMED SEARCH ERROR:",
            error
        )

        raise


def get_xml_text(
    element
):

    if element is None:

        return ""

    return "".join(
        element.itertext()
    ).strip()


def parse_pubmed_articles(
    xml_data
):

    root = ET.fromstring(
        xml_data
    )

    articles = []

    for article in root.findall(
        ".//PubmedArticle"
    ):

        pmid_element = article.find(
            ".//PMID"
        )

        pmid = (
            get_xml_text(pmid_element)
            if pmid_element is not None
            else ""
        )

        title_element = article.find(
            ".//ArticleTitle"
        )

        title = (
            get_xml_text(title_element)
            if title_element is not None
            else "Untitled article"
        )

        abstract_parts = []

        for abstract_text in article.findall(
            ".//Abstract/AbstractText"
        ):

            label = abstract_text.attrib.get(
                "Label"
            )

            text = get_xml_text(
                abstract_text
            )

            if label:

                text = (
                    label
                    + ": "
                    + text
                )

            if text:

                abstract_parts.append(
                    text
                )

        abstract = " ".join(
            abstract_parts
        )

        journal_element = article.find(
            ".//Journal/Title"
        )

        journal = (
            get_xml_text(journal_element)
            if journal_element is not None
            else ""
        )

        # -------------------------------------------------
        # AUTHORS
        # -------------------------------------------------

        authors = []

        for author in article.findall(
            ".//AuthorList/Author"
        ):

            collective = author.find(
                "CollectiveName"
            )

            if collective is not None:

                name = get_xml_text(
                    collective
                )

            else:

                last_name = get_xml_text(
                    author.find("LastName")
                )

                initials = get_xml_text(
                    author.find("Initials")
                )

                if last_name and initials:

                    name = (
                        f"{last_name} "
                        f"{initials}"
                    )

                else:

                    name = (
                        last_name
                        or initials
                    )

            if name:

                authors.append(name)

        # -------------------------------------------------
        # PUBLICATION DATE
        # -------------------------------------------------

        year = ""

        month = ""

        day = ""

        pub_date = article.find(
            ".//JournalIssue/PubDate"
        )

        if pub_date is not None:

            year_element = pub_date.find(
                "Year"
            )

            month_element = pub_date.find(
                "Month"
            )

            day_element = pub_date.find(
                "Day"
            )

            if year_element is not None:

                year = get_xml_text(
                    year_element
                )

            if month_element is not None:

                month = get_xml_text(
                    month_element
                )

            if day_element is not None:

                day = get_xml_text(
                    day_element
                )

        publication_date = " ".join(
            part
            for part in [
                day,
                month,
                year
            ]
            if part
        )

        # -------------------------------------------------
        # DOI
        # -------------------------------------------------

        doi = ""

        for article_id in article.findall(
            ".//ArticleId"
        ):

            if (
                article_id.attrib.get(
                    "IdType"
                )
                == "doi"
            ):

                doi = get_xml_text(
                    article_id
                )

                break

        # -------------------------------------------------
        # ARTICLE TYPES
        # -------------------------------------------------

        article_types = []

        for publication_type in article.findall(
            ".//PublicationTypeList/PublicationType"
        ):

            publication_type_text = (
                get_xml_text(
                    publication_type
                )
            )

            if publication_type_text:

                article_types.append(
                    publication_type_text
                )

        articles.append({

            "pmid": pmid,

            "title": title,

            "abstract": abstract,

            "journal": journal,

            "authors": authors,

            "publication_date": (
                publication_date
            ),

            "doi": doi,

            "article_type": (
                article_types
            ),

            "source": "PubMed",

            "url": (
                "https://pubmed.ncbi.nlm.nih.gov/"
                + pmid
                + "/"
                if pmid
                else ""
            )

        })

    return articles


# =========================================================
# EVIDENCE SERIALIZER
# =========================================================


def evidence_to_dict(
    evidence
):

    authors = []

    if evidence.authors:

        try:

            parsed_authors = json.loads(
                evidence.authors
            )

            if isinstance(
                parsed_authors,
                list
            ):

                authors = parsed_authors

        except Exception:

            authors = [
                evidence.authors
            ]

    article_types = []

    if evidence.article_type:

        try:

            parsed_types = json.loads(
                evidence.article_type
            )

            if isinstance(
                parsed_types,
                list
            ):

                article_types = parsed_types

        except Exception:

            article_types = [
                evidence.article_type
            ]

    return {

        "id": evidence.id,

        "pmid": evidence.pmid,

        "doi": evidence.doi,

        "source": evidence.source,

        "title": evidence.title,

        "abstract": evidence.abstract,

        "journal": evidence.journal,

        "publication_date": (
            evidence.publication_date
        ),

        "authors": authors,

        "article_type": article_types,

        "url": evidence.url,

        "notes": evidence.notes,

        "tags": evidence.tags,

        "relevance": evidence.relevance,

        "case_id": evidence.case_id,

        "created_at": (
            evidence.created_at.isoformat()
            if evidence.created_at
            else None
        )

    }


# =========================================================
# ELORA PATIENT INTELLIGENCE
# =========================================================

def build_patient_intelligence(patient):
    """Build a longitudinal clinical intelligence profile from historical cases.

    This is a decision-support prototype, not a diagnosis.
    """
    cases = ClinicalCase.query.filter_by(patient_id=patient.id).order_by(ClinicalCase.created_at.asc()).all()
    total_cases = len(cases)
    active_cases = [case for case in cases if case.status == "Active"]
    completed_cases = [case for case in cases if case.status == "Completed"]

    symptoms_history = []
    complaint_history = []
    medication_history = []
    medical_history = []
    vital_history = []

    for case in cases:
        date = case.created_at.isoformat() if case.created_at else None
        if case.chief_complaint:
            complaint_history.append({"case_id": case.case_id, "date": date, "value": case.chief_complaint})
        if case.symptoms:
            symptoms_history.append({"case_id": case.case_id, "date": date, "value": case.symptoms})
        if case.medications:
            medication_history.append({"case_id": case.case_id, "date": date, "value": case.medications})
        if case.medical_history:
            medical_history.append({"case_id": case.case_id, "date": date, "value": case.medical_history})
        vital_history.append({
            "case_id": case.case_id, "date": date,
            "blood_pressure": case.blood_pressure,
            "heart_rate": case.heart_rate,
            "temperature": case.temperature,
            "spo2": case.spo2,
            "respiratory_rate": case.respiratory_rate,
            "weight": case.weight
        })

    combined_symptoms = " ".join(item["value"] for item in symptoms_history).lower()
    symptom_keywords = [
        "cough", "fever", "headache", "fatigue", "chest pain",
        "shortness of breath", "dyspnea", "dizziness", "vomiting",
        "nausea", "diarrhea", "abdominal pain", "weakness", "palpitations"
    ]
    recurring_symptoms = []
    for keyword in symptom_keywords:
        occurrences = combined_symptoms.count(keyword)
        if occurrences > 0:
            recurring_symptoms.append({"symptom": keyword, "occurrences": occurrences})
    recurring_symptoms.sort(key=lambda item: item["occurrences"], reverse=True)

    heart_rates, temperatures, spo2_values, weights = [], [], [], []
    systolic_values, diastolic_values = [], []
    for case in cases:
        date = case.created_at.isoformat() if case.created_at else None
        heart_rate = parse_number(case.heart_rate)
        temperature = parse_number(case.temperature)
        spo2 = parse_number(case.spo2)
        weight = parse_number(case.weight)
        systolic, diastolic = parse_blood_pressure(case.blood_pressure)
        if heart_rate is not None: heart_rates.append({"date": date, "value": heart_rate})
        if temperature is not None: temperatures.append({"date": date, "value": temperature})
        if spo2 is not None: spo2_values.append({"date": date, "value": spo2})
        if weight is not None: weights.append({"date": date, "value": weight})
        if systolic is not None: systolic_values.append({"date": date, "value": systolic})
        if diastolic is not None: diastolic_values.append({"date": date, "value": diastolic})

    def calculate_trend(values):
        if len(values) < 2:
            return {"direction": "INSUFFICIENT_DATA", "change": None}
        first = values[0]["value"]
        latest = values[-1]["value"]
        change = round(latest - first, 2)
        direction = "INCREASING" if change > 0 else "DECREASING" if change < 0 else "STABLE"
        return {"direction": direction, "change": change, "first": first, "latest": latest}

    trends = {
        "heart_rate": {"data": heart_rates, "trend": calculate_trend(heart_rates)},
        "temperature": {"data": temperatures, "trend": calculate_trend(temperatures)},
        "spo2": {"data": spo2_values, "trend": calculate_trend(spo2_values)},
        "weight": {"data": weights, "trend": calculate_trend(weights)},
        "systolic": {"data": systolic_values, "trend": calculate_trend(systolic_values)},
        "diastolic": {"data": diastolic_values, "trend": calculate_trend(diastolic_values)}
    }

    risk_signals = []
    for case in cases:
        case_analysis = analyze_clinical_case(case)
        for flag in case_analysis.get("risk_flags", []):
            risk_signals.append({
                "case_id": case.case_id,
                "date": case.created_at.isoformat() if case.created_at else None,
                "level": flag.get("level"),
                "title": flag.get("title"),
                "detail": flag.get("detail")
            })

    high_risk_events = [signal for signal in risk_signals if signal["level"] == "HIGH"]
    moderate_risk_events = [signal for signal in risk_signals if signal["level"] == "MODERATE"]

    timeline = []
    for case in cases:
        timeline.append({
            "id": case.id,
            "case_id": case.case_id,
            "date": case.created_at.isoformat() if case.created_at else None,
            "status": case.status,
            "chief_complaint": case.chief_complaint,
            "severity": case.severity
        })

    evidence_items = Evidence.query.join(
        ClinicalCase, Evidence.case_id == ClinicalCase.id
    ).filter(
        ClinicalCase.patient_id == patient.id
    ).order_by(Evidence.created_at.desc()).all()

    evidence_summary = [
        {
            "id": item.id,
            "pmid": item.pmid,
            "title": item.title,
            "journal": item.journal,
            "publication_date": item.publication_date,
            "relevance": item.relevance,
            "case_id": item.case_id
        }
        for item in evidence_items
    ]

    if high_risk_events:
        overall_signal = "HIGH"
        signal_message = "Historical records contain high-priority clinical warning signals requiring review."
    elif moderate_risk_events:
        overall_signal = "MODERATE"
        signal_message = "Historical records contain clinical findings that warrant continued monitoring and correlation."
    else:
        overall_signal = "LOW"
        signal_message = "No high-priority longitudinal warning pattern was identified from the available records."

    patient_fields = [patient.first_name, patient.last_name, patient.date_of_birth, patient.gender, patient.email, patient.phone]
    completed_patient_fields = sum(1 for field in patient_fields if field and str(field).strip())

    if cases:
        case_information_score = min(100, int(
            sum(
                1 for case in cases
                for field in [
                    case.chief_complaint, case.symptoms, case.onset, case.severity,
                    case.blood_pressure, case.heart_rate, case.temperature, case.spo2,
                    case.respiratory_rate, case.medical_history, case.medications
                ] if field and str(field).strip()
            ) / (len(cases) * 11) * 100
        ))
    else:
        case_information_score = 0

    data_completeness = min(100, int((completed_patient_fields / len(patient_fields) * 50) + (case_information_score * 0.5)))

    if total_cases == 0:
        longitudinal_summary = (
            "No previous clinical cases are available. ELORA will build the patient's longitudinal "
            "profile as additional encounters are recorded."
        )
    elif total_cases == 1:
        longitudinal_summary = (
            "One clinical encounter is currently available. Additional encounters will allow ELORA "
            "to identify meaningful longitudinal trends."
        )
    else:
        longitudinal_summary = (
            f"{total_cases} clinical encounters are available. {len(recurring_symptoms)} recurring symptom "
            f"patterns were identified, with {len(high_risk_events)} high-priority and "
            f"{len(moderate_risk_events)} moderate-priority historical risk signals."
        )

    return {
        "patient": {
            "id": patient.id,
            "patient_id": patient.patient_id,
            "name": patient.full_name,
            "date_of_birth": patient.date_of_birth,
            "gender": patient.gender,
            "email": patient.email,
            "phone": patient.phone
        },
        "overview": {
            "total_cases": total_cases,
            "active_cases": len(active_cases),
            "completed_cases": len(completed_cases),
            "evidence_count": len(evidence_items),
            "overall_signal": overall_signal,
            "signal_message": signal_message,
            "data_completeness": data_completeness
        },
        "longitudinal_summary": longitudinal_summary,
        "timeline": timeline,
        "complaint_history": complaint_history,
        "symptoms_history": symptoms_history,
        "medication_history": medication_history,
        "medical_history": medical_history,
        "recurring_symptoms": recurring_symptoms,
        "vital_history": vital_history,
        "trends": trends,
        "risk_signals": risk_signals,
        "evidence": evidence_summary,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "engine": "ELORA MEDAI Patient Intelligence Engine",
        "version": "1.0",
        "disclaimer": (
            "This longitudinal analysis is a clinical decision-support prototype. It does not "
            "constitute a diagnosis and must be reviewed by a qualified clinician."
        )
    }


# =========================================================
# API — PATIENT INTELLIGENCE
# =========================================================

@app.route("/api/patient/<int:patient_id>/intelligence", methods=["GET"])
def patient_intelligence_api(patient_id):
    if not doctor_logged_in():
        return jsonify({"success": False, "error": "Authentication required."}), 401

    patient = Patient.query.get_or_404(patient_id)
    try:
        intelligence = build_patient_intelligence(patient)
        return jsonify({"success": True, "intelligence": intelligence})
    except Exception as error:
        db.session.rollback()
        print("PATIENT INTELLIGENCE ERROR:", error)
        return jsonify({
            "success": False,
            "error": "Unable to generate patient intelligence."
        }), 500

# =========================================================
# API — CURRENT DOCTOR
# =========================================================


@app.route("/api/me")
def api_me():

    if not doctor_logged_in():

        return jsonify({

            "success": False,

            "authenticated": False

        }), 401

    doctor = get_current_doctor()

    if not doctor:

        session.clear()

        return jsonify({

            "success": False,

            "authenticated": False

        }), 401

    return jsonify({

        "success": True,

        "authenticated": True,

        "doctor": {

            "id": doctor.id,

            "name": doctor.name,

            "email": doctor.email,

            "role": doctor.role,

            "initials": get_doctor_initials()

        }

    })


# =========================================================
# API — ANALYZE CASE
# =========================================================


@app.route(
    "/api/case/<int:case_id>/analyze",
    methods=["POST"]
)
def analyze_case_api(case_id):

    if not doctor_logged_in():

        return jsonify({

            "success": False,

            "error": (
                "Authentication required."
            )

        }), 401

    clinical_case = ClinicalCase.query.get_or_404(
        case_id
    )

    if (
        clinical_case.doctor_id
        != session["doctor_id"]
    ):

        return jsonify({

            "success": False,

            "error": (
                "You are not authorized "
                "to analyze this case."
            )

        }), 403

    try:

        analysis = analyze_clinical_case(
            clinical_case
        )

        return jsonify({

            "success": True,

            "case_id": clinical_case.case_id,

            "database_id": clinical_case.id,

            "patient": (
                clinical_case.patient.full_name
            ),

            "analysis": analysis

        })

    except Exception as error:

        db.session.rollback()

        print(
            "AI ANALYSIS ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "error": (
                "ELORA AI analysis failed."
            )

        }), 500


# =========================================================
# API — GET CASE
# =========================================================


@app.route(
    "/api/case/<int:case_id>",
    methods=["GET"]
)
def api_get_case(case_id):

    if not doctor_logged_in():

        return jsonify({

            "success": False,

            "error": (
                "Authentication required."
            )

        }), 401

    clinical_case = ClinicalCase.query.get_or_404(
        case_id
    )

    if (
        clinical_case.doctor_id
        != session["doctor_id"]
    ):

        return jsonify({

            "success": False,

            "error": "Unauthorized."

        }), 403

    return jsonify({

        "success": True,

        "case": {

            "id": clinical_case.id,

            "case_id": clinical_case.case_id,

            "status": clinical_case.status,

            "created_at": (
                clinical_case.created_at.isoformat()
                if clinical_case.created_at
                else None
            ),

            "patient": {

                "id": clinical_case.patient.id,

                "patient_id": (
                    clinical_case.patient.patient_id
                ),

                "name": (
                    clinical_case.patient.full_name
                ),

                "date_of_birth": (
                    clinical_case.patient.date_of_birth
                ),

                "gender": (
                    clinical_case.patient.gender
                ),

                "email": (
                    clinical_case.patient.email
                ),

                "phone": (
                    clinical_case.patient.phone
                )

            },

            "clinical": {

                "chief_complaint": (
                    clinical_case.chief_complaint
                ),

                "symptoms": (
                    clinical_case.symptoms
                ),

                "onset": (
                    clinical_case.onset
                ),

                "severity": (
                    clinical_case.severity
                ),

                "medical_history": (
                    clinical_case.medical_history
                ),

                "medications": (
                    clinical_case.medications
                )

            },

            "vitals": {

                "blood_pressure": (
                    clinical_case.blood_pressure
                ),

                "heart_rate": (
                    clinical_case.heart_rate
                ),

                "temperature": (
                    clinical_case.temperature
                ),

                "spo2": (
                    clinical_case.spo2
                ),

                "respiratory_rate": (
                    clinical_case.respiratory_rate
                ),

                "weight": (
                    clinical_case.weight
                )

            }

        }

    })


# =========================================================
# EVIDENCE PAGE
# =========================================================


@app.route("/evidence")
def evidence():

    if not doctor_logged_in():

        return redirect(
            url_for("login")
        )

    evidence_items = Evidence.query.filter_by(
        doctor_id=session["doctor_id"]
    ).order_by(
        Evidence.created_at.desc()
    ).all()

    cases = ClinicalCase.query.filter_by(
        doctor_id=session["doctor_id"]
    ).order_by(
        ClinicalCase.created_at.desc()
    ).all()

    return render_template(
        "evidence.html",

        evidence_items=evidence_items,

        cases=cases,

        evidence_count=len(
            evidence_items
        ),

        **doctor_context()
    )


# =========================================================
# API — SEARCH EVIDENCE
# =========================================================


@app.route(
    "/api/evidence/search",
    methods=["GET"]
)
def search_evidence_api():

    if not doctor_logged_in():

        return jsonify({

            "success": False,

            "error": (
                "Authentication required."
            )

        }), 401

    query = request.args.get(
        "q",
        ""
    ).strip()

    limit_value = request.args.get(
        "limit",
        "10"
    )

    try:

        limit = int(
            limit_value
        )

    except (
        ValueError,
        TypeError
    ):

        limit = 10

    limit = max(
        1,
        min(
            limit,
            25
        )
    )

    if not query:

        return jsonify({

            "success": False,

            "error": (
                "Please provide a search query."
            )

        }), 400

    try:

        results = pubmed_search(
            query,
            limit
        )

        return jsonify({

            "success": True,

            "query": query,

            "count": len(results),

            "results": results

        })

    except Exception as error:

        print(
            "EVIDENCE SEARCH ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "error": (
                "Unable to search PubMed "
                "at this time."
            )

        }), 502


# =========================================================
# API — SAVE EVIDENCE
# =========================================================


@app.route(
    "/api/evidence/save",
    methods=["POST"]
)
def save_evidence_api():

    if not doctor_logged_in():

        return jsonify({

            "success": False,

            "error": (
                "Authentication required."
            )

        }), 401

    data = request.get_json(
        silent=True
    ) or {}

    title = str(
        data.get(
            "title",
            ""
        )
    ).strip()

    if not title:

        return jsonify({

            "success": False,

            "error": (
                "Evidence title is required."
            )

        }), 400

    pmid = str(
        data.get(
            "pmid",
            ""
        )
    ).strip()

    doi = str(
        data.get(
            "doi",
            ""
        )
    ).strip()

    url = str(
        data.get(
            "url",
            ""
        )
    ).strip()

    abstract = str(
        data.get(
            "abstract",
            ""
        )
    ).strip()

    journal = str(
        data.get(
            "journal",
            ""
        )
    ).strip()

    publication_date = str(
        data.get(
            "publication_date",
            ""
        )
    ).strip()

    notes = str(
        data.get(
            "notes",
            ""
        )
    ).strip()

    tags = str(
        data.get(
            "tags",
            ""
        )
    ).strip()

    relevance = str(
        data.get(
            "relevance",
            "Unreviewed"
        )
    ).strip()

    allowed_relevance = [

        "Unreviewed",
        "High",
        "Moderate",
        "Low"

    ]

    if relevance not in allowed_relevance:

        relevance = "Unreviewed"

    authors = data.get(
        "authors",
        []
    )

    if not isinstance(
        authors,
        list
    ):

        authors = [
            str(authors)
        ]

    article_type = data.get(
        "article_type",
        []
    )

    if not isinstance(
        article_type,
        list
    ):

        article_type = [
            str(article_type)
        ]

    # -----------------------------------------------------
    # DUPLICATE CHECK
    # -----------------------------------------------------

    if pmid:

        existing = Evidence.query.filter_by(

            doctor_id=session["doctor_id"],

            pmid=pmid

        ).first()

        if existing:

            return jsonify({

                "success": True,

                "duplicate": True,

                "message": (
                    "This evidence is already saved."
                ),

                "evidence": evidence_to_dict(
                    existing
                )

            })

    # -----------------------------------------------------
    # CASE LINK
    # -----------------------------------------------------

    case_id_value = data.get(
        "case_id"
    )

    linked_case = None

    if case_id_value not in [
        None,
        "",
        "null"
    ]:

        try:

            linked_case = ClinicalCase.query.filter_by(

                id=int(case_id_value),

                doctor_id=session["doctor_id"]

            ).first()

        except (
            ValueError,
            TypeError
        ):

            linked_case = None

        if not linked_case:

            return jsonify({

                "success": False,

                "error": (
                    "Selected clinical case "
                    "does not exist or is not accessible."
                )

            }), 400

    evidence_item = Evidence(

        pmid=pmid or None,

        doi=doi or None,

        source=(
            str(
                data.get(
                    "source",
                    "PubMed"
                )
            ).strip()
            or "PubMed"
        ),

        url=url or None,

        title=title,

        abstract=abstract or None,

        journal=journal or None,

        publication_date=(
            publication_date
            or None
        ),

        authors=json.dumps(
            authors
        ),

        article_type=json.dumps(
            article_type
        ),

        notes=notes or None,

        tags=tags or None,

        relevance=relevance,

        doctor_id=session["doctor_id"],

        case_id=(
            linked_case.id
            if linked_case
            else None
        )

    )

    try:

        db.session.add(
            evidence_item
        )

        db.session.commit()

        return jsonify({

            "success": True,

            "duplicate": False,

            "message": (
                "Evidence saved successfully."
            ),

            "evidence": evidence_to_dict(
                evidence_item
            )

        })

    except Exception as error:

        db.session.rollback()

        print(
            "SAVE EVIDENCE ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "error": (
                "Unable to save evidence."
            )

        }), 500


# =========================================================
# API — GET SAVED EVIDENCE
# =========================================================


@app.route(
    "/api/evidence",
    methods=["GET"]
)
def get_evidence_api():

    if not doctor_logged_in():

        return jsonify({

            "success": False,

            "error": (
                "Authentication required."
            )

        }), 401

    case_id_value = request.args.get(
        "case_id"
    )

    query = Evidence.query.filter_by(
        doctor_id=session["doctor_id"]
    )

    if case_id_value:

        try:

            case_id_int = int(
                case_id_value
            )

        except (
            ValueError,
            TypeError
        ):

            return jsonify({

                "success": False,

                "error": (
                    "Invalid case ID."
                )

            }), 400

        case = ClinicalCase.query.filter_by(

            id=case_id_int,

            doctor_id=session["doctor_id"]

        ).first()

        if not case:

            return jsonify({

                "success": False,

                "error": (
                    "Case not found."
                )

            }), 404

        query = query.filter_by(
            case_id=case.id
        )

    items = query.order_by(
        Evidence.created_at.desc()
    ).all()

    return jsonify({

        "success": True,

        "count": len(items),

        "evidence": [

            evidence_to_dict(
                item
            )

            for item in items

        ]

    })


# =========================================================
# API — GET SINGLE EVIDENCE
# =========================================================


@app.route(
    "/api/evidence/<int:evidence_id>",
    methods=["GET"]
)
def get_single_evidence(
    evidence_id
):

    if not doctor_logged_in():

        return jsonify({

            "success": False,

            "error": (
                "Authentication required."
            )

        }), 401

    evidence_item = Evidence.query.filter_by(

        id=evidence_id,

        doctor_id=session["doctor_id"]

    ).first()

    if not evidence_item:

        return jsonify({

            "success": False,

            "error": "Evidence not found."

        }), 404

    return jsonify({

        "success": True,

        "evidence": evidence_to_dict(
            evidence_item
        )

    })


# =========================================================
# API — UPDATE EVIDENCE
# =========================================================


@app.route(
    "/api/evidence/<int:evidence_id>",
    methods=["PUT", "PATCH"]
)
def update_evidence(
    evidence_id
):

    if not doctor_logged_in():

        return jsonify({

            "success": False,

            "error": (
                "Authentication required."
            )

        }), 401

    evidence_item = Evidence.query.filter_by(

        id=evidence_id,

        doctor_id=session["doctor_id"]

    ).first()

    if not evidence_item:

        return jsonify({

            "success": False,

            "error": "Evidence not found."

        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    if "notes" in data:

        evidence_item.notes = str(
            data.get(
                "notes"
            ) or ""
        ).strip() or None

    if "tags" in data:

        evidence_item.tags = str(
            data.get(
                "tags"
            ) or ""
        ).strip() or None

    if "relevance" in data:

        relevance = str(
            data.get(
                "relevance"
            ) or "Unreviewed"
        ).strip()

        if relevance in [
            "Unreviewed",
            "High",
            "Moderate",
            "Low"
        ]:

            evidence_item.relevance = (
                relevance
            )

    if "case_id" in data:

        case_id_value = data.get(
            "case_id"
        )

        if case_id_value in [
            None,
            "",
            "null"
        ]:

            evidence_item.case_id = None

        else:

            try:

                case = ClinicalCase.query.filter_by(

                    id=int(case_id_value),

                    doctor_id=session["doctor_id"]

                ).first()

            except (
                ValueError,
                TypeError
            ):

                case = None

            if not case:

                return jsonify({

                    "success": False,

                    "error": (
                        "Invalid clinical case."
                    )

                }), 400

            evidence_item.case_id = (
                case.id
            )

    try:

        db.session.commit()

        return jsonify({

            "success": True,

            "message": (
                "Evidence updated successfully."
            ),

            "evidence": evidence_to_dict(
                evidence_item
            )

        })

    except Exception as error:

        db.session.rollback()

        print(
            "UPDATE EVIDENCE ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "error": (
                "Unable to update evidence."
            )

        }), 500


# =========================================================
# API — DELETE EVIDENCE
# =========================================================


@app.route(
    "/api/evidence/<int:evidence_id>",
    methods=["DELETE"]
)
def delete_evidence(
    evidence_id
):

    if not doctor_logged_in():

        return jsonify({

            "success": False,

            "error": (
                "Authentication required."
            )

        }), 401

    evidence_item = Evidence.query.filter_by(

        id=evidence_id,

        doctor_id=session["doctor_id"]

    ).first()

    if not evidence_item:

        return jsonify({

            "success": False,

            "error": "Evidence not found."

        }), 404

    try:

        db.session.delete(
            evidence_item
        )

        db.session.commit()

        return jsonify({

            "success": True,

            "message": (
                "Evidence deleted successfully."
            )

        })

    except Exception as error:

        db.session.rollback()

        print(
            "DELETE EVIDENCE ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "error": (
                "Unable to delete evidence."
            )

        }), 500

# =========================================================
# DOCTOR REGISTRATION
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    # If already logged in, go to dashboard
    if doctor_logged_in():
        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        # -------------------------------------------------
        # GET FORM DATA
        # -------------------------------------------------

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        medical_registration_id = request.form.get(
            "medical_registration_id",
            ""
        ).strip()

        country = request.form.get(
            "country",
            ""
        ).strip()

        specialty = request.form.get(
            "specialty",
            ""
        ).strip()

        institution = request.form.get(
            "institution",
            ""
        ).strip()

        ai_preference = request.form.get(
            "ai_preference",
            "balanced"
        ).strip().lower()

        terms = request.form.get("terms")

        clinical_acknowledgment = request.form.get(
            "clinical_acknowledgment"
        )

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not name:
            flash(
                "Full name is required.",
                "error"
            )
            return redirect(
                url_for("register")
            )

        if not email:
            flash(
                "Email address is required.",
                "error"
            )
            return redirect(
                url_for("register")
            )

        if not password:
            flash(
                "Password is required.",
                "error"
            )
            return redirect(
                url_for("register")
            )

        if len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "error"
            )
            return redirect(
                url_for("register")
            )

        if password != confirm_password:
            flash(
                "Passwords do not match.",
                "error"
            )
            return redirect(
                url_for("register")
            )

        if not country:
            flash(
                "Please select your country.",
                "error"
            )
            return redirect(
                url_for("register")
            )

        if not specialty:
            flash(
                "Please select your medical specialty.",
                "error"
            )
            return redirect(
                url_for("register")
            )

        if not institution:
            flash(
                "Institution / hospital is required.",
                "error"
            )
            return redirect(
                url_for("register")
            )

        if not terms:
            flash(
                "You must agree to the Terms of Service and Privacy Policy.",
                "error"
            )
            return redirect(
                url_for("register")
            )

        if not clinical_acknowledgment:
            flash(
                "Please acknowledge the clinical decision-support notice.",
                "error"
            )
            return redirect(
                url_for("register")
            )

        if ai_preference not in [
            "conservative",
            "balanced",
            "detailed"
        ]:
            ai_preference = "balanced"

        # -------------------------------------------------
        # CHECK EXISTING EMAIL
        # -------------------------------------------------

        existing_doctor = Doctor.query.filter_by(
            email=email
        ).first()

        if existing_doctor:

            flash(
                "An account with this email already exists.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        # -------------------------------------------------
        # CREATE DOCTOR
        # -------------------------------------------------

        doctor = Doctor(

            name=name,

            email=email,

            password_hash=generate_password_hash(
                password
            ),

            role="doctor"

        )

        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        try:

            db.session.add(
                doctor
            )

            db.session.commit()

            # -------------------------------------------------
            # CREATE DEFAULT SETTINGS
            # -------------------------------------------------

            doctor_settings = DoctorSettings(

                doctor_id=doctor.id,

                ai_confidence=ai_preference

            )

            db.session.add(
                doctor_settings
            )

            db.session.commit()

            flash(
                "Doctor account created successfully. You can now sign in.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        except Exception as error:

            db.session.rollback()

            print(
                "DOCTOR REGISTRATION ERROR:",
                error
            )

            flash(
                "Unable to create your doctor account.",
                "error"
            )

            return redirect(
                url_for("register")
            )

    # -------------------------------------------------
    # GET REGISTRATION PAGE
    # -------------------------------------------------

    return render_template(
        "register.html"
    )
# =========================================================
# LOGIN
# =========================================================


@app.route(
    "/",
    methods=["GET", "POST"]
)
def login():

    if doctor_logged_in():

        return redirect(
            url_for("dashboard")
        )

    error = None

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            error = (
                "Please enter your email "
                "and password."
            )

            return render_template(
                "login.html",
                error=error
            )

        doctor = Doctor.query.filter_by(
            email=email
        ).first()

        if (
            doctor
            and check_password_hash(
                doctor.password_hash,
                password
            )
        ):

            session.clear()

            session["doctor_id"] = doctor.id

            session["doctor_name"] = (
                doctor.name
            )

            session["doctor_email"] = (
                doctor.email
            )

            session["doctor_role"] = (
                doctor.role
            )

            return redirect(
                url_for("dashboard")
            )

        error = (
            "Invalid email or password."
        )

    return render_template(
        "login.html",
        error=error
    )


# =========================================================
# DASHBOARD
# =========================================================


@app.route("/dashboard")
def dashboard():

    if not doctor_logged_in():

        return redirect(
            url_for("login")
        )

    doctor_id = session["doctor_id"]

    patient_count = Patient.query.count()

    case_count = ClinicalCase.query.filter_by(
        doctor_id=doctor_id
    ).count()

    new_cases = ClinicalCase.query.filter_by(
        doctor_id=doctor_id,
        status="New"
    ).count()

    active_cases = ClinicalCase.query.filter_by(
        doctor_id=doctor_id,
        status="Active"
    ).count()

    completed_cases = ClinicalCase.query.filter_by(
        doctor_id=doctor_id,
        status="Completed"
    ).count()

    evidence_count = Evidence.query.filter_by(
        doctor_id=doctor_id
    ).count()

    recent_cases = ClinicalCase.query.filter_by(
        doctor_id=doctor_id
    ).order_by(
        ClinicalCase.created_at.desc()
    ).limit(5).all()

    return render_template(

        "dashboard.html",

        patient_count=patient_count,

        case_count=case_count,

        new_cases=new_cases,

        active_cases=active_cases,

        completed_cases=completed_cases,

        evidence_count=evidence_count,

        recent_cases=recent_cases,

        **doctor_context()

    )


# =========================================================
# PATIENTS
# =========================================================


@app.route("/patients")
def patients():

    if not doctor_logged_in():

        return redirect(
            url_for("login")
        )

    patients_list = Patient.query.order_by(
        Patient.created_at.desc()
    ).all()

    return render_template(

        "patients.html",

        patients=patients_list,

        **doctor_context()

    )


# =========================================================
# ADD PATIENT
# =========================================================


@app.route(
    "/add-patient",
    methods=["POST"]
)
def add_patient():

    if not doctor_logged_in():

        return redirect(
            url_for("login")
        )

    first_name = request.form.get(
        "first_name",
        ""
    ).strip()

    last_name = request.form.get(
        "last_name",
        ""
    ).strip()

    date_of_birth = request.form.get(
        "date_of_birth",
        ""
    ).strip()

    gender = request.form.get(
        "gender",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    if not first_name:

        flash(
            "First name is required.",
            "error"
        )

        return redirect(
            url_for("patients")
        )

    if not last_name:

        flash(
            "Last name is required.",
            "error"
        )

        return redirect(
            url_for("patients")
        )

    if not date_of_birth:

        flash(
            "Date of birth is required.",
            "error"
        )

        return redirect(
            url_for("patients")
        )

    patient_id = (
        "EL-"
        + uuid.uuid4().hex[:8].upper()
    )

    patient = Patient(

        patient_id=patient_id,

        first_name=first_name,

        last_name=last_name,

        date_of_birth=date_of_birth,

        gender=gender,

        email=email,

        phone=phone

    )

    try:

        db.session.add(
            patient
        )

        db.session.commit()

        flash(

            f"Patient {patient.full_name} "
            f"added successfully.",

            "success"

        )

    except Exception as error:

        db.session.rollback()

        print(
            "ADD PATIENT ERROR:",
            error
        )

        flash(
            "Unable to add patient.",
            "error"
        )

    return redirect(
        url_for("patients")
    )

# =========================================================
# ACTIVATE PATIENT PORTAL
# =========================================================

# =========================================================
# ACTIVATE PATIENT PORTAL ACCOUNT
# =========================================================

@app.route(
    "/patient/<int:patient_id>/activate",
    methods=["POST"]
)
def activate_patient_account(patient_id):

    # -----------------------------------------------------
    # DOCTOR AUTHENTICATION
    # -----------------------------------------------------

    if not doctor_logged_in():
        return redirect(
            url_for("login")
        )

    # -----------------------------------------------------
    # FIND PATIENT
    # -----------------------------------------------------

    patient = Patient.query.get_or_404(
        patient_id
    )

    # -----------------------------------------------------
    # VALIDATE EMAIL
    # -----------------------------------------------------

    if not patient.email:

        flash(
            "This patient does not have an email address.",
            "error"
        )

        return redirect(
            url_for(
                "patient_profile",
                patient_id=patient.id
            )
        )

    # -----------------------------------------------------
    # ACTIVATE PATIENT PORTAL
    # -----------------------------------------------------

    patient.patient_account_active = True

    # -----------------------------------------------------
    # GENERATE TEMPORARY PASSWORD
    # -----------------------------------------------------

    temporary_password = None

    if not patient.password_hash:

        temporary_password = (
            uuid.uuid4().hex[:10]
        )

        patient.password_hash = (
            generate_password_hash(
                temporary_password
            )
        )

    # -----------------------------------------------------
    # SAVE DATABASE
    # -----------------------------------------------------

    try:

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        print(
            "ACTIVATE PATIENT ACCOUNT ERROR:",
            error
        )

        flash(
            "Unable to activate patient portal.",
            "error"
        )

        return redirect(
            url_for(
                "patient_profile",
                patient_id=patient.id
            )
        )

    # -----------------------------------------------------
    # SHOW CREDENTIALS
    # -----------------------------------------------------

    if temporary_password:

        return f"""
        <!DOCTYPE html>

        <html lang="en">

        <head>

            <meta charset="UTF-8">

            <meta
                name="viewport"
                content="width=device-width, initial-scale=1.0"
            >

            <title>
                ELORA MEDAI | Patient Portal Activated
            </title>

            <style>

                * {{
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                }}

                body {{
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background:
                        radial-gradient(
                            circle at top,
                            #102a43,
                            #02070d 65%
                        );
                    color: #ffffff;
                    font-family:
                        Arial,
                        sans-serif;
                    padding: 20px;
                }}

                .card {{
                    width: 100%;
                    max-width: 520px;
                    padding: 40px;
                    border: 1px solid
                        rgba(48, 196, 255, 0.25);
                    border-radius: 20px;
                    background:
                        rgba(7, 18, 31, 0.92);
                    box-shadow:
                        0 0 50px
                        rgba(0, 180, 255, 0.12);
                    text-align: center;
                }}

                .icon {{
                    width: 70px;
                    height: 70px;
                    margin: 0 auto 20px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(0, 255, 170, 0.12);
                    border: 1px solid
                        rgba(0, 255, 170, 0.35);
                    color: #00ffaa;
                    font-size: 32px;
                }}

                h1 {{
                    margin-bottom: 10px;
                    font-size: 25px;
                }}

                .subtitle {{
                    color: #8fa9bd;
                    margin-bottom: 30px;
                    line-height: 1.6;
                }}

                .credential {{
                    margin: 15px 0;
                    padding: 18px;
                    border-radius: 12px;
                    background:
                        rgba(255, 255, 255, 0.04);
                    border:
                        1px solid
                        rgba(255, 255, 255, 0.08);
                    text-align: left;
                }}

                .label {{
                    display: block;
                    margin-bottom: 8px;
                    color: #7d9aae;
                    font-size: 12px;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}

                .value {{
                    color: #ffffff;
                    font-size: 18px;
                    font-weight: 700;
                    word-break: break-all;
                }}

                .password {{
                    color: #00ffaa;
                    letter-spacing: 2px;
                }}

                .warning {{
                    margin-top: 20px;
                    padding: 14px;
                    border-radius: 10px;
                    background:
                        rgba(255, 180, 0, 0.08);
                    border:
                        1px solid
                        rgba(255, 180, 0, 0.2);
                    color: #ffc857;
                    font-size: 13px;
                    line-height: 1.5;
                }}

                .button {{
                    display: inline-block;
                    margin-top: 25px;
                    padding: 13px 22px;
                    border-radius: 10px;
                    background: #0b9ed0;
                    color: white;
                    text-decoration: none;
                    font-weight: 700;
                }}

                .button:hover {{
                    background: #08b8ef;
                }}

            </style>

        </head>

        <body>

            <div class="card">

                <div class="icon">
                    ✓
                </div>

                <h1>
                    Patient Portal Activated
                </h1>

                <p class="subtitle">
                    The ELORA MEDAI patient portal account
                    has been successfully created.
                </p>

                <div class="credential">

                    <span class="label">
                        Patient
                    </span>

                    <div class="value">
                        {patient.full_name}
                    </div>

                </div>

                <div class="credential">

                    <span class="label">
                        Patient ID
                    </span>

                    <div class="value">
                        {patient.patient_id}
                    </div>

                </div>

                <div class="credential">

                    <span class="label">
                        Login Email
                    </span>

                    <div class="value">
                        {patient.email}
                    </div>

                </div>

                <div class="credential">

                    <span class="label">
                        Temporary Password
                    </span>

                    <div class="value password">
                        {temporary_password}
                    </div>

                </div>

                <div class="warning">

                    Give these credentials to the patient
                    securely. The patient can use their
                    Patient ID or email together with this
                    temporary password at the ELORA patient
                    portal.

                </div>

                <a
                    class="button"
                    href="/patient-login"
                >
                    Open Patient Portal
                </a>

            </div>

        </body>

        </html>
        """

    # -----------------------------------------------------
    # ACCOUNT ALREADY HAD A PASSWORD
    # -----------------------------------------------------

    flash(
        f"Patient portal for {patient.full_name} "
        "is already active.",
        "success"
    )

    return redirect(
        url_for(
            "patient_profile",
            patient_id=patient.id
        )
    )
# =========================================================
# PATIENT PROFILE
# =========================================================


@app.route(
    "/patient/<int:patient_id>"
)
def patient_profile(
    patient_id
):

    if not doctor_logged_in():

        return redirect(
            url_for("login")
        )

    patient = Patient.query.get_or_404(
        patient_id
    )

    patient_cases = ClinicalCase.query.filter_by(
        patient_id=patient.id
    ).order_by(
        ClinicalCase.created_at.desc()
    ).all()
    # =====================================================
    # PATIENT HEALTH TREND
    # =====================================================

    health_trend = []

    severity_scores = {
        "critical": 20,
        "severe": 35,
        "high": 40,
        "moderate": 60,
        "medium": 60,
        "mild": 80,
        "low": 85,
        "stable": 90
    }

    for case in reversed(patient_cases):

        severity = (
            case.severity or ""
        ).strip().lower()

        score = severity_scores.get(
            severity,
            70
        )

        health_trend.append({
            "date": case.created_at.strftime("%b %d"),
            "score": score,
            "status": case.status or "New",
            "severity": case.severity or "Not specified",
            "case_id": case.case_id
        })
    return render_template(

        "patient-profile.html",

        patient=patient,

        cases=patient_cases,
        
        health_trend=health_trend,
        **doctor_context()

    )


# =========================================================
# CLINICAL CASES
# =========================================================


@app.route("/cases")
def clinical_cases():

    if not doctor_logged_in():

        return redirect(
            url_for("login")
        )

    patients_list = Patient.query.order_by(
        Patient.first_name.asc()
    ).all()

    cases_list = ClinicalCase.query.filter_by(
        doctor_id=session["doctor_id"]
    ).order_by(
        ClinicalCase.created_at.desc()
    ).all()

    return render_template(

        "cases.html",

        patients=patients_list,

        cases=cases_list,

        **doctor_context()

    )


# =========================================================
# CREATE CLINICAL CASE
# =========================================================


@app.route(
    "/create-case",
    methods=["POST"]
)
def create_case():

    if not doctor_logged_in():

        return redirect(
            url_for("login")
        )

    patient_id_value = request.form.get(
        "patient_id",
        ""
    ).strip()

    if not patient_id_value:

        flash(
            "Please select a patient before "
            "creating the case.",
            "error"
        )

        return redirect(
            url_for("clinical_cases")
        )

    patient = None

    try:

        patient = Patient.query.get(
            int(patient_id_value)
        )

    except (
        ValueError,
        TypeError
    ):

        patient = None

    if not patient:

        patient = Patient.query.filter_by(
            patient_id=patient_id_value
        ).first()

    if not patient:

        flash(
            "Selected patient does not exist.",
            "error"
        )

        return redirect(
            url_for("clinical_cases")
        )

    chief_complaint = request.form.get(
        "chief_complaint",
        ""
    ).strip()

    symptoms = request.form.get(
        "symptoms",
        ""
    ).strip()

    if not chief_complaint:

        flash(
            "Chief complaint is required.",
            "error"
        )

        return redirect(
            url_for("clinical_cases")
        )

    if not symptoms:

        flash(
            "Please enter the patient's "
            "symptoms and findings.",
            "error"
        )

        return redirect(
            url_for("clinical_cases")
        )

    case_id = (
        "ELR-"
        + uuid.uuid4().hex[:8].upper()
    )

    clinical_case = ClinicalCase(

        case_id=case_id,

        patient_id=patient.id,

        doctor_id=session["doctor_id"],

        chief_complaint=chief_complaint,

        symptoms=symptoms,

        onset=request.form.get(
            "onset",
            ""
        ).strip(),

        severity=request.form.get(
            "severity",
            ""
        ).strip(),

        blood_pressure=request.form.get(
            "blood_pressure",
            ""
        ).strip(),

        heart_rate=request.form.get(
            "heart_rate",
            ""
        ).strip(),

        temperature=request.form.get(
            "temperature",
            ""
        ).strip(),

        spo2=request.form.get(
            "spo2",
            ""
        ).strip(),

        respiratory_rate=request.form.get(
            "respiratory_rate",
            ""
        ).strip(),

        weight=request.form.get(
            "weight",
            ""
        ).strip(),

        medical_history=request.form.get(
            "medical_history",
            ""
        ).strip(),

        medications=request.form.get(
            "medications",
            ""
        ).strip(),

        status="New"

    )

    try:

        db.session.add(
            clinical_case
        )

        db.session.commit()

        flash(

            f"Clinical case {case_id} "
            f"created successfully for "
            f"{patient.full_name}.",

            "success"

        )

        return redirect(

            url_for(
                "view_case",
                case_id=clinical_case.id
            )

        )

    except Exception as error:

        db.session.rollback()

        print(
            "CREATE CASE ERROR:",
            error
        )

        flash(
            "Unable to create clinical case.",
            "error"
        )

        return redirect(
            url_for("clinical_cases")
        )


# =========================================================
# VIEW CASE
# =========================================================


@app.route(
    "/case/<int:case_id>"
)
def view_case(case_id):

    if not doctor_logged_in():

        return redirect(
            url_for("login")
        )

    clinical_case = ClinicalCase.query.get_or_404(
        case_id
    )

    if (
        clinical_case.doctor_id
        != session["doctor_id"]
    ):

        flash(
            "You are not authorized "
            "to view this case.",
            "error"
        )

        return redirect(
            url_for("clinical_cases")
        )

    case_evidence = Evidence.query.filter_by(

        doctor_id=session["doctor_id"],

        case_id=clinical_case.id

    ).order_by(
        Evidence.created_at.desc()
    ).all()

    return render_template(

        "case-view.html",

        case=clinical_case,

        patient=clinical_case.patient,

        case_evidence=case_evidence,

        **doctor_context()

    )


# =========================================================
# UPDATE CASE STATUS
# =========================================================


@app.route(
    "/case/<int:case_id>/status",
    methods=["POST"]
)
def update_case_status(case_id):

    if not doctor_logged_in():

        return redirect(
            url_for("login")
        )

    clinical_case = ClinicalCase.query.get_or_404(
        case_id
    )

    if (
        clinical_case.doctor_id
        != session["doctor_id"]
    ):

        flash(
            "You are not authorized "
            "to modify this case.",
            "error"
        )

        return redirect(
            url_for("clinical_cases")
        )

    new_status = request.form.get(
        "status",
        ""
    ).strip()

    allowed_statuses = [

        "New",
        "Active",
        "Completed",
        "Archived"

    ]

    if new_status not in allowed_statuses:

        flash(
            "Invalid case status.",
            "error"
        )

        return redirect(

            url_for(
                "view_case",
                case_id=case_id
            )

        )

    clinical_case.status = new_status

    try:

        db.session.commit()

        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest":

            return jsonify({

                "success": True,

                "status": (
                    clinical_case.status
                )

            })

        flash(
            "Case status updated successfully.",
            "success"
        )

    except Exception as error:

        db.session.rollback()

        print(
            "STATUS UPDATE ERROR:",
            error
        )

        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest":

            return jsonify({

                "success": False,

                "error": (
                    "Unable to update "
                    "case status."
                )

            }), 500

        flash(
            "Unable to update case status.",
            "error"
        )

    return redirect(

        url_for(
            "view_case",
            case_id=case_id
        )

    )


# =========================================================
# DELETE CLINICAL CASE
# =========================================================


@app.route(
    "/case/<int:case_id>/delete",
    methods=["POST"]
)
def delete_case(case_id):

    if not doctor_logged_in():

        if request.is_json:

            return jsonify({

                "success": False,

                "error": (
                    "Authentication required."
                )

            }), 401

        return redirect(
            url_for("login")
        )

    clinical_case = ClinicalCase.query.get_or_404(
        case_id
    )

    if (
        clinical_case.doctor_id
        != session["doctor_id"]
    ):

        if request.is_json:

            return jsonify({

                "success": False,

                "error": "Unauthorized."

            }), 403

        flash(
            "You are not authorized "
            "to delete this case.",
            "error"
        )

        return redirect(
            url_for("clinical_cases")
        )

    try:

        db.session.delete(
            clinical_case
        )

        db.session.commit()

        if (
            request.is_json
            or request.headers.get(
                "X-Requested-With"
            ) == "XMLHttpRequest"
        ):

            return jsonify({

                "success": True,

                "message": (
                    "Clinical case deleted successfully."
                )

            })

        flash(
            "Clinical case deleted successfully.",
            "success"
        )

    except Exception as error:

        db.session.rollback()

        print(
            "DELETE CASE ERROR:",
            error
        )

        if (
            request.is_json
            or request.headers.get(
                "X-Requested-With"
            ) == "XMLHttpRequest"
        ):

            return jsonify({

                "success": False,

                "error": (
                    "Unable to delete "
                    "clinical case."
                )

            }), 500

        flash(
            "Unable to delete clinical case.",
            "error"
        )

    return redirect(
        url_for("clinical_cases")
    )

# =========================================================
# SETTINGS HELPERS
# =========================================================

def get_doctor_settings():

    if not doctor_logged_in():
        return None

    doctor_id = session["doctor_id"]

    settings = DoctorSettings.query.filter_by(
        doctor_id=doctor_id
    ).first()

    if not settings:

        settings = DoctorSettings(
            doctor_id=doctor_id
        )

        try:
            db.session.add(settings)
            db.session.commit()

        except Exception as error:

            db.session.rollback()

            print(
                "CREATE SETTINGS ERROR:",
                error
            )

            return None

    return settings

# =========================================================
# PATIENT AUTHENTICATION HELPERS
# =========================================================

def patient_logged_in():

    return bool(
        session.get("patient_id")
    )


def get_current_patient():

    if not patient_logged_in():
        return None

    patient = Patient.query.filter_by(
        id=session["patient_id"]
    ).first()

    return patient


def patient_context():

    patient = get_current_patient()

    if not patient:
        return {}

    return {

        "patient_name":
            patient.full_name,

        "patient_id":
            patient.patient_id,

        "patient_email":
            patient.email or "",

        "patient_initials":
            (
                patient.first_name[0].upper()
                if patient.first_name
                else "P"
            )
            +
            (
                patient.last_name[0].upper()
                if patient.last_name
                else "T"
            )

    }
  # =========================================================
# PATIENT LOGIN
# =========================================================

@app.route(
    "/patient-login",
    methods=["GET", "POST"]
)
def patient_login():

    if patient_logged_in():

        return redirect(
            url_for("patient_portal")
        )

    error = None

    if request.method == "POST":

        login_id = request.form.get(
            "login",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not login_id or not password:

            error = (
                "Please enter your "
                "patient ID or email and password."
            )

            return render_template(
                "patient-login.html",
                error=error
            )

        patient = Patient.query.filter(
            or_(
                Patient.patient_id == login_id,
                Patient.email == login_id.lower()
            )
        ).first()

        if not patient:

            error = "Invalid patient credentials."

            return render_template(
                "patient-login.html",
                error=error
            )

        if not patient.patient_account_active:

            error = (
                "Patient portal access "
                "has not been enabled."
            )

            return render_template(
                "patient-login.html",
                error=error
            )

        if not patient.password_hash:

            error = (
                "Patient portal account "
                "is not configured."
            )

            return render_template(
                "patient-login.html",
                error=error
            )

        if not check_password_hash(
            patient.password_hash,
            password
        ):

            error = "Invalid patient credentials."

            return render_template(
                "patient-login.html",
                error=error
            )

        session.clear()

        session["patient_id"] = patient.id

        session["patient_name"] = (
            patient.full_name
        )

        session["patient_email"] = (
            patient.email or ""
        )

        session["patient_code"] = (
            patient.patient_id
        )

        patient.patient_last_login = datetime.utcnow()

        try:

            db.session.commit()

        except Exception as error:

            db.session.rollback()

            print(
                "PATIENT LOGIN UPDATE ERROR:",
                error
            )

        return redirect(
            url_for("patient_portal")
        )

    return render_template(
        "patient-login.html",
        error=error
    )
# =========================================================
# CREATE FIRST DOCTOR
# =========================================================

@app.route("/create-doctor")
def create_doctor():

    existing_doctor = Doctor.query.filter_by(
        email="doctor@elora.med"
    ).first()

    if existing_doctor:

        return """
        <!DOCTYPE html>

        <html>

        <head>

            <title>
                ELORA MEDAI
            </title>

        </head>

        <body>

            <h2>
                Doctor account already exists.
            </h2>

            <p>

                <a href="/">
                    Go to Login
                </a>

            </p>

        </body>

        </html>
        """

    doctor = Doctor(

        name="ELORA Doctor",

        email="doctor@elora.med",

        password_hash=generate_password_hash(
            "123456"
        ),

        role="doctor"

    )

    try:

        db.session.add(
            doctor
        )

        db.session.commit()

    except Exception as error:

        db.session.rollback()

        print(
            "CREATE DOCTOR ERROR:",
            error
        )

        return """
        <h2>
            Unable to create doctor account.
        </h2>
        """

    return """
    <!DOCTYPE html>

    <html>

    <head>

        <title>
            ELORA MEDAI
        </title>

    </head>

    <body>

        <h2>
            Doctor account created successfully.
        </h2>

        <p>
            Email: doctor@elora.med
        </p>

        <p>
            Password: 123456
        </p>

        <p>

            <a href="/">
                Go to Login
            </a>

        </p>

    </body>

    </html>
    """

# =========================================================
# SETTINGS PAGE
# =========================================================

@app.route("/settings")
@app.route("/setting")
def settings():
    if not doctor_logged_in():
        return redirect(url_for("login"))

    doctor = get_current_doctor()

    if not doctor:
        session.clear()
        return redirect(url_for("login"))

    doctor_settings = get_doctor_settings()

    if not doctor_settings:
        flash(
            "Unable to load your settings.",
            "error"
        )
        return redirect(url_for("dashboard"))

    return render_template(
        "settings.html",
        doctor=doctor,
        settings=doctor_settings,
        **doctor_context()
    )
# =========================================================
# PHASE 4 — DOCTOR ↔ PATIENT CHAT API
# =========================================================


# =========================================================
# CHAT MESSAGE SERIALIZER
# =========================================================

def chat_message_to_dict(message):

    return {
        "id": message.id,

        "conversation_id":
            message.conversation_id,

        "sender_type":
            message.sender_type,

        "sender_id":
            message.sender_id,

        "message":
            message.message,

        "is_read":
            bool(message.is_read),

        "created_at": (
            message.created_at.isoformat()
            if message.created_at
            else None
        )
    }


# =========================================================
# GET OR CREATE PATIENT CONVERSATION
# =========================================================

def get_or_create_chat_conversation(patient_id):

    doctor_id = session.get(
        "doctor_id"
    )

    if not doctor_id:
        return None, None

    patient = Patient.query.filter_by(
        id=patient_id
    ).first()

    if not patient:
        return None, None

    conversation = ChatConversation.query.filter_by(
        doctor_id=doctor_id,
        patient_id=patient.id
    ).first()

    if not conversation:

        conversation = ChatConversation(
            doctor_id=doctor_id,
            patient_id=patient.id
        )

        db.session.add(
            conversation
        )

        db.session.commit()

    return conversation, patient


# =========================================================
# GET PATIENT CHAT
# =========================================================

@app.route(
    "/api/chat/<int:patient_id>",
    methods=["GET"]
)
def get_patient_chat_api(patient_id):

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    conversation, patient = (
        get_or_create_chat_conversation(
            patient_id
        )
    )

    if not patient:

        return jsonify({
            "success": False,
            "error": "Patient not found."
        }), 404

    messages = []

    if conversation:

        messages = ChatMessage.query.filter_by(
            conversation_id=conversation.id
        ).order_by(
            ChatMessage.created_at.asc()
        ).all()

    return jsonify({

        "success": True,

        "conversation": {

            "id":
                conversation.id
                if conversation
                else None,

            "doctor_id":
                session["doctor_id"],

            "patient_id":
                patient.id

        },

        "patient": {

            "id":
                patient.id,

            "patient_id":
                patient.patient_id,

            "name":
                patient.full_name

        },

        "messages": [

            chat_message_to_dict(
                message
            )

            for message in messages

        ]

    })


# =========================================================
# SEND PATIENT MESSAGE
# =========================================================

@app.route(
    "/api/chat/<int:patient_id>",
    methods=["POST"]
)
def send_patient_chat_message(patient_id):

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    # -----------------------------------------------------
    # GET / CREATE CONVERSATION
    # -----------------------------------------------------

    conversation, patient = (
        get_or_create_chat_conversation(
            patient_id
        )
    )

    if not patient:

        return jsonify({
            "success": False,
            "error": "Patient not found."
        }), 404

    # -----------------------------------------------------
    # REQUEST DATA
    # -----------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    message_text = str(
        data.get(
            "message",
            ""
        )
    ).strip()

    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not message_text:

        return jsonify({
            "success": False,
            "error": "Message cannot be empty."
        }), 400

    if len(message_text) > 2000:

        return jsonify({
            "success": False,
            "error":
                "Message cannot exceed 2000 characters."
        }), 400

    # -----------------------------------------------------
    # CREATE MESSAGE
    # -----------------------------------------------------

    message = ChatMessage(

        conversation_id =
            conversation.id,

        sender_type =
            "doctor",

        sender_id =
            session["doctor_id"],

        message =
            message_text,

        is_read =
            False

    )

    try:

        db.session.add(
            message
        )

        conversation.updated_at = (
            datetime.utcnow()
        )

        db.session.commit()

        return jsonify({

            "success": True,

            "message":
                chat_message_to_dict(
                    message
                )

        })

    except Exception as error:

        db.session.rollback()

        print(
            "SEND PATIENT CHAT ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "error":
                "Unable to send message."

        }), 500


# =========================================================
# MARK PATIENT MESSAGES AS READ
# =========================================================

@app.route(
    "/api/chat/<int:patient_id>/read",
    methods=["POST"]
)
def mark_patient_chat_read(patient_id):

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    doctor_id = session["doctor_id"]

    conversation = ChatConversation.query.filter_by(

        doctor_id=doctor_id,

        patient_id=patient_id

    ).first()

    if not conversation:

        return jsonify({
            "success": True,
            "marked_read": 0
        })

    unread_messages = ChatMessage.query.filter_by(

        conversation_id=
            conversation.id,

        sender_type=
            "patient",

        is_read=False

    ).all()

    for message in unread_messages:

        message.is_read = True

    try:

        db.session.commit()

        return jsonify({

            "success": True,

            "marked_read":
                len(unread_messages)

        })

    except Exception as error:

        db.session.rollback()

        print(
            "MARK CHAT READ ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "error":
                "Unable to mark messages as read."

        }), 500

# =========================================================
# DOCTOR LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )
# =========================================================
# CHAT SUMMARY
# =========================================================

@app.route(
    "/api/chat/<int:patient_id>/summary",
    methods=["GET"]
)
def patient_chat_summary(patient_id):

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    doctor_id = session["doctor_id"]

    patient = Patient.query.filter_by(
        id=patient_id
    ).first()

    if not patient:

        return jsonify({
            "success": False,
            "error": "Patient not found."
        }), 404

    conversation = ChatConversation.query.filter_by(

        doctor_id=doctor_id,

        patient_id=patient.id

    ).first()

    if not conversation:

        return jsonify({

            "success": True,

            "exists": False,

            "unread_count": 0,

            "last_message": None

        })

    last_message = ChatMessage.query.filter_by(

        conversation_id=
            conversation.id

    ).order_by(

        ChatMessage.created_at.desc()

    ).first()

    unread_count = ChatMessage.query.filter_by(

        conversation_id=
            conversation.id,

        sender_type=
            "patient",

        is_read=False

    ).count()

    return jsonify({

        "success": True,

        "exists": True,

        "conversation_id":
            conversation.id,

        "unread_count":
            unread_count,

        "last_message": (

            chat_message_to_dict(
                last_message
            )

            if last_message
            else None

        )

    })

# =========================================================
# SETTINGS SERIALIZER
# =========================================================

def serialize_doctor_settings(doctor_settings):

    return {

        # Notifications
        "email_notifications":
            bool(doctor_settings.email_notifications),

        "case_notifications":
            bool(doctor_settings.case_notifications),

        "evidence_notifications":
            bool(doctor_settings.evidence_notifications),

        "security_notifications":
            bool(doctor_settings.security_notifications),

        # Appearance
        "theme":
            doctor_settings.theme,

        "compact_mode":
            bool(doctor_settings.compact_mode),

        "animations":
            bool(doctor_settings.animations),

        # AI
        "ai_assistance":
            bool(doctor_settings.ai_assistance),

        "ai_evidence":
            bool(doctor_settings.ai_evidence),

        "ai_risk_alerts":
            bool(doctor_settings.ai_risk_alerts),

        "ai_explanations":
            bool(doctor_settings.ai_explanations),

        "ai_confidence":
            doctor_settings.ai_confidence,

        # Clinical
        "default_case_status":
            doctor_settings.default_case_status,

        "auto_save":
            bool(doctor_settings.auto_save),

        "confirm_deletions":
            bool(doctor_settings.confirm_deletions),

        "metric_units":
            bool(doctor_settings.metric_units),

        "show_patient_id":
            bool(doctor_settings.show_patient_id)
    }


# =========================================================
# API — GET SETTINGS
# =========================================================

@app.route("/api/settings", methods=["GET"])
def get_settings_api():

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    doctor_settings = get_doctor_settings()

    if not doctor_settings:

        return jsonify({
            "success": False,
            "error": "Unable to load settings."
        }), 500

    return jsonify({
        "success": True,
        "settings": serialize_doctor_settings(
            doctor_settings
        )
    })


# =========================================================
# API — UPDATE SETTINGS
# =========================================================

@app.route(
    "/api/settings",
    methods=["POST", "PUT", "PATCH"]
)
def update_settings():

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    doctor_settings = get_doctor_settings()

    if not doctor_settings:

        return jsonify({
            "success": False,
            "error": "Unable to load settings."
        }), 500

    data = request.get_json(
        silent=True
    ) or {}

    # =====================================================
    # SAFE BOOLEAN
    # =====================================================

    def get_boolean(key, current_value):

        if key not in data:
            return current_value

        value = data.get(key)

        if isinstance(value, bool):
            return value

        if isinstance(value, str):

            return value.strip().lower() in [
                "true",
                "1",
                "yes",
                "on"
            ]

        if isinstance(value, int):
            return bool(value)

        return current_value


    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    doctor_settings.email_notifications = get_boolean(
        "email_notifications",
        doctor_settings.email_notifications
    )

    doctor_settings.case_notifications = get_boolean(
        "case_notifications",
        doctor_settings.case_notifications
    )

    doctor_settings.evidence_notifications = get_boolean(
        "evidence_notifications",
        doctor_settings.evidence_notifications
    )

    doctor_settings.security_notifications = get_boolean(
        "security_notifications",
        doctor_settings.security_notifications
    )


    # =====================================================
    # APPEARANCE
    # =====================================================

    if "theme" in data:

        theme = str(
            data.get("theme", "")
        ).strip().lower()

        if theme in [
            "dark",
            "light",
            "system"
        ]:

            doctor_settings.theme = theme


    doctor_settings.compact_mode = get_boolean(
        "compact_mode",
        doctor_settings.compact_mode
    )

    doctor_settings.animations = get_boolean(
        "animations",
        doctor_settings.animations
    )


    # =====================================================
    # AI PREFERENCES
    # =====================================================

    doctor_settings.ai_assistance = get_boolean(
        "ai_assistance",
        doctor_settings.ai_assistance
    )

    doctor_settings.ai_evidence = get_boolean(
        "ai_evidence",
        doctor_settings.ai_evidence
    )

    doctor_settings.ai_risk_alerts = get_boolean(
        "ai_risk_alerts",
        doctor_settings.ai_risk_alerts
    )

    doctor_settings.ai_explanations = get_boolean(
        "ai_explanations",
        doctor_settings.ai_explanations
    )


    # IMPORTANT:
    # This now MATCHES your settings.html exactly.
    #
    # HTML:
    # conservative
    # balanced
    # detailed

    if "ai_confidence" in data:

        confidence = str(
            data.get(
                "ai_confidence",
                ""
            )
        ).strip().lower()

        allowed_confidence = [
            "conservative",
            "balanced",
            "detailed"
        ]

        if confidence in allowed_confidence:

            doctor_settings.ai_confidence = confidence


    # =====================================================
    # CLINICAL PREFERENCES
    # =====================================================

    if "default_case_status" in data:

        default_status = str(
            data.get(
                "default_case_status",
                ""
            )
        ).strip()

        allowed_statuses = [
            "New",
            "Active"
        ]

        if default_status in allowed_statuses:

            doctor_settings.default_case_status = (
                default_status
            )


    doctor_settings.auto_save = get_boolean(
        "auto_save",
        doctor_settings.auto_save
    )

    doctor_settings.confirm_deletions = get_boolean(
        "confirm_deletions",
        doctor_settings.confirm_deletions
    )

    doctor_settings.metric_units = get_boolean(
        "metric_units",
        doctor_settings.metric_units
    )

    doctor_settings.show_patient_id = get_boolean(
        "show_patient_id",
        doctor_settings.show_patient_id
    )


    # =====================================================
    # SAVE
    # =====================================================

    try:

        doctor_settings.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({

            "success": True,

            "message":
                "Settings saved successfully.",

            "settings":
                serialize_doctor_settings(
                    doctor_settings
                )

        })

    except Exception as error:

        db.session.rollback()

        print(
            "SETTINGS UPDATE ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "error":
                "Unable to save settings."

        }), 500


# =========================================================
# UPDATE PROFILE
# =========================================================

@app.route(
    "/api/settings/profile",
    methods=["POST"]
)
def update_profile():

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    doctor = get_current_doctor()

    if not doctor:

        return jsonify({
            "success": False,
            "error": "Doctor account not found."
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    name = str(
        data.get(
            "name",
            ""
        )
    ).strip()

    email = str(
        data.get(
            "email",
            ""
        )
    ).strip().lower()


    # =====================================================
    # VALIDATION
    # =====================================================

    if not name:

        return jsonify({
            "success": False,
            "error": "Name is required."
        }), 400

    if not email:

        return jsonify({
            "success": False,
            "error": "Email is required."
        }), 400


    # =====================================================
    # EMAIL DUPLICATE CHECK
    # =====================================================

    existing = Doctor.query.filter(
        Doctor.email == email,
        Doctor.id != doctor.id
    ).first()

    if existing:

        return jsonify({
            "success": False,
            "error":
                "That email address is already in use."
        }), 400


    # =====================================================
    # SAVE PROFILE
    # =====================================================

    try:

        doctor.name = name
        doctor.email = email

        db.session.commit()

        # Update session immediately.
        session["doctor_name"] = doctor.name
        session["doctor_email"] = doctor.email

        return jsonify({

            "success": True,

            "message":
                "Profile updated successfully.",

            "doctor": {

                "name":
                    doctor.name,

                "email":
                    doctor.email,

                "initials":
                    get_doctor_initials()

            }

        })

    except Exception as error:

        db.session.rollback()

        print(
            "PROFILE UPDATE ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "error":
                "Unable to update profile."

        }), 500


# =========================================================
# CHANGE PASSWORD
# =========================================================

@app.route(
    "/api/settings/password",
    methods=["POST"]
)
def change_password():

    if not doctor_logged_in():

        return jsonify({
            "success": False,
            "error": "Authentication required."
        }), 401

    doctor = get_current_doctor()

    if not doctor:

        return jsonify({
            "success": False,
            "error": "Doctor account not found."
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    current_password = str(
        data.get(
            "current_password",
            ""
        )
    )

    new_password = str(
        data.get(
            "new_password",
            ""
        )
    )

    confirm_password = str(
        data.get(
            "confirm_password",
            ""
        )
    )
# =========================================================
# PATIENT CHAT PAGE
# =========================================================

@app.route(
    "/patient/<int:patient_id>/chat"
)
def patient_chat(patient_id):

    if not doctor_logged_in():

        return redirect(
            url_for("login")
        )

    patient = Patient.query.get_or_404(
        patient_id
    )

    # Make sure this doctor has access
    # to the patient's conversation.

    conversation = ChatConversation.query.filter_by(

        doctor_id=session["doctor_id"],

        patient_id=patient.id

    ).first()

    # Create the conversation if it
    # doesn't exist yet.

    if not conversation:

        conversation = ChatConversation(

            doctor_id=session["doctor_id"],

            patient_id=patient.id

        )

        try:

            db.session.add(
                conversation
            )

            db.session.commit()

        except Exception as error:

            db.session.rollback()

            print(
                "CREATE CHAT ERROR:",
                error
            )

            flash(
                "Unable to open patient chat.",
                "error"
            )

            return redirect(
                url_for(
                    "patient_profile",
                    patient_id=patient.id
                )
            )

    return render_template(

        "patient-chat.html",

        patient=patient,

        conversation=conversation,

        messages=conversation.messages,

        **doctor_context()

    )
# =========================================================
# ENABLE PATIENT PORTAL
# =========================================================

@app.route("/patient/<int:patient_id>/enable-portal", methods=["POST"])
def enable_patient_portal(patient_id):

    # Make sure doctor is logged in
    if not doctor_logged_in():
        return redirect(url_for("login"))

    # Find patient
    patient = Patient.query.get_or_404(patient_id)

    # Enable patient portal
    patient.patient_account_active = True

    db.session.commit()

    flash(
        f"Patient portal enabled for {patient.first_name} {patient.last_name}.",
        "success"
    )

    return redirect(
        url_for(
            "patient_profile",
            patient_id=patient.id
        )
    )
    # =====================================================
    # VALIDATION
    # =====================================================

    if not current_password:

        return jsonify({
            "success": False,
            "error":
                "Current password is required."
        }), 400


    if not doctor.password_hash:

        return jsonify({
            "success": False,
            "error":
                "Account password is unavailable."
        }), 500


    if not check_password_hash(
        doctor.password_hash,
        current_password
    ):

        return jsonify({
            "success": False,
            "error":
                "Current password is incorrect."
        }), 400


    if len(new_password) < 6:

        return jsonify({
            "success": False,
            "error":
                "New password must contain "
                "at least 6 characters."
        }), 400


    if new_password != confirm_password:

        return jsonify({
            "success": False,
            "error":
                "New passwords do not match."
        }), 400


    # =====================================================
    # SAVE PASSWORD
    # =====================================================

    try:

        doctor.password_hash = (
            generate_password_hash(
                new_password
            )
        )

        db.session.commit()

        return jsonify({

            "success": True,

            "message":
                "Password changed successfully."

        })

    except Exception as error:

        db.session.rollback()

        print(
            "PASSWORD UPDATE ERROR:",
            error
        )

        return jsonify({

            "success": False,

            "error":
                "Unable to change password."

        }), 500


# =========================================================
# 404
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ELORA MEDAI | 404</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                margin: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #050b14;
                color: white;
                font-family: Arial, sans-serif;
                text-align: center;
            }

            .error-box {
                padding: 40px;
            }

            h1 {
                font-size: 72px;
                margin: 0;
                color: #4ade80;
            }

            h2 {
                margin: 10px 0;
            }

            p {
                color: #94a3b8;
            }

            a {
                display: inline-block;
                margin-top: 20px;
                padding: 12px 22px;
                border-radius: 8px;
                background: #4ade80;
                color: #020617;
                text-decoration: none;
                font-weight: bold;
            }
        </style>
    </head>

    <body>

        <div class="error-box">

            <h1>404</h1>

            <h2>PAGE NOT FOUND</h2>

            <p>
                The requested ELORA MEDAI page does not exist.
            </p>

            <a href="/dashboard">
                Return to Dashboard
            </a>

        </div>

    </body>
    </html>
    """


# =========================================================
# 500
# =========================================================

@app.errorhandler(500)
def internal_server_error(error):

    try:
        db.session.rollback()
    except Exception:
        pass

    return render_template(
        "500.html"
    ), 500


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
    
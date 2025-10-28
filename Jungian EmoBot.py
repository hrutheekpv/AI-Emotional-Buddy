import sys
import threading
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from typing import Optional, Dict
from textblob import TextBlob
import re
import uuid
from datetime import datetime

app = FastAPI(title="AI Therapist Sample Model", description="Mental health resource guidance API")

class MentalHealthResourceGuide:
    CONCERN_PATTERNS = {
        "crisis_immediate": {
            "patterns": [
                r"(suicide|kill myself|end my life|want to die|better off dead)",
                r"(going to hurt myself|self harm|cutting|self injury)",
                r"(no reason to live|can't go on|end it all)"
            ],
            "urgency": "immediate",
            "response_level": "crisis"
        },
        "depression_signs": {
            "patterns": [
                r"(depressed|clinical depression|major depression)",
                r"(hopeless|worthless|empty inside)",
                r"(can't get out of bed|no energy|no motivation)",
                r"(losing interest|don't enjoy anything)",
                r"(crying every day|constant sadness)",
                r"(sleeping too much|too little|appetite changes)",
                r"(thoughts of death|suicidal thoughts)"
            ],
            "urgency": "high",
            "response_level": "professional"
        },
        "anxiety_signs": {
            "patterns": [
                r"(panic attack|anxiety attack)",
                r"(constant worry|can't stop worrying)",
                r"(heart racing|can't breathe|chest tight)",
                r"(avoiding situations|too anxious to)",
                r"(obsessive thoughts|compulsive behaviors)"
            ],
            "urgency": "moderate",
            "response_level": "professional"
        },
        "trauma_signs": {
            "patterns": [
                r"(flashbacks|nightmares|ptsd)",
                r"(traumatic memory|childhood trauma)",
                r"(triggered|reminded of trauma)",
                r"(dissociating|feeling numb)"
            ],
            "urgency": "high",
            "response_level": "professional"
        }
    }

    MENTAL_HEALTH_RESOURCES = {
        "immediate_crisis": {
            "name": "Immediate Crisis Support",
            "description": "Available 24/7 for immediate help",
            "resources": [
                "Vandrevala Foundation: 9999666555",
                "iCall: 9152987821",
                "AASRA: 9820466726",
                "Emergency: 112/108"
            ]
        },
        "therapy_services": {
            "name": "Professional Therapy",
            "description": "Licensed mental health professionals",
            "resources": [
                "Practo - Find Psychiatrists & Therapists",
                "Lybrate - Online Mental Health Consultations",
                "YourDOST - Online Counseling",
                "Manastha - Online Therapy"
            ]
        },
        "depression_support": {
            "name": "Depression Support",
            "description": "Specialized depression resources",
            "resources": [
                "Fortis Stress Helpline: +91-8376804102",
                "NIMHANS Bangalore: 080-46110007",
                "Depression and Bipolar Support Alliance"
            ]
        },
        "anxiety_support": {
            "name": "Anxiety Support",
            "description": "Anxiety-specific help and tools",
            "resources": [
                "Anxiety and Depression Association of America",
                "Calm App for anxiety management",
                "Headspace for mindfulness"
            ]
        }
    }

    def analyze_mental_health_needs(self, text: str) -> Dict:
        detected_concerns = []
        highest_urgency = "low"
        for concern_type, concern_info in self.CONCERN_PATTERNS.items():
            for pattern in concern_info["patterns"]:
                if re.search(pattern, text.lower()):
                    detected_concerns.append({
                        "type": concern_type,
                        "urgency": concern_info["urgency"],
                        "response_level": concern_info["response_level"]
                    })
                    if concern_info["urgency"] == "immediate":
                        highest_urgency = "immediate"
                    elif concern_info["urgency"] == "high" and highest_urgency != "immediate":
                        highest_urgency = "high"
                    elif concern_info["urgency"] == "moderate" and highest_urgency not in ["immediate", "high"]:
                        highest_urgency = "moderate"
                    break
        return {
            "detected_concerns": detected_concerns,
            "highest_urgency": highest_urgency,
            "needs_immediate_help": highest_urgency == "immediate",
            "needs_professional_help": highest_urgency in ["immediate", "high"]
        }

    def get_recommended_resources(self, analysis: Dict) -> Dict:
        resource_categories = []
        if analysis["needs_immediate_help"]:
            resource_categories.extend(["immediate_crisis"])
        if analysis["needs_professional_help"]:
            resource_categories.append("therapy_services")
        for concern in analysis["detected_concerns"]:
            if concern["type"] == "depression_signs":
                resource_categories.append("depression_support")
            elif concern["type"] == "anxiety_signs":
                resource_categories.append("anxiety_support")
            elif concern["type"] == "trauma_signs":
                resource_categories.extend(["therapy_services"])
        unique_categories = list(set(resource_categories))
        resources = {}
        for category in unique_categories:
            resources[category] = self.MENTAL_HEALTH_RESOURCES[category]
        return resources

    def create_mental_health_response(self, user_message: str, analysis: Dict, resources: Dict) -> str:
        if analysis["needs_immediate_help"]:
            response = "I'm deeply concerned about your safety.\n\n"
            response += "What you're describing sounds incredibly painful, and your safety is the most important thing right now.\n\n"
            response += "Please reach out to these crisis services immediately:\n"
            for resource in resources.get("immediate_crisis", {}).get("resources", []):
                response += f"• {resource}\n"
            response += "\nYou don't have to face this alone - there are trained professionals available right now who want to help you."
        elif analysis["needs_professional_help"]:
            response = "Thank you for sharing this with me.\n\n"
            response += "What you're experiencing sounds really challenging, and it takes courage to talk about it. These feelings deserve proper professional support.\n\n"
            response += "I strongly recommend connecting with these resources:\n"
            for category, info in resources.items():
                if category != "immediate_crisis":
                    response += f"\n{info['name']} - {info['description']}:\n"
                    for resource in info["resources"]:
                        response += f"• {resource}\n"
            response += "\nA mental health professional can provide the proper assessment and support you deserve."
        else:
            response = "I hear you.\n\n"
            response += "It sounds like you're going through a difficult time. While I'm here to listen and offer perspectives, these resources might be helpful for additional support:\n"
            for category, info in resources.items():
                response += f"\n{info['name']}:\n"
                for resource in info["resources"][:2]:
                    response += f"• {resource}\n"
            response += "\nRemember that seeking support is a sign of strength, not weakness."
        return response

class IntegratedMentalHealthCompanion:
    def __init__(self):
        self.resource_guide = MentalHealthResourceGuide()

    def analyze_sympathy(self, text: str) -> Dict:
        blob = TextBlob(text)
        polarity = round(blob.sentiment.polarity, 3)
        subjectivity = round(blob.sentiment.subjectivity, 3)
        negative_factor = max(0.0, -polarity)
        raw_score = negative_factor * (1.0 + subjectivity)
        sympathy_score = min(1.0, raw_score / 1.5)
        if sympathy_score >= 0.66:
            level = "high"
        elif sympathy_score >= 0.33:
            level = "moderate"
        else:
            level = "low"
        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "sympathy_score": round(sympathy_score, 3),
            "sympathy_level": level
        }

    def generate_comprehensive_response(self, user_message: str, session_id: str) -> Dict:
        mental_health_analysis = self.resource_guide.analyze_mental_health_needs(user_message)
        resources = self.resource_guide.get_recommended_resources(mental_health_analysis)
        sympathy_analysis = self.analyze_sympathy(user_message)
        user_lower = user_message.lower().strip()

        if any(greet in user_lower for greet in [
            "hi", "hello", "hey", "greetings", "good morning", "good evening", "good afternoon"
        ]):
            base_response = (
                "Hello! 👋 It’s so nice to connect with you. How are you feeling today? "
                "You can share anything on your mind, and I’m here to listen with care."
            )
            response_type = "greeting"
            full_response = f"{base_response}"
       
        elif any(word in user_lower for word in [
            "happy", "joyful", "joy", "glad", "content", "cheerful", "delighted", "pleased", "excited"
        ]):
            base_response = (
                "It’s wonderful to hear that you’re feeling happy! Celebrating these moments of joy is so important. "
                "May your days be filled with many more such moments."
            )
            response_type = "happy_support"
            full_response = f"{base_response}"
        
        else:
            if any(word in user_lower for word in ["sad", "depressed", "hopeless", "empty", "can't get out of bed", "blue", "down"]):
                base_response = (
                    "I hear the profound sadness in your words. Remember, even in dark moments, "
                    "there is hope for renewal. Your feelings are valid and you are not alone."
                )
                response_type = "depression_support"
            elif any(word in user_lower for word in ["anxious", "worried", "panic", "overwhelmed", "stress", "nervous", "tense"]):
                base_response = (
                    "Anxiety can feel overwhelming, but you're showing strength by speaking about it. "
                    "Sometimes, just acknowledging these feelings is the first step to calming your mind."
                )
                response_type = "anxiety_support"
            elif any(word in user_lower for word in ["lonely", "isolated", "alone", "abandoned"]):
                base_response = (
                    "Feeling alone is tough. Remember, connection is possible and you are valued. "
                    "Reaching out takes courage, and I’m here to listen."
                )
                response_type = "loneliness_support"
            elif any(word in user_lower for word in ["angry", "frustrated", "mad", "irritated"]):
                base_response = (
                    "Anger is a natural emotion. It can be a signal that something important needs attention. "
                    "It's okay to feel this way, and expressing it can help bring clarity and relief."
                )
                response_type = "anger_support"
            elif any(word in user_lower for word in ["grateful", "thankful", "blessed"]):
                base_response = (
                    "Gratitude brings light into our lives. Thank you for sharing your positive feelings; "
                    "celebrating these moments is an important part of well-being."
                )
                response_type = "gratitude_support"
            elif any(word in user_lower for word in ["hopeful", "optimistic", "encouraged"]):
                base_response = (
                    "It’s wonderful to sense your hope and optimism. These feelings can be a guiding light "
                    "on your path toward healing and growth."
                )
                response_type = "hope_support"
            elif any(word in user_lower for word in ["dream", "dreamt", "dreamed", "nightmare"]):
                base_response = (
                    "Dreams are voices from your unconscious. In Jungian psychology, exploring them can open "
                    "new ways to understand your inner self."
                )
                response_type = "dream_analysis"
            elif any(word in user_lower for word in ["trauma", "flashback", "ptsd", "nightmare"]):
                base_response = (
                    "What you've experienced is deeply impactful. Healing takes time and support, and Jung believed "
                    "in the psyche's capacity to mend itself."
                )
                response_type = "trauma_support"
            else:
                base_response = (
                    "Thank you for sharing with me. I’m here to hold space for your journey and help you find the "
                    "support that suits your needs."
                )
                response_type = "general_support"

            empathy_preface = ""
            if sympathy_analysis["sympathy_level"] == "high":
                empathy_preface = (
                    "I want you to know I’m truly sorry you’re going through this. You are not alone.\n\n"
                )
            elif sympathy_analysis["sympathy_level"] == "moderate":
                empathy_preface = "I can hear that this is tough for you, and I’m here to support you.\n\n"

            resource_response = self.resource_guide.create_mental_health_response(user_message, mental_health_analysis, resources)
            full_response = f"{empathy_preface}{base_response}\n\n{resource_response}"

        return {
            "response_type": response_type,
            "message": full_response,
            "mental_health_analysis": mental_health_analysis,
            "resources_provided": resources,
            "sympathy_analysis": sympathy_analysis
        }

class MentalHealthMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

companion_system = IntegratedMentalHealthCompanion()

@app.get("/")
def home():
    return {
        "message": "Jungian Mental Health Guide API",
        "version": "4.0",
        "description": "Ethical mental health resource guidance with Jungian psychological support",
        "endpoints": {
            "start_session": "POST /start-mental-health-journey",
            "chat": "POST /mental-health-guide",
            "resources": "GET /mental-health-resources"
        }
    }

@app.post("/start-mental-health-journey")
def start_mental_health_session():
    session_id = str(uuid.uuid4())[:8]
    return {
        "session_id": session_id,
        "message": "Welcome to your Mental Health Companion",
        "guide_description": "I'm here to help you find appropriate mental health resources while offering psychological perspectives.",
        "instructions": "Use this session_id in all future messages to continue our conversation"
    }

@app.post("/mental-health-guide")
def mental_health_guided_chat(message: MentalHealthMessage):
    if not message.session_id:
        raise HTTPException(status_code=400, detail="Please start with /start-mental-health-journey first")
    user_message = message.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    response_data = companion_system.generate_comprehensive_response(user_message, message.session_id)
    return {
        "session_id": message.session_id,
        "response_type": response_data["response_type"],
        "companion_response": response_data["message"],
        "mental_health_analysis": response_data["mental_health_analysis"],
        "resources_provided": response_data["resources_provided"],
        "sympathy_analysis": response_data["sympathy_analysis"],
        "safety_note": "This system provides resource guidance, not medical treatment. Always consult healthcare professionals for medical concerns."
    }

@app.get("/mental-health-resources")
def get_all_resources():
    guide = MentalHealthResourceGuide()
    return {
        "resource_categories": guide.MENTAL_HEALTH_RESOURCES,
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "note": "Always verify resources are current before use"
    }

def run_api():
    uvicorn.run(app, host="0.0.0.0", port=8000)

class MentalHealthChat(QWidget):
    def __init__(self):
        super().__init__()
        self.session_id = None
        self.init_ui()
        self.start_session()

    def init_ui(self):
        self.setWindowTitle("🦚 Jungian Mental Health Companion")
        self.setMinimumSize(620, 500)
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#1E3557"))  
        self.setPalette(palette)

        layout = QVBoxLayout()
        greeting = QLabel("🦚 Welcome! Share how you feel below. Your words are safe here.")
        greeting.setFont(QFont("Segoe UI", 12, QFont.Bold))
        greeting.setStyleSheet("color: #FFE66D; margin-bottom: 12px;")
        greeting.setAlignment(Qt.AlignCenter)
        layout.addWidget(greeting)

        self.conversation = QTextEdit()
        self.conversation.setReadOnly(True)
        self.conversation.setFont(QFont("Segoe UI", 11))
        self.conversation.setStyleSheet("""
            background: #A0DED6;
            border-radius: 12px;
            border: 1.5px solid #4B295A;
            padding: 10px;
            color: #112D32;
        """)
        layout.addWidget(self.conversation)

        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Type your feelings or questions here...")
        self.input_line.setFont(QFont("Segoe UI", 11))
        self.input_line.setStyleSheet("""
            background: #B0FFF7;
            border: 1.5px solid #4B295A;
            border-radius: 8px;
            padding: 6px;
            color: #1E3557;
        """)
        input_layout.addWidget(self.input_line)
        self.input_line.returnPressed.connect(self.send_message)  

        send_btn = QPushButton("🦚 Send")
        send_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        send_btn.setStyleSheet("""
            background-color: #FFE66D;
            color: #1E3557;
            border: none;
            border-radius: 8px;
            padding: 8px 18px;
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)
        self.setLayout(layout)

    def start_session(self):
        try:
            resp = requests.post("http://localhost:8000/start-mental-health-journey")
            if resp.ok:
                data = resp.json()
                self.session_id = data['session_id']
                self.conversation.append("🟢 Session started.\n")
            else:
                self.conversation.append("Failed to start session.\n")
        except Exception:
            self.error_box("Could not connect to backend.")

    def send_message(self):
        user_text = self.input_line.text()
        if not user_text.strip():
            return
        self.conversation.append(f"🧑‍💻 You: {user_text}")
        self.input_line.clear()
        payload = {'message': user_text, 'session_id': self.session_id}
        try:
            resp = requests.post("http://localhost:8000/mental-health-guide", json=payload)
            if resp.ok:
                data = resp.json()
                companion_msg = data['companion_response']
                self.conversation.append(f"💬 Companion:\n{companion_msg}\n")
            else:
                self.conversation.append("Error from API: " + resp.text)
        except Exception:
            self.error_box("Could not send message to backend.")

    def error_box(self, msg):
        QMessageBox.critical(self, "Error", msg)

if __name__ == '__main__':
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()
    app_gui = QApplication(sys.argv)
    chat_app = MentalHealthChat()
    chat_app.show()
    sys.exit(app_gui.exec_())

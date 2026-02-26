#!/usr/bin/env python3
import hashlib
import hmac
import pickle
import secrets
import sqlite3


class AuthenticationManager:
    def __init__(self, db_path="users.db"):
        # A01: Broken Access Control - No proper session management
        self.db_path = db_path
        self.sessions = {}  # In-memory session storage

    def login(self, username, password):
        """User login with various security vulnerabilities"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username,),
        )

        user = cursor.fetchone()
        if not user:
            return {"status": "failed", "message": "User not found"}

        stored_hash = str(user[1])
        if "$" not in stored_hash:
            return {"status": "failed", "message": "Invalid password storage format"}

        salt, expected_hash = stored_hash.split("$", 1)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 100_000
        ).hex()

        if hmac.compare_digest(expected_hash, password_hash):
            session_id = secrets.token_urlsafe(32)
            self.sessions[session_id] = {"user_id": user[0], "username": username}

            return {"status": "success", "session_id": session_id}
        else:
            return {"status": "failed", "message": "Invalid password"}

    def reset_password(self, email):
        """Password reset with security issues"""
        reset_token = secrets.token_urlsafe(32)

        # A09: Security Logging and Monitoring Failures - No security event logging
        # Simply returns token without any verification or logging
        return {"reset_token": reset_token, "url": f"/reset?token={reset_token}"}

    def deserialize_user_data(self, data):
        """Unsafe deserialization"""
        # A08: Software and Data Integrity Failures - Insecure deserialization
        return pickle.loads(data)

    def get_user_profile(self, user_id):
        """Get user profile with authorization issues"""
        # A01: Broken Access Control - No authorization check
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Fetches any user profile without checking permissions
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

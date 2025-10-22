#!/usr/bin/env python3
"""
Simple Flask API server to bridge the frontend with the AI CRM automation backend.
"""

import asyncio
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

from ai_crm_automation.main import async_main

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "AI CRM API"})


@app.route('/chat', methods=['POST'])
def chat():
    """
    Main chat endpoint that processes natural language queries
    and returns AI CRM responses.
    """
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "Missing 'query' in request body"}), 400
        
        user_query = data['query'].strip()
        if not user_query:
            return jsonify({"error": "Query cannot be empty"}), 400
        
        logger.info(f"Processing query: {user_query}")
        
        # Run the async main function with the user query
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Capture the output instead of printing it
            import io
            import sys
            from contextlib import redirect_stdout
            
            output_buffer = io.StringIO()
            
            # Redirect stdout to capture the orchestrator output
            with redirect_stdout(output_buffer):
                result = loop.run_until_complete(async_main(user_query))
            
            # Get the captured output
            response_text = output_buffer.getvalue().strip()
            
            if not response_text:
                response_text = "Request processed successfully"
            
            logger.info(f"Response: {response_text}")
            
            return jsonify({
                "response": response_text,
                "status": "success"
            })
            
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500


@app.route('/api/contacts', methods=['POST'])
def create_contact():
    """Direct API endpoint for creating contacts."""
    try:
        data = request.get_json()
        required_fields = ['email']
        
        if not data or not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Convert to natural language query
        query = f"Create a contact for {data['email']}"
        if data.get('firstName'):
            query += f" named {data['firstName']}"
        if data.get('lastName'):
            query += f" {data['lastName']}"
        if data.get('phone'):
            query += f" with phone {data['phone']}"
        
        # Process through the main system
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            import io
            import sys
            from contextlib import redirect_stdout
            
            output_buffer = io.StringIO()
            with redirect_stdout(output_buffer):
                result = loop.run_until_complete(async_main(query))
            
            response_text = output_buffer.getvalue().strip()
            
            return jsonify({
                "message": response_text or "Contact created successfully",
                "status": "success"
            })
            
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"Failed to create contact: {str(e)}",
            "status": "error"
        }), 500


@app.route('/api/deals', methods=['POST'])
def create_deal():
    """Direct API endpoint for creating deals."""
    try:
        data = request.get_json()
        
        # Convert to natural language query
        query = "Create a deal"
        if data.get('dealName'):
            query += f" named '{data['dealName']}'"
        if data.get('amount'):
            query += f" worth ${data['amount']}"
        if data.get('stage'):
            query += f" in {data['stage']} stage"
        if data.get('associated_contact_email'):
            query += f" for contact {data['associated_contact_email']}"
        
        # Process through the main system
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            import io
            import sys
            from contextlib import redirect_stdout
            
            output_buffer = io.StringIO()
            with redirect_stdout(output_buffer):
                result = loop.run_until_complete(async_main(query))
            
            response_text = output_buffer.getvalue().strip()
            
            return jsonify({
                "message": response_text or "Deal created successfully",
                "status": "success"
            })
            
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Error creating deal: {str(e)}", exc_info=True)
        return jsonify({
            "error": f"Failed to create deal: {str(e)}",
            "status": "error"
        }), 500


if __name__ == '__main__':
    print("🚀 Starting AI CRM API Server...")
    print("📱 Frontend should be served from the 'frontend' directory")
    print("🌐 API will be available at http://localhost:8000")
    print("💡 Make sure your .env file is configured with API keys")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
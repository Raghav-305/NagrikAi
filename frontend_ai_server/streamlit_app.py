import streamlit as st
import requests
import os
from datetime import datetime
import base64

st.set_page_config(page_title="City Smart Portal", page_icon="🏙️")

st.title("🏙️ Smart City CRM (Citizen Portal)")
st.write("Submit a multi-modal complaint (Text + Image + GPS + Time) for automatic AI routing.")

AI_SERVER_URL = os.getenv("AI_SERVER_URL")
INTERNAL_SECRET_TOKEN = os.getenv("INTERNAL_SECRET_TOKEN")

# Multi-modal input

# Text Input (Context)
complaint_text = st.text_area("What is the issue?", placeholder="E.g., Large pothole, sparking wire, garbage pile...")

# Image Input (Ground Truth / Vision Tool)
uploaded_file = st.file_uploader("Capture or upload a photo of the problem:", type=["jpg", "jpeg", "png"])

# Location Input (GIS Tool - Simulated)
location_input = st.text_input("Enter the location or approximate address:", placeholder="E.g., Sector 15, Near Metro Pillar 100")

if st.button("Submit Official Report"):
    if complaint_text and location_input:
        with st.spinner("Uploading and processing multi-modal data..."):
            
            # Timestamp Calculation (Hidden Input)
            submission_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # image conversion utility (must convert to base64 text to send via JSON)
            image_base64_string = ""
            if uploaded_file is not None:
                try:
                    # read file, convert bytes to base64, then base64 to string
                    image_bytes = uploaded_file.read()
                    image_base64 = base64.b64encode(image_bytes)
                    image_base64_string = image_base64.decode('utf-8')
                except Exception as e:
                    st.error(f"Error processing image: {e}")
                    image_base64_string = ""
                    
            
            # --- CONNECTION LAYER ---
            # set up security header and massive multi-modal payload
            headers = {"x-api-token": INTERNAL_SECRET_TOKEN}
            
            payload = {
                "text": complaint_text,
                "image_base64": image_base64_string,
                "location_text": location_input,
                "timestamp": submission_time
            }
            
            # send request to ai server backend
            try:
                response = requests.post(AI_SERVER_URL, json=payload, headers=headers, timeout=120) 
                
                # read the backend's response
                if response.status_code == 200:
                    data = response.json()
                    st.success("Ticket Processed Successfully!")
                    st.subheader("Official Work Order Generated")
                    st.write(f"**Ticket ID:** {data.get('ticket_id')}")
                    st.write(f"**Routed To:** {data.get('final_department')}")
                    st.write(f"**Initial Priority:** {data.get('final_priority')}")
                    st.write(f"**Deadline:** {data.get('deadline')}")
                    st.info(f"**Auditor QC Check:** {data.get('auditor_log')}")
                    st.write(f"**Internal Action Plan:** {data.get('action_plan')}")
                    
                    if uploaded_file:
                        st.image(uploaded_file, caption="Citizen Captured Image", width=300)
                    
                    with st.expander("🛠️ Admin/Developer View: Under the Hood"):
                        st.write("### 1. Raw Vision Analysis")
                        st.info(data.get('raw_analysis'))
                        
                        st.write("### 2. LangGraph Message History")
                        st.write("This is the exact payload moving through your graph:")
                        
                        for msg in data.get('message_history', []):
                            if msg.startswith("HUMAN"):
                                st.success(msg) # Highlights the prompt we sent TO the AI in green
                            else:
                                st.warning(msg) # Highlights the response FROM the AI in yellow
                
                elif response.status_code == 401:
                    st.error("Security Error: The backend rejected our token. Access Denied.")
                elif response.status_code == 413:
                    st.error("Error: Image size too large for current backend limits.")
                else:
                    st.error(f"Server Error: The backend returned status code {response.status_code}")
                    
            except requests.exceptions.Timeout:
                st.error("Connection Timeout. The backend server took too long processing the image.")
            except requests.exceptions.ConnectionError:
                st.error("Connection Failed. Is the FastAPI backend server running?")
    else:
        st.warning("Please provide both the issue description and the location.")
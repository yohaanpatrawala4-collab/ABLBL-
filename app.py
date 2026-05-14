import streamlit as st
import os
from PIL import Image
from ablbl_photo_agent import ABLBLPhotoAgent

st.set_page_config(page_title="Aditya Birla Brands - Photo Frame Generator", layout="centered")

st.title("Aditya Birla Brands Photo Frame Generator")
st.markdown("Upload your portrait to seamlessly merge it into the ABLBL photo frame!")

# Initialize Agent
agent = ABLBLPhotoAgent("dummy_key")

# File uploaders
st.sidebar.header("Configuration")
template_file = st.sidebar.file_uploader("Upload Frame Template (Optional, defaults to existing)", type=["png", "jpg", "jpeg"])
user_file = st.file_uploader("Upload your Portrait (e.g. LinkedIn Headshot)", type=["png", "jpg", "jpeg"])

if st.button("Generate Frame"):
    if user_file is None:
        st.error("Please upload your portrait first!")
    else:
        with st.spinner("Processing..."):
            # Save uploaded user file temporarily
            user_path = "temp_user_upload." + user_file.name.split('.')[-1]
            with open(user_path, "wb") as f:
                f.write(user_file.getbuffer())
                
            # Determine template to use
            template_path = "ABLBL Digital Photo Frame (1).png"
            if template_file is not None:
                template_path = "temp_template." + template_file.name.split('.')[-1]
                with open(template_path, "wb") as f:
                    f.write(template_file.getbuffer())
            elif not os.path.exists(template_path):
                # Check for jpg fallback
                if os.path.exists("ABLBL Digital Photo Frame (1).jpg"):
                    template_path = "ABLBL Digital Photo Frame (1).jpg"
                else:
                    st.error("Default template not found. Please upload it via the sidebar.")
                    st.stop()
            
            output_path = "streamlit_output.png"
            
            # Use agent
            try:
                # If we are using a fresh JPG/PNG that isn't transparent yet, we prepare it
                if template_path != agent.transparent_template_path:
                    agent.prepare_template_from_original(template_path)
                    
                agent.process_user_portrait(user_path, agent.transparent_template_path, output_path)
                
                st.success("Frame generated successfully!")
                
                # Display Result
                result_image = Image.open(output_path)
                st.image(result_image, caption="Your Professional ABLBL Frame", use_container_width=True)
                
                # Download Button
                with open(output_path, "rb") as file:
                    btn = st.download_button(
                        label="Download High-Res Image",
                        data=file,
                        file_name="ABLBL_Profile_Frame.png",
                        mime="image/png"
                    )
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            finally:
                # Cleanup
                if os.path.exists(user_path):
                    os.remove(user_path)

import streamlit as st
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# Set Streamlit page configuration
st.set_page_config(page_title="YouTube Video Summarizer", layout="wide")

# Sidebar for user inputs
google_api_key = st.sidebar.text_input("Google API Key:", type="password")
youtube_link = st.sidebar.text_input("Video Link:")
language = st.sidebar.selectbox("Select Summary Language:", options=['English', 'Hindi','Spanish', 'German', 'French'])

# Summary length customization
summary_length = st.sidebar.select_slider(
    "Select Summary Length:", options=['Short', 'Medium', 'Long'], value='Medium'
)

# Define functions
def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join(segment["text"] for segment in transcript)
    except Exception as e:
        st.sidebar.error(f"An error occurred: {e}")
        return None

def generate_gemini_content(transcript_text, prompt, api_key, language):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-pro")
        prompt_with_language = f"{prompt} Please generate a {summary_length.lower()} summary in {language}."
        response = model.generate_content(prompt_with_language + transcript_text)
        return response.text
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def create_pdf(summary_text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(72, 800, "Summary")
    text = c.beginText(40, 780)
    text.setFont("Helvetica", 12)
    for line in summary_text.split('\n'):
        text.textLine(line)
    c.drawText(text)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

# UI elements
st.title("YouTube Video Summarizer")

# Display video thumbnail
if youtube_link:
    video_id = youtube_link.split("=")[1]
    video_thumbnail = f"http://img.youtube.com/vi/{video_id}/0.jpg"
    st.image(video_thumbnail, caption="Thumbnail", use_column_width=True)

# Process and display summary
if google_api_key and youtube_link and st.button("Generate Summary"):
    transcript_text = extract_transcript_details(youtube_link)
    if transcript_text:
        prompt = """You are a YouTube video summarizer. Summarize the video content into key points within 1500 words."""
        summary = generate_gemini_content(transcript_text, prompt, google_api_key, language)
        if summary:
            st.success("Success!")
            st.subheader("The Summary:")
            st.write(summary)
        else:
            st.error("Failed to generate summary.")
    else:
        st.error("Failed to extract transcript.")

from googleapiclient.discovery import build
from textblob import TextBlob

# Initialize YouTube API client
def initialize_youtube_client(api_key):
    return build('youtube', 'v3', developerKey=api_key)

# Fetch comments from a video
def fetch_comments(youtube, video_id):
    comments = []
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=100,  # Adjust as necessary
        textFormat="plainText"
    )
    response = request.execute()
    
    for item in response.get("items", []):
        text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        comments.append(text)
    return comments

# Analyze sentiment of comments
def analyze_sentiments(comments):
    positive = 0
    negative = 0
    for comment in comments:
        sentiment = TextBlob(comment).sentiment.polarity
        if sentiment > 0:
            positive += 1
        elif sentiment < 0:
            negative += 1
    return positive, negative

# Integrate into Streamlit UI
if google_api_key and youtube_link and st.button("Analyze Comments"):
    youtube = initialize_youtube_client(google_api_key)
    video_id = youtube_link.split("=")[1]
    comments = fetch_comments(youtube, video_id)
    positive, negative = analyze_sentiments(comments)
    
    if positive or negative:
        ratio = positive / max(negative, 1)  # To avoid division by zero
        st.success("Comments analyzed successfully!")
        st.write(f"Positive comments: {positive}")
        st.write(f"Negative comments: {negative}")
        st.write(f"Ratio of Positive to Negative comments: {ratio:.2f}")
    else:
        st.error("No comments found or no clear sentiment.")
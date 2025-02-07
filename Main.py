import os
import pdfplumber
import openai
import time
import logging
import re  # Import regex for parsing numbers
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(pdf_path):
    """Extract text from each page of a PDF and concatenate it into one string."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ''
            for page in pdf.pages:
                full_text += page.extract_text() or ' '
        return full_text
    except Exception as e:
        logging.error(f"Error extracting text from {pdf_path}: {e}")
        return None

def extract_details_with_gpt(client, text):
    """Use GPT-4 to extract names and emails from text."""
    if text is None:
        return "No text extracted from PDF."
    try:
        response = client.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Please extract names and emails and return them."},
                {"role": "user", "content": text}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        logging.error(f"Error using GPT to extract details: {e}")
        return f"Failed to extract details: {e}"

def match_resume_to_job_description(client, resume_text, job_description):
    """Use GPT-4 to assess how well a resume matches a job description."""
    if resume_text is None:
        return 0
    try:
        response = client.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Assess the match percentage between the job description and the resume, and provide a numeric value only."},
                {"role": "user", "content": f"Job Description: {job_description}\nResume Text: {resume_text}"}
            ]
        )
        text_response = response['choices'][0]['message']['content']
        # Parse the first integer or float found in the response
        match_score = re.findall(r"\d+", text_response)
        if match_score:
            return int(match_score[0])  # Assuming the first number is the match score
        else:
            logging.error(f"No match score found in response: {text_response}")
            return 0
    except Exception as e:
        logging.error(f"Error matching resume to job description: {e}")
        return 0

def process_resume(pdf_path, job_description):
    #logging.info(f"Processing {pdf_path}")
    text = extract_text_from_pdf(pdf_path)
    details = extract_details_with_gpt(openai, text)
    match_score = match_resume_to_job_description(openai, text, job_description)
    return {"filename": os.path.basename(pdf_path), "details": details, "match_score": match_score}

def main():
    directory = r"C:\Users\Sharan Kumar\Dropbox\PC\Downloads\Resumes_naukri"
    job_description = """
    Job Description: We are seeking a motivated and tech-savvy intern to join our team as an Artificial Intelligence (AI) Agent Solutions Developer. This role will provide hands-on experience in developing AI-based solutions, contributing to real-world projects, and collaborating with a team of experienced professionals. The ideal candidate is passionate about AI, eager to learn, and excited to apply their skills in a practical setting.

    Preferred candidate profile:
    - Education: Currently pursuing a masters degree in Computer Science, Data Science, AI, Machine Learning, or a related field.
    - Programming Skills: Proficiency in programming languages such as Python or TypeScript, with a strong understanding of libraries like TensorFlow, PyTorch, or scikit-learn.
    - Analytical Skills: Strong analytical and problem-solving abilities, with experience in data manipulation and analysis.
    - Technical Knowledge: Familiarity with AI/ML concepts, algorithms, and frameworks.
    - Communication: Excellent written and verbal communication skills, with the ability to convey complex technical concepts to non-technical stakeholders.
    - Team Player: Ability to work collaboratively in a team environment, showing initiative and flexibility.

    Preferred Skills:
    - Experience with deployment in cloud platforms such as AWS, Google Cloud, or Azure.
    - Knowledge of RAG and agentic frameworks like LangChain, AutoGen, etc.
    - Previous internship or project experience in AI/ML.
    """
    
    req_count = 21
    match_threshold = 0

    pdf_paths = [os.path.join(directory, filename) for filename in os.listdir(directory) if filename.endswith('.pdf')]
    #logging.info(f"Found {len(pdf_paths)} PDFs to process.")
    results = []
    count = 0
    
    start_time = time.perf_counter()
    with ThreadPoolExecutor() as executor:
        future_to_pdf = {executor.submit(process_resume, pdf_path, job_description): pdf_path for pdf_path in pdf_paths}
        for future in as_completed(future_to_pdf):
            count = count+1
            result = future.result()
            if result['match_score'] >= match_threshold:
                results.append(result)

    sorted_resume_data = sorted(results, key=lambda x: x["match_score"], reverse=True)
    end_time = time.perf_counter()
    
    #logging.info(f"Processed {len(results)} resumes with a match score above {match_threshold}")
    #time taken for processing
    elapsed_time = end_time - start_time
    print(f"Time taken to read all the resumes: {round(elapsed_time)} seconds")
    # print(count)
    print("\n")
    countt=0
    
    for resume in sorted_resume_data[:req_count]:
        #logging.info(f"File: {resume['filename']} Match Score: {resume['match_score']}%")
        print(f"File: {resume['filename']}\n{resume['details']}\nMatch Score: {resume['match_score']}%")
        countt = countt +1
        print("\n")
    print(f"Total number of resumes matched: {countt}")

if __name__ == "__main__":
    main()

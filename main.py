import requests
import json, csv
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from textblob import TextBlob
import pandas as pd

# Load the CSV file
def load_data(file_path):
    data = pd.read_csv(file_path)
    # Extract relevant columns
    data = data[[
        "What are your skills ? (Select multiple if necessary)", 
        "What are your interests?",
        "If yes, then what is/was your first Job title in your current field of work? If not applicable, write NA."
    ]]
    # Rename columns for simplicity
    data.columns = ["skills", "interests", "career"]
    # Handle missing values
    data.fillna("", inplace=True)
    return data

# Train the model
def train_model(data):
    vectorizer = CountVectorizer()
    skills = data["skills"]
    vectorizer.fit(skills)
    return vectorizer

# Recommend careers using cosine similarity
def recommend_careers(user_skills, vectorizer, data):
    user_vector = vectorizer.transform([user_skills])
    data_vectors = vectorizer.transform(data["skills"])
    similarities = cosine_similarity(user_vector, data_vectors).flatten()
    recommendations = data.loc[similarities.argsort()[::-1], "career"].unique()
    return recommendations[:3]  # Return top 3 recommendations

def fetch_jobs(career, Country):
    api_url = "https://jsearch.p.rapidapi.com/search"
    params = {
        "query":career, "country":Country, "page":1,
        }
    headers = {"x-rapidapi-key": "ff4738b004msh127262108d94159p1fb06djsn7f768c0a81d9",
	"x-rapidapi-host": "jsearch.p.rapidapi.com"}  # Replace with your API key
    response = requests.get(api_url, params=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
        # return jobs.get("jobs", [])  # Extract job listings
    else:
        print("Error fetching jobs:", response.status_code, response.text)
        return {}

# Function: Fetch course recommendations (mocked or real APIs)
def fetch_courses(keyword):
    # courses = [
    #     {"name": f"{keyword} Essentials", "platform": "Coursera"},
    #     {"name": f"Advanced {keyword} Techniques", "platform": "edX"}
    # ]
    # return courses
    api_url = "https://paid-udemy-course-for-free.p.rapidapi.com/search"
    params = {
        "s":keyword,
        }
    headers = {"x-rapidapi-key": "ff4738b004msh127262108d94159p1fb06djsn7f768c0a81d9",
	"x-rapidapi-host": "paid-udemy-course-for-free.p.rapidapi.com"}  # Replace with your API key
    response = requests.get(api_url, params=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
        # return jobs.get("jobs", [])  # Extract job listings
    else:
        print("Error fetching jobs:", response.status_code, response.text)
        return {}

# # Function: Analyze sentiment of user's input

def analyze_sentiment(text):
    sentiment_score = TextBlob(text).sentiment.polarity

    if sentiment_score > 0:
        return "positive"
    elif sentiment_score < 0:
        return "negative"
    else:
        return "neutral"

# Main Program
if __name__ == "__main__":
    print("Welcome to the Personalized Career Guidance Bot!")
    
    # Load data
    file_path = "career_recommender.csv"  # Replace with the actual file path
    career_data = load_data(file_path)
    

    # Collect user inputs
    name = input("Enter your name: ")
    user_skills = input("Enter your skills (comma-separated): ").lower()
    user_interests = input("Enter your interests (comma-separated): ").lower()
    user_query = input("What are you looking for in your career? ")

    # Analyze user sentiment
    sentiment = analyze_sentiment(user_query)
    print(f"\nYour sentiment towards your career query is: {sentiment}")

    # Train ML model and recommend careers
    vectorizer = train_model(career_data)
    recommended_careers = recommend_careers(user_skills, vectorizer, career_data)

    # Fetch job and course suggestions
    Country = input("Enter your Desired Job Location (Country Name): ")
    
    job_suggestions = {}
    course_suggestions = {}

    # https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch/playground/endpoint_73845d59-2a15-4a88-92c5-e9b1bc90956d
    for career in recommended_careers:
        if career == "" or career == "Student (Unemployed)":
            continue
        job_details = fetch_jobs(career, Country)
        if 'data' not in job_details:
            print(f"Error fetching job listings for {career}")
        else:
   
            comp_job_details = {}
            for job in job_details['data']:
                detail = {}
                detail['id'] = job['job_id']
                detail['title'] = job['job_title']
                detail['company_name'] = job['employer_name']
                detail['employment_type'] = job['job_employment_type']
                detail['apply_link'] = job['job_apply_link']
                detail['location'] = job['job_location']

                comp_job_details[job['job_id']] = detail

            job_suggestions[career] = comp_job_details

        # Courses
        course_details = fetch_courses(career)

        comp_course_details = {}
        for course in course_details:
            detail = {}
            detail['id'] = course['id']
            detail['title'] = course['title']
            detail['price'] = course['org_price']
            detail['url'] = course['coupon']

            comp_course_details[course['id']] = detail
        course_suggestions[career] = comp_course_details

    # Display results
    print(f"\nHello, {name}!")
    print("\nCareer Recommendations:")
    for career in recommended_careers:
        if career == "" or career == "Student (Unemployed)":
            continue
        print(f"- {career}")

    print("\nJob Listings:")

    with open('job_suggestions.txt', 'w') as file:
        json.dump(job_suggestions, file, indent=4)
    with open('job_suggestions.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['Career', 'Job Title', 'Company Name', 'Employment Type', 'Apply Link', 'Location'])
        # Write the data
        for career, jobs in job_suggestions.items():
            for job_title, details in jobs.items():
                writer.writerow([
                    career,
                    details['title'],
                    details['company_name'],
                    details['employment_type'],
                    details['apply_link'],
                    details['location']
                ])
    print('Job Suggestions are saved in job_suggestions.txt file')

    print("\nRecommended Courses:")
    with open('course_suggestions.txt', 'w') as file:
        json.dump(course_suggestions, file, indent=4)

    with open('course_suggestions.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['Career', 'Course Name', 'Price', 'URL'])
        # Write the data
        for career, jobs in course_suggestions.items():
            for job_title, details in jobs.items():
                writer.writerow([
                    career,
                    details['title'],
                    details['price'],
                    details['url']
                ])
    print('Course Suggestions are saved in course_suggestions.txt file')

    print("\nThank you for using the Career Guidance Bot!")


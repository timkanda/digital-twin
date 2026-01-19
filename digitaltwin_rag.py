"""
Digital Twin RAG Application
Based on Binal's production implementation
- Upstash Vector: Built-in embeddings and vector storage
- Groq: Ultra-fast LLM inference
"""

import os
import json
from dotenv import load_dotenv
from upstash_vector import Index
from groq import Groq

# Load environment variables
load_dotenv()

# Constants
JSON_FILE = "digitaltwin.json"
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
DEFAULT_MODEL = "llama-3.1-8b-instant"

def setup_groq_client():
    """Setup Groq client"""
    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not found in .env file")
        return None
    
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq client initialized successfully!")
        return client
    except Exception as e:
        print(f"❌ Error initializing Groq client: {str(e)}")
        return None

def create_content_chunks(profile_data):
    """Convert structured JSON profile into content chunks for vector embedding"""
    chunks = []
    chunk_id = 1
    
    # Personal Information
    if 'personal' in profile_data:
        p = profile_data['personal']
        chunks.append({
            'id': f'chunk_{chunk_id}',
            'title': 'Personal Information',
            'type': 'personal',
            'content': f"Name: {p.get('name', '')}. Title: {p.get('title', '')}. Location: {p.get('location', '')}. {p.get('summary', '')}",
            'metadata': {'category': 'personal', 'tags': ['name', 'title', 'location', 'summary']}
        })
        chunk_id += 1
        
        if p.get('elevator_pitch'):
            chunks.append({
                'id': f'chunk_{chunk_id}',
                'title': 'Elevator Pitch',
                'type': 'personal',
                'content': p['elevator_pitch'],
                'metadata': {'category': 'personal', 'tags': ['elevator_pitch', 'introduction']}
            })
            chunk_id += 1
    
    # Contact Information
    if 'personal' in profile_data and 'contact' in profile_data['personal']:
        c = profile_data['personal']['contact']
        contact_info = f"Email: {c.get('email', '')}. Phone: {c.get('phone', '')}. LinkedIn: {c.get('linkedin', '')}. GitHub: {c.get('github', '')}."
        chunks.append({
            'id': f'chunk_{chunk_id}',
            'title': 'Contact Information',
            'type': 'contact',
            'content': contact_info,
            'metadata': {'category': 'contact', 'tags': ['email', 'phone', 'linkedin', 'github']}
        })
        chunk_id += 1
    
    # Salary and Location Preferences
    if 'salary_location' in profile_data:
        sl = profile_data['salary_location']
        salary_info = f"Salary expectations: {sl.get('salary_expectations', '')}. Location preferences: {', '.join(sl.get('location_preferences', []))}. Remote experience: {sl.get('remote_experience', '')}. Work authorization: {sl.get('work_authorization', '')}."
        chunks.append({
            'id': f'chunk_{chunk_id}',
            'title': 'Salary and Location Preferences',
            'type': 'salary',
            'content': salary_info,
            'metadata': {'category': 'salary', 'tags': ['salary', 'location', 'remote', 'authorization']}
        })
        chunk_id += 1
    
    # Work Experience
    if 'experience' in profile_data:
        for exp in profile_data['experience']:
            exp_content = f"Company: {exp.get('company', '')}. Role: {exp.get('title', '')}. Duration: {exp.get('duration', '')}. Context: {exp.get('company_context', '')}. Team: {exp.get('team_structure', '')}."
            chunks.append({
                'id': f'chunk_{chunk_id}',
                'title': f"Work Experience - {exp.get('company', '')}",
                'type': 'experience',
                'content': exp_content,
                'metadata': {'category': 'experience', 'tags': ['work', 'job', exp.get('company', '').lower()]}
            })
            chunk_id += 1
            
            # STAR achievements for each role
            for i, star in enumerate(exp.get('achievements_star', [])):
                star_content = f"At {exp.get('company', '')}: Situation: {star.get('situation', '')}. Task: {star.get('task', '')}. Action: {star.get('action', '')}. Result: {star.get('result', '')}."
                chunks.append({
                    'id': f'chunk_{chunk_id}',
                    'title': f"Achievement at {exp.get('company', '')} #{i+1}",
                    'type': 'achievement',
                    'content': star_content,
                    'metadata': {'category': 'achievement', 'tags': ['star', 'accomplishment', exp.get('company', '').lower()]}
                })
                chunk_id += 1
            
            # Technical skills used
            skills_used = exp.get('technical_skills_used', [])
            if skills_used:
                chunks.append({
                    'id': f'chunk_{chunk_id}',
                    'title': f"Skills Used at {exp.get('company', '')}",
                    'type': 'skills',
                    'content': f"Technical skills used at {exp.get('company', '')}: {', '.join(skills_used)}.",
                    'metadata': {'category': 'skills', 'tags': skills_used}
                })
                chunk_id += 1
    
    # Technical Skills
    if 'skills' in profile_data and 'technical' in profile_data['skills']:
        tech = profile_data['skills']['technical']
        
        # Programming languages
        if 'programming_languages' in tech:
            langs = []
            for lang in tech['programming_languages']:
                if isinstance(lang, dict):
                    langs.append(f"{lang.get('language', '')} ({lang.get('proficiency', '')}, {lang.get('years', '')} years, frameworks: {', '.join(lang.get('frameworks', []))})")
                else:
                    langs.append(str(lang))
            chunks.append({
                'id': f'chunk_{chunk_id}',
                'title': 'Programming Languages',
                'type': 'skills',
                'content': f"Programming languages: {'; '.join(langs)}.",
                'metadata': {'category': 'skills', 'tags': ['programming', 'languages', 'technical']}
            })
            chunk_id += 1
        
        # Frontend skills
        if 'frontend' in tech:
            chunks.append({
                'id': f'chunk_{chunk_id}',
                'title': 'Frontend Skills',
                'type': 'skills',
                'content': f"Frontend technologies: {', '.join(tech['frontend'])}.",
                'metadata': {'category': 'skills', 'tags': ['frontend', 'ui', 'web']}
            })
            chunk_id += 1
        
        # Backend skills
        if 'backend' in tech:
            chunks.append({
                'id': f'chunk_{chunk_id}',
                'title': 'Backend Skills',
                'type': 'skills',
                'content': f"Backend technologies: {', '.join(tech['backend'])}.",
                'metadata': {'category': 'skills', 'tags': ['backend', 'server', 'api']}
            })
            chunk_id += 1
        
        # Database skills
        if 'databases' in tech:
            chunks.append({
                'id': f'chunk_{chunk_id}',
                'title': 'Database Skills',
                'type': 'skills',
                'content': f"Database technologies: {', '.join(tech['databases'])}.",
                'metadata': {'category': 'skills', 'tags': ['database', 'sql', 'data']}
            })
            chunk_id += 1
        
        # Cloud skills
        if 'cloud_platforms' in tech:
            chunks.append({
                'id': f'chunk_{chunk_id}',
                'title': 'Cloud & DevOps Skills',
                'type': 'skills',
                'content': f"Cloud and DevOps: {', '.join(tech['cloud_platforms'])}.",
                'metadata': {'category': 'skills', 'tags': ['cloud', 'devops', 'aws', 'deployment']}
            })
            chunk_id += 1
        
        # AI/ML skills
        if 'ai_ml' in tech:
            chunks.append({
                'id': f'chunk_{chunk_id}',
                'title': 'AI & Machine Learning Skills',
                'type': 'skills',
                'content': f"AI and ML experience: {', '.join(tech['ai_ml'])}.",
                'metadata': {'category': 'skills', 'tags': ['ai', 'ml', 'machine learning', 'automation']}
            })
            chunk_id += 1
    
    # Soft Skills
    if 'skills' in profile_data and 'soft_skills' in profile_data['skills']:
        chunks.append({
            'id': f'chunk_{chunk_id}',
            'title': 'Soft Skills',
            'type': 'skills',
            'content': f"Soft skills: {', '.join(profile_data['skills']['soft_skills'])}.",
            'metadata': {'category': 'skills', 'tags': ['soft skills', 'interpersonal', 'communication']}
        })
        chunk_id += 1
    
    # Certifications
    if 'skills' in profile_data and 'certifications' in profile_data['skills']:
        certs = profile_data['skills']['certifications']
        cert_list = []
        for cert in certs:
            if isinstance(cert, dict):
                cert_list.append(f"{cert.get('name', '')} from {cert.get('provider', '')} ({cert.get('year', '')})")
            else:
                cert_list.append(str(cert))
        chunks.append({
            'id': f'chunk_{chunk_id}',
            'title': 'Certifications & Training',
            'type': 'certification',
            'content': f"Certifications and training: {'; '.join(cert_list)}.",
            'metadata': {'category': 'certification', 'tags': ['certification', 'training', 'education']}
        })
        chunk_id += 1
    
    # Education
    if 'education' in profile_data:
        edu = profile_data['education']
        edu_content = f"Education: {edu.get('degree', '')} in {edu.get('specialisation', '')} from {edu.get('university', '')}. Graduated: {edu.get('graduation_year', '')}. Location: {edu.get('location', '')}."
        if edu.get('relevant_coursework'):
            edu_content += f" Relevant coursework: {', '.join(edu.get('relevant_coursework', []))}."
        chunks.append({
            'id': f'chunk_{chunk_id}',
            'title': 'Education',
            'type': 'education',
            'content': edu_content,
            'metadata': {'category': 'education', 'tags': ['university', 'degree', 'academic']}
        })
        chunk_id += 1
    
    # Projects
    if 'projects_portfolio' in profile_data:
        for proj in profile_data['projects_portfolio']:
            proj_content = f"Project: {proj.get('name', '')}. Type: {proj.get('type', '')}. Description: {proj.get('description', '')}. Technologies: {', '.join(proj.get('technologies', []))}."
            if proj.get('key_features'):
                proj_content += f" Key features: {', '.join(proj.get('key_features', []))}."
            if proj.get('impact'):
                impact = proj['impact']
                if isinstance(impact, dict):
                    impact_str = ', '.join([f"{k}: {v}" for k, v in impact.items()])
                    proj_content += f" Impact: {impact_str}."
                else:
                    proj_content += f" Impact: {impact}."
            chunks.append({
                'id': f'chunk_{chunk_id}',
                'title': f"Project - {proj.get('name', '')}",
                'type': 'project',
                'content': proj_content,
                'metadata': {'category': 'project', 'tags': proj.get('technologies', [])}
            })
            chunk_id += 1
    
    # Career Goals
    if 'career_goals' in profile_data:
        goals = profile_data['career_goals']
        goals_content = f"Career goals - Short term: {goals.get('short_term', '')}. Long term: {goals.get('long_term', '')}. Learning focus: {', '.join(goals.get('learning_focus', []))}. Industries interested: {', '.join(goals.get('industries_interested', []))}."
        chunks.append({
            'id': f'chunk_{chunk_id}',
            'title': 'Career Goals',
            'type': 'goals',
            'content': goals_content,
            'metadata': {'category': 'goals', 'tags': ['career', 'goals', 'aspirations', 'future']}
        })
        chunk_id += 1
    
    # Interview Prep - Behavioral Questions
    if 'interview_prep' in profile_data and 'common_questions' in profile_data['interview_prep']:
        questions = profile_data['interview_prep']['common_questions']
        
        if 'behavioral' in questions:
            for q in questions['behavioral']:
                if isinstance(q, dict):
                    chunks.append({
                        'id': f'chunk_{chunk_id}',
                        'title': f"Behavioral Q&A - {q.get('question', '')[:50]}...",
                        'type': 'interview',
                        'content': f"Question: {q.get('question', '')}. Answer: {q.get('answer', '')}",
                        'metadata': {'category': 'interview', 'tags': ['behavioral', 'interview', 'question']}
                    })
                    chunk_id += 1
        
        if 'technical' in questions:
            for q in questions['technical']:
                if isinstance(q, dict):
                    chunks.append({
                        'id': f'chunk_{chunk_id}',
                        'title': f"Technical Q&A - {q.get('question', '')[:50]}...",
                        'type': 'interview',
                        'content': f"Question: {q.get('question', '')}. Answer: {q.get('answer', '')}",
                        'metadata': {'category': 'interview', 'tags': ['technical', 'interview', 'question']}
                    })
                    chunk_id += 1
        
        if 'situational' in questions:
            for q in questions['situational']:
                if isinstance(q, dict):
                    chunks.append({
                        'id': f'chunk_{chunk_id}',
                        'title': f"Situational Q&A - {q.get('question', '')[:50]}...",
                        'type': 'interview',
                        'content': f"Question: {q.get('question', '')}. Answer: {q.get('answer', '')}",
                        'metadata': {'category': 'interview', 'tags': ['situational', 'interview', 'question']}
                    })
                    chunk_id += 1
    
    # Weakness Mitigation
    if 'interview_prep' in profile_data and 'weakness_mitigation' in profile_data['interview_prep']:
        for w in profile_data['interview_prep']['weakness_mitigation']:
            chunks.append({
                'id': f'chunk_{chunk_id}',
                'title': f"Weakness & Mitigation - {w.get('weakness', '')[:30]}...",
                'type': 'interview',
                'content': f"Weakness: {w.get('weakness', '')}. Mitigation: {w.get('mitigation', '')}",
                'metadata': {'category': 'interview', 'tags': ['weakness', 'improvement', 'growth']}
            })
            chunk_id += 1
    
    # Interview Signal Summary
    if 'interview_signal_summary' in profile_data:
        summary = profile_data['interview_signal_summary']
        summary_content = f"Strengths: {', '.join(summary.get('strengths', []))}. Recommended for roles: {', '.join(summary.get('recommended_for', []))}. Unique value proposition: {summary.get('unique_value_proposition', '')}."
        chunks.append({
            'id': f'chunk_{chunk_id}',
            'title': 'Professional Summary & Strengths',
            'type': 'summary',
            'content': summary_content,
            'metadata': {'category': 'summary', 'tags': ['strengths', 'value', 'recommendation']}
        })
        chunk_id += 1
    
    print(f"📦 Created {len(chunks)} content chunks from profile data")
    return chunks

def setup_vector_database():
    """Setup Upstash Vector database with built-in embeddings"""
    print("🔄 Setting up Upstash Vector database...")
    
    try:
        index = Index.from_env()
        print("✅ Connected to Upstash Vector successfully!")
        
        # Check current vector count
        try:
            info = index.info()
            current_count = getattr(info, 'vector_count', 0)
            print(f"📊 Current vectors in database: {current_count}")
        except:
            current_count = 0
        
        # Load data if database is empty
        if current_count == 0:
            print("📝 Loading your professional profile...")
            
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    profile_data = json.load(f)
            except FileNotFoundError:
                print(f"❌ {JSON_FILE} not found!")
                return None
            
            # Convert profile data to content chunks
            content_chunks = create_content_chunks(profile_data)
            
            if not content_chunks:
                print("❌ No content chunks created from profile data")
                return None
            
            # Prepare vectors from content chunks
            vectors = []
            for chunk in content_chunks:
                enriched_text = f"{chunk['title']}: {chunk['content']}"
                
                vectors.append((
                    chunk['id'],
                    enriched_text,
                    {
                        "title": chunk['title'],
                        "type": chunk['type'],
                        "content": chunk['content'],
                        "category": chunk.get('metadata', {}).get('category', ''),
                        "tags": chunk.get('metadata', {}).get('tags', [])
                    }
                ))
            
            # Upload vectors
            index.upsert(vectors=vectors)
            print(f"✅ Successfully uploaded {len(vectors)} content chunks!")
        
        return index
        
    except Exception as e:
        print(f"❌ Error setting up database: {str(e)}")
        return None

def query_vectors(index, query_text, top_k=3):
    """Query Upstash Vector for similar vectors"""
    try:
        results = index.query(
            data=query_text,
            top_k=top_k,
            include_metadata=True
        )
        return results
    except Exception as e:
        print(f"❌ Error querying vectors: {str(e)}")
        return None

def generate_response_with_groq(client, prompt, model=DEFAULT_MODEL):
    """Generate response using Groq"""
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an AI digital twin. Answer questions as if you are the person, speaking in first person about your background, skills, and experience."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return completion.choices[0].message.content.strip()
        
    except Exception as e:
        return f"❌ Error generating response: {str(e)}"

def rag_query(index, groq_client, question):
    """Perform RAG query using Upstash Vector + Groq"""
    try:
        # Step 1: Query vector database
        results = query_vectors(index, question, top_k=3)
        
        if not results or len(results) == 0:
            return "I don't have specific information about that topic."
        
        # Step 2: Extract relevant content
        print("\n🧠 Searching your professional profile...\n")
        
        top_docs = []
        for result in results:
            metadata = result.metadata or {}
            title = metadata.get('title', 'Information')
            content = metadata.get('content', '')
            score = result.score
            
            print(f"🔹 Found: {title} (Relevance: {score:.3f})")
            if content:
                top_docs.append(f"{title}: {content}")
        
        if not top_docs:
            return "I found some information but couldn't extract details."
        
        print(f"⚡ Generating personalized response...\n")
        
        # Step 3: Generate response with context
        context = "\n\n".join(top_docs)
        prompt = f"""Based on the following information about yourself, answer the question.
Speak in first person as if you are describing your own background.

Your Information:
{context}

Question: {question}

Provide a helpful, professional response:"""
        
        response = generate_response_with_groq(groq_client, prompt)
        return response
    
    except Exception as e:
        return f"❌ Error during query: {str(e)}"

def main():
    """Main application loop"""
    print("🤖 Your Digital Twin - AI Profile Assistant")
    print("=" * 50)
    print("🔗 Vector Storage: Upstash (built-in embeddings)")
    print(f"⚡ AI Inference: Groq ({DEFAULT_MODEL})")
    print("📋 Data Source: Your Professional Profile\n")
    
    # Setup clients
    groq_client = setup_groq_client()
    if not groq_client:
        return
    
    index = setup_vector_database()
    if not index:
        return
    
    print("✅ Your Digital Twin is ready!\n")
    
    # Interactive chat loop
    print("🤖 Chat with your AI Digital Twin!")
    print("Ask questions about your experience, skills, projects, or career goals.")
    print("Type 'exit' to quit.\n")
    
    print("💭 Try asking:")
    print("  - 'Tell me about your work experience'")
    print("  - 'What are your technical skills?'")
    print("  - 'Describe your career goals'")
    print()
    
    while True:
        question = input("You: ")
        if question.lower() in ["exit", "quit"]:
            print("👋 Thanks for chatting with your Digital Twin!")
            break
        
        if question.strip():
            answer = rag_query(index, groq_client, question)
            print(f"🤖 Digital Twin: {answer}\n")

if __name__ == "__main__":
    main()

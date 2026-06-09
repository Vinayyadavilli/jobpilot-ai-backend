import httpx
from app.core.config import settings


class AIService:

    def __init__(self):
        self.api_key = settings.AI_PROVIDER_API_KEY
        self.api_base = settings.AI_PROVIDER_API_BASE
        self.model = settings.AI_PROVIDER_MODEL

    async def get_chat_completion(self, system_prompt: str, user_prompt: str) -> str:
        """Call the universal OpenAI-compatible chat completions endpoint."""
        # Check if the API key is set to default placeholders
        if not self.api_key or self.api_key == "your-api-key-here" or self.api_key == "":
            return self._get_mock_enhanced_resume(user_prompt)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=45.0
                )
                response.raise_for_status()
                res_data = response.json()
                return res_data["choices"][0]["message"]["content"]
            except Exception as e:
                # If key fails or connection times out and we are in debug mode, fallback gracefully
                if settings.DEBUG:
                    return f"## [AI Mock Correction] (Actual API request failed: {str(e)})\n\n{self._get_mock_enhanced_resume(user_prompt)}"
                raise ValueError(f"AI Service Request failed: {str(e)}")

    async def enhance_resume(self, raw_text: str) -> str:
        """Analyze, format, and enhance raw resume text using the LLM."""
        system_prompt = (
            "You are a professional executive resume writer and career consultant. "
            "Your task is to take raw, unformatted, or poorly written resume text and rewrite/enhance it. "
            "Follow these rules strictly:\n"
            "1. Output the rewritten resume in clean, professional markdown format.\n"
            "2. Use headings (#, ##, ###) for sections like Summary, Experience, Education, and Skills.\n"
            "3. Optimize all bullet points using the STAR method (Situation, Task, Action, Result) with strong action verbs.\n"
            "4. Eliminate typos, grammatical issues, and repetitive phrasing.\n"
            "5. Keep the formatting uniform and clean.\n"
            "Do not output any introductory or concluding conversational text. Start directly with the markdown resume."
        )
        
        user_prompt = f"Here is the raw resume content to enhance:\n\n{raw_text}"
        
        return await self.get_chat_completion(system_prompt, user_prompt)

    def _get_mock_enhanced_resume(self, raw_text: str) -> str:
        """Provide a fallback mock enhanced resume when API keys are not supplied."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        candidate_name = "Candidate Name"
        if lines:
            candidate_name = lines[0]
            
        return (
            f"# {candidate_name} — Professional Resume\n\n"
            "## Summary\n"
            "Dynamic professional with a proven track record of optimizing workflows, "
            "leading cross-functional initiatives, and delivering scalable software engineering solutions.\n\n"
            "## Core Skills\n"
            "* **Languages & Frameworks:** Python, FastAPI, Node.js, React, Swift, SQL\n"
            "* **Tools & DevOps:** Docker, AWS (S3, EC2), Git, CI/CD, Alembic\n"
            "* **AI & ML Integration:** OpenAI API, Gemini, Groq, Llama\n\n"
            "## Professional Experience\n"
            "### Senior Systems Engineer | Tech Solutions Corp\n"
            "* Developed and optimized a universal LLM API wrapper in FastAPI, expanding LLM support (Gemini, Groq, Llama) and improving response performance by 25%.\n"
            "* Designed database indices and parsed complex tables, cutting search query latencies by 40%.\n"
            "* Standardized email notification background tasks using fastapi-mail, resolving delivery issues for over 10,000 active users.\n\n"
            "## Education\n"
            "### Bachelor of Science in Computer Science | Global Tech University\n"
            "* Graduated with Honors. Focused on Database Architectures and Intelligent Systems."
        )

import boto3
from botocore.exceptions import ClientError
import json
import os
from typing import List
from dotenv import load_dotenv
from app.models import JobListing, SearchCriteria, UserProfile

class BedrockAIService:
    def __init__(self):
        load_dotenv()
        # Initialize Bedrock client with credentials
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
            region_name="us-east-1"
        )
        
        # Initialize Bedrock agent client
        self.bedrock_agent = boto3.client(
            'bedrock-agent-runtime',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
            region_name="us-east-1"
        )
        
        # Agent configuration
        self.agent_id = os.getenv('BEDROCK_AGENT_ID')
        self.agent_alias_id = os.getenv('BEDROCK_AGENT_ALIAS_ID')

    def _build_filtering_prompt(self, jobs: List[JobListing], criteria: SearchCriteria) -> str:
        """
        Build a prompt for job filtering based on criteria
        """
        jobs_json = [job.dict() for job in jobs]
        criteria_json = criteria.dict()
        
        return f"""
        Please analyze these jobs and filter them based on the following criteria:
        Jobs: {json.dumps(jobs_json)}
        Criteria: {json.dumps(criteria_json)}
        Return only the jobs that best match the criteria.
        """

    def _parse_filtered_jobs(self, response: str, original_jobs: List[JobListing]) -> List[JobListing]:
        """
        Parse the AI response and match it with original job listings
        """
        try:
            filtered_jobs_data = json.loads(response)
            filtered_jobs = []
            for job_data in filtered_jobs_data:
                # Match with original job objects
                matching_job = next(
                    (job for job in original_jobs if job.id == job_data['id']), 
                    None
                )
                if matching_job:
                    filtered_jobs.append(matching_job)
            return filtered_jobs
        except json.JSONDecodeError:
            return []

    async def filter_relevant_jobs(self, jobs: List[JobListing], criteria: SearchCriteria) -> List[JobListing]:
        """
        Filter jobs using Bedrock's AI capabilities
        """
        try:
            prompt = self._build_filtering_prompt(jobs, criteria)
            response = self.bedrock_runtime.invoke_model(
                modelId="anthropic.claude-v2",
                body=json.dumps({
                    "prompt": prompt,
                    "max_tokens_to_sample": 2000,
                    "temperature": 0.5
                })
            )
            
            response_body = json.loads(response['body'].read())
            return self._parse_filtered_jobs(response_body['completion'], jobs)
            
        except Exception as e:
            print(f"Error in filter_relevant_jobs: {e}")
            return []

    async def analyze_job_fit(self, job: JobListing, user_profile: UserProfile) -> dict:
        """
        Analyze job fit using Bedrock agent
        """
        try:
            session_id = str(hash(f"{job.id}_{user_profile.id}"))
            
            prompt = f"""
            Analyze this job's fit for the user:
            Job: {json.dumps(job.dict())}
            User Profile: {json.dumps(user_profile.dict())}
            Provide a detailed analysis of the match including:
            1. Skills match percentage
            2. Experience level fit
            3. Salary range compatibility
            4. Location/remote work compatibility
            5. Overall fit score (0-100)
            """

            response = self.bedrock_agent.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=session_id,
                inputText=prompt
            )

            # Parse the response
            analysis = ''.join(
                chunk["bytes"].decode() 
                for event in response["completion"] 
                if "bytes" in event.get("chunk", {})
            )

            return json.loads(analysis)

        except Exception as e:
            print(f"Error in analyze_job_fit: {e}")
            return {
                "error": str(e),
                "overall_fit": 0,
                "details": "Failed to analyze job fit"
            }

    def _data_stream_generator(self, response):
        """
        Generator to yield data chunks from the response
        """
        for event in response.get("completion", []):
            chunk = event.get("chunk", {})
            if "bytes" in chunk:
                yield chunk["bytes"].decode()
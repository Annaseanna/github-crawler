from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import asyncio
from uuid import uuid4
from datetime import datetime

# Copy the crawler logic (you'll need to copy the crawler files)
from crawler_github.crawl_repo import crawl_repo
from db import github_collection

app = FastAPI(title="GitHub Crawler Service")

class CrawlRequest(BaseModel):
    url: str

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "github-crawler"}

@app.post("/crawl")
async def crawl_repository(req: CrawlRequest):
    """Crawl a GitHub repository"""
    repo_url = req.url
    
    # Check if already processed
    existing = github_collection.find_one({"repo_url": repo_url})
    if existing:
        return {
            "repo_url": repo_url,
            "job_id": existing.get("job_id", "unknown"),
            "status": "cached",
            "original_status": "finished",
        }
    
    # Generate job ID and start crawling
    job_id = uuid4().hex
    
    try:
        # Run crawler in background
        await asyncio.create_task(run_crawler_async(job_id, repo_url))
        
        return {
            "repo_url": repo_url,
            "job_id": job_id,
            "status": "completed"
        }
    except Exception as e:
        return {
            "repo_url": repo_url,
            "job_id": job_id,
            "status": "failed",
            "error": str(e)
        }

async def run_crawler_async(job_id: str, url: str):
    """Async wrapper for the crawler"""
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, crawl_repo, url)
    except Exception as exc:
        print(f"❌ Error during crawling: {exc}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

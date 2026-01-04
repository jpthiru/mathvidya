"""
S3 Knowledge Base Loader

Loads additional knowledge documents from S3 for the RAG chatbot.
Supports markdown and text files for easy content management.

Knowledge base structure in S3:
    s3://mathvidya-media-prod/knowledge-base/
        ├── faq/
        │   ├── getting-started.md
        │   ├── subscriptions.md
        │   └── exams.md
        ├── help/
        │   ├── technical-support.md
        │   └── browser-requirements.md
        └── policies/
            ├── refund-policy.md
            └── privacy-policy.md
"""

import os
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path
import hashlib
import json

import boto3
from botocore.exceptions import ClientError

from config.settings import settings

logger = logging.getLogger(__name__)

# S3 Configuration
S3_KNOWLEDGE_PREFIX = "knowledge-base/"
LOCAL_CACHE_DIR = Path(__file__).parent.parent / "data" / "knowledge_cache"


def get_s3_client():
    """Get configured S3 client."""
    return boto3.client(
        's3',
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
    )


def ensure_cache_dir():
    """Create local cache directory if it doesn't exist."""
    LOCAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def parse_markdown_document(content: str, source_path: str) -> List[Dict]:
    """
    Parse a markdown document into knowledge entries.

    Splits on H1 or H2 headers to create separate entries.
    Extracts keywords from content.
    """
    documents = []

    # Split on headers (# or ##)
    sections = re.split(r'^(#{1,2})\s+(.+)$', content, flags=re.MULTILINE)

    current_title = Path(source_path).stem.replace('-', ' ').title()
    current_content = []
    current_level = 0

    i = 0
    while i < len(sections):
        section = sections[i].strip()

        if section in ['#', '##']:
            # Save previous section
            if current_content:
                doc_content = '\n'.join(current_content).strip()
                if len(doc_content) > 50:  # Minimum content length
                    documents.append({
                        "title": current_title,
                        "content": doc_content,
                        "keywords": extract_keywords(doc_content),
                        "source": source_path,
                        "category": Path(source_path).parent.name
                    })

            # Start new section
            current_level = len(section)
            current_title = sections[i + 1].strip() if i + 1 < len(sections) else current_title
            current_content = []
            i += 2
        else:
            if section:
                current_content.append(section)
            i += 1

    # Save last section
    if current_content:
        doc_content = '\n'.join(current_content).strip()
        if len(doc_content) > 50:
            documents.append({
                "title": current_title,
                "content": doc_content,
                "keywords": extract_keywords(doc_content),
                "source": source_path,
                "category": Path(source_path).parent.name
            })

    # If no sections found, treat whole document as one entry
    if not documents and content.strip():
        documents.append({
            "title": current_title,
            "content": content.strip(),
            "keywords": extract_keywords(content),
            "source": source_path,
            "category": Path(source_path).parent.name
        })

    return documents


def extract_keywords(text: str) -> List[str]:
    """Extract potential keywords from text."""
    # Common words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'this', 'that', 'these', 'those', 'it', 'its', 'you', 'your', 'we',
        'our', 'they', 'their', 'i', 'me', 'my', 'he', 'she', 'him', 'her',
        'if', 'then', 'else', 'when', 'where', 'why', 'how', 'all', 'each',
        'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
        'not', 'only', 'same', 'so', 'than', 'too', 'very', 'just', 'also'
    }

    # Extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

    # Filter and count
    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1

    # Return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:10] if freq >= 2]


def load_documents_from_s3() -> List[Dict]:
    """
    Load all knowledge documents from S3.

    Returns:
        List of document dictionaries with title, content, keywords, source
    """
    documents = []
    ensure_cache_dir()

    try:
        s3 = get_s3_client()
        bucket = settings.S3_BUCKET

        # List all objects in knowledge-base prefix
        paginator = s3.get_paginator('list_objects_v2')

        for page in paginator.paginate(Bucket=bucket, Prefix=S3_KNOWLEDGE_PREFIX):
            for obj in page.get('Contents', []):
                key = obj['Key']

                # Only process markdown and text files
                if not (key.endswith('.md') or key.endswith('.txt')):
                    continue

                # Skip directory markers
                if key.endswith('/'):
                    continue

                try:
                    # Download file
                    response = s3.get_object(Bucket=bucket, Key=key)
                    content = response['Body'].read().decode('utf-8')

                    # Parse and add documents
                    parsed_docs = parse_markdown_document(content, key)
                    documents.extend(parsed_docs)

                    logger.info(f"Loaded {len(parsed_docs)} documents from {key}")

                except Exception as e:
                    logger.error(f"Failed to load {key}: {e}")
                    continue

        logger.info(f"Total documents loaded from S3: {len(documents)}")

    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            logger.warning(f"S3 bucket {settings.S3_BUCKET} not found")
        else:
            logger.error(f"S3 error: {e}")
    except Exception as e:
        logger.error(f"Failed to load documents from S3: {e}")

    return documents


def get_cached_documents() -> Optional[List[Dict]]:
    """Load documents from local cache if available."""
    cache_file = LOCAL_CACHE_DIR / "s3_documents.json"

    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('documents'):
                    logger.info(f"Loaded {len(data['documents'])} documents from cache")
                    return data['documents']
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")

    return None


def cache_documents(documents: List[Dict]):
    """Save documents to local cache."""
    ensure_cache_dir()
    cache_file = LOCAL_CACHE_DIR / "s3_documents.json"

    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'documents': documents,
                'count': len(documents)
            }, f, ensure_ascii=False, indent=2)
        logger.info(f"Cached {len(documents)} documents")
    except Exception as e:
        logger.warning(f"Failed to cache documents: {e}")


def refresh_knowledge_base() -> List[Dict]:
    """
    Refresh knowledge base from S3 and update cache.

    Call this periodically or when knowledge base updates.
    """
    documents = load_documents_from_s3()
    if documents:
        cache_documents(documents)
    return documents


def get_all_knowledge_documents() -> List[Dict]:
    """
    Get all knowledge documents, from cache or S3.

    Priority:
    1. Try loading from S3
    2. Fall back to cache if S3 fails
    3. Return empty list if both fail
    """
    # Try S3 first
    documents = load_documents_from_s3()

    if documents:
        cache_documents(documents)
        return documents

    # Fall back to cache
    cached = get_cached_documents()
    if cached:
        return cached

    return []


# ============================================
# Sample Knowledge Base Documents
# ============================================

SAMPLE_KNOWLEDGE_DOCS = """
# Sample Knowledge Base Structure

Create these files in S3 under `s3://mathvidya-media-prod/knowledge-base/`:

## faq/getting-started.md
```markdown
# Getting Started with Mathvidya

Welcome to Mathvidya! This guide will help you get started.

## Creating Your Account

1. Visit mathvidya.com
2. Click "Sign Up"
3. Enter your details
4. Verify your email

## Taking Your First Exam

Once registered, go to your dashboard and click "Start New Exam".
```

## faq/subscriptions.md
```markdown
# Subscription Plans

## Basic Plan
- 5 exams per month
- 48-hour evaluation

## Premium Plan
- 50 exams per month
- Unit-wise practice
- Leaderboard access

## Centum Plan
- Same-day evaluation
- Direct teacher access
```

## help/technical-support.md
```markdown
# Technical Support

## Browser Requirements
- Chrome, Firefox, Edge, or Safari
- JavaScript enabled
- Stable internet connection

## Common Issues

### Images Not Uploading
- Use JPEG or PNG format
- Keep file size under 5MB
- Check your internet connection

### Page Not Loading
- Clear browser cache
- Try incognito mode
- Update your browser
```
"""


def create_sample_knowledge_base():
    """
    Create sample knowledge base files in S3.

    Run this once to set up initial structure.
    """
    s3 = get_s3_client()
    bucket = settings.S3_BUCKET

    sample_files = {
        "knowledge-base/faq/getting-started.md": """# Getting Started with Mathvidya

Welcome to Mathvidya, your CBSE Mathematics practice platform!

## Creating Your Account

1. **Visit mathvidya.com** and click "Sign Up"
2. **Enter your details**: Name, email, class (X or XII)
3. **Verify your email**: Enter the 6-digit code sent to you
4. **Choose a plan**: Select the subscription that fits your needs
5. **Start practicing**: Take your first exam!

## Your Dashboard

Your dashboard shows:
- Recent exam scores
- Performance analytics
- Predicted board score
- Quick access to start new exams

## Pro Tips

- Use promo code MATHSTART for 14 days free
- Practice regularly for best results
- Focus on weak units identified in analytics
""",
        "knowledge-base/faq/subscriptions.md": """# Subscription Plans

## Basic Plan
Perfect for casual learners
- 5 exams per month
- Board exam pattern practice
- 48-hour teacher evaluation
- Email support

## Premium Plan (Most Popular!)
For serious students
- 50 exams per month
- Board exam + Unit-wise practice
- 48-hour evaluation
- Leaderboard access
- Monthly coaching session

## Centum Plan
For those aiming for 100%
- 50 exams per month
- All practice modes
- SAME-DAY evaluation
- Direct teacher WhatsApp access
- Priority support
""",
        "knowledge-base/help/technical-support.md": """# Technical Support

## Recommended Browsers
- Google Chrome (best experience)
- Mozilla Firefox
- Microsoft Edge
- Safari (Mac)

## Common Issues

### Images Not Uploading
- Use JPEG or PNG format only
- Keep file size under 5MB
- Ensure good lighting in photos
- Check internet connection stability

### Page Not Loading
- Refresh with Ctrl+F5
- Clear browser cache
- Try incognito/private mode
- Update browser to latest version

### Can't Login
- Check email address is correct
- Use "Forgot Password" to reset
- Check spam folder for emails
- Clear cookies and try again

## Contact Support
Email: support@mathvidya.com
Response time: Within 24 hours
"""
    }

    for key, content in sample_files.items():
        try:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType='text/markdown'
            )
            logger.info(f"Created {key}")
        except Exception as e:
            logger.error(f"Failed to create {key}: {e}")

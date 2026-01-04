#!/usr/bin/env python3
"""
Setup S3 Knowledge Base for Mathvidya Chatbot

This script creates the initial knowledge base structure in S3.
Run this once to set up the knowledge base, then add/update documents as needed.

Usage:
    # From backend directory:
    python scripts/setup_s3_knowledge_base.py

    # Dry run (show what would be created):
    python scripts/setup_s3_knowledge_base.py --dry-run

    # Custom bucket:
    python scripts/setup_s3_knowledge_base.py --bucket my-bucket-name
"""

import argparse
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from botocore.exceptions import ClientError

from config.settings import settings


# ============================================
# Knowledge Base Documents
# ============================================

KNOWLEDGE_DOCUMENTS = {
    # FAQ Documents
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

## First Exam Tips

- Start with a unit-wise practice to warm up
- Use MCQ-only mode for quick practice sessions
- Read questions carefully before answering
- Review your results and learn from mistakes

## Pro Tips

- Use promo code **MATHSTART** for 14 days free
- Practice regularly for best results
- Focus on weak units identified in analytics
- Take full board exams closer to your actual exam date
""",

    "knowledge-base/faq/subscriptions.md": """# Subscription Plans

Mathvidya offers flexible plans to suit every student's needs.

## Basic Plan
Perfect for casual learners who want to practice occasionally.

**Features:**
- 5 exams per month
- Board exam pattern practice
- 48-hour teacher evaluation
- Email support
- Performance analytics

**Best for:** Students who want occasional practice

## Premium Plan (Most Popular!)
For serious students who want comprehensive practice.

**Features:**
- 50 exams per month
- Board exam + Unit-wise practice
- 48-hour evaluation
- Leaderboard access
- Monthly coaching session
- Priority email support

**Best for:** Students preparing seriously for board exams

## Centum Plan
For those aiming for 100% marks.

**Features:**
- 50 exams per month
- All practice modes
- **SAME-DAY evaluation**
- Direct teacher WhatsApp access
- Personalized coaching sessions
- Highest priority support

**Best for:** Students who want the fastest feedback and personal attention

## Comparing Plans

| Feature | Basic | Premium | Centum |
|---------|-------|---------|--------|
| Exams/month | 5 | 50 | 50 |
| Unit-wise practice | No | Yes | Yes |
| Evaluation time | 48 hours | 48 hours | Same day |
| Leaderboard | No | Yes | Yes |
| Direct teacher access | No | No | Yes |

## Payment Options

- Monthly subscription
- Annual subscription (2 months free!)
- All major payment methods accepted
""",

    "knowledge-base/faq/exams.md": """# How Exams Work

Mathvidya provides flexible exam practice aligned with CBSE patterns.

## Exam Types

### Full Board Exam
Complete CBSE pattern simulation:
- 38 questions (Class XII)
- 80 marks total
- Mix of MCQ, VSA, and SA
- 3-hour time limit
- Best for final preparation

### Unit-wise Practice
Focus on specific chapters:
- Choose 1-5 units
- Questions from selected units only
- Great for targeted revision
- Identify weak areas

### MCQ-only Practice
Quick practice sessions:
- 20-30 MCQ questions
- Auto-evaluated instantly
- 30-45 minutes
- Perfect for concept testing

## Question Types

### MCQ (1 mark each)
- Multiple choice with 4 options
- Auto-evaluated immediately
- Results shown right after submission

### VSA - Very Short Answer (2 marks each)
- Write answers on paper
- Take photo and upload
- Teacher evaluates within SLA
- Detailed feedback provided

### SA - Short Answer (3 marks each)
- Write detailed solutions on paper
- Show all working steps
- Upload clear photos
- Teacher provides step-by-step feedback

## Taking an Exam

1. Go to Dashboard
2. Click "Start New Exam"
3. Select exam type
4. Choose units (if unit-wise)
5. Answer MCQs on screen
6. Write VSA/SA on paper
7. Upload answer sheet photos
8. Submit exam
9. View results!

## Tips for Success

- Read questions carefully
- Manage your time
- Show all working steps
- Write clearly and legibly
- Take clear photos in good lighting
""",

    "knowledge-base/faq/results.md": """# Results and Evaluation

## When Will I Get Results?

### MCQ Questions
**Instant!** Results shown immediately after submission.
- See correct answers
- View explanations
- Score breakdown by unit

### VSA/SA Questions (Teacher Evaluated)

| Plan | Evaluation Time |
|------|-----------------|
| Centum | Same working day |
| Premium | Within 48 working hours |
| Basic | Within 48 working hours |

**Working hours:** Monday-Saturday, 9 AM - 6 PM IST
Sundays and public holidays are excluded.

## Viewing Your Results

1. Go to Dashboard > "My Exams"
2. Find exams with "Completed" status
3. Click "View Results"
4. See question-wise breakdown

## Understanding Feedback

For each VSA/SA question, you'll see:
- Your uploaded answer image
- Teacher's annotations (ticks, crosses)
- Marks awarded per step
- Model answer for comparison
- Suggestions for improvement

## Score Calculation

- MCQ: 1 mark for correct, 0 for incorrect
- VSA: 0-2 marks based on completeness
- SA: 0-3 marks with step marking

## Predicted Board Score

Based on your performance, we predict your board exam score:
- Updated after each exam
- Considers all question types
- Shows confidence range
- Tracks improvement over time

## Notifications

You'll receive an email when:
- Results are ready
- New features are available
- Subscription is expiring
""",

    # Help Documents
    "knowledge-base/help/technical-support.md": """# Technical Support

## Common Issues and Solutions

### Page Not Loading
1. Refresh with Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
2. Clear browser cache and cookies
3. Try incognito/private mode
4. Update browser to latest version
5. Check internet connection

### Images Not Uploading
- Use JPEG or PNG format only
- Keep file size under 5MB
- Ensure good lighting in photos
- Check internet connection stability
- Try compressing the image

### Can't Login
- Verify email address is correct
- Use "Forgot Password" to reset
- Check spam folder for emails
- Clear cookies and try again
- Try a different browser

### Exam Not Submitting
- Don't close browser - wait for confirmation
- Check all required questions are answered
- Ensure stable internet connection
- Screenshot answers as backup
- Contact support if stuck

### Video/Math Not Displaying
- Enable JavaScript in browser
- Update to latest browser version
- Disable ad blockers temporarily
- Clear browser cache

## Browser Requirements

**Recommended:**
- Google Chrome (latest) - Best experience
- Mozilla Firefox (latest)
- Microsoft Edge (latest)
- Safari (latest) - Mac only

**Not Supported:**
- Internet Explorer
- Very old browser versions

## Device Requirements

- Smartphone, tablet, laptop, or desktop
- Minimum screen width: 320px
- Camera for uploading answer sheets
- Stable internet (3G or better)

## Contact Support

**Email:** support@mathvidya.com
**Response time:** Within 24 hours

Include in your email:
- Screenshot of the error
- Browser name and version
- Device type
- Steps to reproduce the issue
""",

    "knowledge-base/help/answer-upload-guide.md": """# Answer Sheet Upload Guide

## Writing Your Answers

### Paper Preparation
- Use clean white A4 paper
- Write with black or blue pen
- Leave margins on all sides
- Number your answers clearly

### Writing Tips
- Write legibly and neatly
- Show all working steps
- Box your final answers
- Use proper mathematical notation
- Leave space between questions

## Taking Photos

### Lighting
- Use natural daylight if possible
- Avoid shadows on the paper
- No flash directly on paper
- Ensure even lighting

### Camera Position
- Hold phone directly above paper
- Keep phone parallel to paper
- Capture entire page in frame
- Avoid tilted angles

### Quality Check
- Text should be clearly readable
- No blur or motion effects
- All content visible
- Good contrast

## Uploading

### Step by Step
1. Click "Upload Answer Sheet"
2. Select photo from gallery or take new
3. Preview the image
4. Confirm upload
5. Repeat for additional pages

### File Requirements
- Format: JPEG or PNG
- Max size: 5MB per image
- Resolution: At least 1000x1500 pixels
- Clear and readable

### Multiple Pages
- Upload pages in order
- Label pages if needed (Page 1/3, etc.)
- Ensure all pages are included

## Troubleshooting

### Upload Failing
- Check file size (under 5MB)
- Use JPEG/PNG format
- Check internet connection
- Try compressing image
- Refresh and retry

### Image Too Large
- Use phone's built-in compression
- Try online image compressors
- Reduce resolution slightly
- Crop unnecessary margins

### Poor Quality Warning
- Retake photo with better lighting
- Hold camera steadier
- Clean camera lens
- Move closer to paper
""",

    # Policy Documents
    "knowledge-base/policies/refund-policy.md": """# Refund and Cancellation Policy

## Free Trial

- No charge during 14-day trial period
- Cancel anytime before trial ends
- No payment information required for trial
- Full access to all features during trial

## Paid Subscriptions

### Cancellation
- Cancel anytime from account settings
- Access continues until current period ends
- No automatic renewal after cancellation
- No partial refunds for unused time

### Refund Eligibility

**Full Refund (within 7 days):**
- No exams taken on the account
- Technical issues preventing any use
- Accidental duplicate purchase

**Partial Refund (case by case):**
- Extended technical issues (>24 hours)
- Service unavailability
- Other exceptional circumstances

**Not Eligible:**
- Exams already taken
- Usage after 7 days
- Change of mind after use
- Promo code subscriptions (check terms)

## How to Request Refund

1. Email support@mathvidya.com
2. Subject: "Refund Request - [Your Email]"
3. Include:
   - Reason for refund
   - Transaction ID
   - Date of purchase

## Processing Time

- Refund review: 3-5 business days
- Amount credited: 5-10 business days to bank
- You'll receive email confirmation

## Contact

Questions about refunds?
Email: support@mathvidya.com

We aim to resolve all queries within 24 hours.
""",

    "knowledge-base/policies/privacy-summary.md": """# Privacy Summary

## What We Collect

- Account info (name, email, class)
- Exam answers and scores
- Performance analytics
- Device and browser info (for support)

## How We Use It

- Provide exam practice service
- Generate analytics and predictions
- Improve our platform
- Send important notifications

## What We Don't Do

- Sell your data to third parties
- Share personal info without consent
- Store payment card details
- Track you outside our platform

## Your Rights

- Access your data anytime
- Request data deletion
- Export your performance data
- Opt out of marketing emails

## Data Security

- Encrypted data transmission (HTTPS)
- Secure password storage
- Regular security audits
- Data stored in India (AWS Mumbai)

## Parent Access

- Parents can view child's performance
- Read-only access to scores and analytics
- Cannot take exams or modify data
- Child data protection compliant

## Contact

Privacy questions?
Email: support@mathvidya.com

Full privacy policy available on our website.
""",

    # CBSE Specific
    "knowledge-base/cbse/syllabus-class12.md": """# Class XII Mathematics Syllabus

Mathvidya covers the complete CBSE Class XII Mathematics syllabus.

## Unit-wise Breakdown

### Unit 1: Relations and Functions (8 marks)
- Types of Relations
- Types of Functions
- Composition of Functions
- Inverse of a Function
- Binary Operations

### Unit 2: Algebra (10 marks)
- Matrices
- Determinants

### Unit 3: Calculus (35 marks)
- Continuity and Differentiability
- Applications of Derivatives
- Integrals
- Applications of Integrals
- Differential Equations

### Unit 4: Vectors and 3D Geometry (14 marks)
- Vectors
- Three Dimensional Geometry

### Unit 5: Linear Programming (5 marks)
- Linear Programming Problems
- Graphical Method

### Unit 6: Probability (8 marks)
- Conditional Probability
- Bayes' Theorem
- Random Variables
- Probability Distributions

## Exam Pattern

**Total Marks:** 80 (Theory)
**Duration:** 3 hours

| Section | Questions | Marks |
|---------|-----------|-------|
| MCQ | 20 | 20 |
| VSA | 5 | 10 |
| SA | 6 | 18 |
| LA | 4 | 20 |
| Case Study | 3 | 12 |

## What Mathvidya Covers

Currently available:
- MCQ (1 mark) - All units
- VSA (2 marks) - All units
- SA (3 marks) - All units

Coming soon:
- LA (5 marks) - Long Answer
- Case Study (4 marks) - Application based

## Preparation Tips

1. **Master basics first** - Focus on NCERT
2. **Practice regularly** - Take exams weekly
3. **Review mistakes** - Learn from errors
4. **Time management** - Practice under timed conditions
5. **Unit-wise focus** - Target weak areas
""",

    "knowledge-base/cbse/marking-scheme.md": """# CBSE Marking Scheme

Mathvidya follows the official CBSE marking scheme.

## MCQ Marking

- Correct answer: 1 mark
- Incorrect answer: 0 marks
- No negative marking
- Only one correct option

## VSA Marking (2 marks)

Step marking applied:
- Complete correct answer: 2 marks
- Partially correct: 1 mark
- Only formula/approach: 0.5-1 mark
- Incorrect: 0 marks

## SA Marking (3 marks)

Detailed step marking:
- Each logical step carries marks
- Final answer carries 0.5-1 mark
- Working shown is important
- Alternative methods accepted

### Example SA Marking:
- Correct approach/formula: 0.5-1 mark
- Intermediate steps: 1-1.5 marks
- Final answer: 0.5-1 mark

## Important Notes

### What Gets Full Marks
- Complete solution with steps
- Correct final answer
- Proper mathematical notation
- Clear presentation

### What Loses Marks
- Missing steps
- Calculation errors
- Incorrect method
- Incomplete solution

### Partial Credit
- Correct approach, wrong answer: 50-70% marks
- Right formula, computational error: 70-80% marks
- Only final answer (no steps): 30-50% marks

## How Teachers Evaluate

1. Check approach/method used
2. Verify each step
3. Note any errors
4. Award step-wise marks
5. Provide feedback

## Our Evaluation Standards

- Same as CBSE board evaluation
- Experienced CBSE teachers
- Consistent marking
- Detailed feedback provided
"""
}


def create_knowledge_base(bucket_name: str, dry_run: bool = False):
    """Create knowledge base documents in S3."""

    if dry_run:
        print("=" * 60)
        print("DRY RUN - No files will be created")
        print("=" * 60)

    print(f"\nTarget bucket: {bucket_name}")
    print(f"Documents to create: {len(KNOWLEDGE_DOCUMENTS)}")
    print()

    if not dry_run:
        try:
            s3 = boto3.client(
                's3',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )

            # Verify bucket exists
            s3.head_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' exists and is accessible.\n")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"ERROR: Bucket '{bucket_name}' does not exist.")
            elif error_code == '403':
                print(f"ERROR: Access denied to bucket '{bucket_name}'.")
            else:
                print(f"ERROR: {e}")
            return False

    created = 0
    failed = 0

    for key, content in KNOWLEDGE_DOCUMENTS.items():
        print(f"{'[DRY RUN] ' if dry_run else ''}Creating: {key}")

        if dry_run:
            # Show preview of content
            preview = content[:100].replace('\n', ' ')
            print(f"  Preview: {preview}...")
            print(f"  Size: {len(content)} bytes")
            created += 1
        else:
            try:
                s3.put_object(
                    Bucket=bucket_name,
                    Key=key,
                    Body=content.encode('utf-8'),
                    ContentType='text/markdown; charset=utf-8'
                )
                print(f"  Created successfully ({len(content)} bytes)")
                created += 1
            except Exception as e:
                print(f"  FAILED: {e}")
                failed += 1

    print()
    print("=" * 60)
    print(f"Summary: {created} created, {failed} failed")
    if dry_run:
        print("\nTo actually create files, run without --dry-run")
    print("=" * 60)

    return failed == 0


def list_knowledge_base(bucket_name: str):
    """List existing knowledge base documents in S3."""

    try:
        s3 = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        print(f"\nListing knowledge base in: {bucket_name}")
        print("=" * 60)

        paginator = s3.get_paginator('list_objects_v2')
        total_files = 0
        total_size = 0

        for page in paginator.paginate(Bucket=bucket_name, Prefix='knowledge-base/'):
            for obj in page.get('Contents', []):
                key = obj['Key']
                size = obj['Size']
                modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M')

                if not key.endswith('/'):
                    print(f"  {key}")
                    print(f"    Size: {size} bytes, Modified: {modified}")
                    total_files += 1
                    total_size += size

        print("=" * 60)
        print(f"Total: {total_files} files, {total_size} bytes")

    except ClientError as e:
        print(f"ERROR: {e}")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Setup S3 Knowledge Base for Mathvidya Chatbot'
    )
    parser.add_argument(
        '--bucket',
        default=settings.S3_BUCKET,
        help=f'S3 bucket name (default: {settings.S3_BUCKET})'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without actually creating'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List existing knowledge base documents'
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("Mathvidya S3 Knowledge Base Setup")
    print("=" * 60)

    if args.list:
        success = list_knowledge_base(args.bucket)
    else:
        success = create_knowledge_base(args.bucket, args.dry_run)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

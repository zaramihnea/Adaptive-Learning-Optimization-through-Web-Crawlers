# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

### Project 16 - Adaptive Learning Optimization through Web Crawlers
Theme: Educational Technology and Web Information Retrieval
Tier B
Max: 80p
Difficulty: Hard

### Context and Motivation

Adaptive learning platforms require high-quality educational resources aligned with learner profiles, difficulty levels, and curriculum outcomes. Manual curation is expensive and difficult to scale.

### Research Problem

How can a web-crawling and NLP pipeline collect, filter, classify, and recommend educational resources while preserving quality, relevance, and traceability?

### Objective

Design and evaluate a crawler-based educational content pipeline that maps online resources to learner profiles or course learning outcomes.

### Task Description

The team must implement a crawler, document classifier, ranking component, and simple recommendation interface. Inputs include seed URLs, course topics, learner profiles, and content metadata. Outputs include ranked educational resources with labels, confidence scores, and explanation metadata.

### Three-Week Scope

Keep the implementation narrow and testable. The expected artifact is a crawler-based educational content pipeline that retrieves, filters, classifies, and recommends resources for a clearly specified learner profile. Define the input data, produced output, experimental scenarios, and success criteria before implementation starts.

### Baseline and Evaluation Plan

Compare against keyword search, manual curation, TF-IDF ranking, or a simple topic classifier. Use allowed web sources, open educational resources, cached pages, and a small labelled evaluation set created with clear annotation rules. Report precision@k, topic classification quality, duplication rate, crawling coverage, freshness, relevance, and human-review effort. Include at least one negative or failure-case experiment, not only the best-case result.

### Safety, Privacy, and Deployment Notes

Discuss robots.txt compliance, copyright, content quality, bias in recommendations, learner privacy, and transparency of generated suggestions. Keep final claims aligned with the evidence collected during the short project period; avoid presenting a course prototype as a production-ready or clinically validated system.

### Core Requirements

Respect robots.txt and rate limits; implement content extraction, deduplication, metadata storage, classification or topic modeling, ranking, and evaluation against a manually labeled validation set. Include bias, copyright, hallucination, and content-quality analysis.

### Deliverables

Crawler, NLP pipeline, labeled dataset subset, ranking report, reproducible experiment scripts, standard specification, IEEE-style paper.

### Assessment Focus

Correctness of crawling and parsing; classifier quality; ranking quality; reproducibility; ethical handling of educational data and copyright.

### Suggested Tools

Python, Scrapy, BeautifulSoup, trafilatura, scikit-learn, PyTorch, PostgreSQL, Elasticsearch/OpenSearch.

### Extensions

Retrieval-augmented summarization; multilingual content classification; learning-style adaptation; human-in-the-loop validation.


## Build & Run

```bash
# Install dependencies
# e.g. pip install -r requirements.txt | npm install | go mod tidy

# Run the project
# e.g. python main.py | npm start | go run .

# Run tests
# e.g. pytest | npm test | go test ./...

# Run a single test
# e.g. pytest tests/test_foo.py::test_bar
```

## Architecture

Look at pcd.pdf for student's parts. I am student 1 (Data & Infrastructure Lead) so i am responsible for Implement the web crawler (using tools like Scrapy or BeautifulSoup). Manage the metadata storage (e.g. PostgreSQL or Elasticsearch) and ensure compliance with robots.txt and rate limits.

### My key deliverables:
- Crawler code
- database schema
- crawling coverage report

## Key Conventions

<!-- Any non-obvious conventions specific to this codebase -->

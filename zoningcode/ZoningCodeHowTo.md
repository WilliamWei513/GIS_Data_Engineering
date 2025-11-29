# Sarasota Zoning Code Downloader

Automated script for downloading Sarasota Zoning Code PDF from Municode Library.

## Overview

This script provides automated downloading of Sarasota Zoning Code PDF documents through browser automation and network monitoring. It implements multiple download strategies with fallback mechanisms and includes anti-detection measures to reduce automation detection risk.

## Features

- Automated browser-based download via Selenium WebDriver
- Multiple download strategies with automatic fallback
- Network log monitoring for PDF URL capture via Chrome DevTools Protocol
- Transient tab detection and URL extraction
- Direct HTTP download fallback using captured URLs
- Anti-detection measures to minimize automation signatures

## Prerequisites

- Python 3.8 or higher
- Google Chrome browser installed
- ChromeDriver (automatically managed by webdriver-manager or manually installed)

## Installation

Install required dependencies:

```bash
pip install -r python_requirements.txt
```

## Usage

Execute the script:

```bash
python sarasota_municode_downloader.py
```

## Architecture

### Download Strategies

The script implements two primary strategies for locating download controls:

**Strategy A (Primary):**
- Access Downloads menu from navigation
- Select Zoning publication option
- Trigger download from modal interface

**Strategy B (Fallback):**
- Directly locate modal download interface
- Trigger download if primary strategy fails

### URL Capture Methods

The script employs multiple methods to capture the PDF download URL:

1. **Transient Tab Detection**: Monitors for new browser tabs opened during download initiation
2. **CDP Network Logs**: Captures PDF URLs from Chrome DevTools Protocol performance logs
3. **Request/Response Analysis**: Parses network events for PDF content type or file extensions

### Download Mechanisms

1. **Browser Native Download**: Primary method using Chrome's download functionality
2. **Direct HTTP Download**: Fallback using requests library with Selenium cookies when browser download fails

## Output

Downloaded PDF files are saved in the `./downloads/` directory (or custom directory specified during instantiation).
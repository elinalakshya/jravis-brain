# VA Bot - Multi-Platform Income Stream Automation

## Overview

VA Bot is a comprehensive automation system designed to manage multiple income streams across various platforms including Instagram, Printify, Meshy AI, Fiverr, YouTube, and others. The system operates in phases, with Phase 1 targeting 10 income streams managed by team members (Elina, Kael, and Riva). The bot handles automated posting, order fulfillment, earnings tracking, daily reporting, and API integrations across all platforms using a centralized credential management system.

The system is designed to scale from Phase 1 (₹2.5L-₹6L monthly target) through Phase 3 (global rollout of 30 streams), with automated email reporting, PDF generation for invoices/summaries, and approval workflows for the business owner.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Framework
- **Flask Web Application**: Main application server with health checks, reporting endpoints, and approval workflows
- **Background Scheduler**: APScheduler for automated daily/weekly tasks running at specified IST times
- **Connector Pattern**: Modular connector system where each platform has its own connector class with standardized interfaces
- **State Management**: JSON-based persistence for tracking sent reports, approval states, and connector status

### Authentication & Credential Management
- **Centralized Login System**: Single master credentials (MASTER_USER/MASTER_PASS) used across all platforms
- **Team Credential Router**: Maps platform ownership to team member credentials (Elina, Kael, Riva) based on stream assignments
- **Environment-Based Secrets**: All sensitive data stored in Replit Secrets including email credentials, API keys, and platform passwords

### Platform Integration Architecture
- **Unified Connector Interface**: All platforms implement run_job_once() method for standardized execution
- **Multi-Platform Support**: Instagram (Meta Graph API), Printify (REST API), Meshy AI, YouTube (Google API), Fiverr, CadCrowd, Etsy, Shopify
- **Browser Automation**: Playwright integration for platforms without APIs, with headless browser support
- **API Key Generation**: Automated system to generate and manage API keys where programmatically possible

### Reporting & Communication System
- **Daily Report Generation**: Automated PDF creation with encrypted summaries (password: "MY OG") and open invoice PDFs
- **Email Automation**: SMTP-based email system using team Gmail accounts with app passwords
- **Approval Workflow**: Boss approval system with auto-resume after timeout periods
- **Multi-Recipient Support**: Configurable email distribution to multiple team members

### Data Processing & Storage
- **JSON Data Persistence**: Platform earnings, connector states, and configuration stored in JSON files
- **PDF Generation**: pdfkit with wkhtmltopdf for invoice and report creation
- **State Tracking**: Duplicate prevention and execution history maintenance
- **Earnings Aggregation**: Cross-platform revenue tracking and monthly target monitoring

### Error Handling & Monitoring
- **Alert System**: Email-based error notifications with pause functionality when issues detected
- **Graceful Degradation**: Connectors continue operating even if individual platforms fail
- **Comprehensive Logging**: Structured logging across all components with IST timestamps
- **Health Monitoring**: Dedicated health endpoints for system status checking

### Security Architecture
- **Application Lock**: PIN-based access control for web interface with cookie-based session management
- **PDF Encryption**: Sensitive reports encrypted with business-specific passwords
- **Secret Management**: Environment variable based credential storage with no hardcoded secrets
- **Input Validation**: Request validation and sanitization across all endpoints

### Deployment & Scalability
- **Cloud-Ready Design**: Configured for deployment on Replit, Render, and Google Cloud Platform
- **Containerization Support**: Docker configuration for consistent deployment environments
- **Horizontal Scaling**: Modular connector design allows independent scaling of platform integrations
- **Multi-Environment Support**: Separate configurations for development, staging, and production

## External Dependencies

### Email Services
- **Gmail SMTP**: Primary email delivery using team Gmail accounts with app-specific passwords
- **Email Recipients**: Multi-recipient support for team notifications and boss reporting

### Cloud Platforms & APIs
- **Google Cloud Platform**: OAuth2, YouTube Analytics API, Gmail API integration
- **Meta/Facebook APIs**: Instagram Graph API for automated reel posting and analytics
- **Printify API**: Print-on-demand product management and order processing
- **Meshy AI API**: 3D model marketplace integration for asset uploads and sales tracking

### E-commerce Platforms
- **Etsy API**: Digital product store management and order fulfillment
- **Shopify API**: Online store management and inventory synchronization
- **Amazon KDP**: Book publishing platform integration for automated uploads

### Freelance Marketplaces
- **Fiverr API**: Gig management and order processing automation
- **Upwork API**: Project bidding and client communication automation
- **CadCrowd API**: CAD design project management and submission automation

### Development & Automation Tools
- **Playwright**: Browser automation for platforms lacking APIs
- **APScheduler**: Background task scheduling and cron-like job execution
- **pdfkit/wkhtmltopdf**: Server-side PDF generation for invoices and reports
- **PyPDF2**: PDF manipulation and encryption for sensitive documents

### Monitoring & Communication
- **SMTP Services**: Email delivery infrastructure for notifications and reports
- **Webhook Endpoints**: External service integration for real-time event processing
- **Health Check Services**: Uptime monitoring and system status reporting
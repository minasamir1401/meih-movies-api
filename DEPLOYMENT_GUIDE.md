# Deployment Guide

## Backend Deployment (Render.com)

### Prerequisites
1. Create a Render account at https://render.com
2. Connect your GitHub repository to Render

### Deployment Steps

1. **Create a new Web Service on Render**
   - Go to your Render Dashboard
   - Click "New" → "Web Service"
   - Connect your repository

2. **Configure the service**
   - Name: `meih-movies-api`
   - Environment: `Python 3`
   - Build Command: `bash setup_render.sh`
   - Start Command: `bash start_render.sh`

3. **Add Environment Variables**
   - `PYTHON_VERSION`: `3.10.0`
   - `SCRAPER_API_KEY`: Your ScraperAPI key (if using)
   - `NETWORK_NODES`: Comma-separated list of network nodes

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

### Manual Deployment (Alternative)

If you prefer to deploy manually:

```bash
# Clone the repository
git clone <your-repo-url>
cd <repo-name>/backend

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install-deps
playwright install chromium

# Start the application
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## Frontend Deployment (Vercel.com)

### Prerequisites
1. Create a Vercel account at https://vercel.com
2. Install Vercel CLI: `npm install -g vercel`

### Deployment Steps

1. **Navigate to the frontend directory**
   ```bash
   cd meih-netflix-clone
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Build the project**
   ```bash
   npm run build
   ```

4. **Deploy to Vercel**
   ```bash
   vercel --prod
   ```

### Environment Variables for Frontend

Set these in your Vercel project settings:

- `REACT_APP_API_URL`: The URL of your deployed backend API
- `REACT_APP_BASE_URL`: The base URL of your frontend application

## Docker Deployment (Alternative)

You can also deploy using Docker:

### Backend Docker Deployment

```bash
# Build the Docker image
docker build -t meih-movies-api ./backend

# Run the container
docker run -p 10000:10000 meih-movies-api
```

### Frontend Docker Deployment

```bash
# Build the Docker image
docker build -t meih-netflix-clone ./meih-netflix-clone

# Run the container
docker run -p 3000:3000 meih-netflix-clone
```

## CI/CD Pipeline

### GitHub Actions (Recommended)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Render and Vercel

on:
  push:
    branches: [ main, master ]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to Render
      run: |
        curl -X POST https://api.render.com/v1/services/<service-id>/deploys \
          -H "Authorization: Bearer ${{ secrets.RENDER_API_KEY }}" \
          -H "Content-Type: application/json"

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: |
        cd meih-netflix-clone
        npm install
        
    - name: Deploy to Vercel
      run: |
        cd meih-netflix-clone
        npx vercel --token ${{ secrets.VERCEL_TOKEN }} --prod
```

## Monitoring and Maintenance

### Health Checks

The backend exposes health check endpoints:
- `/health` - Basic health check
- `/system-logs` - Application logs

### Performance Monitoring

Consider adding:
- Application Performance Monitoring (APM) tools like New Relic or DataDog
- Error tracking with Sentry
- Log aggregation with ELK stack

### Scaling

For high traffic:
- Increase worker count in Gunicorn
- Add Redis for caching
- Use a CDN for static assets
- Consider database connection pooling

## Troubleshooting

### Common Issues

1. **Playwright not found**
   - Ensure `playwright install-deps` and `playwright install chromium` are run during deployment

2. **Timeout errors**
   - Increase timeout values in scraper configuration
   - Check network connectivity

3. **CORS issues**
   - Verify CORS middleware configuration in `main.py`

4. **Rate limiting**
   - Adjust rate limiting settings in `main.py`

### Logs and Debugging

Check logs through:
- Render Dashboard → Service → Logs
- Vercel Dashboard → Project → Logs
- Application logs via `/system-logs` endpoint

## Security Considerations

1. **API Keys**
   - Store sensitive keys in environment variables
   - Rotate keys regularly

2. **Rate Limiting**
   - Current implementation limits to 20 requests/minute/IP
   - Adjust as needed for your use case

3. **Input Validation**
   - All API endpoints validate input parameters
   - Regular updates to prevent injection attacks

4. **HTTPS**
   - Render automatically provides HTTPS
   - Ensure all external requests use HTTPS

## Updates and Maintenance

1. **Regular Updates**
   - Update dependencies periodically
   - Monitor for security vulnerabilities

2. **Backup Strategy**
   - Database backups (if using persistent storage)
   - Configuration backups

3. **Version Control**
   - Maintain separate branches for development and production
   - Use tags for releases
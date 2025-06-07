# LangChain Tavily Agent Chat

A chat interface for interacting with a LangChain agent powered by Claude and Tavily search.

## Project Structure

```
├── backend/          # FastAPI backend
├── src/             # React frontend
├── Dockerfile       # Backend container configuration
├── requirements.txt # Python dependencies
└── package.json     # Node.js dependencies
```

## Local Development

### Backend
1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Create .env file
cp .env.example .env
# Add your API keys
ANTHROPIC_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

3. Run the backend:
```bash
cd backend
python main.py
```

### Frontend
1. Install Node.js dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

## Deployment

### Backend Deployment

#### Using Docker
1. Build the Docker image:
```bash
docker build -t langchain-tavily-agent .
```

2. Run the container:
```bash
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_key_here \
  -e TAVILY_API_KEY=your_key_here \
  langchain-tavily-agent
```

#### Cloud Platforms
The backend can be deployed to:
- Heroku
- DigitalOcean App Platform
- Google Cloud Run
- AWS Elastic Beanstalk

Make sure to:
1. Set the required environment variables
2. Configure the production URL in the frontend
3. Set up CORS for your frontend domain

### Frontend Deployment

1. Build the production version:
```bash
npm run build
```

2. Deploy the `build` directory to:
- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages

Remember to:
1. Update the backend API URL in production
2. Configure environment variables
3. Set up custom domains if needed

## Environment Variables

### Backend
- `ANTHROPIC_API_KEY`: Your Claude API key
- `TAVILY_API_KEY`: Your Tavily Search API key

### Frontend
- `REACT_APP_API_URL`: Backend API URL (defaults to http://localhost:8000 in development) 
# OpenAI API Proxy Server

A lightweight HTTP proxy server for the OpenAI Chat Completions API built in Go using only the standard library. This allows you to swap out the OpenAI API URL in your applications without needing to change your code or manually specify environment variables.

## Features

- **Drop-in replacement**: Uses the same API structure as OpenAI's `/v1/chat/completions` endpoint
- **Standard library only**: No external dependencies
- **Comprehensive testing**: Full test suite with mocks and benchmarks
- **Error handling**: Proper error propagation from OpenAI API
- **Health check**: Built-in health endpoint for monitoring
- **Environment-based configuration**: Configure via environment variables

## Quick Start

### Prerequisites

- Go 1.24.4 or later
- OpenAI API key

### Installation & Running

1. **Clone and navigate to the proxy directory:**
   ```bash
   cd proxy
   ```

2. **Set your OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

3. **Run the server:**
   ```bash
   go run main.go
   ```

4. **The server will start on port 8080 by default:**
   ```
   Starting OpenAI proxy server on port 8080
   Chat completions endpoint: http://localhost:8080/v1/chat/completions
   Health check endpoint: http://localhost:8080/health
   ```

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `PORT`: Server port (optional, defaults to 8080)

## Usage

### Using with curl

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "Hello, how are you?"
      }
    ],
    "temperature": 0.7
  }'
```

### Using with existing OpenAI clients

Simply change your base URL from `https://api.openai.com` to `http://localhost:8080`:

**Python (openai library):**
```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:8080",
    api_key="not-needed-but-required-by-client"  # The proxy handles the real API key
)

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)
```

**JavaScript (node.js):**
```javascript
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'http://localhost:8080',
  apiKey: 'not-needed-but-required-by-client'
});

const response = await openai.chat.completions.create({
  model: 'gpt-3.5-turbo',
  messages: [{ role: 'user', content: 'Hello!' }],
});
```

## API Reference

### POST /v1/chat/completions

Proxies chat completion requests to OpenAI API.

**Request Body:**
```json
{
  "model": "gpt-3.5-turbo",
  "messages": [
    {
      "role": "user", 
      "content": "Your message here"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 150,
  "top_p": 1.0
}
```

**Response:**
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-3.5-turbo",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'm doing well, thank you for asking. How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 20,
    "total_tokens": 32
  }
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Testing

Run the comprehensive test suite:

```bash
go test -v
```

Run benchmarks:

```bash
go test -bench=.
```

Run tests with coverage:

```bash
go test -cover
```

## Architecture

The proxy server consists of:

1. **OpenAI Client Interface**: Allows for easy testing with mock implementations
2. **Real OpenAI Client**: Handles actual API communication with OpenAI
3. **Proxy Server**: HTTP server that validates requests and forwards them
4. **Comprehensive Test Suite**: Unit tests, integration tests, and benchmarks

### Key Components

- `OpenAIClient` interface: Defines the contract for OpenAI API communication
- `RealOpenAIClient`: Production implementation that calls OpenAI API
- `MockOpenAIClient`: Test implementation for unit testing
- `ProxyServer`: HTTP server with request validation and error handling

## Error Handling

The proxy server handles various error scenarios:

- **Invalid HTTP methods**: Returns 405 Method Not Allowed
- **Invalid JSON**: Returns 400 Bad Request
- **Missing required fields**: Returns 400 Bad Request with descriptive message
- **OpenAI API errors**: Forwards the original error from OpenAI API
- **Network issues**: Returns 500 Internal Server Error

## Security Considerations

- The proxy server requires the OpenAI API key to be set as an environment variable
- Client applications don't need to include the API key in their requests
- All requests are forwarded directly to OpenAI without modification
- No request/response data is logged or stored

## Deployment

### Docker

Build and run:

```bash
docker build -t openai-proxy .
docker run -e OPENAI_API_KEY=your-key -p 8080:8080 openai-proxy
```

### Production Deployment

For production use, consider:

1. Setting up proper logging
2. Adding request rate limiting
3. Implementing authentication if needed
4. Using HTTPS with TLS certificates
5. Setting up monitoring and alerting
6. Running behind a reverse proxy (nginx, traefik, etc.)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is provided as-is for educational and development purposes. 
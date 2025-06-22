package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// Mock OpenAI client for testing
type MockOpenAIClient struct {
	shouldError bool
	response    *ChatCompletionResponse
	error       error
}

func (m *MockOpenAIClient) CreateChatCompletion(req ChatCompletionRequest) (*ChatCompletionResponse, error) {
	if m.shouldError {
		return nil, m.error
	}
	return m.response, nil
}

// Test helpers
func createTestChatCompletionRequest() ChatCompletionRequest {
	temp := 0.7
	return ChatCompletionRequest{
		Model: "gpt-3.5-turbo",
		Messages: []Message{
			{Role: "user", Content: "Hello, how are you?"},
		},
		Temperature: &temp,
	}
}

func createTestChatCompletionResponse() *ChatCompletionResponse {
	return &ChatCompletionResponse{
		ID:      "chatcmpl-test123",
		Object:  "chat.completion",
		Created: time.Now().Unix(),
		Model:   "gpt-3.5-turbo",
		Choices: []Choice{
			{
				Index: 0,
				Message: Message{
					Role:    "assistant",
					Content: "Hello! I'm doing well, thank you for asking. How can I help you today?",
				},
				FinishReason: "stop",
			},
		},
		Usage: Usage{
			PromptTokens:     12,
			CompletionTokens: 20,
			TotalTokens:      32,
		},
	}
}

func TestProxyServer_HandleChatCompletions_Success(t *testing.T) {
	// Create mock client
	mockClient := &MockOpenAIClient{
		shouldError: false,
		response:    createTestChatCompletionResponse(),
	}

	// Create server
	server := NewProxyServer(mockClient)

	// Create test request
	reqBody := createTestChatCompletionRequest()
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		t.Fatalf("Failed to marshal request: %v", err)
	}

	// Create HTTP request
	req := httptest.NewRequest("POST", "/v1/chat/completions", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")

	// Create response recorder
	w := httptest.NewRecorder()

	// Handle request
	server.handleChatCompletions(w, req)

	// Check status code
	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	// Check content type
	expectedContentType := "application/json"
	if contentType := w.Header().Get("Content-Type"); contentType != expectedContentType {
		t.Errorf("Expected content type %s, got %s", expectedContentType, contentType)
	}

	// Parse response
	var response ChatCompletionResponse
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	// Validate response
	expectedResponse := createTestChatCompletionResponse()
	if response.ID != expectedResponse.ID {
		t.Errorf("Expected ID %s, got %s", expectedResponse.ID, response.ID)
	}
	if response.Model != expectedResponse.Model {
		t.Errorf("Expected model %s, got %s", expectedResponse.Model, response.Model)
	}
	if len(response.Choices) != 1 {
		t.Errorf("Expected 1 choice, got %d", len(response.Choices))
	}
	if response.Choices[0].Message.Content != expectedResponse.Choices[0].Message.Content {
		t.Errorf("Expected content %s, got %s", expectedResponse.Choices[0].Message.Content, response.Choices[0].Message.Content)
	}
}

func TestProxyServer_HandleChatCompletions_InvalidMethod(t *testing.T) {
	server := NewProxyServer(&MockOpenAIClient{})

	req := httptest.NewRequest("GET", "/v1/chat/completions", nil)
	w := httptest.NewRecorder()

	server.handleChatCompletions(w, req)

	if w.Code != http.StatusMethodNotAllowed {
		t.Errorf("Expected status code %d, got %d", http.StatusMethodNotAllowed, w.Code)
	}
}

func TestProxyServer_HandleChatCompletions_InvalidJSON(t *testing.T) {
	server := NewProxyServer(&MockOpenAIClient{})

	req := httptest.NewRequest("POST", "/v1/chat/completions", bytes.NewBufferString("invalid json"))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.handleChatCompletions(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d, got %d", http.StatusBadRequest, w.Code)
	}
}

func TestProxyServer_HandleChatCompletions_MissingModel(t *testing.T) {
	server := NewProxyServer(&MockOpenAIClient{})

	reqBody := ChatCompletionRequest{
		Messages: []Message{
			{Role: "user", Content: "Hello"},
		},
	}
	jsonData, _ := json.Marshal(reqBody)

	req := httptest.NewRequest("POST", "/v1/chat/completions", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.handleChatCompletions(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d, got %d", http.StatusBadRequest, w.Code)
	}
}

func TestProxyServer_HandleChatCompletions_MissingMessages(t *testing.T) {
	server := NewProxyServer(&MockOpenAIClient{})

	reqBody := ChatCompletionRequest{
		Model: "gpt-3.5-turbo",
	}
	jsonData, _ := json.Marshal(reqBody)

	req := httptest.NewRequest("POST", "/v1/chat/completions", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.handleChatCompletions(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status code %d, got %d", http.StatusBadRequest, w.Code)
	}
}

func TestProxyServer_HandleChatCompletions_OpenAIError(t *testing.T) {
	mockClient := &MockOpenAIClient{
		shouldError: true,
		error:       fmt.Errorf("OpenAI API error: rate limit exceeded"),
	}

	server := NewProxyServer(mockClient)

	reqBody := createTestChatCompletionRequest()
	jsonData, _ := json.Marshal(reqBody)

	req := httptest.NewRequest("POST", "/v1/chat/completions", bytes.NewBuffer(jsonData))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()

	server.handleChatCompletions(w, req)

	if w.Code != http.StatusInternalServerError {
		t.Errorf("Expected status code %d, got %d", http.StatusInternalServerError, w.Code)
	}
}

func TestProxyServer_HandleHealth(t *testing.T) {
	server := NewProxyServer(&MockOpenAIClient{})

	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	server.handleHealth(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status code %d, got %d", http.StatusOK, w.Code)
	}

	var response map[string]string
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if response["status"] != "healthy" {
		t.Errorf("Expected status 'healthy', got %s", response["status"])
	}
}

// Test the real OpenAI client structure (without making actual API calls)
func TestRealOpenAIClient_New(t *testing.T) {
	apiKey := "test-api-key"
	client := NewRealOpenAIClient(apiKey)

	if client.APIKey != apiKey {
		t.Errorf("Expected API key %s, got %s", apiKey, client.APIKey)
	}

	expectedBaseURL := "https://api.openai.com/v1"
	if client.BaseURL != expectedBaseURL {
		t.Errorf("Expected base URL %s, got %s", expectedBaseURL, client.BaseURL)
	}
}

// Test JSON marshaling/unmarshaling of our data structures
func TestChatCompletionRequest_JSONMarshaling(t *testing.T) {
	temp := 0.7
	maxTokens := 150
	original := ChatCompletionRequest{
		Model: "gpt-3.5-turbo",
		Messages: []Message{
			{Role: "system", Content: "You are a helpful assistant."},
			{Role: "user", Content: "Hello!"},
		},
		Temperature: &temp,
		MaxTokens:   &maxTokens,
	}

	// Marshal to JSON
	jsonData, err := json.Marshal(original)
	if err != nil {
		t.Fatalf("Failed to marshal to JSON: %v", err)
	}

	// Unmarshal back
	var unmarshaled ChatCompletionRequest
	if err := json.Unmarshal(jsonData, &unmarshaled); err != nil {
		t.Fatalf("Failed to unmarshal from JSON: %v", err)
	}

	// Compare
	if unmarshaled.Model != original.Model {
		t.Errorf("Model mismatch: expected %s, got %s", original.Model, unmarshaled.Model)
	}
	if len(unmarshaled.Messages) != len(original.Messages) {
		t.Errorf("Messages length mismatch: expected %d, got %d", len(original.Messages), len(unmarshaled.Messages))
	}
	if *unmarshaled.Temperature != *original.Temperature {
		t.Errorf("Temperature mismatch: expected %f, got %f", *original.Temperature, *unmarshaled.Temperature)
	}
	if *unmarshaled.MaxTokens != *original.MaxTokens {
		t.Errorf("MaxTokens mismatch: expected %d, got %d", *original.MaxTokens, *unmarshaled.MaxTokens)
	}
}

func TestChatCompletionResponse_JSONMarshaling(t *testing.T) {
	original := createTestChatCompletionResponse()

	// Marshal to JSON
	jsonData, err := json.Marshal(original)
	if err != nil {
		t.Fatalf("Failed to marshal to JSON: %v", err)
	}

	// Unmarshal back
	var unmarshaled ChatCompletionResponse
	if err := json.Unmarshal(jsonData, &unmarshaled); err != nil {
		t.Fatalf("Failed to unmarshal from JSON: %v", err)
	}

	// Compare key fields
	if unmarshaled.ID != original.ID {
		t.Errorf("ID mismatch: expected %s, got %s", original.ID, unmarshaled.ID)
	}
	if unmarshaled.Model != original.Model {
		t.Errorf("Model mismatch: expected %s, got %s", original.Model, unmarshaled.Model)
	}
	if len(unmarshaled.Choices) != len(original.Choices) {
		t.Errorf("Choices length mismatch: expected %d, got %d", len(original.Choices), len(unmarshaled.Choices))
	}
	if unmarshaled.Usage.TotalTokens != original.Usage.TotalTokens {
		t.Errorf("Total tokens mismatch: expected %d, got %d", original.Usage.TotalTokens, unmarshaled.Usage.TotalTokens)
	}
}

// Benchmark tests
func BenchmarkProxyServer_HandleChatCompletions(b *testing.B) {
	mockClient := &MockOpenAIClient{
		shouldError: false,
		response:    createTestChatCompletionResponse(),
	}
	server := NewProxyServer(mockClient)

	reqBody := createTestChatCompletionRequest()
	jsonData, _ := json.Marshal(reqBody)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		req := httptest.NewRequest("POST", "/v1/chat/completions", bytes.NewBuffer(jsonData))
		req.Header.Set("Content-Type", "application/json")
		w := httptest.NewRecorder()

		server.handleChatCompletions(w, req)
	}
}

// Integration-style test (still using mock, but testing the full HTTP flow)
func TestProxyServer_Integration(t *testing.T) {
	// Create mock client
	mockClient := &MockOpenAIClient{
		shouldError: false,
		response:    createTestChatCompletionResponse(),
	}

	// Create server with handlers
	server := NewProxyServer(mockClient)
	mux := http.NewServeMux()
	mux.HandleFunc("/v1/chat/completions", server.handleChatCompletions)
	mux.HandleFunc("/health", server.handleHealth)

	// Create test server
	ts := httptest.NewServer(mux)
	defer ts.Close()

	// Test health endpoint
	healthResp, err := http.Get(ts.URL + "/health")
	if err != nil {
		t.Fatalf("Failed to call health endpoint: %v", err)
	}
	defer healthResp.Body.Close()

	if healthResp.StatusCode != http.StatusOK {
		t.Errorf("Health check failed with status: %d", healthResp.StatusCode)
	}

	// Test chat completions endpoint
	reqBody := createTestChatCompletionRequest()
	jsonData, _ := json.Marshal(reqBody)

	chatResp, err := http.Post(ts.URL+"/v1/chat/completions", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		t.Fatalf("Failed to call chat completions endpoint: %v", err)
	}
	defer chatResp.Body.Close()

	if chatResp.StatusCode != http.StatusOK {
		t.Errorf("Chat completions failed with status: %d", chatResp.StatusCode)
	}

	// Parse and validate response
	var response ChatCompletionResponse
	if err := json.NewDecoder(chatResp.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode chat completions response: %v", err)
	}

	if len(response.Choices) == 0 {
		t.Error("Expected at least one choice in response")
	}
} 
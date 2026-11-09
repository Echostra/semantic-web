package app

import (
	"edinburgh-guide/data"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func resetStores() {
	DataStore = nil
	IntroStore = ""
	TimelineStore = nil
}

func TestGetIntroHandler(t *testing.T) {
	resetStores()
	defer resetStores()

	// Pre-fill the cache to mock the data and avoid hitting the live Wikipedia API
	expectedIntro := "Edinburgh is a beautiful historic city for testing."
	IntroStore = expectedIntro

	req := httptest.NewRequest(http.MethodGet, "/api/intro", nil)
	rr := httptest.NewRecorder()

	GetIntroHandler(rr, req)

	// 1. Check HTTP status code
	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	// 2. Check response headers
	if contentType := rr.Header().Get("Content-Type"); contentType != "application/json" {
		t.Errorf("handler returned wrong content type: got %v want %v", contentType, "application/json")
	}

	// 3. Decode and verify the JSON payload
	var response map[string]string
	if err := json.NewDecoder(rr.Body).Decode(&response); err != nil {
		t.Fatalf("failed to decode JSON response: %v", err)
	}

	if response["text"] != expectedIntro {
		t.Errorf("handler returned unexpected text: got %v want %v", response["text"], expectedIntro)
	}
}

func TestGetSightsHandler(t *testing.T) {
	resetStores()
	defer resetStores()

	mockSights := []data.Sight{
		{
			Name:        "Edinburgh Castle",
			Description: "A historic castle",
			WikiLink:    "https://en.wikipedia.org/wiki/Edinburgh_Castle",
			ImageUrl:    "http://example.com/castle.jpg",
		},
	}
	DataStore = mockSights

	req := httptest.NewRequest(http.MethodGet, "/api/sights", nil)
	rr := httptest.NewRecorder()

	GetSightsHandler(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	var response []data.Sight
	if err := json.NewDecoder(rr.Body).Decode(&response); err != nil {
		t.Fatalf("failed to decode JSON response: %v", err)
	}

	if len(response) != 1 {
		t.Fatalf("expected 1 sight, got %d", len(response))
	}

	if response[0].Name != mockSights[0].Name {
		t.Errorf("expected sight name %q, got %q", mockSights[0].Name, response[0].Name)
	}
}

func TestGetTimelineHandler(t *testing.T) {
	resetStores()
	defer resetStores()

	mockEvents := []data.TimelineEvent{
		{Year: "1130", Title: "Holyrood Abbey", Desc: "Founded by David I"},
		{Year: "1999", Title: "Scottish Parliament", Desc: "Reconvened"},
	}
	TimelineStore = mockEvents

	req := httptest.NewRequest(http.MethodGet, "/api/timeline", nil)
	rr := httptest.NewRecorder()

	GetTimelineHandler(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	var response []data.TimelineEvent
	if err := json.NewDecoder(rr.Body).Decode(&response); err != nil {
		t.Fatalf("failed to decode JSON response: %v", err)
	}

	if len(response) != 2 {
		t.Fatalf("expected 2 timeline events, got %d", len(response))
	}

	if response[1].Year != "1999" {
		t.Errorf("expected second event year to be 1999, got %q", response[1].Year)
	}
}

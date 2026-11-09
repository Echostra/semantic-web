package data

import (
	"testing"
)

func TestFetchCityIntro(t *testing.T) {
	// testing.Short() allows to skip slow network tests by running: go test -short
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	intro, err := FetchCityIntro()
	if err != nil {
		t.Fatalf("FetchCityIntro failed: %v", err)
	}

	if intro == "" {
		t.Error("expected a non-empty introduction string")
	}

	// No test for exact text because Wikipedia can be edited,
	// but we expect the text to be reasonably long.
	if len(intro) < 50 {
		t.Errorf("expected a longer introduction, got: %q", intro)
	}
}

func TestFetchEdinburghSights(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	sights, err := FetchEdinburghSights()
	if err != nil {
		t.Fatalf("FetchEdinburghSights failed: %v", err)
	}

	if len(sights) == 0 {
		t.Fatal("expected to find sights, got 0")
	}

	// Test the duplicate filtering logic by ensuring names are unique
	seen := make(map[string]bool)
	for _, sight := range sights {
		if sight.Name == "" {
			t.Error("found a sight with an empty name")
		}
		if seen[sight.Name] {
			t.Errorf("duplicate sight found: %s", sight.Name)
		}
		seen[sight.Name] = true
	}
}

func TestFetchEdinburghTimeline(t *testing.T) {
	if testing.Short() {
		t.Skip("skipping integration test in short mode")
	}

	events, err := FetchEdinburghTimeline()
	if err != nil {
		t.Fatalf("FetchEdinburghTimeline failed: %v", err)
	}

	if len(events) == 0 {
		t.Fatal("expected to find timeline events, got 0")
	}

	// Ensure the filter is actually working
	for _, event := range events {
		if event.Title == "Canal Museum" {
			t.Error("found Canal Museum in results, but it should have been filtered out")
		}
		if event.Year == "" {
			t.Errorf("event %q has no year", event.Title)
		}
	}
}

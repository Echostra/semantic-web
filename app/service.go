package app

import (
	"edinburgh-guide/data"
	"encoding/json"
	"fmt"
	"net/http"
)

var DataStore []data.Sight
var IntroStore string
var TimelineStore []data.TimelineEvent

// GetSightsHandler handles SPARQL data
func GetSightsHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if len(DataStore) == 0 {
		sights, err := data.FetchEdinburghSights()
		if err != nil {
			fmt.Println("backend error:", err)
			http.Error(w, `{"error": "Failed to fetch semantic data"}`, http.StatusInternalServerError)
			return
		}
		DataStore = sights
	}
	json.NewEncoder(w).Encode(DataStore)
}

// GetIntroHandler handles wikipedia API data
func GetIntroHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if IntroStore == "" {
		intro, err := data.FetchCityIntro()
		if err != nil {
			fmt.Println("WIKI ERROR:", err)
			IntroStore = "Edinburgh is the historic capital of Scotland."
		} else {
			IntroStore = intro
		}
	}
	json.NewEncoder(w).Encode(map[string]string{"text": IntroStore})
}

func GetTimelineHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	if len(TimelineStore) == 0 {
		events, err := data.FetchEdinburghTimeline()
		if err != nil {
			fmt.Println("TIMELINE ERROR:", err)
			http.Error(w, `{"error": "Failed to fetch timeline"}`, http.StatusInternalServerError)
			return
		}
		TimelineStore = events
	}
	json.NewEncoder(w).Encode(TimelineStore)
}

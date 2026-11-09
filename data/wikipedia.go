package data

import (
	"encoding/json"
	"net/http"
)

type WikiResponse struct {
	Query struct {
		Pages map[string]struct {
			Extract string `json:"extract"`
		} `json:"pages"`
	} `json:"query"`
}

// FetchCityIntro uses the MediaWiki Action API
func FetchCityIntro() (string, error) {
	endpoint := "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro&titles=Edinburgh&format=json&explaintext=1"

	// Custom request instead of using http.Get
	req, err := http.NewRequest("GET", endpoint, nil)
	if err != nil {
		return "", err
	}

	// Wikipedia requires a custom User-Agent, otherwise it blocks the request returning HTML instead of JSON
	req.Header.Set("User-Agent", "EdinburghGuideApp/2.0 (StudentProject)")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	var wikiData WikiResponse
	if err := json.NewDecoder(resp.Body).Decode(&wikiData); err != nil {
		return "", err
	}

	// Extract the first page's text
	for _, page := range wikiData.Query.Pages {
		return page.Extract, nil
	}

	return "Welcome to Edinburgh.", nil
}

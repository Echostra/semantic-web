package data

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
)

type Sight struct {
	Name        string `json:"name"`
	Description string `json:"description"`
	WikiLink    string `json:"wikiLink"`
	ImageUrl    string `json:"imageUrl"`
}

type TimelineEvent struct {
	Year  string `json:"year"`
	Title string `json:"title"`
	Desc  string `json:"desc"`
}

type SparqlResponse struct {
	Results struct {
		Bindings []map[string]struct {
			Value string `json:"value"`
		} `json:"bindings"`
	} `json:"results"`
}

func FetchEdinburghSights() ([]Sight, error) {
	query := `
	SELECT DISTINCT ?itemLabel ?desc ?wikiUrl ?pic WHERE {
	  VALUES ?location { wd:Q23436 wd:Q204940 }
	  ?item wdt:P131 ?location; 
	        wdt:P31 ?type;
	        wdt:P18 ?pic.
	  
	  VALUES ?type { wd:Q23413 wd:Q33506 wd:Q4989906 wd:Q1981273 wd:Q16970 }
	  
	  OPTIONAL { ?item schema:description ?desc. FILTER(LANG(?desc) = "en") }
	  OPTIONAL { ?wikiUrl schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> . }
	  
	  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
	} LIMIT 100`

	encodedQuery := url.QueryEscape(query)
	endpoint := fmt.Sprintf("https://query.wikidata.org/sparql?query=%s", encodedQuery)

	req, err := http.NewRequest("GET", endpoint, nil)
	if err != nil {
		return nil, err
	}

	req.Header.Set("User-Agent", "EdinburghGuideApp/3.0 (student@example.com)")
	req.Header.Set("Accept", "application/sparql-results+json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("wikidata returned status %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var sparqlData SparqlResponse
	if err := json.NewDecoder(resp.Body).Decode(&sparqlData); err != nil {
		return nil, err
	}

	var sights []Sight
	seen := make(map[string]bool) // Used to prevent duplicate sights with different images

	for _, binding := range sparqlData.Results.Bindings {
		name := ""
		if val, ok := binding["itemLabel"]; ok {
			name = val.Value
		}

		if seen[name] || name == "" {
			continue
		}
		seen[name] = true

		desc := ""
		if val, ok := binding["desc"]; ok {
			desc = val.Value
		}

		wiki := ""
		if val, ok := binding["wikiUrl"]; ok {
			wiki = val.Value
		}

		pic := ""
		if val, ok := binding["pic"]; ok {
			pic = val.Value
		}

		sights = append(sights, Sight{
			Name:        name,
			Description: desc,
			WikiLink:    wiki,
			ImageUrl:    pic,
		})

		if len(sights) >= 20 {
			break
		}
	}

	return sights, nil
}

func FetchEdinburghTimeline() ([]TimelineEvent, error) {
	query := `
	SELECT DISTINCT ?year ?itemLabel ?desc WHERE {
	  VALUES ?location { wd:Q23436 wd:Q204940 }
	  ?item wdt:P131 ?location;
	        wdt:P31 ?type;
	        wdt:P571 ?date.
	  
	  VALUES ?type { wd:Q23413 wd:Q16970 wd:Q33506 wd:Q3918 wd:Q4989906 wd:Q1981273 }
	  
	  BIND(YEAR(?date) AS ?year)
	  FILTER(?year > 1000 && ?year <= 2024)
	  
	  OPTIONAL { ?item schema:description ?desc. FILTER(LANG(?desc) = "en") }
	  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
	}
	ORDER BY ?year
	LIMIT 100`

	encodedQuery := url.QueryEscape(query)
	endpoint := fmt.Sprintf("https://query.wikidata.org/sparql?query=%s", encodedQuery)

	req, err := http.NewRequest("GET", endpoint, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("User-Agent", "EdinburghGuideApp/3.0 (student@example.com)")
	req.Header.Set("Accept", "application/sparql-results+json")

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("wikidata timeline error %d: %s", resp.StatusCode, string(bodyBytes))
	}

	var sparqlData SparqlResponse
	if err := json.NewDecoder(resp.Body).Decode(&sparqlData); err != nil {
		return nil, err
	}

	var events []TimelineEvent
	seenEvents := make(map[string]bool)

	for _, binding := range sparqlData.Results.Bindings {
		title := ""
		if val, ok := binding["itemLabel"]; ok {
			title = val.Value
		}

		if seenEvents[title] || title == "" || title == "Canal Museum" {
			continue
		}
		seenEvents[title] = true

		year := ""
		if val, ok := binding["year"]; ok {
			year = val.Value
		}

		desc := ""
		if val, ok := binding["desc"]; ok {
			desc = val.Value
		}

		events = append(events, TimelineEvent{
			Year:  year,
			Title: title,
			Desc:  desc,
		})

		if len(events) >= 10 {
			break
		}
	}
	return events, nil
}

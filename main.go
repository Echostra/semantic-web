package main

import (
	"edinburgh-guide/app"
	"log"
	"net/http"
)

func main() {
	http.HandleFunc("/api/sights", app.GetSightsHandler)
	http.HandleFunc("/api/intro", app.GetIntroHandler)
	http.HandleFunc("/api/timeline", app.GetTimelineHandler)

	fs := http.FileServer(http.Dir("./static"))
	http.Handle("/", fs)

	log.Println("Server started on http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}

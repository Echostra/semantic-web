document.addEventListener("DOMContentLoaded", () => {
    // 1. Fetch intro text and handle read from wikipedia API
    fetch('/api/intro')
        .then(res => res.json())
        .then(data => {
            const fullText = data.text;
            const shortText = fullText.length > 600 ? fullText.substring(0, 600) + "..." : fullText;

            const introText = document.getElementById('intro-text');
            const readMoreBtn = document.getElementById('read-more-btn');

            introText.innerText = shortText;

            // Only show button if text is actually long enough
            if (fullText.length > 600) {
                readMoreBtn.classList.remove('hidden');

                readMoreBtn.addEventListener('click', () => {
                    if (readMoreBtn.innerText === "Read more") {
                        introText.innerText = fullText;
                        readMoreBtn.innerText = "Read less";
                    } else {
                        introText.innerText = shortText;
                        readMoreBtn.innerText = "Read more";
                    }
                });
            }
        })
        .catch(err => console.error("Intro fetch error:", err));

    // 2. Fetch timeline from wikidata API
    fetch('/api/timeline')
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('timeline-container');
            container.innerHTML = '';

            data.forEach(event => {
                const item = document.createElement('div');
                item.className = 'timeline-item';
                item.innerHTML = `
                    <div class="timeline-dot"></div>
                    <div class="timeline-content">
                        <h3>${event.year}</h3>
                        <p><strong>${event.title}:</strong> ${event.desc || "Historic establishment founded in Edinburgh."}</p>
                    </div>
                `;
                container.appendChild(item);
            });
        })
        .catch(err => console.error("Timeline error:", err));

    // 3. Fetch sights from wikidata SPARQL API
    fetch('/api/sights')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('sights-container');
            container.innerHTML = '';

            data.forEach(sight => {
                const card = document.createElement('div');
                card.className = 'card';

                // Use dynamic image if available, else use placeholder
                const imgSrc = sight.imageUrl ? sight.imageUrl : "placeholder_castle.png";

                card.innerHTML = `
                    <img src="${imgSrc}" alt="${sight.name}">
                    <div class="card-content">
                        <h2>${sight.name}</h2>
                        <p>${sight.description || "Historical sight in Edinburgh."}</p>
                    </div>
                `;

                card.addEventListener('click', () => openModal(sight));
                container.appendChild(card);
            });
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            document.getElementById('sights-container').innerHTML = '<p class="accent">Failed to load data.</p>';
        });

    // 4. Modal Base Logic
    const modal = document.getElementById('sight-modal');
    const closeBtn = document.querySelector('.close-btn');

    closeBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
    });
});

// 5. Open modal function and dynamic wikipedia links
function openModal(sight) {
    document.getElementById('modal-title').innerText = sight.name;
    document.getElementById('modal-desc').innerText = sight.description || "No description available.";

    const wikiBtn = document.getElementById('modal-link');

    if (sight.wikiLink) {
        // Direct link exists in Wikidata
        wikiBtn.href = sight.wikiLink;
        wikiBtn.innerText = "Read more on Wikipedia";
    } else {
        const searchQuery = encodeURIComponent(sight.name + " Edinburgh");
        wikiBtn.href = `https://en.wikipedia.org/wiki/Special:Search?search=${searchQuery}`;
        wikiBtn.innerText = "Search on Wikipedia";
    }

    wikiBtn.classList.remove('hidden');
    document.getElementById('sight-modal').classList.remove('hidden');
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { openModal };
}
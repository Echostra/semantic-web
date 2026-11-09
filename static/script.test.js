/**
 * @jest-environment jsdom
 */

const { openModal } = require('./main.js');

// Helper to wait for all fetch() Promises to resolve in the test environment
const flushPromises = () => new Promise(process.nextTick);

describe('Edinburgh Guide Frontend Logic', () => {

    // 1. Recreate the bare minimum HTML structure before every single test
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="intro-text"></div>
            <button id="read-more-btn" class="hidden">Read more</button>
            <div id="timeline-container"></div>
            <div id="sights-container"></div>
            
            <div id="sight-modal" class="hidden">
                <button class="close-btn">X</button>
                <h2 id="modal-title"></h2>
                <p id="modal-desc"></p>
                <a id="modal-link" class="hidden" href=""></a>
            </div>
        `;

        // Reset the mock fetch before each test
        global.fetch = jest.fn();
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    test('openModal sets exact wikiLink when provided', () => {
        const mockSight = {
            name: "Edinburgh Castle",
            description: "A famous castle.",
            wikiLink: "https://en.wikipedia.org/wiki/Edinburgh_Castle"
        };

        openModal(mockSight);

        expect(document.getElementById('modal-title').innerText).toBe("Edinburgh Castle");
        expect(document.getElementById('modal-desc').innerText).toBe("A famous castle.");

        const link = document.getElementById('modal-link');
        expect(link.href).toBe("https://en.wikipedia.org/wiki/Edinburgh_Castle");
        expect(link.innerText).toBe("Read more on Wikipedia");
        expect(link.classList.contains('hidden')).toBe(false);
        expect(document.getElementById('sight-modal').classList.contains('hidden')).toBe(false);
    });

    test('openModal generates search link when wikiLink is missing', () => {
        const mockSight = {
            name: "Secret Alley",
            description: null // Testing the fallback description
        };

        openModal(mockSight);

        expect(document.getElementById('modal-desc').innerText).toBe("No description available.");

        const link = document.getElementById('modal-link');
        expect(link.href).toContain("Special:Search?search=Secret%20Alley%20Edinburgh");
        expect(link.innerText).toBe("Search on Wikipedia");
    });

    test('intro text hides read-more button if under 600 characters', async () => {
        const shortText = "This is a very short intro.";

        global.fetch.mockResolvedValueOnce({
            json: jest.fn().mockResolvedValueOnce({ text: shortText })
        });

        // Trigger the DOMContentLoaded event manually
        document.dispatchEvent(new Event('DOMContentLoaded'));
        await flushPromises();

        expect(document.getElementById('intro-text').innerText).toBe(shortText);
        expect(document.getElementById('read-more-btn').classList.contains('hidden')).toBe(true);
    });

    test('sights fetch creates cards with fallback images', async () => {
        const mockSights = [
            { name: "Sight 1", description: "Desc 1", imageUrl: "real.jpg" },
            { name: "Sight 2" } // Missing image and description
        ];

        // Only care about mocking the sights endpoint for this test,
        global.fetch.mockImplementation((url) => {
            if (url === '/api/sights') return Promise.resolve({ json: () => Promise.resolve(mockSights) });
            return Promise.resolve({ json: () => Promise.resolve([]) });
        });

        document.dispatchEvent(new Event('DOMContentLoaded'));
        await flushPromises();

        const cards = document.querySelectorAll('.card');
        expect(cards.length).toBe(2);

        // Check first card has real image
        expect(cards[0].querySelector('img').src).toContain("real.jpg");

        // Check second card uses fallback image and description
        expect(cards[1].querySelector('img').src).toContain("placeholder_castle.png");
        expect(cards[1].querySelector('p').innerText).toBe("Historical sight in Edinburgh.");
    });

    test('sights fetch handles server errors gracefully', async () => {
        global.fetch.mockImplementation((url) => {
            if (url === '/api/sights') return Promise.reject(new Error("Network Error"));
            return Promise.resolve({ json: () => Promise.resolve([]) });
        });

        document.dispatchEvent(new Event('DOMContentLoaded'));
        await flushPromises();

        const container = document.getElementById('sights-container');
        expect(container.innerHTML).toContain("Failed to load data.");
    });

    test('modal closes when close button is clicked', () => {
        openModal({ name: "Test" });
        const modal = document.getElementById('sight-modal');
        expect(modal.classList.contains('hidden')).toBe(false);

        // Simulate script attaching the event listener
        document.dispatchEvent(new Event('DOMContentLoaded'));

        // Click close button
        const closeBtn = document.querySelector('.close-btn');
        closeBtn.click();

        expect(modal.classList.contains('hidden')).toBe(true);
    });
});
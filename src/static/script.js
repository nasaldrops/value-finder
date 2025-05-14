document.addEventListener("DOMContentLoaded", () => {
    const searchForm = document.getElementById("property-search-form");
    const resultsContent = document.getElementById("results-content");
    const loadingIndicator = document.getElementById("loading-indicator");
    const analyzeButton = document.getElementById("analyzeButton");

    searchForm.addEventListener("submit", async (event) => {
        event.preventDefault();
        resultsContent.innerHTML = "<p>Starting analysis...</p>";
        loadingIndicator.style.display = "block";
        analyzeButton.disabled = true;

        const formData = new FormData(searchForm);
        const searchParams = {
            email: formData.get("email"),
            location: formData.get("location"),
            propertyType: formData.get("propertyType"),
            minPrice: formData.get("minPrice"),
            maxPrice: formData.get("maxPrice"),
            minBeds: formData.get("minBeds"),
            maxBeds: formData.get("maxBeds"),
            keywords: formData.get("keywords"),
        };

        try {
            const response = await fetch("/api/analyze", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(searchParams),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ message: `HTTP error! status: ${response.status}` }));
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            resultsContent.innerHTML = `<h3>${data.message}</h3>`;
            if (data.results && data.results.length > 0) {
                const ul = document.createElement("ul");
                data.results.forEach(property => {
                    const li = document.createElement("li");
                    li.innerHTML = `<strong><a href="${property.url}" target="_blank">${property.title}</a></strong> - ${property.price}<br>${property.description}`;
                    ul.appendChild(li);
                });
                resultsContent.appendChild(ul);
            } else if (!data.message && !(data.results && data.results.length > 0)) {
                resultsContent.innerHTML = "<p>No properties found matching your criteria, or an error occurred.</p>";
            }

        } catch (error) {
            console.error("Error during analysis:", error);
            resultsContent.innerHTML = `<p>An error occurred: ${error.message}. Please try again.</p>`;
        } finally {
            loadingIndicator.style.display = "none";
            analyzeButton.disabled = false;
        }
    });
});

document.getElementById('query-form').addEventListener('submit', async function(event) {
    event.preventDefault();
    const query = document.getElementById('query-input').value;
    const outputElement = document.getElementById('response-output');

    outputElement.textContent = 'Processing...';

    try {
        const response = await fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        outputElement.textContent = ''; // Clear the "Processing..." message

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                break;
            }
            const chunk = decoder.decode(value, { stream: true });
            outputElement.textContent += chunk;
        }

    } catch (error) {
        outputElement.textContent = `Error: ${error.message}`;
    }
});

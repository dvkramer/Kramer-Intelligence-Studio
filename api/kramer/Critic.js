import Gemini from './Gemini.js';

class Critic {
    async critique(query, task, result) {
        console.log("KRAMER Critic: Critiquing task:", task);
        console.log("KRAMER Critic: Result:", result);
        const prompt = `The user's original query was: "${query}".
The task was: "${task.description}".
The result of the task was: "${result}".

Does the result successfully complete the task and help answer the user's query?
Return a JSON object with "status" ("success" or "failure") and "justification".`;

        const gemini = new Gemini();
        try {
            let response = await gemini.generateText(prompt);
            console.log("KRAMER Critic: Gemini response:", response);
            // Clean the response by removing markdown backticks and the "json" language specifier
            response = response.replace(/```json/g, '').replace(/```/g, '');
            const critique = JSON.parse(response);
            console.log("KRAMER Critic: Parsed critique:", critique);
            return critique;
        } catch (error) {
            console.error("KRAMER Critic: Error parsing critique from Gemini:", error);
            // Return a default critique or throw the error
            return { status: "failure", justification: "Could not parse critique from Gemini." };
        }
    }
}

export default Critic;

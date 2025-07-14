import Gemini from './Gemini.js';

class Planner {
    async generatePlan(query, chatHistory) {
        console.log("KRAMER Planner: Generating plan for query:", query);
        const prompt = `Based on the user's query and the chat history, create a plan to answer it. The plan should be a list of tasks with dependencies.
User Query: ${query}
Chat History:
${JSON.stringify(chatHistory, null, 2)}

Return a JSON object with a "plan" key, which is an array of tasks. Each task should have "id", "description", and "dependencies".`;

        const gemini = new Gemini();
        try {
            const chat = await gemini.startChat(chatHistory);
            const result = await chat.sendMessage(prompt);
            const response = await result.response;
            let text = response.text();
            console.log("KRAMER Planner: Gemini response:", text);
            // Clean the response by removing markdown backticks and the "json" language specifier
            text = text.replace(/```json/g, '').replace(/```/g, '');
            const plan = JSON.parse(text);
            console.log("KRAMER Planner: Parsed plan:", plan);
            return plan;
        } catch (error) {
            console.error("KRAMER Planner: Error parsing plan from Gemini:", error);
            // Return a default plan or throw the error
            return { plan: [] };
        }
    }
}

export default Planner;

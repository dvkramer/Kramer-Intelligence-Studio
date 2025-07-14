import Gemini from './Gemini.js';

class Planner {
    async generatePlan(query) {
        console.log("KRAMER Planner: Generating plan for query:", query);
        const prompt = `Based on the user's query, create a plan to answer it. The plan should be a list of tasks with dependencies.
User Query: ${query}

Return a JSON object with a "plan" key, which is an array of tasks. Each task should have "id", "description", and "dependencies".`;

        const gemini = new Gemini();
        try {
            let response = await gemini.generateText(prompt);
            console.log("KRAMER Planner: Gemini response:", response);
            // Clean the response by removing markdown backticks and the "json" language specifier
            response = response.replace(/```json/g, '').replace(/```/g, '');
            const plan = JSON.parse(response);
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

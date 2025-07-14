import Gemini from './Gemini.js';

class Executor {
    async executeTask(task, dependencyResults, history) {
        console.log("KRAMER Executor: Executing task:", task);
        console.log("KRAMER Executor: Dependencies:", dependencyResults);
        const prompt = `You are a task executor. Complete the following task.
Task: ${task.description}
Dependencies: ${JSON.stringify(dependencyResults, null, 2)}
Result:`;

        const gemini = new Gemini();
        const result = await gemini.generateText(prompt, history, (task.tool === "google_search"));
        console.log("KRAMER Executor: Gemini result:", result);
        return result;
    }
}

export default Executor;

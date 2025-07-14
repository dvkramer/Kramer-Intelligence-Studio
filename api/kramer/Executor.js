import Gemini from './Gemini.js';

class Executor {
    async executeTask(task, dependencies) {
        console.log("KRAMER Executor: Executing task:", task);
        console.log("KRAMER Executor: Dependencies:", dependencies);
        const prompt = `Complete the following task: ${task.description}.
You have access to the following information from previous tasks:
${JSON.stringify(dependencies, null, 2)}

Provide a direct answer to the task.`;

        const gemini = new Gemini();
        const result = await gemini.generateText(prompt, [], true); // Use Google Search
        console.log("KRAMER Executor: Gemini result:", result);
        return result;
    }
}

export default Executor;

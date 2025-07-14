import Gemini from './Gemini.js';

class Synthesizer {
    async synthesize(query, history, results) {
        console.log("KRAMER Synthesizer: Synthesizing results for query:", query);
        console.log("KRAMER Synthesizer: Results:", results);
        const prompt = `The user's original query was: "${query}".
We have completed the following tasks and have the following results:
${JSON.stringify(results, null, 2)}

Synthesize these results into a single, cohesive answer for the user.`;

        const gemini = new Gemini();
        const result = await gemini.generateText(prompt, history);
        console.log("KRAMER Synthesizer: Gemini result:", result);
        return result;
    }
}

export default Synthesizer;

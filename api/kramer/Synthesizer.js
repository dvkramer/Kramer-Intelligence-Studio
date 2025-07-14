import Gemini from './Gemini.js';

class Synthesizer {
    async synthesize(query, results, chatHistory) {
        console.log("KRAMER Synthesizer: Synthesizing results for query:", query);
        console.log("KRAMER Synthesizer: Results:", results);
        const prompt = `The user's original query was: "${query}".
We have completed the following tasks and have the following results:
${JSON.stringify(results, null, 2)}

Synthesize these results into a single, cohesive answer for the user.
Chat History:
${JSON.stringify(chatHistory, null, 2)}`;

        const gemini = new Gemini();
        const chat = await gemini.startChat(chatHistory);
        const result = await chat.sendMessage(prompt);
        const response = await result.response;
        const text = response.text();
        console.log("KRAMER Synthesizer: Gemini result:", text);
        return text;
    }
}

export default Synthesizer;

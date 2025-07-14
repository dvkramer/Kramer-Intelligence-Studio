import { GoogleGenerativeAI } from '@google/generative-ai';

const MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite-preview-06-17",
];

class Gemini {
    constructor() {
        this.genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    }

    async generateText(prompt, history = [], useGoogleSearch = false) {
        let currentModelIndex = 0;

        while (true) {
            const modelName = MODELS[currentModelIndex];
            console.log(`KRAMER Gemini: Attempting to use model: ${modelName}`);

            try {
                const model = this.genAI.getGenerativeModel({ model: modelName });

                const generationConfig = {
                    temperature: 0.7,
                    topK: 1,
                    topP: 1,
                    maxOutputTokens: 2048,
                };

                const tools = useGoogleSearch ? [{ "googleSearch": {} }] : [];

                if (history.length > 1) {
                    const chat = model.startChat({
                        history,
                        generationConfig,
                        tools
                    });
                    const result = await chat.sendMessage(prompt);
                    const response = await result.response;
                    return response.text();

                } else {
                    const result = await model.generateContent({
                        contents: [{ role: "user", parts: [{ text: prompt }] }],
                        generationConfig,
                        tools,
                    });
                    const response = await result.response;
                    return response.text();
                }

            } catch (error) {
                if (error.status === 429) {
                    console.warn(`KRAMER Gemini: Model ${modelName} is rate-limited. Trying next model.`);
                    currentModelIndex = (currentModelIndex + 1) % MODELS.length;
                    if (currentModelIndex === 0) {
                        console.log("KRAMER Gemini: All models are rate-limited. Waiting 10 seconds to retry.");
                        await new Promise(resolve => setTimeout(resolve, 10000));
                    }
                } else {
                    console.error("KRAMER Gemini: Error generating text:", error);
                    throw error;
                }
            }
        }
    }
}

export default Gemini;

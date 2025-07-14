import Orchestrator from './kramer/Orchestrator.js';

export default async function handler(req, res) {
    console.log("KRAMER API handler started.");
    // --- Security/CORS Headers ---
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }
    if (req.method !== 'POST') {
        res.setHeader('Allow', ['POST']);
        return res.status(405).json({ error: `Method ${req.method} Not Allowed` });
    }

    // Function to write SSE data
    const sendEvent = (data) => {
        res.write(`data: ${JSON.stringify(data)}\n\n`);
    };

    const { history } = req.body;
    if (!history || !Array.isArray(history) || history.length === 0) {
        sendEvent({ type: 'error', data: { message: 'Invalid request body: Missing/invalid "history".' } });
        return res.end();
    }

    const latestMessage = history.pop(); // Remove the latest message from the history
    const query = latestMessage.parts.find(p => p.text)?.text;
    if (!query) {
        sendEvent({ type: 'error', data: { message: 'Could not find text in the latest message.' } });
        return res.end();
    }
    console.log("User query:", query);

    try {
        const onStatusUpdate = (status) => {
            sendEvent({ type: 'status', data: { status } });
        };

        const orchestrator = new Orchestrator(query, history, onStatusUpdate);
        const { finalAnswer, history: updatedHistory } = await orchestrator.run();

        sendEvent({ type: 'result', data: { text: finalAnswer, modelUsed: 'KRAMER' } });

    } catch (error) {
        console.error('KRAMER execution error:', error);
        sendEvent({ type: 'error', data: { message: 'Internal server error during KRAMER execution.', details: error.message } });
    } finally {
        res.end();
        console.log("KRAMER API handler finished.");
    }
}
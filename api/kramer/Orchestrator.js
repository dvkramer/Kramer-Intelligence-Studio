import Planner from './Planner.js';
import Executor from './Executor.js';
import Critic from './Critic.js';
import Synthesizer from './Synthesizer.js';

class Orchestrator {
    constructor(query, onStatusUpdate = () => {}) {
        this.query = query;
        this.onStatusUpdate = onStatusUpdate;
        this.plan = null;
        this.taskResults = {};
        this.planner = new Planner();
        this.executor = new Executor();
        this.critic = new Critic();
        this.synthesizer = new Synthesizer();
    }

    async run() {
        this.onStatusUpdate("Starting...");

        // 1. Planning
        this.onStatusUpdate("Planning...");
        this.plan = await this.planner.generatePlan(this.query);
        this.onStatusUpdate(`Plan created with ${this.plan.plan.length} steps.`);

        // 2. Execution Loop
        const taskQueue = [...this.plan.plan];
        let completedTasks = 0;
        const totalTasks = this.plan.plan.length;

        while (taskQueue.length > 0) {
            const task = taskQueue.shift();

            const dependenciesMet = task.dependencies.every(depId => this.taskResults[depId]);
            if (!dependenciesMet) {
                taskQueue.push(task);
                await new Promise(resolve => setTimeout(resolve, 100)); // Avoid tight loop
                continue;
            }

            const statusMessage = `Executing task ${completedTasks + 1}/${totalTasks}: ${task.description}`;
            this.onStatusUpdate(statusMessage);

            const dependencyResults = {};
            for (const depId of task.dependencies) {
                dependencyResults[depId] = this.taskResults[depId];
            }

            let result = await this.executor.executeTask(task, dependencyResults);
            this.onStatusUpdate(`Critiquing task ${completedTasks + 1}/${totalTasks}...`);
            let critique = await this.critic.critique(this.query, task, result);

            if (critique.status === 'success') {
                this.taskResults[task.id] = result;
                completedTasks++;
            } else {
                this.onStatusUpdate(`Task ${completedTasks + 1}/${totalTasks} failed critique, retrying...`);
                result = await this.executor.executeTask(task, dependencyResults);
                this.taskResults[task.id] = result; // Assume success on retry
                completedTasks++;
            }
        }

        // 3. Synthesis
        this.onStatusUpdate("Synthesizing final answer...");
        const finalAnswer = await this.synthesizer.synthesize(this.query, this.taskResults);

        this.onStatusUpdate("Done.");

        return finalAnswer;
    }
}

export default Orchestrator;

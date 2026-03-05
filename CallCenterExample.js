const SimLuxJS = require('../../SimLuxJS.js').SimLuxJS;
const SimEntity = require('../../SimLuxJS.js').SimEntity;

// Helper Functions
function exponential(mean) {
    return -mean * Math.log(Math.random());
}

function normal(mean, std) {
    let u = 0, v = 0;
    while (u === 0) u = Math.random();
    while (v === 0) v = Math.random();
    return mean + std * Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

// Simulation Parameters
const SIM_TIME = 100000;
const MAX_QUEUE = 20;
const MEAN_SERVICE = 270;
const STD_SERVICE = 60;

// Run one simulation 
async function runCallCenter(meanArrival, numAgents) {
    const sim = new SimLuxJS(false);
    const agentResource = sim.createResource(numAgents);

    let totalCustomers = 0;
    let rejectedCustomers = 0;
    let currentlyWaiting = 0; // manual counter for waiting customers

    async function customer(id) {
        totalCustomers++;

        // Check queue manually with our own counter
        if (currentlyWaiting >= MAX_QUEUE) {
            rejectedCustomers++;
            return;
        }

        currentlyWaiting++;
        let releaseAgent = await sim.waitForResource(agentResource);
        currentlyWaiting--;

        let serviceTime = normal(MEAN_SERVICE, STD_SERVICE);
        if (serviceTime < 1) serviceTime = 1;

        await sim.advance(serviceTime);
        releaseAgent();
    }

    async function arrivalGenerator() {
        let id = 0;
        while (sim.getTime() < SIM_TIME) {
            await sim.advance(exponential(meanArrival));
            id++;
            sim.addSimEntity(new SimEntity(s => customer(id)));
        }
    }

    sim.addSimEntity(new SimEntity(s => arrivalGenerator()));
    await sim.run();

    const rejectionRate = totalCustomers > 0
        ? (rejectedCustomers / totalCustomers) * 100
        : 0;

    return { totalCustomers, rejectedCustomers, rejectionRate };
}


async function main() {
    console.log("=".repeat(60));
    console.log("       CALL CENTER SIMULATION");
    console.log("=".repeat(60));

    // Ankunftsrate 100s
    console.log("\nBasisszenario (mittlere Ankunftsrate = 100s)");
    console.log(`Simulationszeit: ${SIM_TIME}s | Max. Warteschlange: ${MAX_QUEUE}`);
    console.log(`Bearbeitungszeit: Normal(${MEAN_SERVICE}s, ${STD_SERVICE}s)\n`);

    let optimalAgentsBase = null;
    for (let n = 1; n <= 10; n++) {
        const result = await runCallCenter(100, n);
        const status = result.rejectionRate < 5 ? "✓ OK (< 5%)" : "✗ zu hoch";
        console.log(
            `Agenten: ${n.toString().padStart(2)} | ` +
            `Kunden: ${result.totalCustomers.toString().padStart(5)} | ` +
            `Abgewiesen: ${result.rejectedCustomers.toString().padStart(4)} | ` +
            `Rate: ${result.rejectionRate.toFixed(2).padStart(6)}% | ${status}`
        );
        if (result.rejectionRate < 5 && optimalAgentsBase === null) {
            optimalAgentsBase = n;
        }
    }
    console.log(`\n=> Minimale Agentenanzahl (Basis 100s): ${optimalAgentsBase} Agenten`);

    // Worst-Case - Ankunftsrate 50s
    console.log("\n Worst-Case (mittlere Ankunftsrate = 50s)\n");

    let optimalAgentsWorst = null;
    for (let n = 1; n <= 10; n++) {
        const result = await runCallCenter(50, n);
        const status = result.rejectionRate < 5 ? "✓ OK (< 5%)" : "✗ zu hoch";
        console.log(
            `Agenten: ${n.toString().padStart(2)} | ` +
            `Kunden: ${result.totalCustomers.toString().padStart(5)} | ` +
            `Abgewiesen: ${result.rejectedCustomers.toString().padStart(4)} | ` +
            `Rate: ${result.rejectionRate.toFixed(2).padStart(6)}% | ${status}`
        );
        if (result.rejectionRate < 5 && optimalAgentsWorst === null) {
            optimalAgentsWorst = n;
        }
    }
    console.log(`\n=> Minimale Agentenanzahl (Worst-Case 50s): ${optimalAgentsWorst} Agenten`);

    console.log("\n" + "=".repeat(60));
    console.log("ZUSAMMENFASSUNG:");
    console.log(`  Basisszenario (100s): mind. ${optimalAgentsBase} Agenten für < 5% Abweisung`);
    console.log(`  Worst-Case    (50s):  mind. ${optimalAgentsWorst} Agenten für < 5% Abweisung`);
    console.log("=".repeat(60));
}

main().catch(console.error);
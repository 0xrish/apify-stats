import fs from 'fs';

/**
 * FETCH_ACTORS.JS (Dependency-free version)
 * This script uses Node's built-in 'fetch' to bypass npm/registry issues.
 */

async function fetchAllActors() {
    console.log('🚀 Starting Apify Store synchronization (Dependency-free mode)...');
    
    const BASE_URL = 'https://api.apify.com/v2/store';
    const LIMIT = 100;
    const DELAY_MS = 500; // Delay to be polite to the API
    let offset = 0;
    let allActors = [];
    let hasMore = true;

    const sleep = (ms) => new Promise(res => setTimeout(res, ms));

    try {
        while (hasMore) {
            console.log(`📦 Fetching batch: offset ${offset}...`);
            
            const response = await fetch(`${BASE_URL}?limit=${LIMIT}&offset=${offset}`);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Apify API responded with ${response.status}: ${errorText}`);
            }

            const json = await response.json();
            const items = json.data && json.data.items;

            if (!items || items.length === 0) {
                hasMore = false;
            } else {
                allActors = allActors.concat(items);
                console.log(`📑 Total collected: ${allActors.length}`);
                offset += items.length;
                
                if (items.length < LIMIT) {
                    hasMore = false;
                } else {
                    // Wait before next request
                    await sleep(DELAY_MS);
                }
            }
        }

        console.log(`✅ Success! Total actors fetched: ${allActors.length}`);
        
        // Save to actors.json
        fs.writeFileSync('./actors.json', JSON.stringify(allActors, null, 2));
        console.log('💾 Data saved to actors.json');

    } catch (error) {
        console.error('❌ Error fetching actors:', error.message);
        process.exit(1);
    }
}

fetchAllActors();

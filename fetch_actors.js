import fs from 'fs';

/**
 * FETCH_ACTORS.JS (Dependency-free version)
 * This script uses Node's built-in 'fetch' to bypass npm/registry issues.
 */

async function fetchAllActors() {
    console.log('🚀 Starting Apify Store synchronization (Dependency-free mode)...');
    
    const BASE_URL = 'https://api.apify.com/v2/store-actors';
    const LIMIT = 1000;
    let offset = 0;
    let allActors = [];
    let hasMore = true;

    try {
        while (hasMore) {
            console.log(`📦 Fetching actors ${offset} to ${offset + LIMIT}...`);
            
            const response = await fetch(`${BASE_URL}?limit=${LIMIT}&offset=${offset}`);
            
            if (!response.ok) {
                throw new Error(`Apify API responded with ${response.status}: ${await response.text()}`);
            }

            const data = await response.json();
            const items = data.data.items;

            if (!items || items.length === 0) {
                hasMore = false;
            } else {
                allActors = allActors.concat(items);
                offset += LIMIT;
                
                // If the API returns fewer than the limit, we've reached the end
                if (items.length < LIMIT) {
                    hasMore = false;
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
